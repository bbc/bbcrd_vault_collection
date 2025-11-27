import os
import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bbcrd.vault.plugins.module_utils.vault import (
    get_vault_api_request_argument_spec,
    vault_api_request,
)


DOCUMENTATION = r"""
module: bbcrd.vault.vault_token_lookup

short_description: Look up the current token's metadata using the /auth/token/lookup-self API endpoint.

options:
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

RETURN = r"""
token:
    description: |-
        Token information, as returned by the auth/token/lookup-self endpoint.
    type: dict
    returned: always
"""

EXAMPLES = r"""
- name: Look up current token info
  no_log: true
  bbcrd.vault.vault_token_lookup:
  register: token_info
"""

def run_module():
    module_args = dict(
        **get_vault_api_request_argument_spec(),
    )

    module = AnsibleModule(argument_spec=module_args)

    data = vault_api_request(
        module,
        f"/v1/auth/token/lookup-self",
        expected_status=[200, 404],
    ).get("data")

    module.exit_json(changed=False, token=data)


def main():
    run_module()


if __name__ == "__main__":
    main()
