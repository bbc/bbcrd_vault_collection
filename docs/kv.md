Key-Value (KV) secrets engine
=============================

The [`bbcrd.vault.configure_kv_secrets_engine`
role](./roles/configure_kv_secrets_engine.yml) deploys a simple KV [version
1](https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v1) or [version
2](https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2) secrets engine
as selected by the `bbcrd_vault_kv_version` variable.

This role also creates a pair of policies named (by default) `kv_admin` and
`kv_read_only` which grant full, or read-only access respectively.

