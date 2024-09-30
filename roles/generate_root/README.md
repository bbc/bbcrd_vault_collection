`bbcrd.vault.generate_root` role
================================

Generate an (ephemeral) root token using unseal keys and place it in the
variable `ansible_vault_root_token`.

The generated root token will have a finite TTL of
`ansible_vault_root_token_ttl` (see
[`defaults/main.yml`](./defaults/main.yml)). This is by contrast with the
underlying Vault API which always hands out non-expiring root tokens. Use of
expiring root tokens helps minimise the chances of a crashing playbook leaving
a powerful, long-lived credential around.

Will do nothing if `ansible_vault_root_token` is not null. Set to null to force
the generation of a new root token.


Revoke a token
--------------

Run this role with the `revoke.yml` task like so to revoke a generated root
token:

    - import_role:
        name: bbcrd.vault.generate_root
        tasks_from: revoke.yml

This will only revoke the token if `root_token_generated` is True (which is set
by the main role iff it generates a new root token.
