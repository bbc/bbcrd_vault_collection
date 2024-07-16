"""
A lookup plugin which enumerates the fingerprints of all private keys in
the local GnuPG environment.
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

from subprocess import run

class LookupModule(LookupBase):
    
    def run(self, terms, variables=None, **kwargs):
        try:
            output = run(
                [
                    "gpg",
                    # Run in non-interactive, machine-readable mode
                    "--batch",
                    "--no-tty",
                    "--with-colons",
                    # Enumerate private keys
                    "--list-secret-keys",
                ],
                capture_output=True,
                check=True,
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
