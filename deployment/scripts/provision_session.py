#!/usr/bin/env python3
"""
Session Provisioning Tool for Legal AI Research Sandbox

This script generates researcher credentials and creates a sessions.json file
that the backend loads on startup to pre-provision authenticated sessions.

Usage:
    # Generate single researcher session
    python provision_session.py

    # Generate multiple researcher sessions
    python provision_session.py --count 3

    # Specify custom output file
    python provision_session.py --output /custom/path/sessions.json

By default, sessions.json is saved to the backend directory.
"""

import argparse
import json
import secrets
import string
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple
import bcrypt

# Find project root and backend directory
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # deployment/scripts -> deployment -> project root
backend_dir = project_root / "backend"

# Add backend to path for imports if needed
sys.path.insert(0, str(backend_dir))


def generate_password(length: int = 16) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_username() -> str:
    """Generate a unique researcher username."""
    suffix = secrets.token_hex(4)
    return f"researcher_{suffix}"


def hash_password(password: str) -> str:
    """Generate bcrypt hash for password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def generate_session() -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Generate a single researcher session with credentials."""
    username = generate_username()
    password = generate_password()
    password_hash = hash_password(password)
    session_id = secrets.token_urlsafe(32)

    # Calculate session timing
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(hours=72)

    session = {
        "session_id": session_id,
        "username": username,
        "password_hash": password_hash,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "ttl_hours": 72,
        "active": True,
        "documents": [],
        "conversations": []
    }

    # Return both session data and plaintext credentials for admin
    credentials = {
        "username": username,
        "password": password,  # Only for display to admin
        "session_id": session_id,
        "expires_at": expires_at.isoformat()
    }

    return session, credentials


def save_sessions(sessions: List[Dict[str, Any]], output_path: Path) -> None:
    """Save sessions to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sessions_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sessions": sessions
    }

    with open(output_path, 'w') as f:
        json.dump(sessions_data, f, indent=2)

    print(f"\n✓ Sessions saved to: {output_path.resolve()}")


def print_credentials(credentials_list: List[Dict[str, str]]) -> None:
    """Print credentials in a format easy for admin to copy."""
    print("\n" + "="*70)
    print("RESEARCHER CREDENTIALS")
    print("="*70)
    print("\nProvide these credentials to researchers via secure channel:")
    print("(Email template below)\n")

    for i, creds in enumerate(credentials_list, 1):
        print(f"--- Researcher {i} ---")
        print(f"Username: {creds['username']}")
        print(f"Password: {creds['password']}")
        print(f"Session ID: {creds['session_id']}")
        print(f"Expires: {creds['expires_at']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Generate researcher credentials for Legal AI Research Sandbox'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of researcher sessions to generate (default: 1)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for sessions.json file (default: backend/sessions.json)'
    )
    parser.add_argument(
        '--append',
        action='store_true',
        help='Append to existing sessions file instead of overwriting'
    )

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Default to backend/sessions.json relative to project root
        output_path = backend_dir / "sessions.json"

    # Generate sessions
    sessions = []
    credentials_list = []

    print(f"\nGenerating {args.count} researcher session(s)...")
    print(f"Output file: {output_path.resolve()}")

    for i in range(args.count):
        session, credentials = generate_session()
        sessions.append(session)
        credentials_list.append(credentials)
        print(f"  ✓ Generated session {i+1}/{args.count}")

    # Handle append mode
    if args.append and output_path.exists():
        with open(output_path, 'r') as f:
            existing_data = json.load(f)
            if 'sessions' in existing_data:
                sessions = existing_data['sessions'] + sessions
                print(f"  ✓ Appending to existing {len(existing_data['sessions'])} session(s)")

    # Save sessions
    save_sessions(sessions, output_path)

    # Print credentials for admin
    print_credentials(credentials_list)

    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print(f"1. Sessions file saved to: {output_path.resolve()}")
    print("2. Start the backend server (it will load sessions automatically)")
    print("3. Send credentials to researchers via secure channel")
    print("IMPORTANT: Passwords are displayed once here and cannot be recovered. be sure to save them.")
    print()


if __name__ == "__main__":
    main()
