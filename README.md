`bbcrd.vault` Ansible Collection
================================

An Ansible collection for deploying and managing [Hashicorp
Vault](https://www.vaultproject.io/)/[OpenBao](https://openbao.org/) clusters.

This collection provides two major facilities:

1. Playbooks and roles for deploying and maintaining a high-availability Vault
   cluster using secure PGP-based unseal key management. These provide a
   generic and ready-made foundation suited to most Vault deployments.

2. Modules and roles for configuring and managing various secrets engines, auth
   methods, etc. These are added to on an as-needed basis and so may/may not
   completely cover all of your use cases.

**To get started:** Head over to [the documentation in
`docs/`](./docs/README.md).

