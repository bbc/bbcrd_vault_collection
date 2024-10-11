`bbcrd.vault` Ansible collection documentation
==============================================

This collection provides two major facilities:

1. Playbooks and roles for deploying and maintaining a high-availability Vault
   cluster using secure PGP-based unseal key management. These provide a
   generic and ready-made foundation suited to most Vault deployments.

2. Modules and roles for provisioning and managing various secrets engines,
   auth methods, etc. These are added to on an as-needed basis and so may/may
   not completely cover all of your use cases.

This documentation (and indeed the collection itself) is broadly divided
according to which of these two categories it deals with.


Vault cluster deployment and management
---------------------------------------

Vault is an enormously flexible tool and can be deployed in a huge number of
different ways. This collection delibrately focuses on one particular
architecture based on Vault's raft integrated storage and PGP unseal key
encryption.

The chosen architecture provides robust security and high availability and is
intended to work well in both single-administrator and team administration
settings.  It also does not depend on [Vault
Enterprise](https://developer.hashicorp.com/vault/docs/enterprise) features and
can be deployed in any environment including bare metal or public cloud.

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

Whilst the management of a vault cluster is likely to be common to many Vault
deployments, the provisioning of secrets engines, auth methods, identities and
policies within are likely to be unique. As a result, this collection provides a
selection of potentially useful Ansible roles and modules which can be
picked-and-chosen as required.

Given the enormous flexibility and breadth of features in Vault, only a subset
of the possible functions and design patterns are implemented in this
collection.  Likewise, these implementations may be relatively limited to a
specific type of application to avoid enormous complexity. In short, you may
not find everything you need here -- so please feel free to contribute!

Before diving in, it may be helpful to begin with a discussion of the
conventions followed by these non-cluster-management related roles and modules:

* [Ansible conventions for Vault provisioning roles and
  modules](./ansible_provisioning_conventions.md)

The service provisioning and configuration functionality exposed by this
collection is defined in the documentation pages below:

* Vault authentication and authorization
  * [OpenID Connect (OIDC) authentication](./oidc_auth.md)
  * [Machine based auth using AppRoles](./machine_approle_auth.md)
  * [Identity (entity and group) management](./identity_modules.md)
  * [Creating Vault policies](./creating_policies.md)

* Secrets engine deployment
  * [SSH client key signing with Vault](./ssh_client_key_signing.md)
  * [Key-Value (KV) secrets engine](./kv.md)


Collection Test Suite
---------------------

This collection includes a small test suite based on [Ansible
Molecule](https://ansible.readthedocs.io/projects/molecule/). These tests are
currently split into two parts, largely according to the same
deployment-vs-provisioning split as the rest of the collection.

You can install Molecule using:

    $ pip install -r requirements_test.txt

You can then run the two separate test scenarios as follows:

    $ molecule test -s test_deployment
    $ molecule test -s test_provisioning

In both cases, Docker containers will be spawned in which Vault instances will
be installed and tested.

The test suite takes quite a while to run (on the order of half an hour or so).

The `test_deployment` scenario is an integration-style test which uses the
`bbcrd.vault.manage_vault_cluster` playbook to deploy and manipulate a Vault
cluster. It includes tests of functions such as cluster management, unsealing,
unseal key management, rolling upgrades and so on.

The `test_provisioning` scenario uses a simple single-node Vault deployment and
a more unit-test style regime to verify the functionality of the various
modules used for provisioning Vault services. To reduce the test suite run
time, each test begins by resetting the Vault cluster to a blank state from a
snapshot rather than deploying a new Vault instance each time.
