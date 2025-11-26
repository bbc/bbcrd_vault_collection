import os
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)
from ansible_collections.bbcrd.vault.plugins.module_utils.dict_compare import (
    dict_issubset,
)


DOCUMENTATION = r"""
module: bbcrd.vault.vault_approles

short_description: Configure the approles for an AppRoles auth method.

options:
    approles:
        description: |-
            A dictionary from approle names to approle parameters, per the
            Vault docs:
            https://developer.hashicorp.com/vault/api-docs/auth/approle#parameters
            
            Any approles not enumerated here will be deleted. Existing approles
            will be updated. New approles will be created.
        required: true
        type: dict
    mount:
        description: |-
            The mountpoint of the AppRole auth method (without a trailing
            slash).
        required: false
        type: str
        default: "approle"
    vault_url:
        description: |-
          The base URL of the vault server. Overrides any address configured
          via envrionment variables.
        required: false
        type: str
    vault_token:
        description: |-
          Token to use for Vault API calls. Overrides tokens configured in the
          environment, token helpers or .vault-token file.
        required: false
        type: str
    vault_ca_path:
        description: |-
            The filename of the CA PEM file to use. Set to null to use the
            built in certificate store. Overrides any CA path configured in the
            environment.
        required: false
        type: str
        default: null
    vault_implementation:
        description: |-
          The name of the Vault implementation whose conventions for default
          values of 'vault_url', 'vault_token' and 'vault_ca_path' will be
          used. Defaults to 'vault'. E.g. for OpenBao specify 'bao' to try
          'BAO_*' variables before 'VAULT_*'.
"""

RETURN = r"""
role_ids:
    description: |-
        A mapping from role names to role IDs.
    type: dict
    returned: always
"""

EXAMPLES = r"""
- name: Manage approles
  bbcrd.vault.vault_approles:
    approles:
      my-shortlived-role:
        token_ttl: 60
      my-longer-lived-role:
        token_ttl: 3200
"""


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        approles=dict(type="dict", required=True),
        mount=dict(type="str", default="approle"),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)
    result = {"changed": False, "role_ids": {}}
    
    approles = module.params["approles"]
    mount = module.params["mount"]

    existing_approle_names = vault_api_request(
        module,
        f"/v1/auth/{mount}/role",
        method="LIST",
        expected_status=(200, 404),
    ).get("data", {}).get("keys", [])

    # Delete extra approles
    for name in set(existing_approle_names) - set(approles):
        result["changed"] = True
        vault_api_request(module, f"/v1/auth/{mount}/role/{name}", method="DELETE")

    # Create or update approles
    for name, parameters in approles.items():
        # To allow lazy YAML specification
        if parameters is None:
            parameters = {}
        
        existing_parameters = vault_api_request(
            module,
            f"/v1/auth/{mount}/role/{name}",
            expected_status=(200, 404),
        ).get("data")
        if (
            existing_parameters is None
            or any(
                key not in existing_parameters or existing_parameters[key] != value
                for key, value in parameters.items()
            )
        ):
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/auth/{mount}/role/{name}",
                method="POST",
                data=parameters,
            )
        
        # Lookup approle ID
        result["role_ids"][name] = vault_api_request(
            module, f"/v1/auth/{mount}/role/{name}/role-id"
        )["data"]["role_id"]

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
