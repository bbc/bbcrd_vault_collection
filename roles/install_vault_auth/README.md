`bbcrd.vault.install_vault_auth` role
=====================================

This role deploys the [`vault_auth.py`](../../utils/vault_auth.py) script on a
host and optionally sets up a systemd timer which runs it on a regular basis
using a set of app role credentials (e.g. deployed using the
[`bbcrd.vault.issue_approle_credentials` role](../issue_approle_credentials).
