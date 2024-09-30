def enumerate_key_shares(bbcrd_vault_administrators):
    """
    Given an bbcrd_vault_administrators variable, return a list of objects of
    the following shape, one per key share.
    
        {
            "user": <name of administrator>,
            "share_index": <index of key share>,
            "pgp_public_key": <ASCII Armor PGP key>,
        }
    """
    out = []
    
    for user, data in bbcrd_vault_administrators.items():
        if "bbcrd_vault_pgp_public_key" in data:
            for share_index in range(data.get("bbcrd_vault_unseal_key_shares", 1)):
                out.append(
                    {
                        "user": user,
                        "share_index": share_index,
                        "pgp_public_key": data["bbcrd_vault_pgp_public_key"],
                    }
                )
    
    return out

class FilterModule(object):
    def filters(self):
        return {
            'enumerate_key_shares': enumerate_key_shares,
        }
