from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError

from ansible_collections.bbcrd.vault.plugins.module_utils.pgp import (
    in_specified_gnupg_home
)

import os
import sys

from subprocess import run
from base64 import b64decode, b64encode

DOCUMENTATION = r"""
module: bbcrd.vault.pgp_encrypt

short_description: Encrypt PGP-encrypted data (runs on the control host).

options:
    plaintext:
        description: |-
            The base64-encoded plaintext to be encrypted.
        required: true
        type: str
    public_key:
        description: |-
            A GPG-accepted identifier for the public key to use, e.g. a
            fingerprint.
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
ciphertext:
    description: |-
        The base64-encoded ciphertext value.
    type: str
    returned: always
"""

EXAMPLES = r"""
- name: Encrypt some data
  bbcrd.vault.pgp_encrypt:
    plaintext: "{{ lookup('file', 'plaintext.txt') | b64encode }}"
    public_key: 50D33D60B705C5AD601C0214C0035C10517F50F6
  register: result
"""


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars={}):
        with in_specified_gnupg_home(self._task):
            plaintext_base64 = self._task.args["plaintext"]
            public_key = self._task.args["public_key"]
            output = run(
                [
                    "gpg",
                    "--no-tty",
                    "--encrypt",
                    "--trust-model",
                    "always",
                    "--recipient",
                    public_key,
                ],
                input=b64decode(plaintext_base64),
                capture_output=True,
            )
            if output.returncode != 0:
                raise AnsibleError(f"Could not encrypt data.\n{output.stderr.decode()})".rstrip())
            ciphertext_base64 = b64encode(output.stdout).decode()
            
            return {
                "changed": False,
                "ciphertext": ciphertext_base64
            }
