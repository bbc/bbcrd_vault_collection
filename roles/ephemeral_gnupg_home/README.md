`bbcrd.ansible_vault.ephemeral_gnupg_home` role
===============================================

Create an ephemeral GnuPG home on the Ansible control node with all public keys
listed in `ansible_vault_administrators` imported and the currently connected
PGP card detected. Sets `ansible_vault_gnupg_home` to the location of a newly
created GnuPG home. This role will do nothing if `ansible_vault_gnupg_home` is
already defined as something other than null.

This role makes the somewhat opinionated assumption that unseal keys will be
protected by private keys held on PGP compatible smart cards.

Use of this role can be nested: only the first and last matching pair of
invocation and cleanup will have any effect.

This role will attempt to use the PGP card to decrypt some dummy data. This
allows us to fail early if a bad PIN is entered and also caches the PIN for the
remainder of the playbook run. This can be skipped by skipping the
`ansible_vault_precheck_pin` tag.


Cleaning up the ephemeral GnuPG home
------------------------------------

You must clean up the ephemeral GnuPG home (and related gpg-agent process), iff
this role previously created one, using the following

    - import_role:
        name: bbcrd.ansible_vault.ephemeral_gnupg_home
        tasks_from: cleanup.yml
