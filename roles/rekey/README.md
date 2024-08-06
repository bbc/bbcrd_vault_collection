`bbcrd.ansible_vault.rekey` role
================================

Rekey vault with a new set of unseal keys.

By default this role will do nothing if the set of users and key fingerprints
in `ansible_vault_administrators` matches the encrypted unesal keys. You can
force rekeying to take place by setting `ansible_vault_force_rekey` to `True`.

This role will display a diff of any changes to the set of unseal keys and wait
for confirmation prior to rekeying taking place. The interactive prompt can be
bypassed by setting `ansible_vault_skip_confirm_rekey_changes` to True.

By default, rekeying is performed in [verify
mode](https://developer.hashicorp.com/vault/api-docs/system/rekey#read-rekey-verification-progress).
This requires that a set of the newly generated unseal keys be submitted before
the new keys take effect. This ensures that the newly generated keys are
decryptable and protects against accidental lockout. During this phase, the
candidate unesal keys are written to `encrypted_unseal_keys.json.candidate`,
adjacent to the usual encrypted key file.
