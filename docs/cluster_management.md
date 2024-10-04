Cluster management
==================

The `bbcrd.vault` collection uses Vault's raft [HA
mode](https://developer.hashicorp.com/vault/docs/concepts/ha) (along with
[raft-based integrated
storage](https://developer.hashicorp.com/vault/docs/internals/integrated-storage)).
The [raft
autopilot](https://developer.hashicorp.com/vault/docs/concepts/integrated-storage/autopilot)
function is used to stage cluster membership changes.

This collection does not support any Vault Enterprise custering modes (e.g.
disaster recovery, performance secondaries etc.).

The members of the cluster is defined by the set of Ansible hosts in the
Ansible group named by `bbcrd_vault_cluster_ansible_group_name` variable.
Adding or removing hosts from this group will cause the `bbcrd.vault.unseal`
and `bbcrd.vault.remove_old_cluster_nodes` roles to add or permenently remove
the corresponding nodes from the cluster respectively.

Care is taken by the roles in this collection to ensure that cluster membership
changes do not lead to quorum being lost. So long as the running cluster is
already quorate, these roles actively check to ensure they will not cause
quorum to be lost.


Cluster disaster recovery
-------------------------

The roles in this collection can only manage clusters which are already
quorate.

If a majority of cluster members are not up, a cluster will become unavailable
and Vault will stop servicing new requests. Notably this includes requests from
new nodes to join the cluster. This is because without a majority to agree on
it, it is not possible to determine what the actual state of the cluster is in
order to populate the newly added node.

In the event that simultaneous, irrecoverable multiple hardware failure causes
quorum loss it is not possible to recover the cluster without potential data
loss. In this situation there are two routes to recovery:

1. Creating a new (empty) Vault cluster and restoring data from a backup
   snapshot.

2. Using [`peers.json` recovery to manually recover the
   cluster](https://developer.hashicorp.com/vault/docs/concepts/integrated-storage#manual-recovery-using-peers-json)

Option 1 (restore into a new cluster from backup) is the safest option, with a
well define dset of lost changes (i.e. everything since the backup was taken).

Option 2 (`peers.json` recovery) overrides the cluster membership data held by
theremaining cluster nodes to omit the dead nodes. The resulting database state
will be based on the consensus of the remaining nodes. Since this does not
represent a majority of the previous cluster, some changes which were in-flight
when the cluster failed may be lost. It is also possible that no majority can
agree on the cluster state (for example the new cluster could be evenly split
between two possible states). In this case, the cluster will fail to elect a
leader and fail. 

Detailed notes on disaster recovery procedures are provided in the [disaster
recovery documentation](./disaster_recovery.md).


Cluster monitoring access
-------------------------

By default, a policy named `read_cluster_status` is created (by the
`bbcrd.vault.system_policies` role) which allows read-only access to cluster
state. It is strongly recommended that you set up monitoring to alert on
clustering problems. As noted above, if quorum is lost due to irrecoverable
hardware failures, it is impossible to avoid data loss.
