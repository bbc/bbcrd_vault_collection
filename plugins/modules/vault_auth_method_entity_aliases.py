from typing import Dict, Iterable
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)


DOCUMENTATION = r"""
module: bbcrd.vault.vault_auth_method_entity_aliases

short_description: Manage all entity aliases for a particular auth method in a declarative way.

description: |-
    Declaratively control the complete set of entity aliases for a defined for
    a single auth method.

options:
    mount:
        description: |-
            The mountpoint of the auth method (without a trailing slash). For
            example 'userpass'.
        type: str
        required: true
    entity_aliases:
        description: |-
            A dictionary mapping from entity alias names to strings or dictionaries.
            
            Where a string is given, this is the name of the entity this entity
            alias belongs to.
            
            Where a dict is given, this should have the following keys:
            
            * entity_name -- The name of the entity. Required.
            * custom_metadata -- Optional. A string-string dictionary of
              user-defined metadata values for the entity alias.
            
            When an entity with the provided name does not exist, one will be
            created automatically.
            
            Entity aliases for this mount point not enumerated in this argument
            are deleted.
        required: true
        type: dict
    vault_url:
        description: |-
          The base URL of the vault server. Overrides any address configured
          via envrionment variables.
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
- name: Create some entities
  bbcrd.vault.vault_auth_method_entity_aliases:
    mount: github
    entity_aliases:
        # Simple form (mapping entity-alias name, e.g. github user, to entity name)
        mossblaser: jonathah
        andrewbonney: andrewbo
        stuartgrace-bbc: stuartgr
        
        # Complex form, allows adding extra metadata to the entity alias
        jrosser:
          entity_name: jrosser
          custom_metadata:
            boss: true
"""


def run_module():
    module_args = dict(
        mount=dict(type="str", required=True),
        entity_aliases=dict(type="dict", required=True),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)
    mount = module.params["mount"]
    entity_aliases = module.params["entity_aliases"]

    result = {"changed": False}

    # Lookup auth accessor
    mount_accessor = vault_api_request(module, "/v1/sys/auth")["data"][f"{mount}/"][
        "accessor"
    ]

    # Get a list of current entity aliases for this auth method
    existing_entity_aliases = {
        entity_alias_id: params
        for entity_alias_id, params in vault_api_request(
            module,
            "/v1/identity/entity-alias/id",
            method="LIST",
            expected_status=[200, 404],
        )
        .get("data", {})
        .get("key_info", {})
        .items()
        if params["mount_accessor"] == mount_accessor
    }

    # Delete any aliases not listed
    for entity_alias_id, params in existing_entity_aliases.items():
        if params["name"] not in entity_aliases:
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/identity/entity-alias/id/{entity_alias_id}",
                method="DELETE",
            )

    # Add/update the rest where required
    for entity_alias_name, spec in entity_aliases.items():
        if isinstance(spec, str):
            entity_name = spec
            params = {}
        else:
            entity_name = spec.pop("entity_name")
            params = spec
        params.setdefault("custom_metadata", None)

        # Make sure entity exists and get its ID
        entity = vault_api_request(
            module,
            f"/v1/identity/entity/name/{entity_name}",
            expected_status=[200, 404],
        ).get("data")
        if entity is None:
            result["changed"] = True
            entity = vault_api_request(
                module,
                f"/v1/identity/entity/name/{entity_name}",
                method="POST",
                expected_status=[200, 404],
            )["data"]
        entity_id = entity["id"]

        matching_existing_entity_aliases = [
            existing_params
            for existing_entity_alias_id, existing_params in existing_entity_aliases.items()
            if existing_params["name"] == entity_alias_name
        ]
        assert len(matching_existing_entity_aliases) in [0, 1]

        if (
            # New
            matching_existing_entity_aliases == []
            # Needs updating
            or entity_id != matching_existing_entity_aliases[0]["canonical_id"]
            or any(
                v != matching_existing_entity_aliases[0].get(k)
                for k, v in params.items()
            )
        ):
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/identity/entity-alias",
                method="POST",
                data=dict(
                    canonical_id=entity_id,
                    name=entity_alias_name,
                    mount_accessor=mount_accessor,
                    **params,
                ),
            )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
