#!/usr/bin/env python3

from argparse import ArgumentParser
from pathlib import Path
import json
import os
import sys
import tempfile

tokens_file = Path.home() / ".vault-tokens"


def main() -> None:
    parser = ArgumentParser(description="Vault/Bao token helper")
    parser.add_argument("action", choices=["get", "store", "erase"])
    args = parser.parse_args()

    if parser.prog == "bao_token_helper.py":
        variables = ["VAULT_ADDR", "BAO_ADDR"]
    else:
        variables = ["VAULT_ADDR"]

    server_address = "https://127.0.0.1:8200/"
    for var in variables:
        if var in os.environ:
            server_address = os.environ[var]

    if tokens_file.is_file():
        tokens = json.load(tokens_file.open(encoding="utf-8"))
    else:
        tokens = {}

    if args.action == "get":
        print(tokens.get(server_address, ""), end="")
        return  # Exit early, no changes to write-back
    elif args.action == "store":
        tokens[server_address] = sys.stdin.read()
    elif args.action == "erase":
        tokens.pop(server_address, None)

    # Atomically overwrite the tokens file
    temp_fnum, temp_fname = tempfile.mkstemp(
        prefix=tokens_file.name,
        dir=tokens_file.parent,
    )
    os.write(temp_fnum, json.dumps(tokens).encode("utf-8"))
    os.close(temp_fnum)
    os.replace(temp_fname, tokens_file)


if __name__ == "__main__":
    main()
