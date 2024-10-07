SSH client key signing with Vault
=================================

Vault's [SSH secrets
engine](https://developer.hashicorp.com/vault/docs/secrets/ssh) can be used to
sign SSH client (and host) certificates. This can be used to grant time-limited
access to a collection of machines to users with suitable Vault tokens.


Low-level module
-----------------

This collection provides the
[`bbcrd.vault.vault_ssh_signer`](../plugins/modules/vault_ssh_signer.py)
module. This can be used to configure the SSH secrets engine and is largely a
declarative interface to the [relevant Vault
APIs](https://developer.hashicorp.com/vault/api-docs/secret/ssh).


`bbcrd.vault.configure_ssh_client_signer` role
----------------------------------------------

The [`bbcrd.vault.configure_ssh_client_signer`
role](../roles/configure_ssh_client_signer) presents a simple set of defaults
for the `bbcrd.vault.vault_ssh_signer` module.

This role can either generate a new keypair to use for key signing or use an
existing one provided to it (see the
[defaults](../roles/configure_ssh_client_signer/defaults/main.yml) for
details).

The following default variables control the validity and access granted by the
generated signed certificates:

* `bbcrd_vault_ssh_client_signer_ttl`: How long signed certificates remain
  valid.

* `bbcrd_vault_ssh_client_signer_users`: The set of principals (i.e. user
  accounts) the certificate grants access to.

* `bbcrd_vault_ssh_client_signer_extensions`: The set of SSH extensions
  permitted.

By default a policy named `ssh_admin` is created which permits the holder to
sign SSH public keys.


### Signing SSH public keys

Assuming you have the appropriate Vault policies in place, you can sign your
own `id_rsa.pub` SSH key as follows:

    $ vault write \
        -field=signed_key \
        ssh_client_signer/sign/admin \
        public_key=@$HOME/.ssh/id_rsa.pub \
          > ~/.ssh/id_rsa-cert.pub

Alternatively, the [`utils/vault_auth.py` script](../utils/vault_auth.py)
included in this collection will automatically perform this task after
authenticating with Vault.
