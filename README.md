`bbcrd.ansible_vault` Collection
================================

A collection for deploying and managing Hashicorp Vault/OpenBao clusters.

**A work in progress.**

Deployment and cluster management playbooks and roles
-----------------------------------------------------

A number of playbooks and roles are provided which implement a generic Vault
cluster deployment and management tasks. These are likely to be useful for most
Vault deployments.

The relevant playbooks are:

* `bbcrd.ansible_vault.manage_vault_cluster`: Setup and manage a Vault cluster.
  Handles installation, unsealing nodes, managing cluster membership, rolling
  upgrades, backups and unseal key management. Is *not* responsible for the
  configuration of secrets engines, authentication methods and so on.

* `bbcrd.ansible_vault.supply_additional_keys`: Submit additional unseal keys
  to assist another vault administrator running one of the "main"
  roles/playbooks. Needed only when the unseal key threshold is more than than
  the number of unseal keys held by an individual administrator.

* `bbcrd.ansible_vault.generate_root_token`: Generate an ephemeral root token
  for the vault cluster using unseal keys.

* `bbcrd.ansible_vault.decrypt_unseal_keys_file`: Decrypts an encrypted unseal
  keys file (e.g. extracted from a backup archive) for disaster recovery
  purposes. (See also: `utils/run_disaster_recovery_vault_server.py`).

The following roles implement the tasks within the playbooks above and may, if
desired, be used independently:

* `bbcrd.ansible_vault.install`: Installs Vault from a public binary release.
* `bbcrd.ansible_vault.configure_server`: Generate vault cluster configuration files.
* `bbcrd.ansible_vault.init_first_node`: Initialise the very first node in a
  brand new vault cluster. (Does nothing if the cluster is already
  initialised).
* `bbcrd.ansible_vault.unseal`: Unseal all vault nodes, also causing any
  brand-new nodes to join the cluster.
* `bbcrd.ansible_vault.propagate_unseal_keys`: Propagates the encrypted unseal
  keys file to all hosts which don't currently have a copy of it -- i.e. newly
  created nodes.
* `bbcrd.ansible_vault.remove_old_cluster_nodes`: Removes any  nodes from the
  Vault cluster which do not have a corresponding host in the Ansible data.
* `bbcrd.ansible_vault.restart`: Restart and unseal vault cluster members in a
  rolling fashion.
* `bbcrd.ansible_vault.rekey`: Rekey vault with a new set of unseal keys.
* `bbcrd.ansible_vault.configure_backups`: Configures automated backups of the
  vault database and encrypted unseal keys.
* `bbcrd.ansible_vault.enabled_audit_log`: Enables audit logging.

There are also a some lower level roles which are in some cases used by the
above roles but which might also be useful in isolation.

* `bbcrd.ansible_vault.generate_root`: Generate an (ephemeral) root token using
  unseal keys.
* `bbcrd.ansible_vault.decrypt_unseal_keys`: Decrypts unseal keys.
* `bbcrd.ansible_vault.ephemeral_gnupg_home`: Creates a temporary GnuPG home
  directory on the Ansible control node, isolated from the user's own GnuPG
  environment.


Vault secrets engine provisioning roles and modules
---------------------------------------------------

Whilst the manner of deployment of vault clusters may be common betwen Vault
deployments, the provisioning of secrets engines, identities and policies is
not. As a result, this collection only provides a selection of potentially
useful Ansible roles and modules though these are very far from complete.

In brief, the available roles are:

* `bbcrd.ansible_vault.configure_kv_secrets_engine` -- Deploys an empty KV
  secrets engine.
* `bbcrd.ansible_vault.configure_oidc_auth` -- Setup basic OpenID Connect based
  single-sign-on (SSO) authentication for vault.
* `bbcrd.ansible_vault.configure_ssh_client_signer` -- Setup a simple SSH
  client certificate signing secrets engine.

The available modules are:

* Policy management
  * `bbcrd.ansible_vault.vault_policy` -- Create vault policies.
* Secret/auth/audit engine management
  * `bbcrd.ansible_vault.vault_audit` -- Configure auditing engines.
  * `bbcrd.ansible_vault.vault_auth_method` -- Enable and configure auth methods.
  * `bbcrd.ansible_vault.vault_secrets_engine` -- Enable or configure secrets
    engines.
