#!/usr/bin/env python3
"""
SSH Tunnel Manager for plAIground Development

This script creates SSH tunnels to access the frontend and backend services
running on a remote server during development.

Usage:
    python ssh_tunnel.py [user@]server [options]

Examples:
    # Basic tunnel for frontend only
    python ssh_tunnel.py user@myserver.com

    # Tunnel both frontend and backend
    python ssh_tunnel.py user@myserver.com --include-backend

    # Custom ports
    python ssh_tunnel.py user@myserver.com --local-frontend 4000 --remote-frontend 3000

    # With specific SSH key
    python ssh_tunnel.py user@myserver.com -i ~/.ssh/mykey.pem
"""

import argparse
import subprocess
import sys
import time
import signal
from typing import List, Optional


class SSHTunnelManager:
    """Manages SSH tunnels for development access."""

    def __init__(self):
        self.ssh_process: Optional[subprocess.Popen] = None
        self.tunnels: List[tuple] = []

    def add_tunnel(self, local_port: int, remote_port: int, label: str):
        """Add a tunnel configuration."""
        self.tunnels.append((local_port, remote_port, label))

    def build_ssh_command(self, server: str, ssh_key: Optional[str] = None,
                          ssh_port: int = 22, extra_args: Optional[List[str]] = None) -> List[str]:
        """Build the SSH command with tunnel configurations."""
        cmd = ["ssh"]

        # Add SSH key if provided
        if ssh_key:
            cmd.extend(["-i", ssh_key])

        # Add SSH port if not default
        if ssh_port != 22:
            cmd.extend(["-p", str(ssh_port)])

        # Add tunnel configurations
        for local_port, remote_port, _ in self.tunnels:
            cmd.extend(["-L", f"{local_port}:localhost:{remote_port}"])

        # Add common SSH options
        cmd.extend([
            "-N",  # Don't execute remote command
            "-T",  # Disable pseudo-tty allocation
            "-o", "ServerAliveInterval=60",  # Keep connection alive
            "-o", "ServerAliveCountMax=3",
            "-o", "ExitOnForwardFailure=yes",
        ])

        # Add any extra arguments
        if extra_args:
            cmd.extend(extra_args)

        # Add the server
        cmd.append(server)

        return cmd

    def start(self, server: str, ssh_key: Optional[str] = None,
              ssh_port: int = 22, extra_args: Optional[List[str]] = None):
        """Start the SSH tunnel."""
        if not self.tunnels:
            print("❌ No tunnels configured")
            return False

        cmd = self.build_ssh_command(server, ssh_key, ssh_port, extra_args)

        print(f"🚀 Starting SSH tunnels to {server}...")
        print("\nConfigured tunnels:")
        for local_port, remote_port, label in self.tunnels:
            print(f"  📡 {label}: localhost:{local_port} → {server}:{remote_port}")

        print(f"\n📋 SSH Command: {' '.join(cmd)}\n")

        try:
            # Start SSH process
            self.ssh_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Give it a moment to establish
            time.sleep(2)

            # Check if process is still running
            if self.ssh_process.poll() is not None:
                stderr = self.ssh_process.stderr.read() if self.ssh_process.stderr else ""
                print(f"❌ SSH tunnel failed to start: {stderr}")
                return False

            print("✅ SSH tunnels established successfully!\n")
            print("🌐 Access your services at:")
            for local_port, _, label in self.tunnels:
                print(f"   {label}: http://localhost:{local_port}")

            print("\n📝 Press Ctrl+C to close tunnels\n")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start SSH tunnel: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    def stop(self):
        """Stop the SSH tunnel."""
        if self.ssh_process:
            print("\n🛑 Closing SSH tunnels...")
            self.ssh_process.terminate()
            try:
                self.ssh_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ssh_process.kill()
                self.ssh_process.wait()
            print("✅ SSH tunnels closed")
            self.ssh_process = None

    def wait(self):
        """Wait for the SSH process to complete."""
        if self.ssh_process:
            try:
                self.ssh_process.wait()
            except KeyboardInterrupt:
                self.stop()


def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    print("\n📍 Received interrupt signal")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Create SSH tunnels for plAIground development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic frontend tunnel
  %(prog)s user@myserver.com

  # Tunnel both frontend and backend
  %(prog)s user@myserver.com --include-backend

  # Custom local ports
  %(prog)s user@myserver.com --local-frontend 4000 --local-backend 8001

  # With SSH key and custom SSH port
  %(prog)s user@myserver.com -i ~/.ssh/mykey.pem --ssh-port 2222

  # Include Ollama service
  %(prog)s user@myserver.com --include-backend --include-ollama
        """
    )

    # Required arguments
    parser.add_argument(
        "server",
        help="SSH server in format [user@]hostname or [user@]ip"
    )

    # Service selection
    parser.add_argument(
        "--include-backend",
        action="store_true",
        help="Also tunnel the backend API (default: frontend only)"
    )

    parser.add_argument(
        "--include-ollama",
        action="store_true",
        help="Also tunnel the Ollama service"
    )

    # Port configurations
    parser.add_argument(
        "--local-frontend",
        type=int,
        default=3000,
        help="Local port for frontend (default: 3000)"
    )

    parser.add_argument(
        "--local-backend",
        type=int,
        default=8000,
        help="Local port for backend API (default: 8000)"
    )

    parser.add_argument(
        "--local-ollama",
        type=int,
        default=11434,
        help="Local port for Ollama (default: 11434)"
    )

    parser.add_argument(
        "--remote-frontend",
        type=int,
        default=3000,
        help="Remote port for frontend (default: 3000)"
    )

    parser.add_argument(
        "--remote-backend",
        type=int,
        default=8000,
        help="Remote port for backend API (default: 8000)"
    )

    parser.add_argument(
        "--remote-ollama",
        type=int,
        default=11434,
        help="Remote port for Ollama (default: 11434)"
    )

    # SSH options
    parser.add_argument(
        "-i", "--identity-file",
        help="SSH private key file"
    )

    parser.add_argument(
        "--ssh-port",
        type=int,
        default=22,
        help="SSH server port (default: 22)"
    )

    parser.add_argument(
        "--ssh-args",
        help="Additional SSH arguments (e.g., '--ssh-args \"-o StrictHostKeyChecking=no\"')"
    )

    args = parser.parse_args()

    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create tunnel manager
    manager = SSHTunnelManager()

    # Always include frontend
    manager.add_tunnel(
        args.local_frontend,
        args.remote_frontend,
        "Frontend (Next.js)"
    )

    # Optionally include backend
    if args.include_backend:
        manager.add_tunnel(
            args.local_backend,
            args.remote_backend,
            "Backend API (FastAPI)"
        )

    # Optionally include Ollama
    if args.include_ollama:
        manager.add_tunnel(
            args.local_ollama,
            args.remote_ollama,
            "Ollama LLM Service"
        )

    # Parse additional SSH arguments
    extra_ssh_args = []
    if args.ssh_args:
        import shlex
        extra_ssh_args = shlex.split(args.ssh_args)

    # Start the tunnel
    success = manager.start(
        args.server,
        ssh_key=args.identity_file,
        ssh_port=args.ssh_port,
        extra_args=extra_ssh_args
    )

    if success:
        try:
            # Keep the tunnel running
            manager.wait()
        except KeyboardInterrupt:
            pass
        finally:
            manager.stop()
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()