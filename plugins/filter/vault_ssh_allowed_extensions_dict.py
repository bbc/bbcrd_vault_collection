
def vault_ssh_allowed_extensions_dict_filter(allowed_extensions: list[str]) -> dict[str, str]:
    """
    The default_extensions argument to the SSH signer API
    (https://developer.hashicorp.com/vault/api-docs/secret/ssh#default_extensions)
    requires a dictionary where the allowed extensions are the keys and the
    values are all empty strings. This filter converts a list of allowed
    extensions into such a dict.
    """
    return {extension: "" for extension in allowed_extensions}


class FilterModule(object):
    def filters(self):
        return {
            "vault_ssh_allowed_extensions_dict": vault_ssh_allowed_extensions_dict_filter,
        }
