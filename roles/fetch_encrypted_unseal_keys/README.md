`bbcrd.ansible_vault.fetch_encrypted_unseal_keys` role
======================================================

Fetches the encrypted unseal keys into the variable `encrypted_unseal_keys`.
Verifies that all hosts have matching encrypted unseal keys.

You can override the filename of the encrypted key bundle loaded from each
server by setting the `encrypted_unseal_keys_filename` variable. It defaults to
`encrypted_unseal_keys.json`.

