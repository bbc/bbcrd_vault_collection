import os
from itertools import chain
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)
from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.dict_compare import (
    dict_issubset,
)


DOCUMENTATION = r"""
module: bbcrd.ansible_vault.vault_auth_methods

short_description: Enable and disable Vault authentication methods.

description: |-
    Declaratively manage Vault authentication methods.

options:
    auth_methods:
        description: |-
            A dictionary mapping from auth mount names (with no trailing slash)
            to an auth method paramters or to null (to delete the auth method).
            
            An auth method is defined using the parameters defined in the vault
            documentation:
            https://developer.hashicorp.com/vault/api-docs/system/auth#enable-auth-method
            
            If the parameters provided don't match those of the auth method's
            configuration, the auth method will be deleted and recreated as
            Vault doesn't support modifying an existing auth method.
        required: true
        type: dict
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
- name: Create setup auth methods
  bbcrd.ansible_vault.vault_auth_methods:
    auth_methods:
      oidc:
        type: oidc
      github: null   # Delte github auth
"""


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        auth_methods=dict(type="dict", required=True),
        **get_vault_api_request_argument_spec()
    )

    module = AnsibleModule(argument_spec=module_args)
    desired_auth_methods = module.params["auth_methods"]

    result = {"changed": False}
    
    current_auth_methods = vault_api_request(module, f"/v1/sys/auth")["data"]

    to_delete = []
    to_update = {}
    to_create = {}
    for mount, params in desired_auth_methods.items():
        if params is None:
            if f"{mount}/" in current_auth_methods:
                to_delete.append(mount)
        elif f"{mount}/" not in current_auth_methods:
            to_create[mount] = params
        elif not dict_issubset(params, current_auth_methods[f"{mount}/"]):
            to_update[mount] = params

    # Remove deleted or changed auth methods
    for mount in chain(to_delete, to_update):
        result["changed"] = True
        vault_api_request(
            module,
            f"/v1/sys/auth/{mount}",
            method="DELETE",
        )
    
    # Create (or recreate) added or changed methods
    for mount, params in dict(**to_update, **to_create).items():
        result["changed"] = True
        vault_api_request(
            module,
            f"/v1/sys/auth/{mount}",
            method="POST",
            data=params,
        )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
