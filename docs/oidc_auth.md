OpenID Connect (OIDC) authentication
====================================

[OpenID Connect](https://openid.net/developers/how-connect-works/) is a Single
Sign On (SSO) scheme deployed by many orgnaisations and can be used by [Vault's
JWT/OIDC auth method](https://developer.hashicorp.com/vault/docs/auth/jwt) to
defer authentication to a third party.

Low-level modules
-----------------

This collection provides the low-level
[`bbcrd.vault.oidc_configure`](../plugins/modules/oidc_configure.py) and
[`bbcrd.vault.oidc_roles`](../plugins/modules/oidc_roles.py) roles for
declaratively deploying Vault's [JWT/OIDC auth
method](https://developer.hashicorp.com/vault/api-docs/auth/jwt). Refer to the
Vault and module documentation for more details.


`bbcrd.vault.configure_oidc_auth` Simple OIDC Auth Role
-------------------------------------------------------

The [`bbcrd.vault.configure_oidc_auth`](../roles/configure_oidc_auth)
administrative role is provided which sets up basic OIDC auth based on an
explicit mapping between named OIDC users and Vault entities (e.g. Vault
users).

This role is an administrative role (see [documentation on role
conventions](./ansible_provisioning_conventions.md)). This means it should be
run against your Vault hosts and requires a root token.

The full set of variables which configure the role are documented in the
[defaults file](../roles/configure_oidc_auth/defaults/main.yml) but the most
important variables are called out below:

* `bbcrd_vault_oidc_discovery_url`: The discovery URL for the OIDC endpoint you
  wish to authenticate against. Vault must be able to reach this URL, either
  directly or via a an appropriately configured proxy.

* `bbcrd_vault_oidc_ca_pem`: The certificate authority to trust with respect to
  the OIDC service, if not publicly trusted.

* `bbcrd_vault_oidc_client_id`: The OIDC client ID assigned to your Vault
  instance.

* `bbcrd_vault_oidc_client_secret`: The OIDC client secret assigned to your
  Vault instance.

* `bbcrd_vault_oidc_extra_scopes`: A list of additional OIDC scopes to request,
  beyond the mandatory `openid` scope. These will control the set of claims the
  OIDC provider will return. For example, you may wish to add 'email'.

* `bbcrd_vault_oidc_user_claim`: The OIDC claim to use to map from OIDC users
  to Vault entities. For example 'sub' or 'email'. More discussion on this is
  provided below.

* `bbcrd_vault_oidc_user_claim_to_entity_name_mapping`: This is a dictionary
  whose keys are the OIDC claim selected by `bbcrd_vault_oidc_user_claim` and
  whose values are the corresponding Vault entity name. More discussion below.

* `bbcrd_vault_oidc_token_ttl`: The lifetime of tokens issued by the OIDC auth
  endpoint.


### Selecting an OIDC user claim

The OIDC claim named in `bbcrd_vault_oidc_user_claim` is the value which will
be used to map OIDC users to Vault entities.

The safest choice is to use the 'sub' (subject) claim -- as strongly advocated
by the OIDC specification. The sub claim is an opaque ID assigned by the OIDC
provider for each user. This ID is guaranteed to remain stable even in the
event of things like the user changing their name or email address. It is also
guaranteed not to be reused should the original owner leave.

Unfortunately sub IDs are often entirely internal to the OIDC provider and its
common for there to be no way of looking these up. As such, the only way to
obtain them is to instruct a new user to log in and then use logs or other
methods to deterine the sub ID.

Whilst it is explicitly discouraged by the OIDC specification, the 'email'
subject may be a viable option for smaller teams where it can significantly
simplify the process of enrolling users. The primary risks of using 'email' as
the user claim is that email addresses can change and can be reused. As such,
they are only safe to use when Vault administrators are aware of and able to
respond to changes in a timely manner.


### OIDC user to Vault entity mapping

Vault's [identity secrets
engine](https://developer.hashicorp.com/vault/docs/secrets/identity) is used to
map between OIDC users and Vault entities (loosely, "users"). It is by later
granting policies to these Vault entities, or adding them to groups that OIDC
users can gain access to secrets in Vault.

OIDC users are mapped to Vault entities via ['identity
aliases'](https://developer.hashicorp.com/vault/docs/concepts/identity#entities-and-aliases)
associated with the OIDC auth method. The `bbcrd.vault.configure_oidc_auth`
declaratively sets up the entity aliases for the OIDC auth method according to
the mapping in `bbcrd_vault_oidc_user_claim_to_entity_name_mapping`. Entities
which don't yet exist are created automatically.

Any entity aliases not included in
`bbcrd_vault_oidc_user_claim_to_entity_name_mapping` are removed. As a result,
if the removed user attempts to authenticate again, their account will no
longer be matched to their old Vault entity and they will therefore not be
granted any privileges.

Slightly confusingly, users attempting to authenticate with Vault who do not
have an entity alias configured mapping them to a Vault entity are still issued
tokens by Vault. In this scenario, Vault generates a randomly-named entity and
corresponding entity alias automatically. Because these auto-generated entities
do not belong to any groups or hold any policies, the resulting token will only
have access to the `default` policy. This policy allows the user to do little
more than lookup and revoke their own token and so access to Vault secrets is
effectively denied. If a user is later added to
`bbcrd_vault_oidc_user_claim_to_entity_name_mapping`, the auto-generated entity
alias will be replaced with a new one pointing to a real (non-auto generated)
Vault entity.


### Granting policies to OIDC authenticated users

See the [Identity (entity and group) management
documentation](./identity_modules.md) for details of how to create and manage a
group which grants access to Vault secrets to a specified set of entities.


#### Authenticating with Vault

You can authenticate with Vault using OIDC by running:

    $ vault login -method=oidc

Alternatively, this collection includes the [`utils/vault_auth.py`
script](../utils/vault_auth.py) which wraps this command, along with commands
to [sign the users' SSH key using Vault](./ssh_client_key_signing.md).


### OIDC authentication and headless machines

Because OIDC login requires an interactive browser session, it is generally not
possible to use the OIDC login flow on headless remote hosts. If you need to
access vault from such a host, one option is to copy a vault token from your
workstation to that host. The
[`utils/vault_token_send.sh`](../utils/vault_token_send.sh) script is provided
for this purpose and can be used like so:

    $ ./utils/vault_token_send.sh user@host.example.com

> **Warning:** Because your Vault token is sensitive and personal to you, you
> should only use this script for personal (non-shared) remote accounts.
