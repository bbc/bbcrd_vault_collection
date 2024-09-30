from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError

from ansible_collections.bbcrd.vault.plugins.module_utils.pgp import (
    in_specified_gnupg_home,
)

import os
import sys

from subprocess import run
from base64 import b64decode, b64encode

DOCUMENTATION = r"""
module: bbcrd.vault.pgp_detect_card

short_description: Detect any inserted PGP card (e.g. a yubikey) on the control node.

options:
    gnupg_home:
        description: |-
            The GnuPG home directory for gpg. If not given, the GNUPGHOME
            environment variable (on the control node) will be used.
        required: false
        type: str
"""

RETURN = r"""
serial:
    description: |-
        The serial number of the card.
    type: str
    returned: if present
fingerprint:
    description: |-
        The fingerprint of the keypair on the card.
    type: str
    returned: if present
"""

EXAMPLES = r"""
- name: Detect a Yubikey
  bbcrd.vault.pgp_detect_card:
  register: card
"""


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars={}):
        with in_specified_gnupg_home(self._task):
            output = run(
                [
                    "gpg",
                    "--batch",
                    "--no-tty",
                    "--with-colons",  # Machine readable output
                    "--status-fd=1",  # Machine readable status
                    "--card-status",
                ],
                capture_output=True,
            )
            if output.returncode != 0:
                raise AnsibleError(f"Card detection error.\n{output.stderr.decode()})".rstrip())
            
            lines = output.stdout.decode().splitlines()
            
            if lines[0].startswith("[GNUPG:] CARDCTRL 3 "):  # 3 = "Card with serial number detected"
                card_details = {
                    line.partition(":")[0]: line.split(":") for line in lines
                }
                
                return {
                    "serial": card_details["serial"][1],
                    "fingerprint": card_details["fpr"][1] or None,
                    "changed": False,
                }
            else:
                return {"changed": False}
