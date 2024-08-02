`bbcrd.ansible_vault` Collection
================================

A collection for deploying and managing Hashicorp Vault/OpenBao clusters.

**A work in progress.**


`bbcrd.ansible_vault.vault` role
--------------------------------

The `bbcrd.ansible_vault.vault` role is the central component of this
collection. It takes care of the installation of Vault, unsealing and managing
Vault clusters.

As usual, the variables which control this role are enumerated and documented
in [`roles/vault/defaults/main.yml`](./roles/vault/defaults/main.yml).

This role also exposes a few separate behaviours which can be used by setting
[`tasks_from`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/include_role_module.html#parameter-tasks_from).
These are documented in further detail below.


### Unseal key management

This role is regrettably, but necessarily, somewhat opinionated with respect to
the [management of unseal
keys](https://developer.hashicorp.com/vault/docs/concepts/seal). Unseal key
management for Vault is a complex topic with a wide range of possible solutions
each with its own substantial implications for any kind of automation. This
role specifically chooses [a particular PGP-based workflow for unseal key
management](https://developer.hashicorp.com/vault/docs/concepts/pgp-gpg-keybase).
This workflow was designed with the intent of maximising the usability and
security in a non-public-cloud based, open source Vault deployment.

<details>
<summary><strong>Why PGP-based unseal key storage?</strong></summary>

> Vault's PGP support greatly simplifies the process of securely generating and
> distributing unseal keys. By using public key cryptography to encrypt each
> unseal key, no one person is ever responsible for, nor has the opportunity,
> to hold more than their share of the unseal keys.
>
> By providing a PGP public key for each key holder, Vault returns the newly
> generated unseal key shares encrypted with those keys. These can then be
> stored or distributed without any particular precautions.
>
> This role will store the encrypted keys alongside the Vault data directory.
> Since this directory is already (necessarily) accessible to all vault
> administrators this completely avoids the need to explicitly *distribute* the
> keys to the other administrators. This also removes the need to coordinate
> with all administrators during rekeying, making it possible to be carried out
> more regularly.
>
> Alternative unseal key management strategies include HSM or cloud-service
> based automatic unsealing mechanisms. Since these options depend on either
> Vault Enterprise or proprietary public cloud infrastructure, these are not a
> viable option in many settings. Further, the problem of managing recovery
> keys in this setting is essentially the same as managing unseal keys.
>
> The other major alternative -- managing unencrypted unseal keys manually --
> typically results in an ad-hoc solution along the same lines as the PGP-based
> solution. This, however, offers strictly worse security guarantees because
> all of the unseal keys end up in one place in plain-text at the point of
> rekeying.

</details>

Each Vault administrator must supply a PGP public key to this role. When
Vault's unseal keys are (re)generated, Vault uses these public keys to encrypt
the unseal key shards. These encrypted shards are then stored by this role into
the file `/var/lib/vault/encrypted_unseal_keys.json` (by default) on every
cluster host. Its structure is as follows:

    {
      # The time at which the unseal keys were (re)generated
      "timestamp": "2024-08-01T07:56:07Z",
      # The enecrypted unseal key shares
      "shares": [
        {
          # The key of ansible_vault_administrators where the public key used
          # to encrypted this key share came from. (For information only).
          "user": "...",
          # The ASCII Armor encoded PGP public key, reproduced from
          # ansible_vault_administrators.
          "public_key": "...",
          # The full name field extracted from the public key (for information
          # only)
          "name": "...",
          # The keypair's fingerprint extracted from the public key (for
          # information only)
          "fingerprint": "...",
          # A (non-ASCII Armored, plain) base64-encoded encrypted unseal key
          # share, encrypted using the public key above.
          "encrypted_unseal_key": "..."
        },
        ...
      ]
    }

This file must be be backed up and treated with the same level of care as the
main Vault database. Since previous unseal keys are invalidated when the
database is rekeyed, it is essential that backups of the Vault database must be
kept in sync with backups of the encrypted unseal keys.

<details>
<summary><strong>On keeping encrypted keys in sync between cluster nodes.</strong></summary>

> Unlike the Vault database (which is kept consistent using a sophisticated
> distributed consensus algorithm), this role is responsible for ensuring all
> cluster members have a consistent copy of the encrypted unseal keys.
> Consequently, this role will, by default, behave extremely cautiously.
>
> Firstly, this role (by default) checks that *all* members of the cluster are
> up and will refuse to perform a rekeying operation otherwise. This is
> intended to prevent different cluster members from holding stale (and
> inconsistent) encrypted key files. If missing members of the cluster cannot
> be brought up when rekeying is performed, this check can be disabled (using
> `ansible_vault_skip_rekey_sanity_check`). In this case, however, it is the
> operator's responsibility to ensure that the updated encrypted key files are
> propagated correctly once machines have been brought back into service.
>
> Newly added cluster members will automatically receive a copy of the current
> encrypted unseal key file when they're joined to the cluster. Otherwise,
> however, this role will never cross-copy existing unseal keys. Only when
> unseal keys are rotated will the encrypted files be overwritten by this role.
>
> Conversely, when fetching encrypted unseal keys, the role will confirm that
> all available cluster members have a consistent (identical) set of encrypted
> unseal keys. If an inconsistency is detected, the role will refuse to
> continue and it is the operator's responsibility to resolve the
> inconsistency.
>
> The encrypted unseal key file is intended to contain as much information as
> possible to aid in resolving any inconsistencies.
>
> As a further precaution, this role will backup any existing encrypted unseal
> key file before writing a new ones.
>
> Finally, when new keys are generated, the encrypted unseal key data is always
> printed in the Ansible logs. In the unlikely event that the encrypted unseal
> keys are not successfully written, the operator must take care to store and
> propagate the keys manually.

</details>

When this role requires an unseal key, it will read the encrypted keys onto the
Ansible host. It will then use [GnuPG (GPG)](https://www.gnupg.org/) on the
Ansible deployment host to decrypt any unseal keys for which a matching private
key is held in the local GnuPG database.

<details>
<summary><strong>On using GnuPG and PGP cards (e.g. Yubikeys).</strong></summary>

> [GnuPG (GPG)](https://www.gnupg.org/) is a popular open source implementation
> of the PGP standard. This includes support for hardware security devices
> which implement the PGP Card standard. This includes
> [Yubikeys](https://www.yubico.com/products/yubikey-5-overview/). These
> devices can be used to securely (and irretrievably) store a PGP private key.
> This acts as a secure second factor for accessing your private key, and
> therefore an encrypted unseal key.
>
> As part of the wider PGP ecosystem, GnuPG includes a formidable array of
> features focusing on the management of trust relationships between people on
> the Internet. Unfortunately this can make it quite intimidating and confusing
> to use. The extent to which PGP and GPG are used by Vault and this role is
> extremely limited. As such, unless you're already a user of GnuPG, you may
> find a simplified wrapper such as [Cryptie](https://github.com/bbc/cryptie/)
> preferable.

</details>


### TODOC: Submitting additional unseal keys

### TODOC: Obtaining root tokens

### TODOC: Other features to be implemented...
