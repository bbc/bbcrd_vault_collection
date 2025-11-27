"""
An Ansible lookup plugin for obtaining a Vault token from the environment.

Basic usage::

    "{{ lookup('bbcrd.vault.token') }}"

This will attempt to obtain the Vault token from the VAULT_TOKEN environment
variable or Vault token helper.

If using another Vault implementation, e.g. OpenBao, you can specify this and
this tool will also attempt to read (e.g.) BAO_TOKEN and the OpenBao token
helper:

    "{{ lookup('bbcrd.vault.token', 'bao') }}"

If using a Vault address not specified in the environment add this as your
second argument:

    "{{ lookup('bbcrd.vault.token', 'bao', 'https://bao.example.com:8200') }}"
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

from ansible_collections.bbcrd.vault.plugins.module_utils.environment_variables import (
    get_token_from_environment,
)


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        try:
            return [get_token_from_environment(*terms)]
        except Exception as exc:
            raise AnsibleError(f"failed to lookup Vault token: {exc}")
