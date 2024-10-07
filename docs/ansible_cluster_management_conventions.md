Ansible conventions for Vault cluster management playbooks and roles
====================================================================

The Vault *cluster management* playbooks and roles follow a number of common
conventions which are made explicit below.


Vault API commands are sent from the Vault hosts
------------------------------------------------

Whenever a role communicates with a Vault server, requests are made not from
the Ansible control host but from the corresponding vault host itself.

This design allows flexibility in how you expose your Vault instances to the
wider world. For example, in some settings you might choose not expose the
individual Vault nodes' interfaces to the network, only permitting access via a
single VIP. Because some administrative commands require direct access to
specific Vault nodes (e.g. unsealing), running all requests from the Vault
hosts ensures direct access is possible.


GnuPG commands are performed on the Ansible control node
--------------------------------------------------------

All unseal key encryption, decryption and other tasks are performed on the
Ansible control node. By default, the playbooks in this collection will create
an ephemeral GnuPG home environment to avoid polluting your own personal one.
However, you can opt to use your own environment should you wish.


Vault environment variables are ignored
---------------------------------------

In regular uses of Vault in Ansible playbooks it is common to use environment
variables on the Ansible control host to determine the Vault server and
credentials to use.

In our cluster management playbooks and roles, however, we always connect to
Vault servers explicitly identified in the Ansible data (e.g.
`bbcrd_vault_public_url`). Likewise, Vault tokens are always loaded into
Ansible variables (e.g. `bbcrd_vault_root_token`) and never stored in
`~/.vault-token`.


Common variables an defaults are defined in the `bbcrd.vault.common_defaults` role
----------------------------------------------------------------------------------

There are numerous variables which are needed by many of the cluster management
roles. For example, variables such as `bbcrd_vault_public_url` or
`bbcrd_vault_administrators`. These are defined in the otherwise empty
`bbcrd.vault.common_defaults` role which is automatically pulled in as a
dependency by other roles. Make sure to look in its [defaults
file](../roles/common_defaults/defaults/main.yml) for additional relevant
variables.


Cluster management commands are (mostly) performed using the `uri` module
-------------------------------------------------------------------------

For the most part, the cluster management roles use the `uri` module to
interact with the Vault API directly because there is little benefit to
wrapping the functionality into its own module. Cluster management typically
involves a large proportion of one-off commands (e.g. cluster initialisation)
or commands which are unlikely to be reused outside of these roles (e.g.
unsealing). As such, moving this functionality into a module offers little
benefit but obscures the actual steps taken by the roles.

Likewise, due to the convention of running Vault commands on the Vault hosts
rather than the control host, existing Ansible Vault modules and integrations
cannot be used.
