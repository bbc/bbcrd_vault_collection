import os
import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)
from ansible_collections.bbcrd.vault.plugins.module_utils.dict_compare import (
    dict_issubset,
)


DOCUMENTATION = r"""
module: bbcrd.vault.vault_oidc_roles

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
        description: |-
          the base url of the vault server.
        required: false
        default: https://localhost:8200
        type: str
    vault_namespace:
        description: |-
          the vault namespace to issue the command to.
        required: false
        default: ""
        type: str
    vault_token:
        description: |-
          token to use for vault api calls.
        required: false
        default: ""
        type: str
    vault_ca_path:
        description: |-
            the filename of the ca pem file to use. set to none to use the
            built in certificate store.
        required: false
        default: none
        type: str
        default: null
"""

EXAMPLES = r"""
- name: Enable OIDC auth endpoint
  bbcrd.vault.vault_auth_method:
    type: oidc

- name: Configure OIDC
  bbcrd.vault.vault_oidc_configure:
    config:
      # ...
      default_role: default

- name: Create OIDC roles
  bbcrd.vault.vault_oidc_roles:
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
