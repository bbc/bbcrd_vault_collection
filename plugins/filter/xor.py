from base64 import b64decode, b64encode

def xor_b64_bytes(a_base64: str, b_base64: str) -> str:
    """
    Given a pair of base64-encoded byte strings, apply a bitwise XOR operation
    and return the base64 result.
    """
    return b64encode(
        bytes(
            a ^ b
            for a, b in zip(b64decode(a_base64), b64decode(b_base64))
        )
    ).decode()

class FilterModule(object):
    def filters(self):
        return {
            'xor_b64_bytes': xor_b64_bytes,
        }
