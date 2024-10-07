`bbcrd.vault.configure_approle_auth` role
=========================================

This role configures an AppRole auth method for machine access to vault for a
specific set of Ansible hosts. This role pairs up with the
[`bbcrd.vault.issue_approle_credentials` role](../issue_approle_credentials) to
issue app role secret IDs to specific machines.

This role creates an AppRole role for each machine in a given Ansible group.

This role is intended to be executed using a root token during provisioning of
Vault itself. By contrast, the issuance of credentials (using the
`issue_approle_credentials` role) is intended to be performed using a
day-to-day administrator's token using a specially created policy.

See the [Machine based auth using AppRoles](../../docs/machine_approle_auth.md)
documentation for an overview of this role and the corresponding
`bbcrd.vault.issue_approle_credentials` role.
