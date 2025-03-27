`bbcrd.vault.install_environment_vars` role
===========================================

Adds entries to `/etc/environment` which set the `VAULT_ADDR` and
`VAULT_CACERT` environment variables according to the `bbcrd_vault_public_url`
and `bbcrd_vault_ca_path` variables, respectively.

This is not required for any of the roles included in this collection to work,
but makes life more convenient for interactive Vault users on hosts.

