#!/usr/bin/env python3
"""
Active Session Monitor for Legal AI Research Sandbox

This script provides detailed monitoring and management of active session containers.

Usage:
    # List all active sessions with details
    python list_active_sessions.py

    # Show only running containers
    python list_active_sessions.py --containers-only

    # Show session details in JSON format
    python list_active_sessions.py --json

    # Monitor sessions in real-time
    python list_active_sessions.py --watch

    # Show resource usage
    python list_active_sessions.py --resources
"""

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

# Find project root and directories
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
deployment_dir = project_root / "deployment"


def get_container_stats(container_name: str) -> Dict[str, Any]:
    """Get resource usage stats for a container."""
    try:
        result = subprocess.run([
            'docker', 'stats', container_name, '--no-stream', '--format',
            '{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}'
        ], capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split('\t')
            if len(parts) >= 4:
                return {
                    'cpu_percent': parts[0],
                    'memory_usage': parts[1],
                    'network_io': parts[2],
                    'block_io': parts[3]
                }
        return {}
    except Exception:
        return {}


def get_running_containers() -> List[Dict[str, Any]]:
    """Get detailed information about running sandbox containers."""
    try:
        result = subprocess.run([
            'docker', 'ps', '--format',
            '{{.Names}}\t{{.ID}}\t{{.Status}}\t{{.Ports}}\t{{.CreatedAt}}'
        ], capture_output=True, text=True)

        if result.returncode != 0:
            return []

        containers = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) >= 4:
                name = parts[0]
                if 'sandbox' in name:
                    container_info = {
                        'name': name,
                        'id': parts[1][:12],
                        'status': parts[2],
                        'ports': parts[3],
                        'created': parts[4] if len(parts) > 4 else 'Unknown'
                    }
                    containers.append(container_info)

        return containers
    except Exception as e:
        print(f"❌ Error listing containers: {e}")
        return []


def load_session_configs() -> Dict[str, Dict[str, Any]]:
    """Load all session configuration files."""
    session_configs = {}

    for file_path in deployment_dir.glob("session_*.json"):
        try:
            session_id = file_path.name.replace('session_', '').replace('.json', '')
            with open(file_path, 'r') as f:
                config = json.load(f)
                session_configs[session_id] = config
        except Exception as e:
            print(f"⚠ Failed to load {file_path}: {e}")

    return session_configs


def is_session_expired(config: Dict[str, Any]) -> bool:
    """Check if session has expired."""
    try:
        container_config = config.get('container_config', {})
        expires_at_str = container_config.get('expires_at')

        if not expires_at_str:
            sessions = config.get('sessions', [])
            if sessions:
                expires_at_str = sessions[0].get('expires_at')

        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            return datetime.now(timezone.utc) > expires_at

        return False
    except Exception:
        return False


def calculate_time_remaining(config: Dict[str, Any]) -> str:
    """Calculate time remaining for session."""
    try:
        container_config = config.get('container_config', {})
        expires_at_str = container_config.get('expires_at')

        if not expires_at_str:
            sessions = config.get('sessions', [])
            if sessions:
                expires_at_str = sessions[0].get('expires_at')

        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)

            if now > expires_at:
                return "EXPIRED"

            remaining = expires_at - now
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)

            return f"{hours}h {minutes}m"

        return "Unknown"
    except Exception:
        return "Unknown"


