`bbcrd.vault.configure_ssh_client_signer` role
==============================================

This role configures a simple SSH client key signing service.

Add the policy named in `bbcrd_vault_ssh_client_signer_policy` (defaulting to
`ssh_admin`) to any Vault user whom you wish to be able to sign their SSH keys.

Once configured, an SSH key can be signed using a command such as:

    $ vault write \
        -field=signed_key \
        ssh_client_signer/sign/admin \
        public_key=@$HOME/.ssh/id_rsa.pub \
          > ~/.ssh/id_rsa-cert.pub

Vault also provides an unauthenticated API endpoint for obtaining the public
key used for signing:

    $ curl {{ bbcrd_vault_public_url }}/v1/ssh-client-signer/public_key

For now, anything beyond a single class of users is out of scope. You should
instead use the [`bbcrd.vault.vault_ssh_signer`
module](../../plugins/modules/vault_ssh_signer.py) directly.

See the [SSH client key signing with Vault
documentation](../../docs/ssh_client_key_signing.md) for more details.
