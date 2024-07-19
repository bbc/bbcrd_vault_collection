from subprocess import run, PIPE, DEVNULL
from base64 import b64decode, b64encode

def ascii_armor_to_base64(ascii_armor: str) -> str:
    """
    Convert an ASCII Armor formatted string (see RFC 4880 section 6) into a
    plain base64 string. All metadata is ignored and the checksum is not
    verified.
    """
    lines = ascii_armor.strip().splitlines()
    
    header = lines.pop(0)
    if not (header.startswith("-----") and header.endswith("-----")):
        raise ValueError("Missing ASCII Armor header line")
    
    tail = lines.pop(-1)
    if not (tail.startswith("-----") and tail.endswith("-----")):
        raise ValueError("Missing ASCII Armor tail")
    
    # Strip (and ignore) headers and the empty line
    while lines.pop(0):
        pass
    
    # Strip (and don't check) the checksum
    checksum = lines.pop(-1)
    if not checksum.startswith("="):
        raise ValueError("Missing ASCII Armor checksum")
    
    # All that's left is glorious base64 data!
    return "".join(lines)

def _gpg_import_show_only(pgp_key_base64: str) -> list[list[str]]:
    """
    Given a base64-encoded PGP certificate, return the parsed colon-formatted
    output of ``gpg --import`` in show-only mode.
    """
    output = run(
        [
            "gpg",
            # Run in non-interactive, machine-readable mode
            "--batch",
            "--no-tty",
            "--with-colons",
            # Just read the certificate
            "--import",
            "--import-option=show-only",
        ],
        input=b64decode(pgp_key_base64),
        capture_output=True,
        check=True,
    )
    # See GnuPG DETAILS documentation for output format:
    # https://github.com/gpg/gnupg/blob/master/doc/DETAILS
    return [
        line.split(":")
        for line in output.stdout.decode().splitlines()
    ]

def pgp_public_key_to_name(pgp_key_base64: str) -> str:
    """
    Given a base64-encoded PGP certificate, return the name, email address and
    comment string.
    """
    for columns in _gpg_import_show_only(pgp_key_base64):
        if columns[0] == "uid":
            return columns[9]

def pgp_public_key_to_fingerprint(pgp_key_base64: str) -> str:
    """
    Given a base64-encoded PGP certificate, return its fingerprint.
    """
    for columns in _gpg_import_show_only(pgp_key_base64):
        if columns[0] == "fpr":
            return columns[9]

def pgp_decrypt(ciphertext_base64: str) -> str:
    """
    Given some base64-encoded ciphertext, return the base64-encoded plaintext
    resulting from using gpg to decrypt the data.
    """
    output = run(
        [
            "gpg",
            "--no-tty",
            "--decrypt",
        ],
        input=b64decode(ciphertext_base64),
        capture_output=True,
        check=True,
    )
    return b64encode(output.stdout).decode()

class FilterModule(object):
    def filters(self):
        return {
            'pgp_public_key_to_name': pgp_public_key_to_name,
            'pgp_public_key_to_fingerprint': pgp_public_key_to_fingerprint,
            'pgp_decrypt': pgp_decrypt,
            'ascii_armor_to_base64': ascii_armor_to_base64,
        }