def display_sessions_table(session_configs: Dict[str, Dict[str, Any]],
                          containers: List[Dict[str, Any]],
                          show_resources: bool = False) -> None:
    """Display sessions in a formatted table."""
    print("\n" + "="*90)
    print("LEGAL AI RESEARCH SANDBOX - ACTIVE SESSIONS")
    print("="*90)

    if not session_configs and not containers:
        print("No active sessions found.")
        return

    # Create container lookup
    container_lookup = {c['name']: c for c in containers}

    print(f"{'SESSION ID':<15} {'STATUS':<10} {'TIME LEFT':<12} {'FRONTEND':<15} {'BACKEND':<15} {'CONTAINER':<10}")
    print("-" * 90)

    for session_id, config in session_configs.items():
        container_config = config.get('container_config', {})
        is_expired = is_session_expired(config)

        # Determine container status
        container_name = f"legal_sandbox_{session_id}_frontend"
        backend_name = f"legal_sandbox_{session_id}_backend"

        status = "EXPIRED" if is_expired else "ACTIVE"
        if container_name in container_lookup or backend_name in container_lookup:
            status = "RUNNING"
        elif not is_expired:
            status = "STOPPED"

        time_left = calculate_time_remaining(config)
        frontend_port = container_config.get('frontend_port', 'N/A')
        backend_port = container_config.get('backend_port', 'N/A')

        frontend_url = f":{frontend_port}" if frontend_port != 'N/A' else "N/A"
        backend_url = f":{backend_port}" if backend_port != 'N/A' else "N/A"

        container_status = "✓" if status == "RUNNING" else "✗"

        print(f"{session_id:<15} {status:<10} {time_left:<12} {frontend_url:<15} {backend_url:<15} {container_status:<10}")

        # Show resource usage if requested
        if show_resources and status == "RUNNING":
            for name in [container_name, backend_name]:
                if name in container_lookup:
                    stats = get_container_stats(name)
                    if stats:
                        service = "Frontend" if "frontend" in name else "Backend"
                        print(f"    {service}: CPU {stats.get('cpu_percent', 'N/A')}, "
                              f"Memory {stats.get('memory_usage', 'N/A')}")

    # Show orphaned containers (containers without session configs)
    orphaned = []
    for container in containers:
        found = False
        for session_id in session_configs.keys():
            if session_id in container['name']:
                found = True
                break
        if not found:
            orphaned.append(container)

    if orphaned:
        print("\n" + "="*50)
        print("ORPHANED CONTAINERS (no session config)")
        print("="*50)
        for container in orphaned:
            print(f"{container['name']} ({container['id']}) - {container['status']}")

    # Summary
    total_sessions = len(session_configs)
    running_sessions = sum(1 for config in session_configs.values() if not is_session_expired(config))
    expired_sessions = total_sessions - running_sessions

    print(f"\n📊 Summary: {total_sessions} total, {running_sessions} active, {expired_sessions} expired")


def display_sessions_json(session_configs: Dict[str, Dict[str, Any]],
                         containers: List[Dict[str, Any]]) -> None:
    """Display session information in JSON format."""
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sessions": {},
        "containers": containers,
        "summary": {
            "total_sessions": len(session_configs),
            "active_sessions": 0,
            "expired_sessions": 0,
            "running_containers": len(containers)
        }
    }

    for session_id, config in session_configs.items():
        is_expired = is_session_expired(config)
        if is_expired:
            output["summary"]["expired_sessions"] += 1
        else:
            output["summary"]["active_sessions"] += 1

        output["sessions"][session_id] = {
            "config": config,
            "status": "expired" if is_expired else "active",
            "time_remaining": calculate_time_remaining(config),
            "is_expired": is_expired
        }

    print(json.dumps(output, indent=2))


def watch_sessions() -> None:
    """Monitor sessions in real-time."""
    print("🔍 Monitoring sessions (Ctrl+C to exit)...")

    try:
        while True:
            # Clear screen (works on most terminals)
            print("\033[2J\033[H")

            session_configs = load_session_configs()
            containers = get_running_containers()

            display_sessions_table(session_configs, containers, show_resources=True)

            time.sleep(10)  # Update every 10 seconds

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")


def main():
    parser = argparse.ArgumentParser(
        description='Monitor active session containers for Legal AI Research Sandbox'
    )
    parser.add_argument(
        '--containers-only',
        action='store_true',
        help='Show only running containers'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output session details in JSON format'
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Monitor sessions in real-time'
    )
    parser.add_argument(
        '--resources',
        action='store_true',
        help='Show resource usage for running containers'
    )

    args = parser.parse_args()

    if args.watch:
        watch_sessions()
        return

    session_configs = load_session_configs()
    containers = get_running_containers()

    if args.containers_only:
        print("\n🐳 Running Containers:")
        if not containers:
            print("No containers running.")
        else:
            for container in containers:
                print(f"  • {container['name']} ({container['id']})")
                print(f"    Status: {container['status']}")
                print(f"    Ports: {container['ports']}")
                print(f"    Created: {container['created']}")
                print()
    elif args.json:
        display_sessions_json(session_configs, containers)
    else:
        display_sessions_table(session_configs, containers, args.resources)


if __name__ == "__main__":
    main()
