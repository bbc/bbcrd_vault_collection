import os
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)


DOCUMENTATION = r"""
module: bbcrd.ansible_vault.vault_policy

short_description: Create, update or delete a Vault policy.

options:
    name:
        description: |-
            Name of the policy.
        required: true
        type: str
    policy:
        description: |-
            The HCL policy document.
        required: false
        type: str
    state:
        description: |-
            The state this policy should be in: 'present' or 'absent'
        required: true
        type: str
        default: "present"
    vault_url:
        description: The base URL of the vault server. Defaults to the contents
        of the VAULT_ADDR environment variable.
        required: false
        type: str
    vault_token:
        description: Token to use for Vault API calls. Defaults to the contents
        of the VAULT_TOKEN environment variable.
        required: false
        type: str
    vault_ca_path:
        description: |-
            The filename of the CA PEM file to use. Leave blank to use the
            built in certificate store. Defaults to the the VAULT_CACERT
            environment variable.
        required: false
        type: str
        default: null
"""

EXAMPLES = r"""
- name: Create a vault policy
  bbcrd.ansible_vault.vault_policy:
    name: "cluster-status-reader"
    policy: |-
      path "sys/storage/raft/autopilot/state" {
        capabilities = ["read"]
      }

- name: Delete a policy
  bbcrd.ansible_vault.vault_policy:
    name: "obsolete-policy"
    state: absent
"""


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type="str", required=True),
        policy=dict(type="str", required=False),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)
    result = {"changed": False}

    name = module.params["name"]
    state = module.params["state"]

    existing_policy = vault_api_request(
        module,
        f"/v1/sys/policy/{name}",
        expected_status=(200, 404),
    ).get("rules")

    if state == "present":
        if "policy" not in module.params:
            module.fail_json(msg="'policy' must be specified when state = present.")
        policy = module.params["policy"]

        # Create-or-update
        if policy != existing_policy:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/policy/{name}",
                method="POST",
                data={
                    "policy": policy,
                },
            )

    elif state == "absent":
        # Delete
        if existing_policy:
            result["changed"] = True
            vault_api_request(module, f"/v1/sys/policy/{name}", method="DELETE")

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
