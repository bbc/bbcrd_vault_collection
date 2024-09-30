`bbcrd.vault.configure_oidc_auth` role
======================================

This role configures simplistic OIDC-based authentication for Vault.
Specifically, it will accept any and all logins to the configured OIDC endpoint
and it is left up to you to give the chosen subset of entities appropriate
policies. (The rest will be issued tokens with only default privileges).

For now, anything beyond very simple authentication is out-of-scope for this
role. You should instead use the `bbcrd.vault.vault_oidc_configure` and
`bbcrd.vault.vault_oidc_roles` directly.
