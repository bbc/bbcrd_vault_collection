from subprocess import run, PIPE, DEVNULL
from base64 import b64decode, b64encode

from ansible_collections.bbcrd.ansible_vault.plugins.module_utils.pgp import (
    ascii_armor_to_base64,
    pgp_key_metadata,
)



def pgp_public_key_to_name(pgp_key_base64: str) -> str:
    """
    Given a base64-encoded PGP certificate, return the name, email address and
    comment string.
    """
    return pgp_key_metadata(b64decode(pgp_key_base64))["name"]

def pgp_public_key_to_fingerprint(pgp_key_base64: str) -> str:
    """
    Given a base64-encoded PGP certificate, return its fingerprint.
    """
    return pgp_key_metadata(b64decode(pgp_key_base64))["fingerprint"]

class FilterModule(object):
    def filters(self):
        return {
            'pgp_public_key_to_name': pgp_public_key_to_name,
            'pgp_public_key_to_fingerprint': pgp_public_key_to_fingerprint,
            'ascii_armor_to_base64': ascii_armor_to_base64,
        }
