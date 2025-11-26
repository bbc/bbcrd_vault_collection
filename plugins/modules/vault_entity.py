from typing import Dict, Iterable
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)


DOCUMENTATION = r"""
module: bbcrd.vault.vault_entity

short_description: Create, modify and delete Vault entities

options:
    name:
        description: |-
            The entity name.
        required: true
        type: str
    metadata:
        description: |-
            User-defined metadata associated with the entity.
        required: false
        type: dict
    policies:
        description: |-
            A list of policies to give the entity.
        required: false
        type: list
    disabled:
        description: |-
            Whether to disable this entity.
        required: false
        type: bool
    state:
        description: |-
            'present' or 'absent' (defaults to present).
        required: false
        type: str
    vault_url:
        description: |-
          The base URL of the vault server. Overrides any address configured
          via envrionment variables.
        required: false
        type: str
    vault_namespace:
        description: |-
          The vault namespace to issue the command to. Overrides any namespace
          configured via envrionment variables.
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

EXAMPLES = r"""
- name: Create an entity
  bbcrd.vault.vault_entity:
    name: jonathan
    metadata:
      team: cans
      created_by: ansible
    policies:
      - admin

- name: Delete an entity
  bbcrd.vault.vault_entity:
    name: fred
    state: absent
"""

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type="str", required=True),
        metadata=dict(type="dict", required=False, default={}),
        policies=dict(type="list", required=False, default=[]),
        disabled=dict(type="bool", required=False, default=False),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)
    name = module.params["name"]
    metadata = module.params["metadata"]
    policies = module.params["policies"]
    disabled = module.params["disabled"]
    state = module.params["state"]

    result = {"changed": False}
    
    # Get current state (if any)
    existing_entity = vault_api_request(
        module,
        f"/v1/identity/entity/name/{name}",
        expected_status=[200, 404],
    ).get("data")
    
    if state == "present":
        if (
            existing_entity is None
            or existing_entity["metadata"] != metadata
            or sorted(existing_entity["policies"]) != sorted(policies)
            or existing_entity["disabled"] != disabled
        ):
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/identity/entity/name/{name}",
                method="POST",
                data={
                    "metadata": metadata,
                    "policies": policies,
                    "disabled": disabled,
                }
            )
    elif state == "absent":
        if existing_entity is not None:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/identity/entity/name/{name}",
                method="DELETE",
            )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
