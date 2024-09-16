from shutil import rmtree
from pathlib import Path

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError

from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.pgp import (
    in_specified_gnupg_home,
    kill_gpg_agent,
)

DOCUMENTATION = r"""
module: bbcrd.ansible_vault.cleanup_ephemeral_gnupg_home

short_description: Destroy an ephemeral GnuPG home.

description: |-
    Destroy an ephemeral GnuPG home, e.g. as created by
    bbcrd.ansible_vault.create_ephemeral_gnupg_home.
    
    Kills any GnuPG agent running in the ephemeral environment before deleting
    it.

options:
    gnupg_home:
        description: |-
            The ephemeral GnuPG home directory.
        required: false
        type: str
"""

EXAMPLES = r"""
- name: Cleanup an ephemeral GnuPG environment
  bbcrd.ansible_vault.cleanup_ephemeral_gnupg_home:
    gnupg_home: "{{ gnupg_home }}"
"""

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars={}):
        with in_specified_gnupg_home(self._task):
            kill_gpg_agent()
        
        gnupg_home = self._task.args["gnupg_home"]
        if Path(gnupg_home).is_dir():
            rmtree(gnupg_home)
            return {"changed": True}
        else:
            return {"changed": False}
