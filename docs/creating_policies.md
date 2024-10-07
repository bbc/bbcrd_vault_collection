Creating Vault policies
=======================

The [`bbcrd.vault.vault_policy` module](../plugins/modules/vault_policy.md) may
be used to straightforwardly define (or update or delete) Vault policies.

For example:

    - name: Create metric reading policy
      bbcrd.vault.vault_policy:
        name: "read-metrics"
        policy: |-
          # Read vault metrics
          path "sys/metrics" {
            capabilities = ["read"]
          }
        
        vault_url: "{{ bbcrd_vault_public_url }}"
        vault_token: "{{ bbcrd_vault_root_token }}"
        vault_ca_path: "{{ bbcrd_vault_ca_path | default(omit) }}"

> **Hint:** In the example above we're making our API request and setting our
> Vault server details and credentials as per the [conventions for
> administrative roles and modules](./ansible_provisioning_conventions.md).
