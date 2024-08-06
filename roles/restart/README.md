`bbcrd.ansible_vault.restart` role
==================================

Restart and unseal vault cluster members in a rolling fashion.

Restarts are performed one-at-a-time, with each restarted machine being
unsealed and rejoined to the cluster before moving on. This role will also (by
default) ensure that enough nodes are present in the cluster that a restart
will not take it below quorum, avoiding outages. This check can be bypassed by
setting `ansible_vault_allow_loss_of_quorum_on_restart` to `True`.

By default this role will only restart servers which are running a version of
Vault which doesn't match the installed binary (e.g. need restarting after an
update). You can force a restart of one or more specific hosts by setting the
`ansible_vault_restart_servers` variable to a list of hosts.
