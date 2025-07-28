import os
import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)


DOCUMENTATION = r"""
module: bbcrd.vault.vault_secrets_engine

short_description: Enable, configure (or disable) a secrets engine.

options:
    mount: str
        description: |-
            The mount point of the secrets engine (without the trailing slash).
        type: str
        required: true
    type: str
        description: |-
            The secrets engine type.
        type: str
        required: true
    description: str
        description: |-
            Human-readable description.
        type: str
        required: false
    config: str
        description: |-
            Configuration options for the secrets engine, see Vault docs:
            https://developer.hashicorp.com/vault/api-docs/system/mounts#config
        type: dict
        required: false
    options: str
        description: |-
            Type-specific options for the secrets engine, see Vault docs:
            https://developer.hashicorp.com/vault/api-docs/system/mounts#options
            
            Warning: Changing this option will cause any existing secrets
            engine to be destroyed and recreated!
        type: dict
        required: false
    state:
        description: |-
            One of 'present' or 'absent'.
    vault_url:
        description: |-
          The base URL of the vault server. Defaults to the contents of the
          VAULT_ADDR environment variable.
        required: false
        type: str
    vault_token:
        description: |-
          Token to use for Vault API calls. Defaults to the contents of the
          VAULT_TOKEN environment variable.
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
- name: Configure KV v1 secrets engine
  bbcrd.vault.vault_secrets_engine
    mount: secret
    type: kv
    options:
      version: "1"
"""

def run_module():
    module_args = dict(
        mount=dict(type="str", required=True),
        type=dict(type="str", required=True),
        description=dict(type="str", default=""),
        config=dict(type="dict", default={}),
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
    config = module.params["config"]
    options = module.params["options"]
    state = module.params["state"]
    
    # Delete any secrets engine with the wrong config at this mount point
    existing_engine = vault_api_request(
        module,
        f"/v1/sys/mounts/{mount}",
        expected_status=[200, 400],
    ).get("data")
    if (
        existing_engine is not None
        and (
            # Can't change type without recreating
            existing_engine["type"] != type
            # Can't change options without recreating
            or any(
                key not in existing_engine["options"] or existing_engine["options"][key] != value
                for key, value in options.items()
            )
        )
    ):
        result["changed"] = True
        vault_api_request(
            module,
            f"/v1/sys/mounts/{mount}",
            method="DELETE",
        )
        existing_engine = None
    
    # Enable/disable secrets engine as needed
    if state == "present":
        if existing_engine is None:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/mounts/{mount}",
                method="POST",
                data={
                    "type": type,
                    "description": description,
                    "config": config,
                    "options": options,
                },
            )
        elif (
            # Description changes
            existing_engine["description"] != description
            # Config option changed
            or any(
                key not in existing_engine["config"] or existing_engine["config"][key] != value
                for key, value in config.items()
            )
        ):
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/mounts/{mount}/tune",
                method="POST",
                data=dict(config, description=description),
            )
    elif state == "absent":
        if existing_engine is not None:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/mounts/{mount}",
                method="DELETE",
            )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
