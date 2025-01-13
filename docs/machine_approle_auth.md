Machine based auth using AppRoles
=================================

Vault's [AppRole auth
method](https://developer.hashicorp.com/vault/docs/auth/approle) provides a
mechanism for automated systems (e.g. CI systems or automated processes) to
authenticate with Vault.


AppRole auth primer
-------------------

AppRole auth is, essentially, a more sophisticated username and password
authentication flow. During AppRole based authentication a role ID (nee
username) and secret ID (nee password) are presented in exchange for a Vault
token.

The principal difference between AppRole and simple username/password
authentication is how the secret IDs (i.e. passwords) are created and
distributed.

Secret IDs are generally issued by Vault, rather than being chosen by the user.
Through the careful use of [response
wrapping](https://developer.hashicorp.com/vault/docs/concepts/response-wrapping)
it is possible to verifiably distribute secret IDs to a host without any other
host -- including the issuer -- having access to them.

Furthermore, each AppRole role ID (i.e. username) may have multiple valid
secret IDs at once. Since secret IDs can optionally have a finite lifetime this
allows secrets to be rotated with a grace period where both old and new secret
IDs can be used.

> **Note:** The higher-level modules and roles in this collection, however,
> make relatively simple use of AppRole auth which don't exploit all of these
> features.

As a final note, it is a common pattern to have multiple AppRole auth methods
mounted at once in Vault, for example one per class of machine user. By doing
this it becomes straightforward to declaratively manage the set of permitted
role IDs for each class of user.


Low-level modules
-----------------

The [`bbcrd.vault.vault_approles` module](../plugins/modules/vault_approles.py)
can be used to create an AppRole auth method and declaratively define the list
of roles within it.

The [`bbcrd.vault.vault_approle_secret`
module](../plugins/modules/vault_approle_secret.py) can be used to generate
secret IDs for existing roles.


High-level roles
----------------

This collection provides a pair of high level roles which wrap the modules
above for handling the common-case of issuing machine credentials to Ansible
hosts.

The [`bbcrd.vault.configure_approle_auth`
role](../roles/configure_approle_auth) is an administrative role (see
[documentation on role conventions](./ansible_provisioning_conventions.md))
which configures an AppRole auth method. It creates role IDs for each Ansible
host in the Ansible group named by `bbcrd_vault_approle_ansible_group_name`. It
also creates a Vault policy which allows generation of secret IDs for these
roles.

The [`bbcrd.vault.issue_approle_credentials`
role](../roles/issue_approle_credentials) is a secret deployment role (see
[documentation on role conventions](./ansible_provisioning_conventions.md))
which can be included in the playbooks which manage the hosts needing to
authenticate with Vault. It is responsible for generating secret IDs and
writing them, along with the corresponding role ID, into a JSON file on the
target host. This can then be used by services running on that host to
authenticate with Vault.

The [`bbcrd.vault.install_vault_auth` role](../roles/install_vault_auth)
deploys the [`vault_auth.py`](../../utils/vault_auth.py) script on a host and
optionally sets up a systemd timer which runs it on a regular basis using a set
of app role credentials installed by (e.g.)
[`bbcrd.vault.issue_approle_credentials`
role](../roles/issue_approle_credentials).


### Configuring machine auth

As usual, the [defaults defined by the `bbcrd.vault.configure_approle_auth`
role](../roles/configure_approle_auth/defaults/main.yml) document the full set
of options for the role. Below we highlight the most significant variables and
walk through a sample configuration for a typical machine based authentication
setup.

In our example setup we'll define two AppRole auth endpoints for two different
groups of hosts. One group will be Jenkins CI agents which require access to
secrets and SSH signing. The other group will be for hosts running backup
processes which only requires SSH signing permissions. The Jenkins hosts are
identified by being in the `jenkins_group` Ansible group. The backup hosts will
be in the `backup_group`.

In this example setup, we'll use the `bbcrd.vault.configure_approle_auth` role
twice to create the two different AppRole auth mount points, one for the
Jenkins agents (`jenkins_agent_auth`) and the other for the backup hosts
(`backup_auth`).

#### Configuring AppRole role parameters

The configuration for each AppRole role (i.e. machine user) is defined in the
`bbcrd_vault_approle.<AppRole mount>` variable.

We start by defining the
base role configuration in our Vault cluster's group vars.  (Remember the
`bbcrd.vault.configure_approle_auth` role is an administrative role so [by
convention](./ansible_provisioning_conventions.md) we'll run it on the Vault
cluter nodes.

We can then override values on a host-by-host basis by defining
`bbcrd_vault_approle` in the host vars of the respective hosts we're
configuring.

```
# In Vault cluster's group vars:
bbcrd_vault_approle:
  jenkins_agent_auth:
    token_ttl: 3600  # 1 hour
    token_max_ttl: 3600  # 1 hour
    token_policies:
      - "ssh-sign"
      - "kv-read-only"
  backup_hosts_auth:
    token_ttl: 60  # 1 minute
    token_max_ttl: 60  # 1 minute
    token_policies:
      - "ssh-sign"
```

```
# In the jenkins_group group vars:
bbcrd_vault_approle:
  jenkins_agent_auth:
    # For reasons known only to Vault, token_bound_cidrs ending in `/32` is
    # normalised by Vault to not include the `/32` whilst secret_id_bound_cidrs
    # isn't. To avoid spurious change reports, we must match Vault's
    # normalisation...
    secret_id_bound_cidrs: ["{{ ansible_default_ipv4 }}/32"]
    token_bound_cidrs: ["{{ ansible_default_ipv4 }}"]
```

```
# In the backup_group group vars:
bbcrd_vault_approle:
  backup_auth:
    secret_id_bound_cidrs: ["{{ ansible_default_ipv4 }}/32"]
    token_bound_cidrs: ["{{ ansible_default_ipv4 }}"]
```


In our example we've used `token_policies` to specify the policies which will
be granted to the tokens issued by our app roles. Assuming the existance of the
policies in this example, our Jenkins agents will get access to our key value
store and access to SSH key signing. Our backup hosts, however, only gain
access to SSH key signing.

We're using the `token_ttl` and `token_max_ttl` to restrict the lifetime of
tokens issued after authenticating. Here we've chosen a one hour lifetime for
the Jenkins hosts (e.g. to allow access to secrets for the full runtime of a
long-running job). Conversely for the backup hosts we might choose a very short
lifetime as the only thing their token would be used for is to sign an SSH key
immediately after authentication.

Next, we're refining the role (user) parameters on a host-by-host basis by
specifying the `secret_id_bound_cidrs` and `token_bound_cidrs` variables within
`bbcrd_vault_approle` in the groupvars of our Jenkins and backup hosts. Here we
restrict the use of the AppRole and the generated tokens to only the IP address
of that server. (Note that you must have gathered facts on these servers for
this specific example to work!)

> **Warning:** The `ansible_default_ipv4` fact used in this exampmle doesn't
> always contain what you think it might -- and if you're using dynamic
> addressing this approach won't work for you at all! In a real implementation
> you might choose a variable which you've used to define the hosts' static IP
> address or even just set a loose CIDR for the appropriate subnet.

See the [Vault documentation on role
parameters](https://developer.hashicorp.com/vault/api-docs/auth/approle#parameters)
for the parameters available.


#### Creating AppRole auth methods

With our AppRole configuration data in place, the following role invocations
(running against our Vault cluster) will deploy our two AppRole auth methods
and the roles within them:


    - name: Configure AppRole for Jenkins agent authentication
      import_role:
        name: bbcrd.vault.configure_approle_auth
      vars:
        bbcrd_vault_approle_mount: "jenkins_agent_auth"
        bbcrd_vault_approle_ansible_group_name: "jenkins_group"
    
    - name: Configure AppRole for backup host authentication
      import_role:
        name: bbcrd.vault.configure_approle_auth
      vars:
        bbcrd_vault_approle_mount: "backup_auth"
        bbcrd_vault_approle_ansible_group_name: "backup_group"

Here we're setting the `bbcrd_vault_approle_mount` to the name of the AppRole
auth's mount name in Vault -- matching the entries in our `bbcrd_vault_approle`
variables.

The `bbcrd_vault_approle_ansible_group_name` gives the name of the Ansible
groups defining the hosts to create AppRole roles (users) for.


### Issuing secret IDs

The [`bbcrd.vault.issue_approle_credentials`
role](../roles/issue_approle_credentials) pairs up with the
`bbcrd.vault.configure_approle_auth` role to generate secret IDs and deploy
AppRole credentials files to hosts.

As a secret deployment role (see [documentation on role
conventions](./ansible_provisioning_conventions.md)), this role should be run
against the hosts you wish to deploy AppRole credentials to. The role will
interact with Vault using the configuration and credentials available on the
Ansible control node -- i.e. your personal Vault token. (See the
[defaults](../roles/issue_approle_credentials/defaults/main.yml) for details).

> **Hint:** As well as configuring the AppRole auth method, the
> `bbcrd.vault.configure_approle_auth` role also creates a Vault policy named,
> by default, `approle_<AppRole mount name>_admin`. This policy grants the
> holder the ability to look up role IDs and generate secret IDs for the
> AppRole roles configured by the `bbcrd.vault.configure_approle_auth` role.
> Continuing the example started above, this means the following pair of
> policies would be created:
>
> * `approle_jenkins_agent_auth_admin`
> * `approle_backup_auth_admin`
>
> By assigning these policies to your day-to-day Vault account you will have
> the necessary rights to run the `bbcrd.vault.issue_approle_credentials` role.

The `bbcrd.vault.issue_approle_credentials` role requires
`bbcrd_vault_approle_mount` to be set to the name of the AppRole mount point,
but all other options can be left at their
[defaults](../roles/issue_approle_credentials/defaults/main.yml) in most cases.

You can then add the `bbcrd.vault.issue_approle_credentials` role to your host
playbooks. This will create a file named `/etc/vault_approle_<AppRole mount
name>_credentials.json` on each host. This will contain a JSON object which
looks as follows:

    {
        "approle_mount": "jenkins_agent_auth",
        "role_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "secret_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "secret_id_accessor": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }

The fields contain:

* `approle_mount` -- The AppRole auth mountpoint
* `role_id` -- The role ID.
* `secret_id` -- The secret ID.
* `secret_id_accessor` -- The secret ID accessor. This is used by the
  `bbcrd.vault.issue_approle_credentials` role to detect when a secret ID has
  been revoked so that it knows to issue a new one. It is not required for
  AppRole auth.


### Authenticating with AppRole auth

Slightly scruffily, there is no `vault login` argument for authenticating with
AppRole auth. Instead you manually send a POST (or 'write' in Vault terms) to
the `auth/<AppRole mount name>/login` endpoint ([read more in the Vault
docs](https://developer.hashicorp.com/vault/api-docs/auth/approle#login-with-approle)).
This can be done manually using the `vault` command line tool like so:

    $ CREDENTIALS=/etc/vault_approle_jenkins_agent_auth_credentials.json
    $ ROLE_ID="$(jq -r .role_id "$CREDENTIALS")"
    $ APPROLE_MOUNT="$(jq -r .approle_mount "$CREDENTIALS")"
    $ jq -r .secret_id "$CREDENTIALS" \
        | vault write \
            -field token \
            "auth/$APPROLE_MOUNT/login" \
            role_id="$ROLE_ID" \
            secret_id=- \
        | vault login -

More conveniently, perhaps, this collection includes the [`utils/vault_auth.py`
script](../utils/vault_auth.py) which, when used with the `--app-role`
argument, performs the above steps, along with commands to [sign the users' SSH
key using Vault](./ssh_client_key_signing.md). For example:

    $ ./utils/vault_auth.py --app-role=/etc/vault_approle_jenkins_agent_auth_credentials.json

The [`bbcrd.vault.install_vault_auth` role](../roles/install_vault_auth) can be
used to install the [`vault_auth.py`](../../utils/vault_auth.py) script on a
host and set up a systemd timer which runs it on a regular basis.
