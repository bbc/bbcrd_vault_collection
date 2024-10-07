`bbcrd.vault.propagate_unseal_keys` role
========================================

This role propagates the encrypted unseal keys file to all hosts which don't
currently have a copy of it -- i.e. newly created nodes.

This role specifically *doesn't* attempt to make an otherwise inconsistent
situation consistent since we don't have enough information to do this!

See the [unseal key management
documentation](../../docs/unseal_key_management.md) for more information about
the management and propogation of unseal keys.
