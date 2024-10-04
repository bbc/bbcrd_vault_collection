`bbcrd.vault` Ansible Collection
================================

An Ansible collection for deploying and managing [Hashicorp
Vault](https://www.vaultproject.io/)/[OpenBao](https://openbao.org/) clusters.

This collection provides two major facilities:

1. Playbooks and roles for deploying and maintaining a high-availability Vault
   cluster using secure PGP-based unseal key management. These provide a
   generic and ready-made foundation for any Vault deployment.

2. Modules and roles for configuring and managing various secrets engines, auth
   methods, etc. These are added to on an as-needed basis and so may/may not
   completely cover all of your use cases.



[**Get started with the documentation in `docs/`**](./docs).



Vault secrets engine and auth provisioning roles and modules
------------------------------------------------------------

Whilst the manner of deployment of vault clusters may be common betwen Vault
deployments, the provisioning of secrets engines, auth methods, identities and
policies is not. As a result, this collection only provides a selection of
potentially useful Ansible roles and modules though these are very far from
complete.

In brief, the available roles are:

* `bbcrd.vault.configure_kv_secrets_engine` -- Deploys an empty KV
  secrets engine.
* `bbcrd.vault.configure_oidc_auth` -- Setup basic OpenID Connect based
  single-sign-on (SSO) authentication for vault.
* `bbcrd.vault.configure_ssh_client_signer` -- Setup a simple SSH
  client certificate signing secrets engine.
* `bbcrd.vault.configure_approle_auth` -- Configure an AppRole auth
  endpoint with roles for each host in an Ansible group for machine auth
  purposes.
* `bbcrd.vault.issue_approle_credentials` -- Issues AppRole credentials
  (role IDs and secret IDs) to Ansible hosts. For use with
  `bbcrd.vault.configure_approle_auth`.

The available modules are:

* Policy management
  * `bbcrd.vault.vault_policy` -- Create vault policies.
* Secret/auth/audit engine management
  * `bbcrd.vault.vault_audit` -- Configure auditing engines.
  * `bbcrd.vault.vault_auth_method` -- Enable and configure auth methods.
  * `bbcrd.vault.vault_secrets_engine` -- Enable or configure secrets
    engines.
* Entity/Group management
  * `bbcrd.vault.vault_auth_method_entity_aliases` -- Configure entity
    alias mappings for a particular auth method. (That is, map auth method users
    to Vault entities).
  * `bbcrd.vault.vault_group` -- Create and configure vault (entity) groups.
  * `bbcrd.vault.vault_entity` -- Create and configure entities.
* AppRole auth configuration
  * `bbcrd.vault.vault_approles` -- Manage the set of roles for an
    AppRoles auth endpoint.
  * `bbcrd.vault.vault_approle_secret` -- Generate (or set) AppRole
    secret IDs.
* OIDC Auth configuration
  * `bbcrd.vault.vault_oidc_configure` -- Configure the OIDC auth method.
  * `bbcrd.vault.vault_oidc_roles` -- Configure roles for the OIDC auth
    method.
* SSH Secrets engine configuration
  * `bbcrd.vault.vault_ssh_signer` -- Configure the SSH signer secrets
    engine.


Common default variables
------------------------

The majority of roles automatically pull in the common default variable values
defined in the otherwise empty `bbcrd.vault.common_defaults` role.


Utilities
---------

The `utils/` directory contains a selection of scripts which may be useful for
users of a Vault deployment.

* `utils/vault_auth.py` -- Logs into Vault using either OIDC (for humans) or
  AppRole (for machines) and signs your SSH key.
* `utils/vault_token_send.sh` -- Use your Vault token to log into Vault on a
  remote machine.
* `utils/run_disaster_recovery_vault_server.sh` -- Spin up an ephemeral vault
  server on your local machine, optionally loading a Vault snapshot (i.e.
  backup) into it for disaster recovery or backup validation purposes.
