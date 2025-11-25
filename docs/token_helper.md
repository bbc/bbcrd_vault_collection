Vault Token Helper
==================

A simple [token
helper](https://developer.hashicorp.com/vault/docs/commands/token-helper)
implementation is provided in
[`utils/vault_token_helper.py`](../utils/vault_token_helper.py). This stores
Vault tokens for multiple servers in a JSON file named `~/.vault-tokens`. This
makes it easier to work with multiple Vault servers simultaneously.

To install for use with Hashicorp Vault, add the following line to `~/.vault`:

    token_helper = "/path/to/vault_token_helper.py"

To install for use with OpenBao, add the following line to `~/.bao`:

    token_helper = "/path/to/bao_token_helper.py"

> [!NOTE]
>
> When the script name is `bao_token_helper.py`, the value of `BAO_ADDR` will
> be used in preference to `VAULT_ADDR` if defined. A symlink to the token
> helper script named `bao_token_helper.py` is included in this repository for
> this purpose.
