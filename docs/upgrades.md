Upgrading Vault
===============


To perform a rolling upgrade of your Vault (server) cluster you can follow the
procedure below:

0. Create a backup backup of the Vault database.

   > [!WARNING]
   >
   > Older version of Vault do not support reading databases written by newer
   > versions. If you need to roll-back your Vault cluster you'll also need to
   > restore from an older backup snapshot.
   >
   > Be aware that Vault does not immediately fail when presented with a
   > database newer than it supports and instead has the potential for silent
   > data corruption.

   If you've configured backups using the [`bbcrd.vault.configure_backups`
   role](../roles/configure_backups), you can log into any of your Vault
   cluster nodes and run:

       $ systemctl start vault_backup
   
   And look for the freshly created backup file in `/var/lib/vault_backup`.

1. Increment the Vault version number in your variables to the desired version.
   Refer to the [Vault upgrade
   documentation](https://developer.hashicorp.com/vault/docs/upgrading) and
   release notes for guidance on acceptable version jumps.
   
   > [!WARNING]
   >
   > Downgrades are *not* supported by Vault. A downgrade must be achieved by
   > creating a new Vault cluster running the old version number and restoring
   > the backup into it.

2. Run the [`bbcrd.vault.manage_vault_cluster`
   playbook](./manage_vault_cluster_playbook.md). This will perform a rolling
   upgrade, upgrading, restarting and unsealing each node one at a time.
   Assuming suitable load-balancing infrastructure, this should be a
   zero-down-time process.
   
   Vault's built-in Autopilot function is responsible for automatically
   managing the process of deciding when the upgraded nodes the cluster take
   over responsibility for the database from the nodes yet to be upgraded. See
   the [the Vault
   documentation](https://developer.hashicorp.com/vault/docs/concepts/integrated-storage/autopilot#automated-upgrades)
   for more details.
