import os
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)
from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.dict_compare import (
    dict_issubset,
)


DOCUMENTATION = r"""
module: bbcrd.ansible_vault.vault_approle

short_description: Create, update or delete a Vault AppRole auth method role

options:
    name:
        description: |-
            Name of the role.
        required: true
        type: str
    parameters:
        description: |-
            The approle parameters, see the Vault docs:
            https://developer.hashicorp.com/vault/api-docs/auth/approle#parameters
        required:
        type: dict
    mount:
        description: |-
            The mountpoint of the AppRole auth method (without a trailing
            slash).
        required: false
        type: str
        default: "approle"
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
- name: Create an AppRole role
  bbcrd.ansible_vault.vault_approle:
    name: "my-role"
    parameters:
      token_ttl: 600

- name: Delete an AppRole role
  bbcrd.ansible_vault.vault_approle:
    name: "obsolete-role"
    state: absent
"""


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type="str", required=True),
        mount=dict(type="str", default="approle"),
        parameters=dict(type="dict", default={}),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)
    result = {"changed": False}
    
    name = module.params["name"]
    state = module.params["state"]
    mount = module.params["mount"]
    parameters = module.params["parameters"]

    existing_approle = vault_api_request(
        module,
        f"/v1/auth/{mount}/role/{name}",
        expected_status=(200, 404),
    ).get("data")

    if state == "present":
        # Create-or-update
        if existing_approle is None or not dict_issubset(parameters, existing_approle):
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/auth/{mount}/role/{name}",
                method="POST",
                data=parameters,
            )

    elif state == "absent":
        # Delete
        if existing_approle is not None:
            result["changed"] = True
            vault_api_request(module, f"/v1/auth/{mount}/role/{name}", method="DELETE")

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
