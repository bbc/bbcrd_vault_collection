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

The membership of the cluster is defined by the set of Ansible hosts in the
Ansible group named by `bbcrd_vault_cluster_ansible_group_name` variable.
Adding or removing hosts from this group will cause the `bbcrd.vault.unseal`
and `bbcrd.vault.remove_old_cluster_nodes` roles to add or [permenently
remove](#reintroducing-a-node-to-the-cluster) the corresponding nodes from the
cluster respectively.

Care is taken by the roles in this collection to ensure that cluster membership
changes do not lead to quorum being lost. So long as the cluster is already
quorate, these roles (by default) will refuse to make any change which would
cause quorum to be lost.


Reintroducing a node to the cluster
-----------------------------------

If a Vault instance is explicitly removed from the cluster (as opposed to it
simply going down and then returning), it is not possible to reintroduce it to
the cluster. Instead you must erase its state and rejoin it as a new node:

0. Shutdown the Vault server on that host

       $ sudo systemctl stop vault

1. Delete (or move elsewhere) the contents of the Vault data directory.
   
       $ sudo mv /var/lib/vault/data /var/lib/vault/data_old
       $ sudo mkdir /var/lib/vault/data

2. Start Vault again.

3. Run the `bbcrd.vault.manage_vault_cluster` playbook to join the (now empty)
   node to the cluster.


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

2. Using `peers.json` recovery to manually recover the cluster

Option 1 (restore into a new cluster from backup) is the safest option, with a
well define dset of lost changes (i.e. everything since the backup was taken).

Option 2 (`peers.json` recovery) overrides the cluster membership data held by
the remaining cluster nodes to omit the dead nodes. The resulting database
state will be based on the consensus formed by the remaining nodes. Since this
does not represent a majority of the original cluster, some changes may be
lost. It is also possible that no majority opinion exists on the cluster state
(for example the new cluster could be evenly split between two possible
states). In this case, the cluster will fail to elect a leader and fail. 

Procedures for both options are provided in the [disaster recovery
documentation](./disaster_recovery.md).


Cluster monitoring access
-------------------------

By default, a policy named `read_cluster_status` is created (by the
[`bbcrd.vault.system_policies` role](../roles/system_policies)) which allows
read-only access to cluster state. It is strongly recommended that you set up
monitoring to alert on clustering problems. As noted above, if quorum is lost
due to irrecoverable hardware failures, it is impossible to avoid data loss and
service interruption.
