`bbcrd.vault.issue_approle_credentials` role
============================================

This role deploys a credentials file containing an AppRole role ID and secret
ID for use in AppRole auth on a host. This role pairs up with the
[`bbcrd.vault.configure_approle_auth` role](../configure_approle_auth) which is
responsible for configuring the AppRole auth endpoint and roles.

This role should be run against the host on which the credentials are to be
written. By default, Vault commands will be issued from the Ansible control
node using your current Vault credentials.

Once a credentials file has been created, you could use the
`utils/vault_auth.py` utility script to authenticate with Vault like so:

    $ utils/vault_auth.py --app-role /etc/vault_approle_machine_credentials.json

Tip: This script will also attempt to sign your SSH public key using Vault by
default (see the `bbcrd.vault.configure_ssh_client_signer` role). You
can disable this behaviour using the `--no-ssh` argument.

See the [machine based auth using AppRoles
documentation](../../docs/machine_approle_auth.md) for an introduction to this
role and the matching `bbcrd.vault.configure_approle_auth` role.
