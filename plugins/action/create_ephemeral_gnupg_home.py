from tempfile import mkdtemp
from pathlib import Path

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError

from ansible_collections.bbcrd.vault.plugins.module_utils.pgp import (
    kill_gpg_agent,
)

DOCUMENTATION = r"""
module: bbcrd.vault.create_ephemeral_gnupg_home

short_description: Create an ephemeral GnuPG home on the control node.

description: |-
    Create an ephemeral GnuPG home, killing any running GnuPG agents to prevent
    conflicts in accessing PGP card devices.

options:
    set_fact:
        description: |-
            The name of a fact to set to the path of the created GnuPG home
            directory on the control node. If null, no fact is set.
        required: false
        type: str or null
        default: gnupg_home
"""

RETURN = r"""
gnupg_home:
    description: |-
        The GnuPG home directory which was created on the control node.
    type: str
    returned: always
"""

EXAMPLES = r"""
- name: Create an ephemeral GnuPG home
  bbcrd.vault.create_ephemeral_gnupg_home:
    set_fact: gnupg_home
"""

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars={}):
        # Kill any GnuPG agent running the surrounding environment to prevent
        # it blocking access to PGP cards.
        kill_gpg_agent()
        
        # Create an empty, private directory for the GnuPG home (gpg will
        # initialise it on first use).
        gnupg_home = Path(mkdtemp(prefix="ephemeral_gnupg_home_"))
        gnupg_home.chmod(0o700)
        
        fact_name = self._task.args.get("set_fact")
        if fact_name is not None:
            ansible_facts = {fact_name: str(gnupg_home)}
        else:
            ansible_facts = {}
        
        return {
            "changed": True,
            "gnupg_home": str(gnupg_home),
            "ansible_facts": ansible_facts,
        }
