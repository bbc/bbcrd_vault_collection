from typing import Dict, Iterable
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)


DOCUMENTATION = r"""
module: bbcrd.vault.vault_namespace

short_description: Create and destroy namespaces.

description: |-
    Create and destroy namespaces.

options:
    name:
        description: |-
            The name of the namespace (without a trailing slash). If
            vault_namespace is set, this will create a child namespace.
        type: str
        required: true
    custom_metadata:
        description: |-
            Custom metadata to be associated with the namespace.
        type: dict
        required: false
    state:
        description: |-
            Either present or absent.
        required: false
        type: str
        default: "present"
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
- name: Create a namespace
  bbcrd.vault.vault_namespace:
    name: ns1
"""


def run_module():
    module_args = dict(
        name=dict(type="str", required=True),
        custom_metadata=dict(type="dict", required=False, default={}),
        state=dict(
            type="str",
            choices=[
                "present",
                "absent",
            ],
            default="present",
        ),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)
    name = module.params["name"]
    custom_metadata = module.params["custom_metadata"]
    state = module.params["state"]

    result = {"changed": False}

    # Get namespace state
    existing_namespace = vault_api_request(
        module,
        f"/v1/sys/namespaces/{name}",
        expected_status=(200, 404),
    )
    namespace_exists = "data" in existing_namespace

    if state == "absent":
        # Delete if present
        if namespace_exists:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/namespaces/{name}",
                method="DELETE"
            )
    elif state == "present":
        # Create if not present
        if not namespace_exists:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/namespaces/{name}",
                data={"custom_metadata": custom_metadata},
                method="POST"
            )
        # Update if custom_metadata changed
        elif existing_namespace["data"]["custom_metadata"] != custom_metadata:
            removed_keys = set(existing_namespace["data"]["custom_metadata"]) - set(custom_metadata)
            for key in removed_keys:
                custom_metadata[key] = None
            
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/namespaces/{name}",
                data={"custom_metadata": custom_metadata},
                method="PATCH"
            )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
