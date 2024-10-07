`bbcrd.vault.decrypt_unseal_keys` role
======================================

Decrypts as many unseal keys as possible into `bbcrd_vault_unseal_keys`. Also
sets `encrypted_unseal_keys` to the JSON-decoded contents of the encrypted
unseal key bundle.

Verifies that all hosts have matching encrypted unseal keys and that at least
one of the unseal keys could be decrypted.

You can override the filename of the encrypted key bundle the encrypted unseal
keys are loaded from by setting the `encrypted_unseal_keys_filename` variable.
It defaults to `encrypted_unseal_keys.json`.

NB: by default, this role will do nothing if `bbcrd_vault_unseal_keys` is
already not-null. Set this variable to null before calling the role to force
fetching and decryption of unseal keys.

You can limit the set of unseal keys which will be decrypted by setting
`bbcrd_vault_pgp_key_fingerprints` to a list of PGP key fingerprints to
attempt to use.

See the [unseal key management documentation](./unseal_key_management.md) for
details on the conventions used by this collection for unseal key management.


Skipping decryption
-------------------

You can alternatively just fetch the encrypted unseal key bundle into
`encrypted_unseal_keys` (without decrypting it) using:

    - import_role:
        name: bbcrd.vault.decrypt_unseal_keys
        tasks_from: fetch.yml

When used this way, the role will always fetch the encrypted unseal keys from
scratch.


Skipping encrypted unseal key fetching
--------------------------------------

If you wish to decrypt a set of unseal keys in an encrypted unseal key bundle
you've already fetched manually (e.g. perhaps manually extracted from a backup)
you can use something like the following:

    - import_role:
        name: bbcrd.vault.decrypt_unseal_keys
        tasks_from: decrypt.yml
      vars:
        encrypted_unseal_keys: "{{ lookup('file', '/path/to/encrypted_unseal_keys.json') | from_json }}"


Clearing decrypted unseal keys
------------------------------

The `clear.yml` utility task is included in this role which will automatically
clear the `bbcrd_vault_unseal_keys` variable iff it was set by this role.
(The `unseal_keys_decrypted` variable is set by this role during decryption and
used to decide whehter to clear the unseal keys or not).

    - import_role:
        name: bbcrd.vault.decrypt_unseal_keys
        tasks_from: clear.yml
