`bbcrd.vault.configure_backups` role
====================================

This role configures simple local backups on every Vault server in the cluster.

At a regular interval, a snapshot of the Vault database, along with the
encrypted unseal key file, is zipped up into `/var/lib/vault_backup` (see
`bbcrd_vault_backup_location`).


Backup script authentication
----------------------------

The backup script authenticates with vault using an AppRole authentication
endpoint configured at `vault_backup_approle` (see
`bbcrd_vault_backup_approle_mount`). The resulting token is then permitted to
make a single request to the [raft snapshot
endpoint](https://developer.hashicorp.com/vault/api-docs/system/storage/raft#take-a-snapshot-of-the-raft-cluster).
The role ID and secret ID credentials needed to do this are written to
`/etc/vault_backup_credentials.env` (see `bbcrd_vault_backup_auth_file`).


Restoring a backup
------------------

Each backup file contains a copy of the encrypted unseal keys (and associated
public keys) and a snapshot of the Vault database. For advice on restoring or
validating this backup, see the [disaster recovery
documentation](../../docs/disaster_recovery.md).

