`bbcrd.vault.configure_backups` role
====================================

This role configures simple local backups on every Vault server in the cluster.

At a regular interval, a snapshot of the Vault database, along with the
encrypted unseal key file, is zipped up into `/var/lib/vault_backup` (see
`ansible_vault_backup_location`).


Backup script authentication
----------------------------

The backup script authenticates with vault using an AppRole authentication
endpoint configured at `vault_backup_approle` (see
`ansible_vault_backup_approle_mount`). The resulting token is then permitted to
make a single request to the [raft snapshot
endpoint](https://developer.hashicorp.com/vault/api-docs/system/storage/raft#take-a-snapshot-of-the-raft-cluster).
The role ID and secret ID credentials needed to do this are written to
`/etc/vault_backup_credentials.env` (see `ansible_vault_backup_auth_file`).


Restoring a backup
------------------

Each backup file contains a copy of the encrypted unseal keys (and associated
public keys) and a snapshot of the Vault database. The restore process consists
of the following steps:

1. Bring up a new (empty) Vault cluster using the raft storage engine.

2. Restore the backed up database snapshot inside the backup file using:
   
   ```
   $ vault operator raft snapshot restore --force vault.db
   ```
   
   Warning: You *must* address this restore operation to the current Vault
   leader node due to [Vault issue
   15258](https://github.com/hashicorp/vault/issues/15258). If you don't you'll
   get an opaque error message. You can discover the current leader node using:
   
   ```
   $ vault operator raft autopilot state
   ```
   
   After restoring the database, the vault will become sealed again.

3. Unseal vault using the backed up unseal keys.
   
   If you're restoring to a cluster managed by the roles and playbooks in this
   role, you should copy the encrypted unseal key file onto all cluster nodes
   in `/etc/vault/encrypted_unseal_keys.json` (by default), overwriting the
   existing file. At this point, you can use the usual playbooks/procedures to
   unseal the cluster.
   
   If you're manually restoring into a temporary vault instance, you will need
   to manually provide sufficient set of unseal keys associated with the
   snapshot and unseal vault.

In a disaster-recovery situation, or to non-invasively validate your backups
you may wish to spin-up an ephemeral Vault cluster on your laptop with a
minimum of fuss. The `bbcrd.vault.decrypt_unseal_keys_file` playbook
and
[`utils/run_disaster_recovery_vault_server.py`](../utils/run_disaster_recovery_vault_server.py)
utility are provided to facilitate these tasks.

1. Extract the backup you want to load:

       $ unzip vault_backup_XXXX-XX-XX_XX-XX-XX.zip

3. Start a local ephemeral vault server using the snapshot:

       $ python3 utils/run_disaster_recovery_vault_server.py vault.db

2. In another terminal, decrypt the unseal keys and unseal vault:

       $ ansible-playbook bbcrd.vault.decrypt_unseal_keys_file
       
       $ export VAULT_ADDR=http://localhost:8200
       $ vault operator unseal

4. Either authenticate with this vault however your normally would or generate
   a root token to use.

       $ vault login -method oidc
       
       or
       
       $ vault operator generate-root -init
       $ vault operator generate-root
       <supply unseal key>
       $ vault login $(vault operator generate-root -decode <encoded token> -otp <otp from -init command>)

NB: If you require multiple people's unseal keys to unseal vault you will need
to contrive a secure way for your colleagues to supply these to your server.
Options might include:

* Having them set up an SSH port forward to your server and issuing vault API
  commands via that (e.g. using):

     $ ssh -L 8200:localhost:8200 <your machine>

* Having them physically decrypt and enter them using your computer

Note that the `run_disaster_recovery_vault_server.py` script *only* listens on
loopback and cannot be reached over the network.
