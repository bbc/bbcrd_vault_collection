`bbcrd.ansible_vault.configure_backups` role
============================================

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

1. Bring up a new Vault cluster using the raft storage engine.
   
   Note: You cannot restore a snapshot to non-raft storage backends, for
   example the in-memory backend used by the dev server.
   
   If you are trying to temporarily restore a backup to a minimal Vault
   deployment on your laptop in an emergency (for example), you could use the
   following configuration:
   
   ```
   storage "raft" {
     path = "data"
     node_id = "vault"
   }
   listener "tcp" {
     address = "127.0.0.1:8200"
     cluster_address = "127.0.0.1:8201"
     tls_disable = true
   }
   api_addr = "http://127.0.0.1:8200"
   cluster_addr = "https://127.0.0.1:8201"
   disable_mlock = true
   ```
   
   This vault server could then be started using:
   
   ```
   $ vault server -config=config.hcl
   ```
   
   And then initialised and unsealed like so:
   
   ```
   $ export VAULT_ADDR=http://127.0.0.1:8200
   $ vault operator init -key-shares=1 -key-threshold=1
   $ vault operator unseal <unseal key printed during init>
   $ vault login <root token printed during init>
   ```

2. Restore the backed up database snapshot using:
   
   ```
   $ vault operator raft snapshot restore --force vault.db
   ```
   
   After restoring the database, the vault will become sealed again.

3. Unseal vault using the backed up unseal keys.
   
   If you're restoring to a cluster managed by the roles and playbooks in this
   role, you should copy the encrypted unseal key file onto all cluster nodes
   in `/etc/vault/encrypted_unseal_keys.json` (by default). At this point, you
   can use the usual playbooks/procedures to unseal the cluster.
   
   If you're manually restoring into a temporary vault instance, you will need
   to manually decrypt a sufficient set of unseal keys and unseal vault. You
   could do this using the following procedure.

   First, identify a suitable key share in the encrypted unseal key file. You
   can then extract the public key and encrypted data into files using `jq` and
   `base64` as follows:
   
   ```
   $ jq -r .shares[0].public_key encrypted_unseal_keys.json > public_key.pgp
   $ jq -r .shares[0].encrypted_unseal_key encrypted_unseal_keys.json | base64 -d > encrypted_unseal_key.pgp
   ```
   
   You can then use [Cryptie](https://github.com/bbc/cryptie/) to decrypt the
   unseal key. (You could alternatively use GnuPG/OpenPGP to do this if your
   PGP setup is more complicated).
   
   ```
   $ cryptie decrypt public_key.pgp encrypted_unseal_key.pgp
   ```
   
   You can now submit this unseal key to vault using:
   
   ```
   $ vault operator unseal
   ```
   
   This process may need to be repeated until enough unseal keys have been
   presented.
