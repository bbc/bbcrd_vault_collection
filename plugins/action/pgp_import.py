from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError

from ansible_collections.bbcrd.vault.plugins.module_utils.pgp import (
    in_specified_gnupg_home,
    pgp_key_metadata,
    ascii_armor_to_base64,
    pgp_list_fingerprints,
)

import os
import sys

from subprocess import run
from base64 import b64decode, b64encode

DOCUMENTATION = r"""
module: bbcrd.vault.pgp_import

short_description: Import a PGP public key into the GnuPG environment on the control host.

options:
    public_key:
        description: |-
            The ASCII-armoured PGP public key to be imported.
        required: true
        type: str
    gnupg_home:
        description: |-
            The GnuPG home directory for gpg. If not given, the GNUPGHOME
            environment variable (on the control node) will be used.
        required: false
        type: str
"""

EXAMPLES = r"""
- name: Import a public key
  bbcrd.vault.pgp_import:
    public_key: "{{ lookup('file', 'public_key.pgp') }}"
  register: result
"""


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars={}):
        with in_specified_gnupg_home(self._task):
            public_key = b64decode(ascii_armor_to_base64(self._task.args["public_key"]))
            
            # Don't import if already imported
            fingerprint = pgp_key_metadata(public_key)["fingerprint"]
            if fingerprint in pgp_list_fingerprints():
                return {"changed": False}
            
            output = run(
                [
                    "gpg",
                    "--batch",
                    "--no-tty",
                    "--import",
                ],
                input=public_key,
                capture_output=True,
            )
            if output.returncode != 0:
                raise AnsibleError(f"Could not import public key.\n{output.stderr.decode()})".rstrip())
            return {
                "changed": True,
            }
