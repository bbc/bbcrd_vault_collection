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
