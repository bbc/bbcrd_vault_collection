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
module: bbcrd.ansible_vault.vault_auth_method

short_description: Enable (or disable) a Vault authentication method.

description: |-
    Warning: If any of the parameters provided don't match those of the auth
    method's configuration, the auth method will be deleted and recreated as
    Vault doesn't support modifying an existing auth method.

options:
    type:
        description: |-
            The type of auth method to enable.
        type: str
        required: if state = present or mount not given.
    mount:
        description: |-
            The the mount point for this auth method, without the trailing
            slash. Defaults to the value of 'type'.
        type: str
        required: if state = absent and type not given.
    description:
        description: |-
            Free-text description.
        type: str
        required: false
    config:
        description: |-
            Configuration options for the auth method. See the vault docs: https://developer.hashicorp.com/vault/api-docs/system/auth#config
        type: dict
        required: false
    state:
        description: |-
            Either present or absent.
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

EXAMPLES = r"""
- name: Create setup auth methods
  bbcrd.ansible_vault.vault_auth_method:
    type: oidc
"""


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        type=dict(type="str", required=False, default=None),
        mount=dict(type="str", required=False, default=None),
        description=dict(type="str", required=False, default=""),
        config=dict(type="dict", required=False, default={}),
        state=dict(
            type="str",
            choices=[
                "present",
                "absent",
            ],
            default="present",
        ),
        **get_vault_api_request_argument_spec()
    )

    module = AnsibleModule(argument_spec=module_args)
    type = module.params["type"]
    mount = module.params["mount"]
    description = module.params["description"]
    config = module.params["config"]
    state = module.params["state"]

    result = {"changed": False}
    
    # Guess mount/type from their counterpart
    if mount is None:
        mount = type
    if type is None:
        type = mount
    if mount is None or type is None:
        module.fail_json(msg="Either mount or type must be specified.")
    
    desired = {
        "type": type,
        "description": description,
        "config": config,
    }
    
    actual = vault_api_request(
        module,
        f"/v1/sys/auth",
    )["data"].get(f"{mount}/")

    if state == "present":
        if actual is None or not dict_issubset(desired, actual):
            result["changed"] = True
            if actual is not None:
                vault_api_request(
                    module,
                    f"/v1/sys/auth/{mount}",
                    method="DELETE",
                )
            vault_api_request(
                module,
                f"/v1/sys/auth/{mount}",
                method="POST",
                data=desired,
            )
    elif state == "absent":
        if actual is not None:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/auth/{mount}",
                method="DELETE",
            )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
