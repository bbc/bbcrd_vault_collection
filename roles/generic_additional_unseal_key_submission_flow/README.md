`bbcrd.vault.generic_additional_unseal_key_submission_flow` role
================================================================

Low-level role which supplies additional unseal keys to vault when required to
meet an unseal key threshold. This role is the logical companion to the
[`bbcrd.vault.generic_unseal_key_submission_flow`](../generic_unseal_key_submission_flow)
role, but intended for the 'other' administrators.

This role will attempt to supply all but the last key required. The final key
is always left to be submitted by the person running whatever role is
performing the desired higher-level action. (See the
`generic_unseal_key_submission_flow` README).

See [the `bbcrd.vault.manage_vault_cluster` playbook (and friends)
documentation](../../docs/manage_vault_cluster_playbook.md) for the bigger
picture of workflows used by this collection.

Inputs/Outputs
--------------

The following variables must be set:

* `status_api_url`: The API endpoint to poll to monitor the status of key
  submission.

* `submit_api_url`: The API endpoint to POST the final unseal key to.

* `submit_once`: Should status/submit API endpoints be hit on one host or all
  hosts?

* `purpose`: A human readable string stating what the unseal keys are being
  used for (e.g. 'to unseal vault' or 'for verification').

* `encrypted_unseal_keys_filename`: (Optional.) The filename to pull encrypted
  unseal keys from.

* `status_status_code`: A list of valid status codes responses for
  `status_api_url`. Defaults to [200, 503].



