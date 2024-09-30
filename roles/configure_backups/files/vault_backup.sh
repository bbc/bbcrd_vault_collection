#!/bin/bash

# Create a timestamped snapshot of the Vault database along with the encrypted
# unseal keys into the provided backup directory. Optionally deletes old
# backups.
#
# Bare-bones usage:
#
#    $ export ROLE_ID=...
#    $ export SECRET_ID=...
#    $ ./bbcrd_bbcrd_vault_shapshot.sh /path/to/backup_dir
#
# The following environment variables are used:
#
# * ROLE_ID -- (Required) The approle role ID to use to authenticate.
# * SECRET_ID -- (Required) The approle secret ID to use to authenticate.
# * NUM_BACKUPS -- The number of backup files to keep, deleting all but the
#                  most recent N backups. If zero or not defined, keeps all
#                  backup files.
# * ENCRYPTED_UNSEAL_KEYS_FILE -- The location of the encrypted unseal keys
#                                 file. Defaults to
#                                 '/etc/vault/encrypted_unseal_keys.json'.
# * VAULT_ADDR -- The vault server base address with no trailing slash.
#                 Defaults to 'https://localhost:8200'.
# * APPROLE_MOUNT -- The mount point of the approle auth endpoint with no
#                    trailing slash. Defaults to 'vault_backup_approle'.
# * SSL_CERT_FILE -- If set, the path to the CA certificate to use to
#   authenticate the Vault server.

set -e

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Expected backup directory as only argument."
    exit 1
fi

# Create working dir to collect together the backed up data
WORKING_DIR="$(mktemp --directory)"
trap 'rm -rf "$WORKING_DIR"' EXIT

# Authenticate with Vault using AppRole
VAULT_TOKEN="$(
    curl \
        --silent \
        --show-error \
        --fail \
        --request POST \
        --header "Content-Type: application/json" \
        --data "{\"role_id\": \"$ROLE_ID\", \"secret_id\": \"$SECRET_ID\"}" \
        "${VAULT_ADDR:-https://localhost:8200}/v1/auth/${APPROLE_MOUNT:-vault_backup_approle}/login" \
    | jq --raw-output .auth.client_token
)"

# Download a Vault database snapshot
#
# Due the the following Vault bug:
#
#     https://github.com/hashicorp/vault/issues/15258
#
# Any snapshot API call sent to a non-leader node will result in a 307 redirect
# to the leader. The `--location` argument to curl is needed to ensure that
# we follow the redirect.
#
# It is due to this bug that we cannot use the ordinary vault client: it
# appears unable to follow the 307 redirect.
curl \
    --silent \
    --show-error \
    --fail \
    --header "X-Vault-Token: $VAULT_TOKEN" \
    --location \
    "${VAULT_ADDR:-https://localhost:8200}/v1/sys/storage/raft/snapshot" \
    --output "$WORKING_DIR/vault.db"

# Sanity check that we've received a valid snapshot. This manually recreates
# Vault's own logic for checking snapshots are complete. See:
#
#     https://github.com/hashicorp/vault/pull/12388
if ! ( tar --list --file "$WORKING_DIR/vault.db" SHA256SUMS.sealed > /dev/null); then
  echo "FATAL ERROR: Incomplete (corrupt) snapshot received from vault. Abandoning backup."
  exit 2
fi


# Copy the encrypted unseal key file
cp \
    "${ENCRYPTED_UNSEAL_KEYS_FILE:-/etc/vault/encrypted_unseal_keys.json}" \
    "$WORKING_DIR/encrypted_unseal_keys.json"

# Create backup file (with a lexicographically sortable name)
zip \
    --quiet \
    --junk-paths \
    "$BACKUP_DIR/vault_backup_$(date +\%Y-\%m-\%d_\%H-\%M-\%S).zip" \
    "$WORKING_DIR/vault.db" \
    "$WORKING_DIR/encrypted_unseal_keys.json"

# Delete older backup files
if [ "${NUM_BACKUPS:-0}" -gt 0 ]; then
    find "$BACKUP_DIR" -name "vault_backup_*.zip" \
        | sort \
        | head -n-$NUM_BACKUPS \
        | xargs --no-run-if-empty rm
fi
