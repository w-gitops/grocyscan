#!/usr/bin/env python3
"""Generate a bcrypt password hash for configuration.

Usage:
    python scripts/generate_password_hash.py [password]

If no password is provided, prompts for input.
"""

import getpass
import sys

from app.services.auth import hash_password


def main() -> None:
    """Generate and print a password hash."""
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("Passwords do not match!")
            sys.exit(1)

    hashed = hash_password(password)
    print(f"\nPassword hash (add to .env as AUTH_PASSWORD_HASH):\n{hashed}")


if __name__ == "__main__":
    main()
