#!/usr/bin/env python3

r"""
Authenticate with Vault using OIDC (for humans) or AppRole (for machines) and
sign your SSH key.

Usage (for humans):

    $ ./vault_auth.py

Usage (for machines):

    $ ./vault_auth.py --app-role /path/to/credentials_file.json

This script is a wrapper around the following commands:

    $ # For OIDC-based login
    $ vault login -method oidc

    $ # For AppRole-based login
    $ jq -r .secret_id credentials.json \
      | vault write -field token \
        "auth/$(jq -r .approle_mount credentials.json)/login" \
        role_id="$(jq -r .role_id credentials.json)" \
        secret_id=- \
      | vault login -

    $ # For SSH key signing
    $ vault write \
        -field=signed_key \
        ssh_signer_mount/sign/ssh_signer_role \
        public_key=@$HOME/.ssh/id_rsa.pub \
        > $HOME/.ssh/id_rsa-cert.pub
"""

from typing import NamedTuple
from argparse import ArgumentParser
from subprocess import run, DEVNULL, PIPE, CalledProcessError
from pathlib import Path
import json
import shlex
import sys


def oidc_login(vault_command: str, verbose: bool) -> None:
    """Log into Vault using OIDC."""
    run(
        [vault_command, "login", "-method", "oidc"],
        stdout=None if verbose else DEVNULL,
        check=True,
    )


def app_role_login(vault_command: str, verbose: bool, credentials_file: Path) -> None:
    """Log into Vault using AppRole."""
    credentials = json.load(credentials_file.open())

    token = run(
        [
            vault_command,
            "write",
            "-field",
            "token",
            f"auth/{credentials['approle_mount']}/login",
            f"role_id={credentials['role_id']}",
            f"secret_id=-",
        ],
        input=credentials["secret_id"].encode("ascii"),
        stdout=PIPE,
        check=True,
    ).stdout

    run(
        [vault_command, "login", "-"],
        input=token,
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

    login_type_group = parser.add_argument_group(
        "auth method"
    ).add_mutually_exclusive_group()
    login_type_group.add_argument(
        "--oidc",
        action="store_true",
        default=False,
        help="""
            Login using OpenID Connect. (The default)
        """,
    )
    login_type_group.add_argument(
        "--app-role",
        type=Path,
        metavar="CREDENTIALS_FILE",
        default=None,
        help="""
            Login using AppRole authentication. The argument should be a file
            containing the credentials to use for AppRole authentication. It
            should contain a JSON object containing the fields 'role_id',
            'secret_id' and 'approle_mount'.
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
        "-r",
        default="default",
        help="""
            The SSH signer role name to use. Defaults to %(default)s.
        """,
    )
    args = parser.parse_args()

    try:
        if args.login:
            if args.app_role is not None:
                app_role_login(
                    vault_command=args.vault_command,
                    verbose=args.verbose,
                    credentials_file=args.app_role,
                )
            else:
                oidc_login(
                    vault_command=args.vault_command,
                    verbose=args.verbose,
                )

        if args.ssh:
            ssh_sign(
                vault_command=args.vault_command,
                ssh_public_key=Path(args.ssh_public_key),
                ssh_signer_mount=args.ssh_signer_mount.rstrip("/"),
                ssh_signer_role=args.ssh_signer_role,
                verbose=args.verbose,
            )
    except CalledProcessError as exc:
        print(
            f"ERROR: {shlex.join(exc.cmd)} returned {exc.returncode}", file=sys.stderr
        )
        sys.exit(exc.returncode)


if __name__ == "__main__":
    main()
