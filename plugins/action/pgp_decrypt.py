from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError

from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.pgp import (
    in_specified_gnupg_home
)

import os
import sys

from subprocess import run
from base64 import b64decode, b64encode

DOCUMENTATION = r"""
module: bbcrd.ansible_vault.pgp_decrypt

short_description: Decrypt PGP-encrypted data (runs on the control host).

options:
    ciphertext:
        description: |-
            The base64-encoded ciphertext to be decrypted.
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
plaintext:
    description: |-
        The base64-encoded decrypted value.
    type: str
    returned: always
"""

EXAMPLES = r"""
- name: Decrypt some data
  bbcrd.ansible_vault.pgp_decrypt:
    ciphertext: "{{ lookup('file', 'encrypted.pgp') | b64encode }}"
  register: result
"""


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars={}):
        with in_specified_gnupg_home(self._task):
            ciphertext_base64 = self._task.args["ciphertext"]
            output = run(
                [
                    "gpg",
                    "--no-tty",
                    "--decrypt",
                ],
                input=b64decode(ciphertext_base64),
                capture_output=True,
            )
            if output.returncode != 0:
                raise AnsibleError(f"Could not decrypt data.\n{output.stderr.decode()})".rstrip())
            plaintext_base64 = b64encode(output.stdout).decode()
            
            return {
                "changed": False,
                "plaintext": plaintext_base64
            }
