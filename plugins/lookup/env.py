"""
An Ansible lookup plugin for obtaining Vault configuration environment
variables, accounting for the plurality of names tried by implementations such
as OpenBao.

Tries 'VAULT_ADDR':

    "{{ lookup('bbcrd.vault.env', 'ADDR') }}"

Tries 'BAO_ADDR' then 'VAULT_ADDR':

    "{{ lookup('bbcrd.vault.env', 'ADDR', 'bao') }}"

Also accepts custom default values (rather than the default of None) when no
variable is set:

    "{{ lookup('bbcrd.vault.env', 'ADDR', 'bao', 'https://localhost:8200') }}"
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

from ansible_collections.bbcrd.vault.plugins.module_utils.environment_variables import (
    get_vault_environment_variable
)


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        try:
            return [get_vault_environment_variable(*terms)]
        except Exception as exc:
            raise AnsibleError(f"failed to lookup Vault token: {exc}")
