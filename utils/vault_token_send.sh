#!/bin/bash

# Log into Vault on a remote host using your token.
#
# Usage:
#
#     $ ./vault_token_send.sh [<ssh args> ...] <hostname>
#
# NB: The remote host must have VAULT_ADDR etc. configured in its environment
# for this to work.


# NB: We use `bash --login` to ensure that we have access to the user's
# VAULT_ADDR and other vault related environment variables.
vault print token | ssh "$@" bash --login -c '"vault login -"'
