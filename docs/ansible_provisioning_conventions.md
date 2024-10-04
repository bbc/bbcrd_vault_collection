Ansible conventions for Vault provisioning roles and modules
============================================================

The roles and modules designed for Vault provisioning and configuration (as
opposed to cluster management) follow a number of common conventions outlined
below.


Role conventions
----------------

The Vault provisioning roles in this collection fall into one of two
categories:

1. Administrative roles which provision services within Vault (e.g. secrets
   engines or auth methods) and set sensitive options (e.g. user policies).

2. Secret deployment roles which read or write secrets in Vault, e.g. as part
   of the deployment of other hosts in an Ansible playbook.

Administrative roles deal with highly sensitive configuration options and
generally require the use of a root token. Because of this, these roles are
deliberately designed to integrate into the cluster management workflow. As
such administrative roles follow the [same conventions as cluster management
roles](./ansible_cluster_management_conventions.md). For example, Vault server
details are passed as Ansible variables and Vault API commands are sent from
the Vault hosts rather than the Ansible control host.

Secret deployment roles are intended to be integrated into regular playbooks
for administering other Ansible hosts. For example, these might be used to
install in AppRole credentials to facilitate machine authentication. As a
result, these roles follow the more usual convention of determining Vault
configuration from environment variables and running all Vault commands on the
Ansible control host. The Vault tokens used day-to-day by administrators are
expected to have suitable policies assigned to permit access to the needed
secrets.

Generally speaking, secret deployment roles pair up with corresponding
administrative roles which are responsible for setting up the secrets and Vault
services needed.


Module conventions
------------------

Unlike other common Ansible modules and utilities for interacting with Vault,
all of the modules defined in this collection are intended to be able to run on
a remote host, rather than the Ansible control node. This design choice
reflects the fact that many of these modules are used from administrative roles
where this pattern is used. Secret deployment roles are able to run Vault
commands locally by delegating to localhost and reading configuration and
credentials from the environment.


Integration of administrative roles and modules with cluster management playbooks
---------------------------------------------------------------------------------

Since cluster management and administrative roles and modules follow the same
conventions, and require the same authorisation, the following example
illustrates how single playbook could be created which carries out both roles:

    ---
    - name: Create ephemeral GnuPG environment for handling unseal keys
      hosts: vault_cluster
      become: yes
      tags: always
      gather_facts: false
      tasks:
        - name: Create ephemeral GnuPG environment for handling unseal keys
          import_role:
            name: bbcrd.vault.ephemeral_gnupg_home
    
    - name: Deploy/manage vault cluster, unseal keys etc.
      become: true
      tags: deploy
      import_playbook: bbcrd.vault.manage_vault_cluster
      vars:
        bbcrd_vault_cluster_ansible_group_name: vault_cluster
    
    - name: Provision secrets engines, authentication methods, users, etc.
      hosts: vault_cluster
      become: yes
      tags: provision
      
      tasks:
        - block:
            - import_role:
                name: bbcrd.vault.decrypt_unseal_keys
            - import_role:
                name: bbcrd.vault.generate_root
    
            - name: (Example) setup KV secrets engine
              import_role:
                name: bbcrd.vault.configure_kv_secrets_engine
              tags: provision_kv
            
            - name: (Example) configure administrator group
              run_once: true
              tags: provision_administrator_group
              bbcrd.vault.vault_group:
                name: "administrators"
                members:
                  - jonathah
                  - bonneya
                policies:
                  - kv_admin
                vault_url: "{{ bbcrd_vault_public_url }}"
                vault_token: "{{ bbcrd_vault_root_token }}"
                vault_ca_path: "{{ bbcrd_vault_ca_path | default(omit) }}"
            
            # And so on...
            
          always:
            - name: Revoke generated root token
              import_role:
                name: bbcrd.vault.generate_root
                tasks_from: revoke.yml
              tags: always
              
            - name: Clear any decrypted unseal keys
              import_role:
                name: bbcrd.vault.decrypt_unseal_keys
                tasks_from: clear.yml
              tags: always
    
    - name: Clean up ephemeral GnuPG environment
      hosts: vault_cluster
      become: yes
      tags: always
      gather_facts: false
      tasks:
        - name: Cleanup ephemeral GnuPG environment
          import_role:
            name: bbcrd.vault.ephemeral_gnupg_home
            tasks_from: cleanup.yml
