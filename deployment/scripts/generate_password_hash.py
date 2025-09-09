#!/usr/bin/env python3
"""
Password Hash Generator for plAIground Backend

This script generates bcrypt password hashes for use in the plAIground backend
application, particularly for setting up admin credentials in the .env file.

Usage:
    python generate_password_hash.py "your-password"

Requirements:
    - For development: source the backend .venv first
      cd backend && source .venv/bin/activate

Example:
    python generate_password_hash.py "admin123"
    # Output: Hash: $2b$12$xyz...

The generated hash can be copied to the ADMIN_PASSWORD_HASH variable in your .env file.
"""

import argparse
import bcrypt


def main():
    parser = argparse.ArgumentParser(description='Generate a bcrypt password hash')
    parser.add_argument('password', help='Password to hash')

    args = parser.parse_args()

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(args.password.encode('utf-8'), salt)

    print(f"Password: {args.password}")
    print(f"Hash: {hashed_password.decode('utf-8')}")

if __name__ == "__main__":
    main()
