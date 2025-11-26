from typing import Tuple, Any, Optional
import os
import re
import json
from pathlib import Path
from subprocess import run

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def get_vault_environment_variable(
    name: str,
    implementation: str = "vault",
    default: Optional[str] = None,
) -> Optional[str]:
    """
    Get the value of the named environment variable.

    For example if 'ADDR' is passed, will look up 'VAULT_ADDR'.

    If implementation is set to "bao", will try 'BAO_[name]' before
    'VAULT_[name]'.

    If no environment variable has been set, returns the default.
    """
    for prefix in [f"{implementation.upper()}_", "VAULT_"]:
        if prefix + name in os.environ:
            return os.environ[prefix + name]

    return default


def get_token_from_environment(
    implementation: str = "vault",
    vault_url: Optional[str] = None,
    config_dir: str = str(Path.home()),
) -> Optional[str]:
    """
    Determine the Vault token from information in the envrionment in the same
    way the Vault CLI does.

    If the VAULT_TOKEN environment variable is defined, its value will be
    returned.

    If a Vault token helper is configured, this will be used.

    If no token helper is configured, the .vault-token file will be used.

    If using OpenBao, the 'implementation' may be set to 'bao' to make this
    function consider the `BAO_ADDR` environment variable and OpenBao token
    helper.

    The 'vault_url' argument may be used to override the VAULT_ADDR (or similar
    for other implementations) from whatever the current environment specifies.

    The 'config_dir' argument is intended for test use only.
    """
    # Determine Vault URL
    if vault_url is None:
        vault_url = get_vault_environment_variable(
            "ADDR",
            implementation,
            "https://localhost:8200",
        )

    # Look up token in environment
    if vault_token := get_vault_environment_variable("TOKEN", implementation):
        return vault_token

    # Look in token helper
    vault_config_file = Path(config_dir) / f".{implementation}"
    token_helper_configured = False
    if vault_config_file.is_file():
        for line in vault_config_file.open():
            if match := re.match(r"^\s*token_helper\s*=\s*(.*)$", line):
                token_helper_configured = True
                helper_path = json.loads(match.group(1))
                helper = run(
                    [helper_path, "get"],
                    capture_output=True,
                    text=True,
                    check=True,
                    env=dict(
                        os.environ,
                        **{
                            "VAULT_ADDR": vault_url,
                            f"{implementation.upper()}_ADDR": vault_url,
                        },
                    ),
                )

                if helper.stdout:
                    return helper.stdout

    # Look in .vault-token if helper not configured
    if not token_helper_configured:
        token_file = Path(config_dir) / ".vault-token"
        if token_file.is_file():
            return token_file.read_text()

    # No token found
    return None


def get_vault_api_request_argument_spec() -> dict:
    """
    Return Ansible module arugment spec variables for the arguments
    expected/used by vault_api_request.
    """
    return dict(
        vault_url=dict(type="str", required=False),
        vault_token=dict(type="str", required=False),
        vault_ca_path=dict(type="str", required=False),
        vault_implementation=dict(type="str", required=False, default="vault"),
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
    vault_implementation = module.params["vault_implementation"]

    if "vault_url" in module.params:
        vault_url = module.params["vault_url"]
    else:
        vault_url = get_token_from_environment(
            "ADDR", vault_implementation, "https://localhost:8200"
        )

    if "vault_token" in module.params:
        vault_token = module.params["vault_token"]
    else:
        vault_token = get_token_from_environment(
            vault_implementation,
            vault_url=vault_url,
        )

    if "vault_ca_path" in module.params:
        vault_ca_path = module.params["vault_ca_path"]
    else:
        vault_ca_path = get_token_from_environment("CACERT", vault_implementation)

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
