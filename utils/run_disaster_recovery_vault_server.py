#!/usr/bin/env python3

"""
This script starts up an ephemeral local Vault server from a Vault Raft
snapshot (backup) for use in disaster recovery scenarios.

Usage::

    $ python run_disaster_recovery_vault_server.py [snapshot filename]

If a snapshot is provided, it will be loaded into the vault server and be left
ready for you to unseal. Otherwise, keys for the empty vault instance are
provided.

NB: You must disable swap when using this server with 'real' secrets to avoid
the possibility of any plaintext secrets being swapped to disk.
"""

from typing import NamedTuple, Iterator, BinaryIO

import sys
import json
import time
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import contextmanager
from textwrap import dedent

import requests


@contextmanager
def vault_server(
    port: int = 8200,
    cluster_port: int = 8201,
    vault_command: str = "vault",
    log_file: BinaryIO = sys.stderr.buffer,
    log_level: str = "error",
    startup_timeout: int = 10,
) -> str:
    """
    Start a new, ephemeral Vault server using raft storage. The server is
    killed and all data deleted on exiting the context manager.

    Parameters
    ==========
    port : int
        The http (non TLS) port to listen on on localhost.
    cluster_port : int
        The port to use for the (mandatory, but unused in this environment)
        clustering API endpoint.
    vault_command : str
        The name of the command to run vault.
    log_file : writable file opened in binary mode
        The file to redirect all vault server output to.
    log_level: str
        The vault log level to use. See `-log-level` in `vault server -help`.
    startup_timeout : int
        Number of seconds to wait for the Vault server to become responsive.

    Returns
    =======
    str
        The vault server address. (Always "http://localhost:{port}").
    """
    with TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        # Create Raft data directory
        data_dir = tmp_dir / "data"
        data_dir.mkdir()

        # Create Vault config file
        config_file = tmp_dir / "config.hcl"
        config_file.write_text(
            dedent(
                f"""
                    storage "raft" {{
                        path = {json.dumps(str(data_dir))}
                        node_id = "vault"
                    }}
                    listener "tcp" {{
                        address = "localhost:{port}"
                        cluster_address = "localhost:{cluster_port}"
                        tls_disable = true
                    }}
                    api_addr =  "http://localhost:{port}"
                    cluster_addr = "https://localhost:{cluster_port}"
                    disable_mlock = true
                    log_level = {json.dumps(log_level)}
                    ui = true
                """
            ).lstrip()
        )

        # Start the vault server
        process = subprocess.Popen(
            [
                vault_command,
                "server",
                "-config",
                str(config_file),
            ],
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        try:
            # Wait for server startup
            for _ in range(int(startup_timeout)):
                time.sleep(1)
                try:
                    response = requests.get(f"http://localhost:{port}/v1/sys/init")
                    if response.status_code == 200:
                        # Checking for non-initialised sanity checks that we're
                        # connected to this Vault (or at least one equally
                        # worthless!) and not some already-running Vault
                        # instance using the same port.
                        if response.json()["initialized"] is not False:
                            raise Exception(
                                f"Another server is already running on port {port}"
                            )
                        break
                except:
                    pass
            else:
                raise Exception("Vault server API failed to start.")

            yield f"http://localhost:{port}"
        finally:
            process.kill()


def wait_for_vault_cluster_to_come_up(vault_addr: str, timeout: int = 10) -> None:
    """Wait for Vault's clustering to come up."""
    for _ in range(int(timeout)):
        time.sleep(1)
        try:
            # We use the root-key generation status API endpoint to verify
            # cluster membership. This API is a cluster-wide command (i.e.
            # requires cluster membership) but doesn't require a valid token
            # of any kind.
            response = requests.get(f"{vault_addr}/v1/sys/generate-root/attempt")
            if response.status_code == 200:
                return
        except:
            pass
    else:
        raise Exception("Vault cluster failed to come up.")


class VaultInitialKeys(NamedTuple):
    unseal_keys: list[str]
    root_token: str


def vault_init(
    vault_addr: str, secret_shares: int = 1, secret_threshold: int = 1
) -> VaultInitialKeys:
    """Initialise a vault server."""

    response = requests.post(
        f"{vault_addr}/v1/sys/init",
        json={
            "secret_shares": secret_shares,
            "secret_threshold": secret_threshold,
        },
    )
    response.raise_for_status()
    return VaultInitialKeys(
        unseal_keys=response.json()["keys"],
        root_token=response.json()["root_token"],
    )


def vault_unseal(vault_addr: str, unseal_keys: list[str]) -> None:
    """Unseal vault."""
    # Restart unseal process
    response = requests.post(
        f"{vault_addr}/v1/sys/unseal",
        json={"reset": True},
    )
    response.raise_for_status()

    # Insert keys until unsealed
    for unseal_key in unseal_keys:
        response = requests.post(
            f"{vault_addr}/v1/sys/unseal",
            json={"key": unseal_key},
        )
        response.raise_for_status()
        if not response.json()["sealed"]:
            return  # Done!

    raise Exception("Not enough unseal keys provided")


def vault_snapshot_restore(vault_addr: str, root_token: str, snapshot: Path) -> None:
    """Force-restore a Raft snapshot."""

    response = requests.post(
        f"{vault_addr}/v1/sys/storage/raft/snapshot-force",
        headers={"X-Vault-Token": root_token},
        data=snapshot.open("rb"),
    )
    response.raise_for_status()


def main() -> None:
    parser = ArgumentParser(
        description="""
            Start an ephemeral vault server, optionally importing a raft
            snapshot (i.e. Vault integrated storage backup).
        """
    )

    parser.add_argument(
        "snapshot",
        type=Path,
        nargs="?",
        help="""
            A Raft snapshot (e.g. backup) to load into the fresly created
            server, leaving the server sealed and awaiting the matching unseal
            keys.
        """,
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8200,
        help="""
            The port number to listen on. Defaults to %(default)s. (NB: This
            script will *only* listen on localhost without HTTPS encryption)
        """,
    )
    parser.add_argument(
        "--cluster-port",
        "-P",
        type=int,
        default=8201,
        help="""
            The port number for the clustering API to use. Defaults to
            %(default)s. This can be set to anything and is essentially unused:
            our cluster consists of only one member so nothing will ever
            connect to this port.
        """,
    )
    parser.add_argument(
        "--vault-log-level",
        "-L",
        type=str,
        default="error",
        help="""
            The log level for the vault server to use. Defaults to %(default)s.
        """,
    )
    parser.add_argument(
        "--vault-command",
        "-V",
        type=str,
        default="vault",
        help="""
            The name of the vault command. Defaults to %(default)s.
        """,
    )

    args = parser.parse_args()

    print("Starting ephemeral Vault server...")
    with vault_server(
        port=args.port,
        cluster_port=args.cluster_port,
        log_level=args.vault_log_level,
        vault_command=args.vault_command,
    ) as vault_addr:
        print("Initialising vault...")
        initial_keys = vault_init(vault_addr)

        print("Unsealing empty vault...")
        vault_unseal(vault_addr, initial_keys.unseal_keys)
        wait_for_vault_cluster_to_come_up(vault_addr)

        if args.snapshot:
            print("Loading snapshot...")
            vault_snapshot_restore(vault_addr, initial_keys.root_token, args.snapshot)

        print(
            dedent(
                f"""
                    Vault running at {vault_addr}.

                    Hint:

                        $ export VAULT_ADDR={vault_addr}
                """
            ).lstrip()
        )

        if args.snapshot:
            print(
                dedent(
                    """
                        The vault is now sealed with the unseal keys belonging to the snapshot.

                        1. Obtain the unseal keys. Hint:

                               $ cat encrypted_unseal_keys.json   # Put the encrypted unseal keys here!
                               $ ansible-playbook bbcrd.ansible_vault.decrypt_unseal_keys_file
                               ...snip...
                               TASK [Display decrypted unseal keys]
                               ok: [localhost] => {
                                   "ansible_vault_unseal_keys": [
                                       "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                                   ]
                               }

                        2. Unseal vault. Hint:

                               $ vault operator unseal

                        Tip: Vault server errors messages about HA locks and raft failures can be
                        safely ignored.
                    """
                ).lstrip()
            )
        else:
            print(
                dedent(
                    f"""
                        Ephemeral server credentials:

                            Unseal key: {", ".join(initial_keys.unseal_keys)}
                            Root token: {initial_keys.root_token}

                        Hint:

                            $ vault login {initial_keys.root_token}
                    """
                ).lstrip()
            )

        input("<Press enter to kill server (destroying all data)>\n")


if __name__ == "__main__":
    main()
