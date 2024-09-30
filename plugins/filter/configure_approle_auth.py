"""
Filters specifically for use within the
bbcrd.vault.configure_approle_auth role and not intended for external
use.
"""

from typing import Any

def aggregate_approle_parameters(
    hosts: list[str],
    mount: str,
    defaults: dict[str, dict[str, Any]],
    hostvars,
) -> dict[str, dict[str, Any]]:
    """
    Assemble a mapping {host: {approle_param: approle_value, ...}, ...} based
    on the defaults given and the `ansible_vault_approle[mount]` values defined
    in the hostvars of the given hosts.
    """
    roles = {}
    for host in hosts:
        params = defaults.get(mount, {}).copy()
        params.update(hostvars[host].get("ansible_vault_approle", {}).get(mount, {}))
        roles[host] = params
    return roles


class FilterModule(object):
    def filters(self):
        return {
            "aggregate_approle_parameters": aggregate_approle_parameters,
        }
