`bbcrd.vault.configure_ssh_client_signer` role
==============================================

This role configures a simple SSH client key signing service and, optionally,
policies to go with it.

Once configured, an SSH key can be signed using a command such as:

    $ vault write \
        -field=signed_key \
        ssh_client_signer/sign/role_name_here \
        public_key=@$HOME/.ssh/id_rsa.pub \
          > ~/.ssh/id_rsa-cert.pub

Vault also provides an unauthenticated API endpoint for obtaining the public
key used for signing:

    $ curl {{ bbcrd_vault_public_url }}/v1/ssh_client_signer/public_key

See the [SSH client key signing with Vault
documentation](../../docs/ssh_client_key_signing.md) and
[`defaults/main.yml`](./defaults/main.yml) for more details.
