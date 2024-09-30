import os
import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)


DOCUMENTATION = r"""
module: bbcrd.vault.vault_audit

short_description: Enable, configure or disable an audit device.

description: |-
    Warning: Changing any setting will result in a new audit device being
    created from scratch. This will delete the state needed to compute HMACs of
    secret values in the old audit log.

options:
    mount: str
        description: |-
            The mount point of the audit device (without the trailing slash).
        type: str
        required: true
    type: str
        description: |-
            The audit device type.
        type: str
        required: true
    description: str
        description: |-
            Human-readable description.
        type: str
        required: false
    options: str
        description: |-
            Type-specific options for the audit device, see Vault docs:
            https://developer.hashicorp.com/vault/api-docs/system/audit#options
        type: dict
        required: false
    state:
        description: |-
            One of 'present' or 'absent'.
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
- name: Enable audit logging to stdout
  bbcrd.vault.vault_audit
    mount: stdout
    type: file
    options:
      file_path: stdout
"""

def run_module():
    module_args = dict(
        mount=dict(type="str", required=True),
        type=dict(type="str", required=True),
        description=dict(type="str", default=""),
        options=dict(type="dict", default={}),
        state=dict(
            type="str",
            choices=["present", "absent"],
            default="present",
        ),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)
    result = {"changed": False}

    mount = module.params["mount"]
    type = module.params["type"]
    description = module.params["description"]
    options = module.params["options"]
    state = module.params["state"]
    
    # Delete any audit device with the wrong config at this mount point
    audit_devices = vault_api_request(module, f"/v1/sys/audit").get("data", {})
    existing_device = audit_devices.get(f"{mount}/")
    if (
        existing_device is not None
        and (
            existing_device["type"] != type
            or existing_device["description"] != description
            or any(
                key not in existing_device["options"] or existing_device["options"][key] != value
                for key, value in options.items()
            )
        )
    ):
        result["changed"] = True
        vault_api_request(
            module,
            f"/v1/sys/audit/{mount}",
            method="DELETE",
        )
        existing_device = None
    
    # Enable/disable audit device as needed
    if state == "present":
        # NB: If it still exists, its config is correct so no need to do
        # anything
        if existing_device is None:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/audit/{mount}",
                method="POST",
                data={
                    "type": type,
                    "description": description,
                    "options": options,
                },
            )
    elif state == "absent":
        if existing_device is not None:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/audit/{mount}",
                method="DELETE",
            )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
