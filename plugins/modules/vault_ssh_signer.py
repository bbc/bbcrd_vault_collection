import os
import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)


DOCUMENTATION = r"""
module: bbcrd.ansible_vault.vault_ssh_signer

short_description: Configure the Vault SSH signing secrets engine.

options:
    ca:
        description: |-
            The certificate authority to configure, as per the vault docs:
            https://developer.hashicorp.com/vault/api-docs/secret/ssh#parameters-7
            
            Unless state is 'replaced', the configuration will only be written
            the first time this module runs.
        required: true
        type: dict
    roles:
        description:
            A mapping from role-name to role configuration parameters as
            defined in the vault docs:
            https://developer.hashicorp.com/vault/api-docs/secret/ssh#parameters
            
            Roles which are not present in this list will be deleted.
        required: false
        type: dict
        default: []
    state:
        description: |-
            One of the following options:
            
            * 'present' -- Enables the secrets engine and configures the set of
              specified roles. Only writes the CA configuration on first use.
            * 'replaced' -- Like 'present' but writes (and potentially
              regenerates if generate_signing_key is True) the CA information
              on every use.
            * 'absent' -- Disables the secrets engine.
    mount:
        description: |-
            The mountpoint of the SSH secrets engine, without the trailing
            slash.
        required: false
        type: str
        default: "ssh"
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
- name: Configure SSH signing engine
  bbcrd.ansible_vault.vault_ssh_signer
    ca:
      generate_signing_key: true
    roles:
      admin:
        # Use Key-signing mode
        key_type: ca
        # Sign a user (not host) keys
        allow_user_certificates: true
        algorithm_signer: rsa-sha2-512
        # "user" = "principals"
        default_user: root,pdumon
        allowed_users: root,pdumon
        default_extensions:
          permit-X11-forwarding: ""
          permit-agent-forwarding: ""
          permit-port-forwarding: ""
          permit-pty: ""
          permit-user-rc: ""
        ttl: 43200
        max_ttl: 43200
    mount: ssh-client-signer
"""


def configure_ssh_secrets_engine(module: AnsibleModule, result: dict) -> None:
    state = module.params["state"]
    mount = module.params["mount"]
    
    # Remove any non-SSH secrets engine at the mount point
    existing_engine_type = vault_api_request(
        module,
        f"/v1/sys/mounts/{mount}",
        expected_status=[200, 400],
    ).get("data", {}).get("type")
    if existing_engine_type is not None and existing_engine_type != "ssh":
        result["changed"] = True
        vault_api_request(
            module,
            f"/v1/sys/mounts/{mount}",
            method="DELETE",
        )
    
    # Enable/disable SSH secrets engine as needed
    if state != "absent":
        if existing_engine_type != "ssh":
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/mounts/{mount}",
                method="POST",
                data={"type": "ssh"},
            )
    elif state == "absent":
        if existing_engine_type == "ssh":
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/sys/mounts/{mount}",
                method="DELETE",
            )


def configure_ca(module: AnsibleModule, result: dict) -> None:
    ca = module.params["ca"]
    state = module.params["state"]
    mount = module.params["mount"]
    
    if state in ("present", "replaced"):
        existing_ca = vault_api_request(
            module,
            f"/v1/{mount}/config/ca",
            method="GET",
            expected_status=[200, 400],
        ).get("data")
        if (
            existing_ca is None
            or (
                state == "replaced"
                and ca.get("public_key") != existing_ca["public_key"]
            )
        ):
            result["changed"] = True
            vault_api_request(
                module,
                f"/v1/{mount}/config/ca",
                method="POST",
                data=ca,
            )


def configure_roles(module: AnsibleModule, result: dict) -> None:
    roles = module.params["roles"]
    state = module.params["state"]
    mount = module.params["mount"]
    
    if state in ("present", "replaced"):
        existing_roles = vault_api_request(
            module,
            f"/v1/{mount}/roles",
            method="LIST",
            expected_status=[200, 404],
        ).get("data", {}).get("keys", [])
        
        # Delete roles
        for role_name in set(existing_roles) - set(roles):
            result["changed"] = True
            vault_api_request(module, f"/v1/{mount}/roles/{role_name}", method="DELETE")
        
        # Create/update roles
        for role_name, params in roles.items():
            existing_params = vault_api_request(
                module,
                f"/v1/{mount}/roles/{role_name}",
                expected_status=[200, 404],
            ).get("data")
            if (
                existing_params is None
                or any(
                    key not in existing_params or existing_params[key] != value
                    for key, value in params.items()
                )
            ):
                result["changed"] = True
                vault_api_request(
                    module,
                    f"/v1/{mount}/roles/{role_name}",
                    method="POST",
                    data=params
                )


def run_module():
    module_args = dict(
        ca=dict(type="dict", default={}),
        roles=dict(type="dict", default={}),
        state=dict(
            type="str",
            choices=[
                "present",
                "replaced",
                "absent",
            ],
            default="present",
        ),
        mount=dict(type="str", default="ssh"),
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)
    result = {"changed": False}

    configure_ssh_secrets_engine(module, result)
    configure_ca(module, result)
    configure_roles(module, result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
