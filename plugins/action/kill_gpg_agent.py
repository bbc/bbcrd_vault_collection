from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError

from ansible_collections.bbcrd.vault.plugins.module_utils.pgp import (
    in_specified_gnupg_home,
    kill_gpg_agent,
)

DOCUMENTATION = r"""
module: bbcrd.vault.kill_gpg_agent

short_description: Kill the running GnuPG agent on the control node.

options:
    gnupg_home:
        description: |-
            The GnuPG home directory for gpg. If not given, the GNUPGHOME
            environment variable (on the control node) will be used.
        required: false
        type: str
"""

EXAMPLES = r"""
- name: Kill the GnuPG agent
  bbcrd.vault.kill_gpg_agent:
"""

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars={}):
        with in_specified_gnupg_home(self._task):
            kill_gpg_agent()
        return {"changed": False}  # No way to tell, sadly!
