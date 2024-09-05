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
module: bbcrd.ansible_vault.vault_oidc_roles

short_description: Configure roles for the OIDC auth method.

options:
    roles:
        description: |-
            A dictionary from role name to role parameters, see the Vault docs:
            https://developer.hashicorp.com/vault/api-docs/auth/jwt#parameters-1
            
            Any roles configured in the server and not listed in this
            dictionary will be deleted.
        required:
        type: dict
    mount:
        description: |-
            The mountpoint of the OIDC auth method (without a trailing slash).
        required: false
        type: str
        default: "oidc"
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
- name: Enable OIDC auth endpoint
  bbcrd.ansible_vault.vault_auth_method:
    type: oidc

- name: Configure OIDC
  bbcrd.ansible_vault.vault_oidc_configure:
    config:
      # ...
      default_role: default

- name: Create OIDC roles
  bbcrd.ansible_vault.vault_oidc_roles:
    default:
      user_claim: email
      allowed_redirect_uris:
        # For CLI login
        - http://localhost:8250/oidc/callback
        # For Vault UI login
        - https://vault.example.com:8200/ui/vault/auth/oidc/oidc/callback
"""


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        roles=dict(type="dict", default={}),
        mount=dict(type="str", default="oidc"),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)
    result = {"changed": False}

    mount = module.params["mount"]
    roles = module.params["roles"]

    existing_roles = vault_api_request(
        module,
        f"/v1/auth/{mount}/role",
        method="LIST",
        expected_status=[200, 404],
    ).get("data", {"keys": []})["keys"]

    # Delete any roles not defined in the input
    for role_id in set(existing_roles) - set(roles):
        result["changed"] = True
        vault_api_request(module, f"/v1/auth/{mount}/role/{role_id}", method="DELETE")

    # Write any new/changed roles
    for role_id, params in roles.items():
        existing_params = vault_api_request(
            module, f"/v1/auth/{mount}/role/{role_id}", expected_status=[200, 404]
        ).get("data")

        if existing_params is None or not dict_issubset(params, existing_params):
            result["changed"] = True
            vault_api_request(
                module, f"/v1/auth/{mount}/role/{role_id}", method="POST", data=params
            )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
