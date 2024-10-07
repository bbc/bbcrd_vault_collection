Identity (entity and group) management
======================================

Vault's [identity secrets
engine](https://developer.hashicorp.com/vault/docs/secrets/identity) is the
system which manages the notion of identity (e.g. users and groups) in Vault.
This mechanism is a useful way of handing out policy rights to vault users.
This collection provides a limited collection of modules for configuring the
identity secrets engine.


Managing entities (a.k.a. users)
--------------------------------

An entity typically represents a particular person (or perhaps machine user).
The [`bbcrd.vault.vault_entity` module](../plugins/modules/vault_entity.py) may
be used to create, configure or delete entities. In particular, it may be used
to grant particular policies to any person authenticating as that entity. In
practice, however, it is more convenient -- and safer -- to use groups to grant
policies to a given entity (see later). In practice, you're unlikely to use
this module.


Managing entity aliases (auth-to-entity mappings)
-------------------------------------------------

An Vault entity is only useful if you can authenticate as that entity. For this
there needs to be some mapping between user accounts as defined by a given auth
method (e.g. OIDC, LDAP or Active Directory) and Vault entities. Entity aliases
are those mappings.

Each Vault auth method effectively has its own independent set of entity
aliases, i.e. its own mapping from auth system accounts to Vault entities. The
[`bbcrd.vault.vault_auth_method_entity_aliases`
module](../plugins/modules/vault_auth_method_entity_aliases.py) can be used to
declaratively manage this mapping for a particular auth method.

> **Hint:** An entity can, in theory, have multiple entity aliases pointing at
> it. For example, you could allow authentication via both LDAP and GitHub
> credeitnaisl. In this caes, an entity alias for both auth methods would point
> to the same entity.
>
> An entity with no entity aliases pointing at it, however, is effectively
> disabled since you cannot authenticate as that entity.

Because the `bbcrd.vault.vault_auth_method_entity_aliases` module deletes any
entity aliases not given in its input, it also revokes access to Vault to users
removed from its input. Whilst the old entities continue to exist in Vaul,
because the user will no longer be mapped to that entity once the entity alias
has been removed their access will be effectively withdrawn.

> **Note:** When a user without an existing entity alias logs in with a
> particular auth method, a new entity and corresponding entity alias is
> auto-generated. Auto-generated entities are assigned no policies and can't do
> anything. Their only useful purpose is in helping track account usage in
> audit logs.

For an example of the `bbcrd.vault.vault_auth_method_entity_aliases` module in
use, refer to the [`bbcrd.vault.configure_oidc_auth`
role](../roles/configure_oidc_auth).


Managing Groups
---------------

The [`bbcrd.vault.vault_group` module](../plugins/modules/vault_group.py)
module can be used to declaratively create a group, set its membership and
choose the policies granted to its members.

By contrast with using the `bbcrd.vault.vault_entity` module, the
`bbcrd.vault.vault_group` module is declarative. This ensures that entities
removed from its input have their relevant access revoked.

Unlike assigning policies at the auth method level (e.g. assigning all users
authenticated with that auth method a common set of policies), you can achieve
finer grained control by using groups. For example, while it might [make sense
for all machine users authenticated by a given
AppRole](./machine_approle_auth.md), the same is unlikely true of all OIDC
users. In the latter case, you'll probbaly want to grant specific collections
of policies to specific groups of users.

For example, you might use the following invocation to grant a set of
policies to particular administrators:

    - name: Grant administrator policies
      run_once: true
      bbcrd.vault.vault_group:
        name: administrators  # Group name
        
        members:  # List of entity names
          - jonathah
          - bonneya
          - rosserj
        
        policies:  # Policies to grant
          - ssh-admin
          - kv-admin
        
        vault_url: "{{ bbcrd_vault_public_url }}"
        vault_token: "{{ bbcrd_vault_root_token }}"
        vault_ca_path: "{{ bbcrd_vault_ca_path | default(omit) }}"

> **Hint:** In the example above we're making our API request and setting our
> Vault server details and credentials as per the [conventions for
> administrative roles and modules](./ansible_provisioning_conventions.md).

Re-running the module with a different set of users or policies (but the same
group name!) will result in access rights being added or removed as appropriate
in a declarative way.
