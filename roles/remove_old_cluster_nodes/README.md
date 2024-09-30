`bbcrd.vault.remove_old_cluster_nodes` role
===========================================

This role removes any  nodes from the Vault cluster which do not have a
corresponding host in the Ansible data.

By default, this role will verify that removing nodes will not cause the
cluster to lose quorum.

If the number of working cluster nodes falls below quorum, the cluster will
become inoperative until enough existing but non-working nodes are restored to
operation. Adding new blank nodes is not sufficient since they cannot join the
cluster until the existing cluster is operational. If the non-working nodes
cannot be recovered, a manual [`peers.json`
recovery](https://developer.hashicorp.com/vault/docs/concepts/integrated-storage#manual-recovery-using-peers-json)
must be carried out to remove them from a non-operating cluster.
