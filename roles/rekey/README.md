`bbcrd.vault.rekey` role
========================

Rekey vault with a new set of unseal keys.

By default this role will do nothing if the set of users and key fingerprints
in `bbcrd_vault_administrators` matches the encrypted unesal keys. You can
force rekeying to take place by setting `bbcrd_vault_force_rekey` to `True`.

This role will display a diff of any changes to the set of unseal keys and wait
for confirmation prior to rekeying taking place. The interactive prompt can be
bypassed by setting `bbcrd_vault_skip_confirm_rekey_changes` to True.

By default, rekeying is performed in [verify
mode](https://developer.hashicorp.com/vault/api-docs/system/rekey#read-rekey-verification-progress).
This requires that a set of the newly generated unseal keys be submitted before
the new keys take effect. This ensures that the newly generated keys are
decryptable and protects against accidental lockout. During this phase, the
candidate unesal keys are written to `encrypted_unseal_keys.json.candidate`,
adjacent to the usual encrypted key file.

This role will accept and use any unseal keys provided via the
`bbcrd_vault_unseal_keys` variable to begin rekeying. These may be obtained
using `bbcrd.vault.decrypt_unseal_keys` but may be supplied separately.
However, if verify mode is used (i.e. `bbcrd_vault_verify_rekey` is True, the
default), the role will use the `bbcrd.vault.decrypt_unseal_keys` role
to decrypt the newly generated unseal keys for verification. If this is not
acceptable, you must disable verify mode.

See the [unseal key management
documentation](../../docs/unseal_key_management.md) for more details on unseal
key handling by this collection.
