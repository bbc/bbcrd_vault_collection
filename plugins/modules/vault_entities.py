from typing import Dict, Iterable
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)


DOCUMENTATION = r"""
module: bbcrd.ansible_vault.vault_entities

short_description: Create, modify and delete Vault entities and entity aliases.

description: |-
    Declaratively manage entities and entity-aliases in Vault's identity secret
    store.

options:
    entities:
        description: |-
            A dictionary mapping from entity names to an entity definition (to
            create/update the entity) or to null (to delete the entity).
            
            An entity definition is a dictionary with the following keys:
            
            * metadata -- Optional. A string-string dictionary of user-defined
              metadata values. Default: {}.
            * policies -- Optional. A list of policy names. Default: []
            * disabled -- Optional. Default false.
            * aliases -- Optional: The entity-alias definitions for this
              entity. Any entity-aliases not specified in this list will be
              deleted. Default: [].
            
            An entity-alias definition is a dictionary with the following keys:
            
            * name -- The name of the entity-alias. Required.
            * mount_accessor -- The name of the associated auth method's mount
              accessor. Required iff auth_mount is not specified.
            * auth_mount -- The mount path of the associated auth method (e.g.
              'oidc/'. Required iff mount_accessor is not specified.
            * custom_metadata -- Optional. A string-string dictionary of
              user-defined metadata values. Default: {}.
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
- name: Create some entities
  bbcrd.ansible_vault.vault_entities:
    entities:
      jonathan:
        metadata:
          team: cans
          created_by: ansible
        policies:
          - admin
        aliases:
          - name: jonathan.heathcote@bbc.co.uk
            auth_mount: oidc/
          - name: jonathah
            auth_mount: ldap/
          - name: mossblaser
            auth_mount: github/
      judas: null  # Delete this entity
"""

RETURN = r"""
entities:
    description: |-
        The full details of the resulting entities and entity aliases for each
        of the defined entities provided.
    type: dict
    returned: always
    sample:
        jonathan:
            aliases:
              - canonical_id: "3e21898e-97ba-5d49-ed25-2aaccb132d78",
                id: "214ca34f-f81d-ac1e-2bb4-1eb7dd86a029",
                mount_accessor: "auth_oidc_9383b083",
                name: "jonathan.heathcote@bbc.co.uk"
                custom_metadata: {},
                ...
              ...
            id: "3e21898e-97ba-5d49-ed25-2aaccb132d78"
            metadata:
              team: cans
              created_by: ansible
            name: "jonathan"
            policies:
              - admin
            ...
        ...
"""


def fill_entity_defaults(params: dict) -> dict:
    """Return a copy of the entity parameters with default values filled in."""
    params = params.copy()
    params.setdefault("metadata", {})
    params.setdefault("policies", [])
    params.setdefault("disabled", False)
    params.setdefault("aliases", [])
    return params


def enumerate_named_entities(
    module: AnsibleModule, names: Iterable[str]
) -> Dict[str, dict]:
    """
    Enumerate the details of entities with the provided names. Where a name
    does not exist, no value will be present in the returned dictionary.
    """
    entities = {}

    for name in names:
        response = vault_api_request(
            module,
            f"/v1/identity/entity/name/{name}",
            expected_status=(200, 404),
        ).get("data")
        if response is not None:
            entities[name] = response

    return entities


def modify_entities(module: AnsibleModule) -> dict:
    """Add/Remove/Change entities as required."""
    result = {}

    entities_to_delete = [
        name for name, params in module.params["entities"].items() if params is None
    ]
    desired_entities = {
        name: fill_entity_defaults(params)
        for name, params in module.params["entities"].items()
        if params is not None
    }

    # Remove deleted entities (if present)
    for name in enumerate_named_entities(module, entities_to_delete):
        result["changed"] = True
        vault_api_request(module, f"/v1/identity/entity/name/{name}", method="DELETE")

    # Create or update entities
    current_entities = enumerate_named_entities(module, desired_entities)
    for name, desired_entity in desired_entities.items():
        changed_or_new = (
            name not in current_entities
            or desired_entity["metadata"] != current_entities[name]["metadata"]
            or desired_entity["disabled"] != current_entities[name]["disabled"]
            or sorted(desired_entity["policies"])
            != sorted(current_entities[name]["policies"])
        )
        if changed_or_new:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/identity/entity/name/{name}",
                method="POST",
                data={
                    "metadata": desired_entity["metadata"],
                    "policies": desired_entity["policies"],
                    "disabled": desired_entity["disabled"],
                },
            )

    return result


def fill_entity_alias_defaults(
    params: dict, canonical_id: str, mount_accessors: Dict[str, str]
) -> dict:
    """
    Return a copy of the entity alias parameters with default values filled in.

    Takes the associated entity ID (canonical_id) and a lookup from auth mount
    point to mount accessor.
    """
    params = params.copy()
    params.setdefault("custom_metadata", {})
    params.setdefault("canonical_id", canonical_id)
    if "auth_mount" in params:
        params.setdefault("mount_accessor", mount_accessors[params["auth_mount"]])
    return params


def modify_entity_aliases(module: AnsibleModule) -> dict:
    """Add/Remove/Change entity aliases as required."""
    result = {}

    # Enumerate existing entity-aliases
    entity_names = {
        name for name, entity in module.params["entities"].items() if entity is not None
    }
    current_entities = enumerate_named_entities(module, entity_names)
    current_aliases = {
        (alias["name"], alias["mount_accessor"]): alias
        for entity in current_entities.values()
        for alias in entity["aliases"]
    }

    # Enumerate mount accessors (to translate from auth mounts to accessors)
    mount_accessors = {
        path: details["accessor"]
        for path, details in vault_api_request(module, "/v1/sys/auth")["data"].items()
    }

    # Enumerate desired entity-aliases
    desired_aliases = {}
    for entity_name, entity in module.params["entities"].items():
        if entity is not None:
            for alias in fill_entity_defaults(entity)["aliases"]:
                alias = fill_entity_alias_defaults(
                    alias,
                    canonical_id=current_entities[entity_name]["id"],
                    mount_accessors=mount_accessors,
                )
                desired_aliases[(alias["name"], alias["mount_accessor"])] = alias

    # Delete extra entity-aliases
    for key in set(current_aliases) - set(desired_aliases):
        result["changed"] = True
        vault_api_request(
            module,
            f"/v1/identity/entity-alias/id/{current_aliases[key]['id']}",
            method="DELETE",
        )

    # Create/update entity-aliases
    for key, desired_alias in desired_aliases.items():
        changed_or_new = (
            key not in current_aliases
            or desired_alias["custom_metadata"]
            != current_aliases[key]["custom_metadata"]
            or desired_alias["canonical_id"] != current_aliases[key]["canonical_id"]
        )
        if changed_or_new:
            result["changed"] = True
            vault_api_request(
                module,
                "/v1/identity/entity-alias",
                method="POST",
                data={
                    "canonical_id": desired_alias["canonical_id"],
                    "name": desired_alias["name"],
                    "mount_accessor": desired_alias["mount_accessor"],
                    "custom_metadata": desired_alias["custom_metadata"],
                },
            )

    return result


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        entities=dict(type="dict", required=True),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)

    result = {"changed": False}
    
    # Perform the modifications
    result.update(modify_entities(module))
    result.update(modify_entity_aliases(module))

    # Get the resulting entities
    result["entities"] = enumerate_named_entities(
        module,
        [name for name, entity in module.params["entities"].items() if entity is not None],
    )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
