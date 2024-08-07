`bbcrd.ansible_vault.decrypt_unseal_keys` role
==============================================

Decrypts as many unseal keys as possible into `ansible_vault_unseal_keys`.
Verifies that all hosts have matching encrypted unseal keys and that at least
one of the unseal keys could be decrypted.

You can override the filename of the encrypted key bundle the encrypted unseal
keys are loaded from by setting the `encrypted_unseal_keys_filename` variable.
It defaults to `encrypted_unseal_keys.json`.

NB: by default, this role will do nothing if `ansible_vault_unseal_keys` is
already not-null. Set this variable to null before calling the role to force
fetching and decryption of unseal keys.


Skipping decryption
-------------------

You can alternatively just fetch the encrypted unseal key bundle into
`encrypted_unseal_keys` (without decrypting it) using:

    import_role:
      name: bbcrd.ansible_vault.decrypt_unseal_keys
      tasks_from: fetch.yml

When used this way, the role will always fetch the encrypted unseal keys from
scratch.


Clearing decrypted unseal keys
------------------------------

The `clear.yml` utility task is included in this role which will automatically
clear the `ansible_vault_unseal_keys` variable iff it was set by this role.
(The `unseal_keys_decrypted` variable is set by this role during decryption and
used to decide whehter to clear the unseal keys or not).

    - import_role:
        name: bbcrd.ansible_vault.decrypt_unseal_keys
        tasks_from: clear.yml
