def enumerate_key_shares(ansible_vault_administrators):
    """
    Given an ansible_vault_administrators variable, return a list of objects of
    the following shape, one per key share.
    
        {
            "user": <name of administrator>,
            "share_index": <index of key share>,
            "pgp_public_key": <ASCII Armor PGP key>,
        }
    """
    out = []
    
    for user, data in ansible_vault_administrators.items():
        for share_index in range(data.get("ansible_vault_unseal_key_shares", 1)):
            out.append(
                {
                    "user": user,
                    "share_index": share_index,
                    "pgp_public_key": data["ansible_vault_pgp_public_key"],
                }
            )
    
    return out

class FilterModule(object):
    def filters(self):
        return {
            'enumerate_key_shares': enumerate_key_shares,
        }
