from typing import Tuple, Any
import os
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

def get_vault_api_request_argument_spec() -> dict: 
    """
    Return Ansible module arugment spec variables for the arguments
    expected/used by vault_api_request.
    """
    return dict(
        vault_url=dict(
            type="str",
            required=False,
            default=os.environ.get("VAULT_ADDR", "https://localhost:8200"),
        ),
        vault_token=dict(
            type="str",
            required="VAULT_TOKEN" not in os.environ,
            default=os.environ.get("VAULT_TOKEN"),
        ),
        vault_ca_path=dict(
            type="str", required=False, default=os.environ.get("VAULT_CACERT")
        ),
    )


def vault_api_request(
    module: AnsibleModule,
    api_path: str,
    method: str = "GET",
    data: Any = None,
    expected_status: Tuple[int] = (200, 204),
) -> Any:
    """
    Make a vault API request using the base URL, CA certificate and vault token
    supplied to the module.

    The api_path should be a URL suffix to append to the base URL.

    The data, if not None, will be JSON encoded and sent as the payload with an
    appropriate Content-Type header.

    The response will be JSON decoded (if appropriate) or None if a 204 status
    was returned.

    Status codes outside expected_status will be treated as a fatal error.
    """
    vault_url = module.params["vault_url"]
    vault_token = module.params["vault_token"]
    vault_ca_path = module.params["vault_ca_path"]

    headers = {"X-Vault-Token": vault_token}

    if data is not None:
        data = json.dumps(data)
        headers["Content-Type"] = "application/json"

    response, info = fetch_url(
        module,
        f"{vault_url}{api_path}",
        method=method,
        data=data,
        headers=headers,
        ca_path=vault_ca_path,
    )
    if response is None:
        module.fail_json(info)

    # Retrieve response
    response_body = response.read() if info["status"] < 400 else info["body"]

    # Check status code
    if info["status"] not in expected_status:
        module.fail_json(
            msg=f"Got {info['status']} status, expected {expected_status}",
            method=method,
            api_path=api_path,
            data=data,
            response_body=response_body,
        )

    # Unpack JSON response (if JSON)
    if info["status"] == 204:
        response_body = None
    elif response_body and info.get("content-type") == "application/json":
        response_body = json.loads(response_body)

    return response_body
