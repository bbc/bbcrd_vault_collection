from typing import Iterable

import os
from pathlib import Path
from contextlib import contextmanager
from subprocess import run
from base64 import b64decode

from ansible.errors import AnsibleError
from ansible.playbook.task import Task


@contextmanager
def in_specified_gnupg_home(task: Task) -> Iterable[str | None]:
    """
    A context manager which sets the GNUPGHOME environment variable to the
    GnuPG home directory specified in either:

    * The 'gnupg_home' module parameter
    * The 'GNUPGHOME' environment variable (on the control node)
    * The system default GnuPG home (i.e. GNUPGHOME is not set).

    With the top-most option being preferred.
    """
    environment_gnupg_home = os.environ.get("GNUPGHOME")
    parameter_gnupg_home = task.args.get("gnupg_home")

    gnupg_home = parameter_gnupg_home or environment_gnupg_home

    if gnupg_home is not None:
        os.environ["GNUPGHOME"] = gnupg_home
    else:
        os.environ.pop("GNUPGHOME", None)

    try:
        yield gnupg_home
    finally:
        # Restore GNUPGHOME environment variable
        if environment_gnupg_home is not None:
            os.environ["GNUPGHOME"] = environment_gnupg_home
        else:
            os.environ.pop("GNUPGHOME", None)


def pgp_list_fingerprints(private_keys: bool = False) -> list[str]:
    """
    Enumerates the PGP fingerprints for all stored public keys (or private keys
    if private_keys is True).
    """
    try:
        output = run(
            [
                "gpg",
                # Run in non-interactive, machine-readable mode
                "--batch",
                "--no-tty",
                "--with-colons",
                # Enumerate private keys
                "--list-secret-keys" if private_keys else "--list-keys",
            ],
            capture_output=True,
        )
        if output.returncode != 0:
            raise AnsibleError(
                f"Could enumerate keys.\n{output.stderr.decode()})".rstrip()
            )
        # See GnuPG DETAILS documentation for output format:
        # https://github.com/gpg/gnupg/blob/master/doc/DETAILS
        return [
            line.split(":")[9]
            for line in output.stdout.decode().splitlines()
            if line.startswith("fpr:")
        ]
    except Exception as exc:
        raise AnsibleError(f"Failed to enumerate private keys: {exc}")


def pgp_key_metadata(pgp_key: bytes) -> dict[str, str | None]:
    """
    Given a binary PGP certificate, return selected metadata.
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
        input=pgp_key,
        capture_output=True,
        check=True,
    )
    # See GnuPG DETAILS documentation for output format:
    # https://github.com/gpg/gnupg/blob/master/doc/DETAILS
    output = [line.split(":") for line in output.stdout.decode().splitlines()]

    name = None
    for columns in output:
        if columns[0] == "uid":
            name = columns[9]
            break

    fingerprint = None
    for columns in output:
        if columns[0] == "fpr":
            fingerprint = columns[9]
            break

    return {
        "name": name,
        "fingerprint": fingerprint,
    }


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


def kill_gpg_agent() -> None:
    """Kill any running GnuPG agent."""
    run(
        [
            "gpgconf",
            "--kill",
            "gpg-agent",
        ],
        check=True,
    )
