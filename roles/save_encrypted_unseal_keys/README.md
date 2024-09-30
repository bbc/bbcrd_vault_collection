`bbcrd.vault.save_encrypted_unseal_keys` role
=============================================

Write the encrypted unseal keys in the `encrypted_unseal_keys_base64` variable
into a the file named by the `encrypted_unseal_keys_filename` variable,
defaulting to `encrypted_unseal_keys.json`.

The encrypted unseal keys must be presented in the same order as the
corresponding users in `unseal_key_shares` (defined in the `common_defaults`
vars).

