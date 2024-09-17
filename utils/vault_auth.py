#!/usr/bin/env python3

r"""
Authenticate with Vault using OIDC and sign your SSH key.

Usage:

    $ ./vault_auth.py

This script is a wrapper around the following pair of commands:

    $ vault login -method oidc
    
    $ vault write \
        -field=signed_key \
        ssh_signer_mount/sign/admin \
        public_key=@$HOME/.ssh/id_rsa.pub \
        > $HOME/.ssh/id_rsa-cert.pub
"""

from argparse import ArgumentParser
from subprocess import run, DEVNULL
from pathlib import Path


def login(vault_command: str, verbose: bool) -> None:
    """Log into Vault."""
    run(
        [vault_command, "login", "-method", "oidc"],
        stdout=None if verbose else DEVNULL,
        check=True,
    )


def ssh_sign(
    vault_command: str,
    ssh_public_key: Path,
    ssh_signer_mount: str,
    ssh_signer_role: str,
    verbose: bool,
) -> None:
    """Sign the users' SSH key using Vault."""
    if not ssh_public_key.is_file():
        ssh_public_key = Path.home() / ".ssh" / ssh_public_key
    if not ssh_public_key.is_file():
        raise FileNotFoundError(ssh_public_key)

    ssh_cert = ssh_public_key.with_name(
        f"{ssh_public_key.stem}-cert{ssh_public_key.suffix}"
    )

    with ssh_cert.open("wb") as f:
        run(
            [
                vault_command,
                "write",
                "-field=signed_key",
                f"{ssh_signer_mount}/sign/{ssh_signer_role}",
                f"public_key=@{ssh_public_key}",
            ],
            stdout=f,
            check=True,
        )
        if verbose:
            # Print certiicate information
            print("Signed SSH key {ssh_public_key.name}")
            run(
                [
                    "ssh-keygen",
                    "-Lf",
                    str(ssh_cert),
                ]
            )


def main() -> None:
    parser = ArgumentParser(
        description="""
            Authenticate with Vault using BBC Login, optionally signing your
            SSH key.
        """,
    )

    parser.add_argument(
        "--vault-command",
        "-V",
        default="vault",
        help="""
            The Vault CLI binary name. Default: %(default)s.
        """,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        default=False,
        action="store_true",
        help="""
            Show additional information during login.
        """,
    )

    login_group = parser.add_argument_group("login options")
    login_group.add_argument(
        "--no-login",
        "-L",
        dest="login",
        action="store_false",
        default=True,
        help="""
            If given, do not log into Vault. (You must already have a valid
            Vault token).
        """,
    )

    ssh_group = parser.add_argument_group("SSH signing options")
    ssh_group.add_argument(
        "--no-ssh",
        "-S",
        dest="ssh",
        action="store_false",
        default=True,
        help="""
            If given, do not sign your SSH key.
        """,
    )
    ssh_group.add_argument(
        "--ssh-public-key",
        "-s",
        default="id_rsa.pub",
        help="""
            The SSH public key to sign. Defaults to %(default)s.
        """,
    )
    ssh_group.add_argument(
        "--ssh-signer-mount",
        default="ssh_client_signer",
        help="""
            The Vault mount point of the SSH signer to use. Defaults to
            %(default)s.
        """,
    )
    ssh_group.add_argument(
        "--ssh-signer-role",
        default="admin",
        help="""
            The role name of the SSH signer to use. Defaults to
            %(default)s.
        """,
    )
    args = parser.parse_args()

    if args.login:
        login(
            vault_command=args.vault_command,
            verbose=args.verbose,
        )

    if args.ssh:
        ssh_sign(
            vault_command=args.vault_command,
            ssh_public_key=Path(args.ssh_public_key),
            ssh_signer_mount=args.ssh_signer_mount.rstrip("/"),
            ssh_signer_role=args.ssh_signer_role.rstrip("/"),
            verbose=args.verbose,
        )


if __name__ == "__main__":
    main()
