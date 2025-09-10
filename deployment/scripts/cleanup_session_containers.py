#!/usr/bin/env python3
"""
Session Container Cleanup Tool for Legal AI Research Sandbox

This script manages the lifecycle of session containers, including:
- Manual cleanup of expired sessions
- Automatic cleanup based on TTL
- Emergency cleanup of all sessions
- Resource monitoring and reporting

Usage:
    # Cleanup expired sessions
    python cleanup_session_containers.py

    # Cleanup specific session
    python cleanup_session_containers.py --session SESSION_ID

    # Emergency cleanup all sessions
    python cleanup_session_containers.py --all

    # Dry run (show what would be cleaned up)
    python cleanup_session_containers.py --dry-run

    # List active sessions
    python cleanup_session_containers.py --list
"""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# Find project root and directories
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
deployment_dir = project_root / "deployment"


def get_docker_containers() -> List[Dict[str, Any]]:
    """Get all running Docker containers with legal sandbox prefix."""
    try:
        result = subprocess.run([
            'docker', 'ps', '--format', '{{.Names}}\t{{.ID}}\t{{.Status}}\t{{.Ports}}'
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Failed to list Docker containers: {result.stderr}")
            return []

        containers = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) >= 3:
                name = parts[0]
                if name.startswith('legal_sandbox_') or 'sandbox' in name:
                    containers.append({
                        'name': name,
                        'id': parts[1],
                        'status': parts[2],
                        'ports': parts[3] if len(parts) > 3 else ''
                    })

        return containers
    except Exception as e:
        print(f"❌ Error listing containers: {e}")
        return []


def get_session_files() -> List[Path]:
    """Get all session configuration files."""
    session_files = []
    sessions_dir = deployment_dir / "sessions"

    if sessions_dir.exists():
        # New structure: deployment/sessions/{session_id}/
        for session_dir in sessions_dir.iterdir():
            if session_dir.is_dir():
                session_json = session_dir / "session.json"
                env_file = session_dir / ".env"
                if session_json.exists():
                    session_files.append(session_json)
                if env_file.exists():
                    session_files.append(env_file)

    for file_path in deployment_dir.glob(".env.*"):
        if file_path.name != ".env.container.template":
            session_files.append(file_path)

    return session_files


def load_session_config(session_file: Path) -> Optional[Dict[str, Any]]:
    """Load session configuration from file."""
    try:
        with open(session_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠ Failed to load {session_file}: {e}")
        return None


def is_session_expired(session_config: Dict[str, Any]) -> bool:
    """Check if session has expired based on TTL."""
    try:
        container_config = session_config.get('container_config', {})
        expires_at_str = container_config.get('expires_at')

        if not expires_at_str:
            # Fallback to session data
            sessions = session_config.get('sessions', [])
            if sessions:
                expires_at_str = sessions[0].get('expires_at')

        if not expires_at_str:
            print("⚠ No expiration date found in session config")
            return False

        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
        return datetime.now(timezone.utc) > expires_at

    except Exception as e:
        print(f"⚠ Error checking session expiration: {e}")
        return False


def stop_container(container_name: str) -> bool:
    """Stop a specific container."""
    try:
        result = subprocess.run([
            'docker', 'stop', container_name
        ], capture_output=True, text=True)

        if result.returncode == 0:
            return True
        else:
            print(f"❌ Failed to stop container {container_name}: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error stopping container {container_name}: {e}")
        return False


def remove_container(container_name: str) -> bool:
    """Remove a specific container."""
    try:
        result = subprocess.run([
            'docker', 'rm', container_name
        ], capture_output=True, text=True)

        if result.returncode == 0:
            return True
        else:
            print(f"❌ Failed to remove container {container_name}: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error removing container {container_name}: {e}")
        return False


def cleanup_session_files(session_id: str) -> None:
    """Remove session configuration files."""
    # New structure: deployment/sessions/{session_id}/
    session_dir = deployment_dir / "sessions" / session_id
    if session_dir.exists():
        try:
            import shutil
            shutil.rmtree(session_dir)
            print(f"  ✓ Removed session directory: {session_dir.name}")
        except Exception as e:
            print(f"  ⚠ Failed to remove session directory {session_dir}: {e}")



def cleanup_docker_compose(session_id: str) -> bool:
    """Stop docker-compose services for a session."""
    # Try new structure first
    env_file = deployment_dir / "sessions" / session_id / ".env"

    if not env_file.exists():
        print(f"  ⚠ Environment file not found: {env_file}")
        return False

    try:
        result = subprocess.run([
            'docker-compose',
            '-f', str(project_root / 'docker-compose.yml'),
            '--env-file', str(env_file),
            'down'
        ],
        cwd=str(project_root),
        capture_output=True,
        text=True
        )

        if result.returncode == 0:
            print(f"  ✓ Stopped docker-compose services")
            return True
        else:
            print(f"   Failed to stop docker-compose: {result.stderr}")
            return False

    except Exception as e:
        print(f"   Error stopping docker-compose: {e}")
        return False


def list_active_sessions() -> None:
    """List all active session containers."""
    containers = get_docker_containers()
    session_files = get_session_files()

    print("\n" + "="*70)
    print("ACTIVE SESSION CONTAINERS")
    print("="*70)

    if not containers and not session_files:
        print("No active sessions found.")
        return

    # Show running containers
    if containers:
        print("\n🐳 Running Containers:")
        for container in containers:
            print(f"  • {container['name']} ({container['id'][:12]})")
            print(f"    Status: {container['status']}")
            if container['ports']:
                print(f"    Ports: {container['ports']}")

    # Show session files
    session_configs = {}
    for file_path in session_files:
        if file_path.name == 'session.json':
            session_id = file_path.parent.name
            config = load_session_config(file_path)
            if config:
                session_configs[session_id] = config
        elif file_path.name.startswith('session_'):
            session_id = file_path.name.replace('session_', '').replace('.json', '')
            config = load_session_config(file_path)
            if config:
                session_configs[session_id] = config

    if session_configs:
        print("\n📋 Session Configurations:")
        for session_id, config in session_configs.items():
            container_config = config.get('container_config', {})
            is_expired = is_session_expired(config)
            status = "EXPIRED" if is_expired else "ACTIVE"

            print(f"  • {session_id} [{status}]")
            if container_config:
                print(f"    Frontend: http://localhost:{container_config.get('frontend_port', 'N/A')}")
                print(f"    Backend:  http://localhost:{container_config.get('backend_port', 'N/A')}")
                print(f"    Expires:  {container_config.get('expires_at', 'N/A')}")


def cleanup_session(session_id: str, dry_run: bool = False) -> bool:
    """Clean up a specific session."""
    print(f"\n🧹 Cleaning up session: {session_id}")

    if dry_run:
        print("  [DRY RUN] Would perform cleanup operations")
        return True

    success = True

    # Stop docker-compose services
    if not cleanup_docker_compose(session_id):
        success = False

    # Remove session files
    cleanup_session_files(session_id)

    # Force remove any remaining containers
    containers = get_docker_containers()
    for container in containers:
        if session_id in container['name']:
            print(f"  🛑 Force removing container: {container['name']}")
            stop_container(container['name'])
            remove_container(container['name'])

    if success:
        print(f"  ✓ Session {session_id} cleaned up successfully")

    return success


def cleanup_expired_sessions(dry_run: bool = False) -> None:
    """Clean up all expired sessions."""
    print(f"\n🕰️  Cleaning up expired sessions...")

    session_files = [f for f in get_session_files() if f.name == 'session.json' or f.name.startswith('session_')]
    expired_count = 0

    for session_file in session_files:
        config = load_session_config(session_file)
        if not config:
            continue

        if is_session_expired(config):
            if session_file.name == 'session.json':
                session_id = session_file.parent.name
            else:
                session_id = session_file.name.replace('session_', '').replace('.json', '')

            expired_count += 1

            if dry_run:
                print(f"  [DRY RUN] Would cleanup expired session: {session_id}")
            else:
                cleanup_session(session_id, dry_run=False)

    if expired_count == 0:
        print("  ✓ No expired sessions found")
    else:
        print(f"  ✓ Processed {expired_count} expired session(s)")


def cleanup_all_sessions(dry_run: bool = False) -> None:
    """Emergency cleanup of all sessions."""
    print(f"\n🚨 EMERGENCY CLEANUP: Removing all sessions...")

    if not dry_run:
        confirm = input("Are you sure you want to remove ALL sessions? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cleanup cancelled.")
            return

    containers = get_docker_containers()
    session_files = get_session_files()

    # Stop all containers
    for container in containers:
        if dry_run:
            print(f"  [DRY RUN] Would stop container: {container['name']}")
        else:
            print(f"  🛑 Stopping container: {container['name']}")
            stop_container(container['name'])
            remove_container(container['name'])

    # Remove all session files
    for file_path in session_files:
        if dry_run:
            print(f"  [DRY RUN] Would remove: {file_path.name}")
        else:
            try:
                file_path.unlink()
                print(f"  ✓ Removed {file_path.name}")
            except Exception as e:
                print(f"  ⚠ Failed to remove {file_path}: {e}")

    if not dry_run:
        print("  ✓ All sessions cleaned up")


def main():
    parser = argparse.ArgumentParser(
        description='Cleanup session containers for Legal AI Research Sandbox'
    )
    parser.add_argument(
        '--session',
        type=str,
        help='Clean up specific session by ID'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Emergency cleanup of all sessions (requires confirmation)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all active sessions'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be cleaned up without actually doing it'
    )

    args = parser.parse_args()

    # Check Docker availability
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True)
        if result.returncode != 0:
            print("Docker not available. Container cleanup requires Docker.")
            return
    except FileNotFoundError:
        print("Docker not found. Container cleanup requires Docker.")
        return

    if args.list:
        list_active_sessions()
    elif args.session:
        cleanup_session(args.session, args.dry_run)
    elif args.all:
        cleanup_all_sessions(args.dry_run)
    else:
        # Default: cleanup expired sessions
        cleanup_expired_sessions(args.dry_run)


if __name__ == "__main__":
    main()
