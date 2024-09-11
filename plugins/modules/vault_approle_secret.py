import os
import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)
from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.dict_compare import (
    dict_issubset,
)


DOCUMENTATION = r"""
module: bbcrd.ansible_vault.vault_approle_secret

short_description: Manage an AppRole's secret_ids.

options:
    approle_name:
        description: |-
            Name of the role.
        required: true
        type: str
    secret_id:
        description: |-
            If given, specifies the secret to be set. If omitted, a secret ID
            will be generated automatically by vault.
        required: false
        type: str
    parameters:
        description: |-
            The approle secret parameters, see the Vault docs:
            https://developer.hashicorp.com/vault/api-docs/auth/approle#parameters-5
            
            As a convenience, if 'metadata' is provided as a dict, not a
            JSON-string, it will be automatically converted as required by the
            API.
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
            The mode of operation for this module with respect to existing
            secret IDs. One of:
            
            * 'singular' -- Deletes all existing secrets for the approle
              before creating a new secret ID. (Default)
            * 'added' -- Create a new secret ID on every invocation, leaving
              any existing secrets as-is.
            * 'absent' -- Deletes all existing secrets for the role. Does not
              create a new secret ID.
        required: false
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

RETURN = r"""
secret_id:
    description: |-
        The secret ID.
    type: str
    returned: unless state = "absent"
secret_id_accessor:
    description: |-
        The secret ID accessor.
    type: str
    returned: unless state = "absent"
"""

EXAMPLES = r"""
- name: Create (or replace) the secret for foobar.example.com
  bbcrd.ansible_vault.vault_approle_secret:
    approle_name: "my-role"
    parameters:
      metadata:
        host: foobar.example.com
    state: "replaced"
"""


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        approle_name=dict(type="str", required=True),
        secret_id=dict(type="str", default=None),
        parameters=dict(type="dict", default={}),
        state=dict(
            type="str",
            choices=[
                "singular",
                "added",
                "absent",
            ],
            default="singular",
        ),
        mount=dict(type="str", default="approle"),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)
    result = {"changed": False}

    approle_name = module.params["approle_name"]
    secret_id = module.params["secret_id"]
    state = module.params["state"]
    mount = module.params["mount"]
    parameters = module.params["parameters"]

    # Remove existing secrets
    if state in ["absent", "singular"]:
        secret_id_accessors = vault_api_request(
            module,
            f"/v1/auth/{mount}/role/{approle_name}/secret-id",
            method="LIST",
            expected_status=[200, 404],
        ).get("data", {}).get("keys", [])
        for secret_id_accessor in secret_id_accessors:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/auth/{mount}/role/{approle_name}/secret-id-accessor/destroy",
                method="POST",
                data={"secret_id_accessor": secret_id_accessor},
            )

    # Generate new secret
    if state != "absent":
        # Convert metadata parameter to a JSON string for use with the secret
        # creation API (as a convenience)
        if "metadata" in parameters and not isinstance(parameters["metadata"], str):
            parameters["metadata"] = json.dumps(parameters["metadata"])
        
        if secret_id is None:
            response = vault_api_request(
                module,
                f"/v1/auth/{mount}/role/{approle_name}/secret-id",
                method="POST",
                data=parameters,
            )
        else:
            response = vault_api_request(
                module,
                f"/v1/auth/{mount}/role/{approle_name}/custom-secret-id",
                method="POST",
                data=dict(parameters, secret_id=secret_id),
            )

        result["changed"] = True
        result["secret_id"] = response["data"]["secret_id"]
        result["secret_id_accessor"] = response["data"]["secret_id_accessor"]

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
