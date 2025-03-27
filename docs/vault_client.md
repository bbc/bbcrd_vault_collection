Installing the Vault client
===========================

Whislt this collection is mostly concerned with setting up Vault servers, a
subset of the roles can be used to deploy the Vault CLI and associated
configuration. These are:

* [`bbcrd.vault.install` role](../roles/install) -- Installs the Vault binary
  for interactive or scripted use.
* [`bbcrd.vault.install_environment_vars`
  role](../roles/install_environment_vars) -- Sets the `VAULT_ADDR` and
  `VAULT_CACERT` environment variables system wide (as required).
* [`bbcrd.vault.install_ca_bundle` role](../roles/install_ca_bundle) --
  Installs a custom certificate bundle, only useful if using a custom CA.
