"""
Utilities for determining Vault configuration from the environment.
"""

from typing import Optional

import os
import re
import json
from pathlib import Path
from subprocess import run


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
    ignore_environment: bool = False,
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

    The 'config_dir' argument is intended for test use only. Its behaviour is
    to change where we look for the .vault or .bao config file.
    
    The 'ignore_environment' argument is also intended for test use only and
    its behaviour is to ignore any environment variables.
    """
    # Determine Vault URL
    if vault_url is None:
        vault_url = get_vault_environment_variable(
            "ADDR",
            implementation,
            "https://localhost:8200",
        )

    # Look up token in environment
    if not ignore_environment:  # Used only in tests
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
