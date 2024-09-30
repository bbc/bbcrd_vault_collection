`bbcrd.vault.configure_kv_secrets_engine` role
==============================================

This role sets up the kv secrets engine and creates a policy which grants
unlimited access to its contents (named by
`ansible_vault_kv_admin_policy_name`, defaulting to `kv_admin`).
