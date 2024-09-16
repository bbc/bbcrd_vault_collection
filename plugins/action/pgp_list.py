from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError

from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.pgp import (
    in_specified_gnupg_home,
    pgp_list_fingerprints,
)

import os
import sys

from subprocess import run
from base64 import b64decode, b64encode

DOCUMENTATION = r"""
module: bbcrd.ansible_vault.pgp_list

short_description: Enumerate the fingerprints of available public or private PGP keys on the control node.

options:
    type:
        description: |-
            One of 'public' or 'private'.
        required: true
        type: str
    gnupg_home:
        description: |-
            The GnuPG home directory for gpg. If not given, the GNUPGHOME
            environment variable (on the control node) will be used.
        required: false
        type: str
"""

RETURN = r"""
fingerprints:
    description: |-
        The available key fingerprints.
    type: str
    returned: always
"""

EXAMPLES = r"""
- name: Enumerate private key fingerprints
  bbcrd.ansible_vault.pgp_list
    type: private
  register: result
"""


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars={}):
        with in_specified_gnupg_home(self._task):
            type = self._task.args["type"]
            if type == "public":
                return {"fingerprints": pgp_list_fingerprints(private_keys=False)}
            elif type == "private":
                return {"fingerprints": pgp_list_fingerprints(private_keys=True)}
            else:
                raise AnsibleError("'type' must be 'public' or 'private'")
