The `bbcrd.vault.manage_vault_cluster` playbook (and friends)
=============================================================

The [`bbcrd.vault.manage_vault_cluster`
playbook](../playbooks/manage_vault_cluster.yml) (and the roles it calls) take
care of the tasks involved in building and looking after a Vault cluster. As
well as installation and initialisation it also handles ongoing maintainace
tasks such as:

* Unsealing vault
* Performing rolling (zero downtime) upgrades
* Manging rotation of unseal keys as team members join or leave
* Manging cluster membership

It also configures a limited set of baseline Vault features which are likely to
be used in any deployment. These include:

* Enabling audit logging
* Generation of policies permitting common system administration tasks
* Automated database (and encrypted unseal key) backups

It is intended that this collection of playbooks and roles will be applicable
to a wide range of different Vault deployments.

The `bbcrd.vault.manage_vault_cluster` playbook does *not* configure any
secrets engines or auth methods. Those tasks are deferred to [other roles and
modules in the
collection](./README.md#vault-service-provisioning-and-configuration) which can
be picked-and-mixed depending on the needs of an individual deployment. These
will not be discussed further here.


Configuration
-------------

Though each role called by the [`bbcrd.vault.manage_vault_cluster`
playbook](../playbooks/manage_vault_cluster.yml) has its own set of defaults
which you may override, there are a number of variables which almost all
deployments are likely to need to set. The following non-exhaustive list
enumerates some of the more significant ones.

From the [`bbcrd.vault.common_defaults`
role](../roles/common_defaults/defaults/main.yml) inherited by most roles in
this playbook:

* `bbcrd_vault_cluster_ansible_group_name`: This must be set to the name of the
  Ansible group identifying the set of hosts which will make up your Vault
  cluster.

* `bbcrd_vault_public_url`: This must be set (for each host) to the publicly
  reachable URL of the vault API. Specifically, it must be set individually for
  each host to point at that host's URL, rather than (e.g.) a shared VIP. See
  the [VIP and HTTPS certificate management
  documentation](./vip_and_https_certificate_management.md) for further
  discussion on how to expose your Vault endpoints to the network.

* `bbcrd_vault_ca_path`: If your vault server's API HTTPS certificate is not
  signed by a publicly trusted certificate authority, this must be the path of
  the relevant certificate root PEM file on each host.

* `bbcrd_vault_administrators`: Enumerates the administrators of the vault
  cluster -- the people who will be issued unseal keys. More specifically this
  variable enumerates each administrator's PGP keys and the number of unseal
  keys to be issued. Read more about how unseal keys are managed in the [unseal
  key management documentation](./unseal_key_management.md).

* `bbcrd_vault_unseal_key_threshold`: Specifies the number of unseal keys which
  are required to unseal Vault (or generate root tokens). See above.

Make sure to peruse the `defaults/main.yml` files of each of the roles in the
playbook (as well as the `bbcrd.vault.common_defaults` role) for complete
documentation of all available settings.


Calling the playbook/roles
--------------------------

Assuming that all of the required configuration variables are set as Ansible
group or host vars, you can run the playbooks in this colletion directly using
`ansible-playbook`:

    $ ansible-playbook bbcrd.vault.manage_vault_cluster -e bbcrd_vault_cluster_ansible_group_name=my_group_name

If your vault cluster's Ansible group is named 'vault', you can omit the `-e
...` argument in the example above.

Alternatively you can import the playbook from your own playbooks using (at
the top-level -- not task level -- of your playbook):

    - name: Deploy/manage vault cluster, unseal keys etc.
      import_playbook: bbcrd.vault.manage_vault_cluster
      
      become: true  # If required by your hosts
      
      # Optional: only required if your group is not called 'vault'
      vars:
        bbcrd_vault_cluster_ansible_group_name: my_group_name

Equally, if you prefer you could directly call (a subset of) the roles as
illustrated in the playbook. Note that the ordering of these roles is often
significant -- for example, initialising and unsealing the cluster must come
before most other tasks!


Installation and ongoing cluster management
-------------------------------------------

Assuming you're using a Yubikey (or other PGP device) (see [unseal key
management documentation](./unseal_key_management.md)) an administrator can
install, unseal, upgrade and manage membership of the vault cluster by
inserting their Yubikey and running the playbook.

The playbook will then perform the following sequence of steps (which
correspond to the various roles it calls):

* **Create an ephemeral GnuPG environment.**
  ([`bbcrd.vault.ephemeral_gnupg_home` role](../roles/ephemeral_gnupg_home))
  
  The inserted Yubikey will be detected and matched to the corresponding public
  key in the `bbcrd_vault_administrators` variable. You will also be prompted
  for the PIN. (See [unseal key management
  documentation](./unseal_key_management.md)).
  
  Skip with `--skip-tags bbcrd_vault_ephemeral_gnupg_home`.

* **Install Vault.** ([`bbcrd.vault.install` role](../roles/install))

  Skip with `--skip-tags bbcrd_vault_install`.

* **Write Vault server configuration.** ([`bbcrd.vault.configure_server`
  role](../roles/configure_server))
  
  Skip with `--skip-tags bbcrd_vault_configure_server`.

* **Initialise first cluster node and generate first unseal keys.**
  ([`bbcrd.vault.init_first_node` role](../roles/init_first_node))
  
  The encrypted unseal keys are written to the host's disk (See [unseal key
  management documentation](./unseal_key_management.md)). Skipped if at least
  one cluster node is already initialised.
  
  Skip with `--skip-tags bbcrd_vault_init_first_node`.

* **Fetch and decrypt encrypted unseal keys.**
  ([`bbcrd.vault.decrypt_unseal_keys` role](../roles/decrypt_unseal_keys))
  
  Skip with `--skip-tags bbcrd_vault_decrypt_unseal_keys`.

* **Unseal cluster members and join new nodes into the cluster.**
  ([`bbcrd.vault.unseal` role](../roles/unseal))
  
  See [unseal key management documentation](./unseal_key_management.md).
  
  Skip with `--skip-tags bbcrd_vault_unseal`.

* **Propagate encrypted unseal keys file to new nodes in the cluster.**
  ([`bbcrd.vault.propagate_unseal_keys` role](../roles/propagate_unseal_keys))
  
  Skip with `--skip-tags bbcrd_vault_propagate_unseal_keys`.

* **Generate an (ephemeral) root token using unseal keys.**
  ([`bbcrd.vault.generate_root` role](../roles/generate_root))
  
  This token will be used to perform subsequent administrative actions.
  
  Explicitly skip using `--skip-tags bbcrd_vault_generate_root`.

* **Permenently remove old cluster members.**
  ([`bbcrd.vault.remove_old_cluster_nodes`
  role](../roles/remove_old_cluster_nodes))
  
  That is, any nodes which aren't members of the Ansible group named by
  `bbcrd_vault_cluster_ansible_group_name`. The role will carefully order node
  removals to avoid outages if it is possible to do so. If removing a node from
  the cluster would make the cluster lose quorum (e.g. as too many of the
  remaining nodes are down) an error will be produced by default. See the
  [cluster management documentation](./cluster_management.md) for more
  information.
  
  Skip using `--skip-tags bbcrd_vault_remove_old_cluster_nodes`.

* **Perform a rolling (zero downtime) server restart if needed.**
  ([`bbcrd.vault.restart` role](../roles/restart))
  
  For example, to complete a Vault server upgrade or apply a new configuration.
  Otherwise, servers are not restarted.  You can force a restart by setting
  `bbcrd_vault_restart` to True for the servers which you wish to restart. Once
  restarted, each server will be unsealed. The role defaults to failing if
  restarting a server would bring the cluster out of quorum leading to an
  outage.
  
  Skip using `--skip-tags bbcrd_vault_restart`.

* **Rekey the unseal keys if administrators have changed.**
  ([`bbcrd.vault.rekey` role](../roles/rekey))
  
  If an administrator is added, removed or modified in
  `bbcrd_vault_administrators`, Vault will be rekeyed and the new encrypted
  unseal keys are written to the vault hosts.  (See [unseal key management
  documentation](./unseal_key_management.md)). The new keys are verified during
  this process and the keys are only rotated if the new keys can be
  successfully used. This reduces the chances of becoming locked out of Vault. By
  default you must interactively confirm the change in unseal key holders to
  reduce the chances of a malicious change being applied by accident.
  
  Skip rekeying using `--skip-tags bbcrd_vault_rekey`.

* **Configure automatic backups.** ([`bbcrd.vault.configure_backups`
  role](../roles/configure_backups))
  
  By default one week worth of hourly backups will be retained in
  `/var/lib/vault_backup`. Each backup contains a snapshot of the encrypted
  Vault database along with the corresponding encrypted unseal keys.
  Propagating these backups to suitable external (and ideally off-site) storage
  is left as an excercise. See the [disaster recovery
  documentation](./backups_and_disaster_recovery.md) for more details.
  
  Skip using `--skip-tags bbcrd_vault_configure_backups`.

* **Enable the audit log.** ([`bbcrd.vault.configure_auditing`
  role](../roles/configure_auditing))
  
  Simple [audit logging](https://developer.hashicorp.com/vault/docs/audit) will
  be enabled to the leader Vault node's stdout.
  
  Skip using `--skip-tags bbcrd_vault_configure_auditing`.

* **Create generic system administration policies.**
  ([`bbcrd.vault.system_policies` role](../roles/system_policies))
  
  These general-purpose administrative policies provide access to various Vault
  system interfaces commonly used by adminstrators or monitoring
  infrastructure. You are free to add these to tokens/entities/groups as
  required. See the [`bbcrd.vault.system_policies`
  role](../roles/system_policies/defaults/main.yml) for more details.
  
  Skip using `--skip-tags bbcrd_vault_system_policies`.

* **Revoke generated root tokens and delete ephemeral GnuPG environments.**
  ([`bbcrd.vault.generate_root` role](../roles/generate_root) 
  and [`bbcrd.vault.ephemeral_gnupg_home` role](../roles/ephemeral_gnupg_home)
  again)
  
  Skip using `--skip-tags bbcrd_vault_revoke_root_token` and `--skip-tags
  bbcrd_vault_ephemeral_gnupg_home`.


Multi-administrator key submission
----------------------------------

If you have chosen to require multiple administrators to supply their unseal
keys to unseal Vault (and generate root tokens) the
[`bbcrd.vault.supply_additional_keys`](../playbooks/supply_additional_keys.yml)
playbook can be used by colleagues to supply their keys. The workflow in this
setup is as follows:

1. The first administrator runs the `bbcrd.vault.manage_vault_cluster` playbook
   as usual.

2. When the playbook needs to use an unseal key (e.g. during unsealing or root
   token generation), the playbook will pause and wait for more unseal keys to
   be supplied. For most operations a nonce will be shown. The first
   administrator should share this nonce with the second administrator.

3. The second administrator should now run the
   `bbcrd.vault.supply_additional_keys` playbook. This will work out what needs
   to be done and ask the second administrator to confirm that the nonce
   matches the expected value before their unseal keys are submitted.

4. Once the additional unseal keys have been submitted, the first
   administrators playbook will automatically continue.
   
   Steps 2 and 3 must be repeated as necessary until the
   `bbcrd.vault.manage_vault_cluster` playbook completes. Depending on the
   number of unsealing or root token generation operations needed this may be
   several times.

If more than two people are required to submit unseal keys, additional
administrators should take it in turns to run the
`bbcrd.vault.supply_additional_keys` playbook. Do not run it in parallel.

Like the `bbcrd.vault.manage_vault_cluster` playbook, you can run the
`bbcrd.vault.supply_additional_keys` playbook either from the command line:

    $ ansible-playbook bbcrd.vault.supply_additional_keys -e bbcrd_vault_cluster_ansible_group_name=my_group_name

Or from another playbook:

    - name: Supply additional unseal keys
      import_playbook: bbcrd.vault.supply_additional_keys
      become: true
      vars:
        bbcrd_vault_cluster_ansible_group_name: my_group_name


Root token generation for manual/emergency administration
---------------------------------------------------------

The [`bbcrd.vault.generate_root_token`
playbook](../playbooks/generate_root_token.yml) can be used to generate (and
display) a root token for interactive use using unseal keys. This token can be
used to manually perform administrative tasks -- though ideally these should be
performed in your own playbooks instead!

Like the other playbooks, you can run this playbook from the shell:

    $ ansible-playbook bbcrd.vault.generate_root_token -e bbcrd_vault_cluster_ansible_group_name=my_group_name

Or from another playbook:

    - name: Generate a root token
      import_playbook: bbcrd.vault.generate_root_token
      become: true
      vars:
        bbcrd_vault_cluster_ansible_group_name: my_group_name

Once the root token has been generated, the playbook will run `vault login`
(writing the token to your `~/.vault-token`) and display the root token on
screen.

Pressing enter (or killing the playbook with Ctrl+C) will cause the token to be
revoked. The generated root token also has a finite (by default 8 hour) TTL.
These precautions reduce the chances of a generated root token accidentally
persisting.
