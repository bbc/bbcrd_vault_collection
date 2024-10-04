`bbcrd.vault` Ansible collection documentation
==============================================

This collection provides two major facilities:

1. Playbooks and roles for deploying and maintaining a high-availability Vault
   cluster using secure PGP-based unseal key management. These provide a
   generic and ready-made foundation for any Vault deployment.

2. Modules and roles for provisioning and managing various secrets engines,
   auth methods, etc. These are added to on an as-needed basis and so may/may
   not completely cover all of your use cases.

This documentation (and indeed the collection itself) is broadly divided into
dealing with these two categories.


Vault Cluster Deployment and Management
---------------------------------------

Vault is an enormously flexible tool and can be deployed in a huge number of
different ways. This collection delibrately focuses on one particular
architecture based on Vault's raft integrated storage and PGP unseal key
encryption.

The chosen architecture provides robust security and high availability and is
intended to work well in both single-administrator and team administration
settings.  It also does not depend on [Vault
Enterprise](https://developer.hashicorp.com/vault/docs/enterprise) features and
can be deployed on any environment ranging from bare metal to public cloud.

The following documentation explains the workflows and functionality
implemented by this collection for cluster management.

* [The `bbcrd.vault.manage_vault_cluster` playbook (and friends)](./manage_vault_cluster_playbook.md)
* [Unseal key management](./unseal_key_management.md)
* [Cluster management](./cluster_management.md)
* [VIP and HTTPS certificate management](./vip_and_https_certificate_management.md)
* [Disaster recovery](./disaster_recovery.md)
* [Ansible conventions for Vault cluster management playbooks and
  roles](./ansible_cluster_management_conventions.md)


Vault service provisioning and configuration
--------------------------------------------

TODO
