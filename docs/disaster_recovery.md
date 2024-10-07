Disaster recovery
=================

This document outlines various options available for recovering from a serious
Vault failure.


Restoring Vault state from a backup
-----------------------------------

In the event that you manage to delete some extremely important data or
configuration from your Vault and you wish to roll the database back to a
backup, follow the steps below.

**You will need:**

* A working Vault cluster
* A valid set of (current) unseal keys.
* A vault raft snapshot (i.e. vault database backup) and matching unseal keys
  (if they differ from the current Vault state)

**Steps:**

> **Warning:** You must address the restore operations above to the
> current Vault leader node using the `VAULT_ADDR` environment variable due to
> [Vault issue 15258](https://github.com/hashicorp/vault/issues/15258). If you
> don't you'll get an opaque error message.
>
> You can discover the current leader
> node using:
>
>     $ vault operator raft autopilot state

0. If using an automatic backup as set up by this collection, first extract the
   vault database snapshot (`vault.db`) and encrypted unseal keys
   (`encrypted_unseal_keys.json`) files.

1. Obtain a root token (e.g. using the `bbcrd.vault.generate_root_token`
   playbook)

2. Create a fresh backup *right now*: restoring a backup will delete everything
   in the database! To [create a database
   snapshot](https://developer.hashicorp.com/vault/docs/commands/operator/raft#snapshot-save0):
   
       $ vault operator raft snapshot save pre_restore_snapshot.db
   
   Also make a backup of the current encrypted unseal keys (by default in
   `/etc/vault/encrypted_unseal_keys.json`).

3. Perform a database restore.

   **If the unseal keys have not changed since the snapshot was taken**, you can
   use the following to perform an on-line restore:
   
       $ vault operator raft snapshot restore path/to/vault.db
   
   Vault will stop responding to requests for a few moments whilst the data is
   restored. On completion Vault will remain unsealed but wound back to the
   specified snapshot. At this point, you're done and can skip the remaining
   steps.
   
   **If the unseal keys for the backup are different from the cluster**, you need
   to perform a *forced* restore instead:
   
       $ vault operator raft snapshot restore -force path/to/vault.db
   
   After the restore completes the cluster will become sealed.

4. Once the database is restored you must manually propagate the encrypted
   unseal keys to the cluster (e.g. by `scp`-ing them to
   `/etc/vault/encrypted_unseal_keys.json` on *every host in the cluster*).

5. You can now use the `bbcrd.vault.manage_vault_cluster` playbook to unseal
   the cluster as normal. At this point Vault should be unsealed and ready to
   use.


Restoring a Vault database backup into a new Vault cluster
----------------------------------------------------------

If your Vault cluster is irrecoverable, you can recover by creating a new
cluster and restoring a backup of your old Vault database into it.

**You will need:**

* A set of hosts ready to host the new Vault cluster
* A vault raft snapshot (i.e. vault database backup) and matching unseal keys

**Steps:**

0. Deploy a new (empty) cluster using the `bbcrd.vault.manage_vault_cluster`
   playbook.

1. Follow the steps for 'Restoring Vault state from a backup' above to restore
   your backup into the new cluster. Note that since the new cluster will have
   its own freshly generated unseal keys you will need to follow the 'forced
   restore' steps.


Restoring a Vault database into a local, ephemeral Vault server
---------------------------------------------------------------

There are a number of scenarios where it might be helpful to create an
ephemeral Vault server running on your laptop with the restored contents of
your vault database. These situations might include:

* Verifying backup integrity.

* Accessing a single deleted secret in an emergency from a backup without
  invasively overwriting the whole database.

* Cycle-breaking during a bootstrapping excercise (e.g. you need some
  credentials in Vault in order to deploy the Vault cluster, or a service the
  Vault cluster depends on).

* Disaster recovery situation where you need access to secrets but your Vault
  cluster is inaccessible.

**You will need:**

* A computer.
* A vault raft snapshot (i.e. vault database backup) and matching unseal keys

**Steps:**

0. If using an automatic backup as set up by this collection, first extract the
   vault database snapshot (`vault.db`) and encrypted unseal keys
   (`encrypted_unseal_keys.json`) files.

1. Using the
   [`utils/run_disaster_recovery_vault_server.py`](../utils/run_disaster_recovery_vault_server.py)
   utility script, start an ephemeral Vault server from the backup file:

       $ python3 utils/run_disaster_recovery_vault_server.py path/to/vault.db

   A vault server will be launched listening on `http://localhost:8200`. This
   server is *not* reachable over the network. Pressing enter (or killing the
   script) will shut down the Vault instance and deleting all data.
   
2. You must now decrypt the unseal keys associated with the backup as the newly
   started server will be sealed. The
   [`bbcrd.vault.decrypt_unseal_keys_file`](../playbooks/decrypt_unseal_keys_file.yml`)
   playbook is provided to decrypt `encrypted_unseal_keys.json` files
   automatically using your Yubikey:
   
       $ cp path/to/encrypted_unseal_keys.json encrypted_unseal_keys.json
       $ ansible-playbook bbcrd.vault.decrypt_unseal_keys_file

3. Making sure to set the `VAULT_ADDR` environment to point at your ephemeral
   Vault server, unseal the vault:
   
       $ export VAULT_ADDR=http://localhost:8200
       $ vault operator unseal
   
   If multiple people's unseal keys are required to unseal the vault you will
   need to contrive a secure way for your colleagues to supply these to your
   server. Options might include:

   * Having them set up an SSH port forward to your server and issuing vault API
     commands via that (e.g. using):

         $ ssh -L 8200:localhost:8200 <your machine>

   * Having them physically decrypt and enter them using your computer

4. At this point you can authenticate with the ephemeral Vault instance the
   same way you would the real cluster. Alternatively, you could [generate a
   root
   token](https://developer.hashicorp.com/vault/docs/commands/operator/generate-root)
   using unseal keys:

       $ vault operator generate-root -init
       $ vault operator generate-root
       <supply unseal key>
       $ vault operator generate-root
       <supply unseal key>
       $ ...
       $ vault operator generate-root -decode <encoded token> -otp <otp from -init command> | vault login -


Recovering a cluster which has lost quorum
------------------------------------------

If your cluster has permenantly lost quorum, e.g. because a number of nodes
failed simultaneously, it is not possible to recover by simply adding new
nodes. If the existing nodes cannot be recovered, you have two options, both of
which could result in data loss:

1. Create a new (empty) Vault cluster and restore the data from a backup
   snapshot (e.g. see 'Restoring a Vault database backup into a new Vault
   cluster' above).

2. Perform a `peers.json` recovery to manually recover the cluster.

The first option is the preferred option if you have a sufficiently recent
backup. If this is not possible, Vault provides the [`peers.json`
mechanism](https://developer.hashicorp.com/vault/docs/concepts/integrated-storage#manual-recovery-using-peers-json)
to manually recover your cluster.

> **Warning:** As noted in the [cluster management
> documentation](./cluster_management.md), this kind of recovery risks the loss
> of any data being written, or still being propagated when the cluster lost
> quorum and so unpredictable loss of very recent changes is possible.
>
> Further, whilst Vault makes an effort to only update its database in sensible
> atomic units, recovering a cluster using `peers.json` recovery has the
> potential to run into Vault bugs.

**You will need:**

* An existing Vault cluster which has lost quorum.
* A valid set of unseal keys.

**Steps:**

0. Manually shut down the Vault server on all hosts, e.g. using:

       $ sudo systemctl stop vault

1. Create a sufferage information file which enumerates the remaining members
   of your cluster which looks like so:
   
       [
         {
           "id": "vault-1",
           "address": "vault-1.example.com:8201",
           "non_voter": false
         },
         {
           "id": "vault-2",
           "address": "vault-2.example.com:8201",
           "non_voter": false
         },
         {
           "id": "vault-3",
           "address": "vault-2.example.com:8201",
           "non_voter": false
         }
       ]
   
   The `id`s should match the `node_id` value in the `storage "raft"` block of
   the Vault configuration file on each server. By default this resides in
   `/etc/vault/config.hcl`.
   
   The `address`es should match the `cluster_addr` config value, with the
   leading `https://` removed. Note that this is the clustering protocol
   address, not the regular Vault API, and is usually on port 8201.
   
   Assuming all remaining nodes were cluster members for at least a few seconds
   before the cluster went down, all nodes are voters.
   
   > **Tip:** Remember JSON doesn't permit trailing commas on arrays!

2. Copy your sufferage information file into `raft/peers.json` in the vault
   data directory on every host. By default this is
   `/var/lib/vault/data/raft/peers.json`.

3. Start the Vault server on each host

       $ sudo systemctl start vault

   At this point vault will read and then delete the `peers.json` file and
   attempt to start up.

4. You should now be able to unseal the cluster using the
   `bbcrd.vault.manage_vault_cluster` playbook as usual.


If the manually recovered cluster fails to reach a consensus, you can, in a
last-ditch effort, force a consensus by destroying all but one of the cluster
members. To do this, use the following steps:

0. Shutdown all Vault instances:

       $ sudo systemctl stop vault

1. Delete (or move elsewhere) the contents of the Vault data directory on all
   but one server.
   
       $ sudo mv /var/lib/vault/data /var/lib/vault/data_old
       $ sudo mkdir /var/lib/vault/data

2. Create a sufferage information file containing only the remaining cluster
   member on the host with the remaining copy of the data.
   
       [
         {
           "id": "vault-1",
           "address": "vault-1.example.com:8201",
           "non_voter": false
         }
       ]

3. Start the cluster node.

4. Run the `bbcrd.vault.manage_vault_cluster` playbook to unseal the vault and
   restart and rejoin the other (now empty) cluster nodes.
