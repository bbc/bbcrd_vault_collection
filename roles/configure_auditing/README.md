`bbcrd.ansible_vault.configure_auditing` role
=============================================

This role is a wrapper around the `bbcrd.ansible_vault.vault_audit` module
which defaults to simple stdout auditing.

Warning: changing any setting will result in the audit engine being replaced,
erasing the HMAC salt in any existing engine.

Tip: The file/stdout audit engine only writes audit messages to the leader
nodes' stdout stream.
