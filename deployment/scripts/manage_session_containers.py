#!/usr/bin/env python3
"""
Session Container Management Tool for Legal AI Research Sandbox

This script provides comprehensive management of session containers including:
- Starting and stopping individual sessions
- Extending session TTL
- Resource monitoring and limits
- Health checks and diagnostics

Usage:
    # Start a session container
    python manage_session_containers.py --start SESSION_ID

    # Stop a session container
    python manage_session_containers.py --stop SESSION_ID

    # Restart a session container
    python manage_session_containers.py --restart SESSION_ID

    # Extend session TTL
    python manage_session_containers.py --extend SESSION_ID --hours 24

    # Check session health
    python manage_session_containers.py --health SESSION_ID

    # Show session logs
    python manage_session_containers.py --logs SESSION_ID
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Find project root and directories
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
deployment_dir = project_root / "deployment"


def load_session_config(session_id: str) -> Optional[Dict[str, Any]]:
    """Load session configuration by ID."""
    # Try new structure first
    session_file = deployment_dir / "sessions" / session_id / "session.json"

    if not session_file.exists():
        print(f"Session configuration not found: {session_id}")
        return None

    try:
        with open(session_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load session config: {e}")
        return None


def save_session_config(session_id: str, config: Dict[str, Any]) -> bool:
    """Save session configuration."""
    # Try new structure first
    session_file = deployment_dir / "sessions" / session_id / "session.json"

    if not session_file.exists():
        print(f"Session file not found: {session_file}")
        return False

    try:
        with open(session_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save session config: {e}")
        return False


def get_container_status(session_id: str) -> Dict[str, str]:
    """Get status of containers for a session."""
    status = {}

    container_names = [
        f"legal_sandbox_{session_id}_backend",
        f"legal_sandbox_{session_id}_frontend"
    ]

    for container_name in container_names:
        try:
            result = subprocess.run([
                'docker', 'inspect', '--format', '{{.State.Status}}', container_name
            ], capture_output=True, text=True)

            if result.returncode == 0:
                service = "backend" if "backend" in container_name else "frontend"
                status[service] = result.stdout.strip()
            else:
                service = "backend" if "backend" in container_name else "frontend"
                status[service] = "not_found"
        except Exception:
            service = "backend" if "backend" in container_name else "frontend"
            status[service] = "error"

    return status


def start_session(session_id: str) -> bool:
    """Start containers for a session."""
    print(f"🚀 Starting session: {session_id}")

    config = load_session_config(session_id)
    if not config:
        return False

    # Try new structure first
    env_file = deployment_dir / "sessions" / session_id / ".env"

    if not env_file.exists():
        print(f"Environment file not found: {env_file}")
        return False

    try:
        result = subprocess.run([
            'docker-compose',
            '-f', str(project_root / 'docker-compose.yml'),
            '--env-file', str(env_file),
            'up', '-d'
        ],
        cwd=str(project_root),
        capture_output=True,
        text=True
        )

        if result.returncode == 0:
            print(f"  ✓ Session containers started")

            # Wait for services to be ready
            import time
            time.sleep(5)

            # Check health
            container_config = config.get('container_config', {})
            backend_port = container_config.get('backend_port')
            frontend_port = container_config.get('frontend_port')

            if backend_port and frontend_port:
                print(f"  🌐 Frontend: http://localhost:{frontend_port}")
                print(f"  🔗 Backend:  http://localhost:{backend_port}")

            return True
        else:
            print(f"   Failed to start containers: {result.stderr}")
            return False

    except Exception as e:
        print(f"   Error starting session: {e}")
        return False


def stop_session(session_id: str) -> bool:
    """Stop containers for a session."""
    print(f"🛑 Stopping session: {session_id}")

    # Try new structure first
    env_file = deployment_dir / "sessions" / session_id / ".env"

    if not env_file.exists():
        print(f"Environment file not found, trying direct container stop")

        # Try to stop containers directly
        container_names = [
            f"legal_sandbox_{session_id}_backend",
            f"legal_sandbox_{session_id}_frontend"
        ]

        success = True
        for container_name in container_names:
            try:
                result = subprocess.run(['docker', 'stop', container_name],
                                      capture_output=True)
                if result.returncode == 0:
                    print(f"  ✓ Stopped {container_name}")
                else:
                    print(f"   Failed to stop {container_name}")
                    success = False
            except Exception as e:
                print(f"   Error stopping {container_name}: {e}")
                success = False

        return success

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
            print(f"  ✓ Session containers stopped")
            return True
        else:
            print(f"   Failed to stop containers: {result.stderr}")
            return False

    except Exception as e:
        print(f"   Error stopping session: {e}")
        return False


def restart_session(session_id: str) -> bool:
    """Restart containers for a session."""
    print(f"🔄 Restarting session: {session_id}")

    if stop_session(session_id):
        import time
        time.sleep(2)  # Brief pause
        return start_session(session_id)

    return False


def extend_session(session_id: str, additional_hours: int) -> bool:
    """Extend session TTL by specified hours."""
    print(f"⏰ Extending session {session_id} by {additional_hours} hours")

    config = load_session_config(session_id)
    if not config:
        return False

    try:
        # Update container config
        container_config = config.get('container_config', {})
        current_expires = datetime.fromisoformat(
            container_config['expires_at'].replace('Z', '+00:00')
        )
        new_expires = current_expires + timedelta(hours=additional_hours)
        container_config['expires_at'] = new_expires.isoformat()

        # Update session config
        sessions = config.get('sessions', [])
        if sessions:
            sessions[0]['expires_at'] = new_expires.isoformat()
            sessions[0]['ttl_hours'] = sessions[0].get('ttl_hours', 72) + additional_hours

        # Save updated config
        if save_session_config(session_id, config):
            print(f"  ✓ Session extended until: {new_expires.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            return True
        else:
            return False

    except Exception as e:
        print(f"   Error extending session: {e}")
        return False


def check_session_health(session_id: str) -> None:
    """Check health of session containers."""
    print(f"🏥 Health check for session: {session_id}")

    config = load_session_config(session_id)
    if not config:
        return

    container_config = config.get('container_config', {})
    status = get_container_status(session_id)

    # Check container status
    print(f"  Container Status:")
    for service, state in status.items():
        icon = "✓" if state == "running" else "❌" if state == "exited" else "⚠"
        print(f"    {service.capitalize()}: {icon} {state}")

    # Check network connectivity
    backend_port = container_config.get('backend_port')
    if backend_port and status.get('backend') == 'running':
        try:
            result = subprocess.run([
                'curl', '-f', '-s', f'http://localhost:{backend_port}/health'
            ], capture_output=True, timeout=5)

            if result.returncode == 0:
                print(f"  Backend Health: ✓ Healthy")
            else:
                print(f"  Backend Health: Unhealthy")
        except Exception:
            print(f"  Backend Health: ⚠ Cannot reach")

    # Check session expiration
    expires_at_str = container_config.get('expires_at')
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)

            if now > expires_at:
                print(f"  Session TTL: ❌ EXPIRED ({expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')})")
            else:
                remaining = expires_at - now
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                print(f"  Session TTL: ✓ {hours}h {minutes}m remaining")
        except Exception:
            print(f"  Session TTL: ⚠ Cannot parse expiration")

    # Show access URLs
    frontend_port = container_config.get('frontend_port')
    if frontend_port:
        print(f"  Access URLs:")
        print(f"    Frontend: http://localhost:{frontend_port}")
        if backend_port:
            print(f"    Backend:  http://localhost:{backend_port}")


def show_session_logs(session_id: str, service: Optional[str] = None) -> None:
    """Show logs for session containers."""
    container_names = []

    if service == "backend":
        container_names = [f"legal_sandbox_{session_id}_backend"]
    elif service == "frontend":
        container_names = [f"legal_sandbox_{session_id}_frontend"]
    else:
        container_names = [
            f"legal_sandbox_{session_id}_backend",
            f"legal_sandbox_{session_id}_frontend"
        ]

    for container_name in container_names:
        print(f"\n📋 Logs for {container_name}:")
        print("-" * 50)

        try:
            result = subprocess.run([
                'docker', 'logs', '--tail', '50', container_name
            ], capture_output=True, text=True)

            if result.returncode == 0:
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
            else:
                print(f"❌ Failed to get logs: {result.stderr}")

        except Exception as e:
            print(f"❌ Error getting logs: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Manage session containers for Legal AI Research Sandbox'
    )
    parser.add_argument('session_id', nargs='?', help='Session ID to manage')

    # Actions
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--start', action='store_true', help='Start session containers')
    action_group.add_argument('--stop', action='store_true', help='Stop session containers')
    action_group.add_argument('--restart', action='store_true', help='Restart session containers')
    action_group.add_argument('--health', action='store_true', help='Check session health')
    action_group.add_argument('--logs', action='store_true', help='Show session logs')
    action_group.add_argument('--extend', action='store_true', help='Extend session TTL')

    # Options
    parser.add_argument('--hours', type=int, help='Hours to extend session TTL')
    parser.add_argument('--service', choices=['backend', 'frontend'], help='Specific service for logs')

    args = parser.parse_args()

    if not args.session_id:
        print("❌ Session ID is required")
        return 1

    # Validate session exists
    session_file_new = deployment_dir / "sessions" / args.session_id / "session.json"

    if not session_file_new.exists() and not args.logs:  # logs can work without config file
        print(f"❌ Session configuration not found: {args.session_id}")
        return 1

    # Execute action
    success = True

    if args.start:
        success = start_session(args.session_id)
    elif args.stop:
        success = stop_session(args.session_id)
    elif args.restart:
        success = restart_session(args.session_id)
    elif args.health:
        check_session_health(args.session_id)
    elif args.logs:
        show_session_logs(args.session_id, args.service)
    elif args.extend:
        if not args.hours:
            print("❌ --hours is required when extending session")
            return 1
        success = extend_session(args.session_id, args.hours)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