* Entity/Group management
  * `bbcrd.ansible_vault.vault_auth_method_entity_aliases` -- Configure entity
    alias mappings for a particular auth method. (That is, map auth method users
    to Vault entities).
  * `bbcrd.ansible_vault.vault_group` -- Create and configure vault (entity) groups.
  * `bbcrd.ansible_vault.vault_entity` -- Create and configure entities.
* AppRole auth configuration
  * `bbcrd.ansible_vault.vault_approles` -- Manage the set of roles for an
    AppRoles auth endpoint.
  * `bbcrd.ansible_vault.vault_approle_secret` -- Generate (or set) AppRole
    secret IDs.
* OIDC Auth configuration
  * `bbcrd.ansible_vault.vault_oidc_configure` -- Configure the OIDC auth method.
  * `bbcrd.ansible_vault.vault_oidc_roles` -- Configure roles for the OIDC auth
    method.
* SSH Secrets engine configuration
  * `bbcrd.ansible_vault.vault_ssh_signer` -- Configure the SSH signer secrets
    engine.


Common default variables
------------------------

The majority of roles automatically pull in the common default variable values
defined in the otherwise empty `bbcrd.ansible_vault.common_defaults` role.


Unseal key management
---------------------

This collection is regrettably, but necessarily, somewhat opinionated with
respect to the [management of unseal
keys](https://developer.hashicorp.com/vault/docs/concepts/seal). Unseal key
management for Vault is a complex topic with a wide range of possible solutions
each with its own substantial implications for any kind of automation. This
collection specifically chooses [a particular PGP-based workflow for unseal key
management](https://developer.hashicorp.com/vault/docs/concepts/pgp-gpg-keybase).
This workflow was designed with the intent of maximising the usability and
security in a non-public-cloud based, open source Vault deployment.

<details>
<summary><strong>Why PGP-based unseal key storage?</strong></summary>

> Vault's PGP support greatly simplifies the process of securely generating and
> distributing unseal keys. By using public key cryptography to encrypt each
> unseal key, no one person is ever responsible for, nor has the opportunity,
> to hold more than their share of the unseal keys.
>
> By providing a PGP public key for each key holder, Vault returns the newly
> generated unseal key shares encrypted with those keys. These can then be
> stored or distributed without any particular precautions.
>
> This roles in this collection store the encrypted keys alongside the Vault
> data directory.  Since this directory is already (necessarily) accessible to
> all vault administrators this completely avoids the need to explicitly
> *distribute* the keys to the other administrators. This also removes the need
> to coordinate with all administrators during rekeying, making it possible to
> be carried out more regularly.
>
> Alternative unseal key management strategies include HSM or cloud-service
> based automatic unsealing mechanisms. Since these options depend on either
> Vault Enterprise or proprietary public cloud infrastructure, these are not a
> viable option in many settings. Further, the problem of managing recovery
> keys in this setting is essentially the same as managing unseal keys.
>
> The other major alternative -- managing unencrypted unseal keys manually --
> typically results in an ad-hoc solution along the same lines as the PGP-based
> solution. This, however, offers strictly worse security guarantees because
> all of the unseal keys end up in one place in plain-text at the point of
> rekeying.

</details>

Each Vault administrator must supply a PGP public key. When Vault's unseal keys
are (re)generated, Vault uses these public keys to encrypt the unseal key
shards. These encrypted shards are then stored into the file
`/etc/vault/encrypted_unseal_keys.json` (by default) on every cluster host.
Its structure is as follows:

    {
      # The time at which the unseal keys were (re)generated
      "timestamp": "2024-08-01T07:56:07Z",
      # The enecrypted unseal key shares
      "shares": [
        {
          # The key of ansible_vault_administrators where the public key used
          # to encrypted this key share came from. (For information only).
          "user": "...",
          # The ASCII Armor encoded PGP public key, reproduced from
          # ansible_vault_administrators.
          "public_key": "...",
          # The full name field extracted from the public key (for information
          # only)
          "name": "...",
          # The keypair's fingerprint extracted from the public key (for
          # information only)
          "fingerprint": "...",
          # A (non-ASCII Armored, plain) base64-encoded encrypted unseal key
          # share, encrypted using the public key above.
          "encrypted_unseal_key": "..."
        },
        ...
      ]
    }

This file must be be backed up and treated with the same level of care as the
main Vault database. Since previous unseal keys are invalidated when the
database is rekeyed, it is essential that backups of the Vault database must be
kept in sync with backups of the encrypted unseal keys.

<details>
<summary><strong>On keeping encrypted keys in sync between cluster nodes.</strong></summary>

> Unlike the Vault database (which is kept consistent using a sophisticated
> distributed consensus algorithm), this collection's roles are responsible for
> ensuring all cluster members have a consistent copy of the encrypted unseal
> keys. Roles by default, therefore, behave extremely cautiously.
>
> Firstly, by default, *all* members of the cluster must be up to perform a
> rekeying operation. This is intended to prevent different cluster members
> from holding stale (and inconsistent) encrypted key files. If missing members
> of the cluster cannot be brought up when rekeying is performed, this check
> can be disabled (using `ansible_vault_skip_rekey_sanity_check`). In this
> case, however, it is the operator's responsibility to ensure that the updated
> encrypted key files are propagated correctly once machines have been brought
> back into service.
>
> Newly added cluster members automatically receive a copy of the current
> encrypted unseal key file when they're joined to the cluster. Otherwise
> existing unseal keys are never cross-copied between nodes to avoid accidental
> inconsistencies. Otherwise, encrypted unseal key files are only overwritten
> as a result of rekeying.
>
> When fetching encrypted unseal keys, the available cluster members' encrypted
> unseal key files are checked for consistency and it is the operator's
> responsibility to resolve any inconsistencies.
>
> The encrypted unseal key file is intended to contain as much information as
> possible to aid in resolving any inconsistencies. As a further precaution,
> this backups are made of any existing encrypted unseal key files before
> writing a new ones. This is intended to assist in the event manual recovery
> is necessary.
>
> Finally, when new keys are generated, the encrypted unseal key data is always
> printed in the Ansible logs. In the unlikely event that the encrypted unseal
> keys are not successfully written, the operator must take care to store and
> propagate the keys manually.

</details>

Whenever an unseal key is required by any of the roles in this playbook, the
encrypted unseal keys are automatically fetched and decrypted using the
`bbcrd.ansible_vault.decrypt_unseal_keys` role. This internally uses [GnuPG
(GPG)](https://www.gnupg.org/) on the Ansible deployment host to decrypt any
unseal keys for which a matching private key exists in the local GnuPG
database.

<details>
<summary><strong>On using GnuPG and PGP cards (e.g. Yubikeys).</strong></summary>

> [GnuPG (GPG)](https://www.gnupg.org/) is a popular open source implementation
> of the PGP standard. This includes support for hardware security devices
> which implement the PGP Card standard. This includes
> [Yubikeys](https://www.yubico.com/products/yubikey-5-overview/). These
> devices can be used to securely (and irretrievably) store a PGP private key.
> This acts as a secure second factor for accessing your private key, and
> therefore an encrypted unseal key.
>
> As part of the wider PGP ecosystem, GnuPG includes a formidable array of
> features focusing on the management of trust relationships between people on
> the Internet. Unfortunately this can make it quite intimidating and confusing
> to use. The extent to which PGP and GPG are used by Vault and this collection
> is extremely limited. As such, unless you're already a user of GnuPG, you may
> find a simplified wrapper such as [Cryptie](https://github.com/bbc/cryptie/)
> preferable.

</details>


By default, the top-level playbooks in this collection will use the
`ephemeral_gnupg_home` role to create an ephemeral GnuPG environment isolated
from any other you might be using. The public keys in the Ansible data will be
automatically imported and a connected PGP smart card detected. This design
works on the assumption that your private key is stored on a PGP card (e.g. a
Yubikey). You can opt-out of this and use an existing GnuPG environment by
setting the `ansible_vault_gnupg_home` variable.


Utilities
---------

The `utils/` directory contains a selection of scripts which may be useful for
users of a Vault deployment.

* `utils/vault_auth.py` -- Logs into Vault using OIDC and signs your SSH key.
* `utils/vault_token_send.sh` -- Use your Vault token to log into Vault on a
  remote machine.
* `utils/run_disaster_recovery_vault_server.sh` -- Spin up an ephemeral vault
  server on your local machine, optionally loading a Vault snapshot (i.e.
  backup) into it for disaster recovery or backup validation purposes.
