from typing import Dict, Iterable
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)


DOCUMENTATION = r"""
module: bbcrd.vault.vault_group

short_description: Create, manage or delete a (local) identity group in Vault.

description: |-
    Declaratively control the complete membership and policy set of a Vault
    group.

options:
    name:
        description: |-
            The group's name
        required: true
        type: str
    metadata:
        description: |-
            Any user-defined metadata to associate with the group.
        required: false
        type: dict
        default: {}
    policies:
        description: |-
            The list of policies granted as a result of membership of this
            group.
        required: false
        type: list
        default: []
    members:
        description: |-
            List of entity names to be made members of this group. Entities
            which don't exist will be created automatically.
        required: false
        type: list
        default: []
    member_groups:
        description: |-
            List of group names to make members of this group.
        required: false
        type: list
        default: []
    state:
        description: |-
            'present' or 'absent' (defaults to present).
        required: false
        type: str
        default: present
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
- name: Create a group
  bbcrd.vault.vault_group:
    name: administrators
    policies:
      - kv_admin
      - ssh_admin
    members:
      - jonathah
      - andrewbo
      - stuartgr
      - jrosser
"""


def run_module():
    module_args = dict(
        name=dict(type="str", required=True),
        metadata=dict(type="dict", required=False, default={}),
        policies=dict(type="list", required=False, default=[]),
        members=dict(type="list", required=False, default=[]),
        member_groups=dict(type="list", required=False, default=[]),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)
    name = module.params["name"]
    metadata = module.params["metadata"]
    policies = module.params["policies"]
    members = module.params["members"]
    member_groups = module.params["member_groups"]
    state = module.params["state"]

    result = {"changed": False}

    # Get existing config
    existing_config = vault_api_request(
        module,
        f"/v1/identity/group/name/{name}",
        expected_status=[200, 404],
    ).get("data")

    # Apply the change
    if state == "present":
        # Lookup (and create if non-existing) entities
        member_entity_ids = []
        for entity_name in members:
            entity_id = vault_api_request(
                module,
                f"/v1/identity/entity/name/{entity_name}",
                expected_status=[200, 404],
            ).get("data", {}).get("id")
            
            if entity_id is None:
                result["changed"] = True
                entity_id = vault_api_request(
                    module,
                    f"/v1/identity/entity/name/{entity_name}",
                    method="POST",
                )["data"]["id"]
            
            member_entity_ids.append(entity_id)

        # Lookup member groups
        member_group_ids = []
        for group_name in member_groups:
            group_id = vault_api_request(
                module,
                f"/v1/identity/group/name/{group_name}",
            )["data"]["id"]
            member_group_ids.append(group_id)

        if (
            existing_config is None
            or existing_config["metadata"] != metadata
            or sorted(existing_config["member_entity_ids"]) != sorted(member_entity_ids)
            or sorted(existing_config["member_group_ids"] or []) != sorted(member_group_ids)
            or sorted(existing_config["policies"]) != sorted(policies)
        ):
            result["xxx_existing"] = existing_config
            result["xxx_metadata"] = metadata
            result["xxx_entity_ids"] = member_entity_ids
            result["xxx_group_ids"] = member_group_ids
            result["xxx_policies"] = policies
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/identity/group/name/{name}",
                method="POST",
                data={
                    "metadata": metadata,
                    "member_entity_ids": member_entity_ids,
                    "member_group_ids": member_group_ids,
                    "policies": policies,
                },
            )
    elif state == "absent":
        if existing_config is not None:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/identity/group/name/{name}",
                method="DELETE",
            )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
