#!/usr/bin/env python3
"""
Session Provisioning Tool for Legal AI Research Sandbox

This script generates researcher credentials and creates session containers
for the Legal AI Research Sandbox with complete isolation.

Usage:
    # Generate single containerized session
    python provision_session.py

    # Generate multiple sessions
    python provision_session.py --count 3

    # Specify custom base port
    python provision_session.py --base-port 8100

Features:
- Creates isolated Docker containers per researcher
- Automatic port allocation and network isolation
- Session cleanup and lifecycle management
- Generates secure credentials for each researcher
"""

import argparse
import json
import secrets
import string
import sys
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple
import bcrypt

# Find project root and directories
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # deployment/scripts -> deployment -> project root
backend_dir = project_root / "backend"
deployment_dir = project_root / "deployment"
sessions_dir = project_root / "sessions"

# Add backend to path for imports if needed
sys.path.insert(0, str(backend_dir))

# Container configuration
DOCKER_COMPOSE_FILE = project_root / "docker-compose.yml"
BASE_SUBNET = "172.20"


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
    session_id = 'Session_' + secrets.token_hex(8)

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




def find_available_ports(base_port: int, count: int = 2) -> List[int]:
    """Find available ports starting from base_port."""
    available_ports = []
    port = base_port

    while len(available_ports) < count:
        # Check if port is available
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()

        if result != 0:  # Port is available
            available_ports.append(port)

        port += 1

        # Safety check to prevent infinite loop
        if port > base_port + 1000:
            raise RuntimeError(f"Could not find {count} available ports starting from {base_port}")

    return available_ports


def find_available_subnet() -> str:
    """Find an available Docker subnet that doesn't conflict with existing networks."""
    import random

    # Get existing Docker networks
    try:
        result = subprocess.run(
            ['docker', 'network', 'ls', '--format', '{{.Name}}'],
            capture_output=True,
            text=True
        )
        existing_networks = result.stdout.strip().split('\n') if result.stdout else []

        # Get subnets of existing networks
        existing_subnets = set()
        for network in existing_networks:
            if network:
                inspect_result = subprocess.run(
                    ['docker', 'network', 'inspect', network, '--format', '{{range .IPAM.Config}}{{.Subnet}}{{end}}'],
                    capture_output=True,
                    text=True
                )
                subnet = inspect_result.stdout.strip()
                if subnet:
                    existing_subnets.add(subnet)
    except:
        existing_subnets = set()

    # Try to find an available subnet in the 172.20-172.31 range
    for _ in range(100):
        # Generate random subnet in 172.20.x.0/24 to 172.31.x.0/24 range
        second_octet = random.randint(20, 31)
        third_octet = random.randint(0, 255)
        subnet = f"172.{second_octet}.{third_octet}.0/24"

        if subnet not in existing_subnets:
            return subnet

    # Fallback to a high random range if nothing found
    return f"172.{random.randint(100, 200)}.{random.randint(0, 255)}.0/24"


def generate_container_config(session: Dict[str, Any], backend_port: int, frontend_port: int) -> Dict[str, Any]:
    """Generate container-specific configuration."""
    session_id = session['session_id']  # Use full session ID
    subnet = find_available_subnet()  # Find an available subnet

    container_config = {
        'session_id': session_id,
        'session_full_id': session['session_id'],
        'backend_port': backend_port,
        'frontend_port': frontend_port,
        'subnet': subnet,
        'container_name': f"legal_sandbox_{session_id}",
        'created_at': session['created_at'],
        'expires_at': session['expires_at'],
        'ttl_hours': session['ttl_hours']
    }

    return container_config


def create_container_env_file(container_config: Dict[str, Any], session_config_path: Path) -> Path:
    """Create environment file for container deployment."""
    session_id = container_config['session_id']
    session_dir = deployment_dir / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    env_file_path = session_dir / ".env"

    # Generate secret key for this session
    secret_key = secrets.token_urlsafe(32)

    env_content = f"""# Container Environment for Session {container_config['session_id']}
# Generated at: {datetime.now(timezone.utc).isoformat()}

# Session Identification
SESSION_ID={container_config['session_id']}
SESSION_TTL_HOURS={container_config['ttl_hours']}

# Port allocation
BACKEND_PORT={container_config['backend_port']}
FRONTEND_PORT={container_config['frontend_port']}

# Network configuration
SESSION_SUBNET={container_config['subnet']}

# Security
SECRET_KEY={secret_key}

# Session configuration file path
SESSION_CONFIG_PATH={session_config_path.resolve()}

# LLM Configuration (disabled by default)
ENABLE_LLM=false
OLLAMA_MODEL=llama3:8b
"""

    with open(env_file_path, 'w') as f:
        f.write(env_content)

    return env_file_path


