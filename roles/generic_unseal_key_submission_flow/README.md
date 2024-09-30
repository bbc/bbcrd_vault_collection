`bbcrd.vault.generic_unseal_key_submission_flow` role
=====================================================

> **Hint:** If you're looking for a high-level role for unsealing Vault nodes,
> see the [`bbcrd.vault.unseal`](../unesal) role instead.

Low-level role which implements the generic workflow whereby unseal keys are
supplied one-by-one to Vault to achieve some goal. This might be for basic
unsealing of a server or for some other action like root token generation.


Inputs/Outputs
--------------

The following variables must be set:

* `status_api_url`: The API endpoint to poll to monitor the status of key
  submission.

* `submit_api_url`: The API endpoint to POST the final unseal key to.

* `bbcrd_vault_unseal_keys`: A valid set of unseal keys. See the
  [`bbcrd.vault.decrypt_unseal_keys`](../decrypt_unseal_keys) role.

* `nonce`: The nonce for the submission process. If null, no nonce is used
  (or checked for).

* `purpose`: A human readable string stating what the unseal keys are being
  used for (e.g. 'to unseal vault' or 'for verification').

* `check_complete`: (Optional, default = true). If set to False, skips check
  that the unseal flow reported completeness in its final step. This may be
  useful when joining new nodes to the cluster which don't immediately report
  unsealed.

If these requests should be sent to only one host (rather than all hosts),
you must wrap the role in a `run_once` block.

On completing the role, the following variables will be set:

* `submission.json`: The JSON response from the final key submission API call.


Workflow
--------

Key submission consists of three phases:

1. First we submit up to threshold-1 of our own unseal keys, making sure to
   save at least one of our unseal keys to use later.

2. Next we wait for others to submit all but the last unseal key.
   This can be done using the `bbcrd.vault.supply_additional_keys`
   playbook.

3. Finally we submit our own last unseal key and capture whatever output is
   produced at that point.

The reason for waiting to be the last person to submit the last unseal key is
that some APIs will offer up their output to whoever provides the final unseal
key. For example this might be an (encrypted) root token during generate-root
or new unseal keys (during rekeying). Waiting to submit the last unseal key
avoids requiring role users to pass these values via a human-to-human side
channel.


Provide additional keys hook
----------------------------

The `bbcrd_vault_provide_additional_unseal_keys_tasks` variable may be
changed from its default `None` to a task file to import whenever additional
unseal keys are required (i.e. immediately prior to step '2' above). When
imported, the following additional variables will be set:

* `required`: The number of additional unseal keys which must be provided

The main intended purpose of this hook is to facilitate automated testing of
this role.
