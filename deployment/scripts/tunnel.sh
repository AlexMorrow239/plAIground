#!/bin/bash
# SSH Tunnel Helper Script for plAIground Development
# Quick wrapper for the Python SSH tunnel script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the Python script with all arguments passed through
python3 "$SCRIPT_DIR/ssh_tunnel.py" "$@"