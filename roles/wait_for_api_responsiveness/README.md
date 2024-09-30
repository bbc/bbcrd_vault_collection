`bbcrd.vault.wait_for_api_responsiveness` role
==============================================

Wait for a Vault node to be responsive to API requests.

This is necessary after unsealing/joining a node to the cluster since nodes
will report being unsealed some time before they're capable of making API
requests.
