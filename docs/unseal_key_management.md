Unseal key management
=====================

This collection is regrettably, but necessarily, somewhat opinionated with
respect to the [management of unseal
keys](https://developer.hashicorp.com/vault/docs/concepts/seal). Unseal key
management for Vault is a complex topic with a wide range of possible solutions
each with its own substantial implications for any kind of automation. This
collection specifically chooses [a PGP-based workflow for unseal key
management](https://developer.hashicorp.com/vault/docs/concepts/pgp-gpg-keybase).


Vault PGP unseal key support primer
-----------------------------------

When Vault generates (or rekeys) its unseal keys, you can [optionally provide a
set of PGP public
keys](https://developer.hashicorp.com/vault/api-docs/system/rekey#pgp_keys),
one per unseal key. The generated unseal keys are then encrypted using these
unseal keys before being returned to the user. These can only be decrypted
again using the corresponding PGP private keys. The operator is thus freed from
the burden of securely handling a complete set of plaintext unseal keys. The
encrypted keys can be safely stored in a shared location. Operators also never
have the opportunity to see anyone elses keys making robust multi-operator
operation possible.

Because PGP implementations such as [GnuPG](https://www.gnupg.org/) support
generating and irretrivably storing private keys on hardware devices (e.g.
[Yubikeys](https://www.yubico.com/products/yubikey-5-overview/)), two factor
security is possible.

<details>
<summary><strong>What about other unseal key management options?</strong></summary>

> Alternative unseal key management strategies include HSM or cloud-service
> based automatic unsealing mechanisms. Since these options depend on either
> Vault Enterprise or proprietary public cloud infrastructure, these are not a
> viable option in many settings. Further, the problem of managing recovery
> keys in this setting is essentially the same as managing unseal keys.
>
> The other major alternative -- managing unencrypted unseal keys manually --
> typically results in an ad-hoc solution along the same lines as the PGP-based
> solution. This, however, offers strictly worse security guarantees because
> all of the plaintext unseal keys being in one place at once at the point of
> rekeying.

</details>


Creating PGP key pairs
----------------------

[GnuPG](https://www.gnupg.org/) can be used directly to create a public/private
PGP key pairs for use with this collection. However, unless you are already
familliar with GnuPG and PGP, this comes with a fairly steep learning curve. If
you intend to use a
[Yubikey](https://www.yubico.com/products/yubikey-5-overview/) or other PGP
smart card to hold your private key -- and this is strongly recommended -- the
much simpler [Cryptie](https://github.com/bbc/cryptie/) tool can be used.

To generate a new keypair using Cryptie, use:

    $ cryptie init-card john_doe.gpg "John Doe"

This will generate a new public and private key pair on your Yubikey (or other
PGP card) and write the public key to `john_doe.gpg`. The private key remains
on the device at all times and cannot be extracted later. This makes the
Yubikey a robust second factor in addition to the PIN set on the device.

Please read the [Cryptie documentation](https://github.com/bbc/cryptie) for a
detailed introduction, including how to set your PIN and how to manually
encrypt and decrypt data.


Disaster recovery preparations
------------------------------

It is strongly recommended that you have an 'emergency' keypair stored (for
example) on a Yubikey kept in a safe and secure location. You might use a tool
like [split-pin](https://github.com/bbc/split-pin/) to securely distribute the
PIN. This keypair should be allocated sufficient unseal key shares that it
covers any realistic possibility of lost Yubikeys and forgotten PINs amongst
administrators.

It is also recommended that regular drills are performed in which all
administrators verify that they can access (and remember the PIN for) their
Yubikeys. In the event that a keypair (or its passphrase or PIN is forgotten),
a new one should be generated and Vault rekeyed.


Configuring unseal key shares
-----------------------------

The PGP public keys of all Vault administrators must be provided via the
`bbcrd_vault_administrators` variable (see the [`bbcrd.vault.common_defaults`
role](../roles/common_defaults/defaults/main.yml)). This should look something
like:

    bbcrd_vault_administrators:
      jonathan:
        bbcrd_vault_unseal_key_shares: 2
        bbcrd_vault_pgp_public_key: |-
          -----BEGIN PGP PUBLIC KEY BLOCK-----

          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          ...snip...
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          xxxxxxxxxxxxxxxxxxxxxxxxxxxx
          =abcd
          -----END PGP PUBLIC KEY BLOCK-----
      andrew:
        bbcrd_vault_unseal_key_shares: 2
        bbcrd_vault_pgp_public_key: |-
          -----BEGIN PGP PUBLIC KEY BLOCK-----

          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          ...snip...
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          xxxxxxxxxxxxxxxxxxxxxxxxxxxx
          =abcd
          -----END PGP PUBLIC KEY BLOCK-----

Each administrator is issued the number of unseal key shares indicated by the
`bbcrd_vault_unseal_key_shares` value (which defaults to 1 if not specified).
It is often useful to issue each administrator more than one key share since
Vault requires that the unseal threshold is two or more keys. The unseal key
threshold is itself set by the `bbcrd_vault_unseal_key_threshold` variable like
so:

    bbcrd_vault_unseal_key_threshold: 2

Any user with at least `bbcrd_vault_unseal_key_shares` shares will be able to
unseal the vault alone. If a user is configured with fewer than this number of
shares, they will need to enlist another administrator to supply additional
unseal keys when required.

> **Tip:** Vault does not support setting the unseal key threshold to 1 when
> multiple unseal keys are used. If you have multiple administrators and any of
> them to be able to unseal Vault, set their `bbcrd_vault_unseal_key_shares` to
> at the `bbcrd_vault_unseal_key_threshold` value.


Encrypted unseal key storage
----------------------------

The `bbcrd.vault` collection stores a copy of the encrypted unseal keys in a
JSON file on each of the Vault cluster hosts. By default this is
`/etc/vault/encrypted_unseal_keys.json` and its structure is illustrated below:

    {
      # The time at which the unseal keys were (re)generated
      "timestamp": "2024-08-01T07:56:07Z",
      
      # The enecrypted unseal key shares
      "shares": [
        {
          # The name of the correspnding entry in bbcrd_vault_administrators.
          # (NB: Users with more than one unseal key share will have several
          # entries in this list!)
          "user": "...",
          
          # The 'full name' field extracted from the PGP public key
          "name": "...",
          
          # The keypair's fingerprint of the PGP public key
          "fingerprint": "...",
          
          # The ASCII Armor encoded PGP public key, as in
          # bbcrd_vault_administrators.<name>.bbcrd_vault_pgp_public_key.
          "public_key": "...",
          
          # A non-ASCII Armored, plain base64-encoded encrypted unseal key
          # share, encrypted using the public key above.
          "encrypted_unseal_key": "..."
        },
        ...
      ]
    }

Whenever an unseal key is required by any of the roles in this playbook, the
encrypted unseal keys are automatically fetched and decrypted using the
`bbcrd.vault.decrypt_unseal_keys` role.

The encrypted unseal keys file must be be backed up and treated with the same
level of care as the main Vault database. Since previous unseal keys are
invalidated when the database is rekeyed, it is essential that backups of the
Vault database must be kept in sync with backups of the encrypted unseal keys.
The `bbcrd.vault.configure_backups` role will automatically include the
encrypted unseal key file with every backup.


### On keeping encrypted keys in sync between cluster nodes.

Unlike the Vault database (which is kept consistent using a sophisticated
distributed consensus algorithm), this collection's roles are responsible for
ensuring the encrypted unseal key file is kept in sync on all cluster members.
This is necessary to ensure that the encrypted unseal keys are always
available, even in the event of an outage of some nodes.

To ensure consistency, rekeying operations will be refused by default if any
cluster members are down. This ensures that new encrypted unseal keys can
always be written to every host.  This check can be disabled (using
`bbcrd_vault_skip_rekey_sanity_check`) but it becomes your responsibility to
manually propagate the new encrypted unseal keys. The encrypted unseal key file
contains as much information as possible to aid in manually resolving any
accidental inconsistencies.


Multiple-administrator unseal key operation
-------------------------------------------

The playbooks in this collection will automatically retrieve and decrypt the
encrypted unseal keys as required. If the threshold number of keys required is
greater than the number of keys held by an administrator, a colleague must
supply any extra keys. Whenver unseal keys are used, the main administrators'
playbook will pause whilst waiting for a colleague to supply additional keys.
The
[`bbcrd.vault.supply_additional_keys`](../playbooks/supply_additional_keys.yml)
playbook is provided to perform exactly this task. You can read more about this
workflow in the [`bbcrd.vault.manage_vault_cluster` playbook (and friends)
documentation](./manage_vault_cluster_playbook.md).


Verification during rekeying
----------------------------

The playbooks and roles in this collection which perform rekeying of Vault's
unseal keys default to running in [verify
mode](https://developer.hashicorp.com/vault/docs/commands/operator/rekey#verify).
In this mode, new candidate unseal keys must be submitted back to Vault before
they can be used. As a result this substantially reduces the possibility of
locking yourself out of Vault.


Decryption of unseal keys
-------------------------

This collection uses [GnuPG](https://www.gnupg.org/), running on the Ansible
control node, is used by this collection to decrypt encrypted unseal keys. (See
the `bbcrd.vault.decrypt_unseal_keys` role).

By default, playbooks in this collection will use the
`bbcrd.vault.ephemeral_gnupg_home` role to create an ephemeral GnuPG
environment using the private key on a hardware device (e.g. Yubikey) to
perform decryption. If you used [Cryptie](https://github.com/bbc/cryptie) to
generate your key pair, this approach will be ideal.

Alternatively, you can use your own manually set up GnuPG environment by
skipping this role (e.g. using `--skip-tags bbcrd_vault_ephemeral_gnupg_home`).


### Manual decription of unseal keys

Under normal circumstances the playbooks in this collection will automatically
handle the process of decrypting unseal keys whenever they're needed. In the
event that you require direct access to the unseal keys (for example in a
disaster recovery scenario) the
[`bbcrd.vault.decrypt_unseal_keys_file`](../playbooks/decrypt_unseal_keys_file.yml)
playbook automates the process of decrypting the unseal keys in an encrypted
unseal key file named `encrypted_unseal_keys.json` in the current working
directory. For example:

    $ cp some/location/eg/a/backup/encrypted_unseal_keys.json ./encrypted_unseal_keys.json
    $ ansible-playbook bbcrd.vault.decrypt_unseal_keys_file
    <... snip ...>
    TASK [Display decrypted unseal keys] *************************************
    ok: [localhost] => {
        "bbcrd_vault_unseal_keys": [
            "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        ]
    }

Note that only unseal keys for which you have the matching private key will be
decrypted and shown.