def create_session_container(container_config: Dict[str, Any], session_config_path: Path) -> bool:
    """Create and start a Docker container for the session."""
    try:
        # Create environment file
        env_file = create_container_env_file(container_config, session_config_path)

        print(f"  🐳 Starting container for session {container_config['session_id']}")
        print(f"     Backend:  http://localhost:{container_config['backend_port']}")
        print(f"     Frontend: http://localhost:{container_config['frontend_port']}")

        # Start the container using docker-compose
        # --build flag ensures frontend is built with correct NEXT_PUBLIC_API_URL
        result = subprocess.run([
            'docker-compose',
            '-f', str(DOCKER_COMPOSE_FILE),
            '--env-file', str(env_file),
            'up', '--build', '-d'
        ],
        cwd=str(project_root),
        capture_output=True,
        text=True
        )

        if result.returncode == 0:
            print(f"  ✓ Container started successfully")

            # Wait a moment for services to start
            time.sleep(3)

            # Check health
            health_check = subprocess.run([
                'docker', 'exec', f"{container_config['session_id']}_backend",
                'curl', '-f', 'http://localhost:8000/health'
            ], capture_output=True)

            if health_check.returncode == 0:
                print(f"  ✓ Backend health check passed")
            else:
                print(f"  ⚠ Backend health check failed, but container is running")

            return True
        else:
            print(f"  ❌ Failed to start container: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Error creating container: {e}")
        return False


def save_container_session_config(session: Dict[str, Any], container_config: Dict[str, Any]) -> Path:
    """Save session configuration file for container use."""
    session_id = container_config['session_id']
    session_dir = deployment_dir / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    session_config_file = session_dir / "session.json"

    session_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "container_config": container_config,
        "sessions": [session]
    }

    with open(session_config_file, 'w') as f:
        json.dump(session_data, f, indent=2)

    return session_config_file


def print_container_info(container_configs: List[Dict[str, Any]], credentials_list: List[Dict[str, str]]) -> None:
    """Print container access information."""
    print("\n" + "="*70)
    print("CONTAINER SESSION ACCESS")
    print("="*70)

    for i, (config, creds) in enumerate(zip(container_configs, credentials_list), 1):
        print(f"\n--- Session {i}: {config['session_id']} ---")
        print(f"Frontend URL: http://localhost:{config['frontend_port']}")
        print(f"Backend URL:  http://localhost:{config['backend_port']}")
        print(f"Username:     {creds['username']}")
        print(f"Password:     {creds['password']}")
        print(f"Expires:      {creds['expires_at']}")
        print(f"Container:    {config['container_name']}")

    print("\n" + "="*70)
    print("CONTAINER MANAGEMENT")
    print("="*70)
    print("Stop containers:")
    for config in container_configs:
        print(f"  docker-compose --env-file deployment/sessions/{config['session_id']}/.env down")

    print("\nRestart containers (if needed):")
    for config in container_configs:
        print(f"  docker-compose --env-file deployment/sessions/{config['session_id']}/.env up --build -d")

    print("\nCleanup all:")
    print("  python deployment/scripts/cleanup_session_containers.py --all")


def main():
    parser = argparse.ArgumentParser(
        description='Generate containerized researcher sessions for Legal AI Research Sandbox'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of researcher sessions to generate (default: 1)'
    )
    parser.add_argument(
        '--base-port',
        type=int,
        default=8100,
        help='Base port for container deployment (default: 8100)'
    )

    args = parser.parse_args()

    print(f"\nCreating {args.count} isolated container session(s)")
    print(f"Base port: {args.base_port}")

    # Check Docker/Podman availability
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True) or subprocess.run(['podman', '--version'], capture_output=True)
        if result.returncode != 0:
            print("Docker or Podman not available. Please install Docker or Podman.")
            return
    except FileNotFoundError:
        print("Docker or Podman not found. Please install Docker or Podman.")
        return

    # Create deployment directory if it doesn't exist
    deployment_dir.mkdir(exist_ok=True)

    # Generate sessions and containers
    sessions = []
    credentials_list = []
    container_configs = []

    # Find available ports
    try:
        port_pairs = []
        current_base = args.base_port
        for i in range(args.count):
            ports = find_available_ports(current_base, 2)
            port_pairs.append((ports[0], ports[1]))  # backend, frontend
            current_base = ports[1] + 1
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    for i in range(args.count):
        session, credentials = generate_session()
        sessions.append(session)
        credentials_list.append(credentials)

        backend_port, frontend_port = port_pairs[i]
        container_config = generate_container_config(session, backend_port, frontend_port)
        container_configs.append(container_config)

        print(f"  ✓ Generated session {i+1}/{args.count}: {container_config['session_id']}")

        # Save session-specific config
        session_config_path = save_container_session_config(session, container_config)

        # Create and start container
        success = create_session_container(container_config, session_config_path)
        if not success:
            print(f"  ❌ Failed to create container for session {container_config['session_id']}")
            continue

    # Print container access information
    print_container_info(container_configs, credentials_list)

    print("\n" + "="*70)
    print("CONTAINER SESSIONS ACTIVE")
    print("="*70)
    print("Each researcher now has an isolated container with:")
    print("- Complete session isolation")
    print("- Ephemeral tmpfs storage")
    print("- Automatic cleanup after TTL")
    print("- Individual authentication")


if __name__ == "__main__":
    main()
