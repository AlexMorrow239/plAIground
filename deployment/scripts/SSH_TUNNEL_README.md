# SSH Tunnel Setup for Remote Development

This guide helps you access the plAIground frontend (and optionally backend) running on a remote server through SSH tunnels.

## Quick Start

### Basic Usage (Frontend Only)

```bash
# From the project root
python deployment/scripts/ssh_tunnel.py user@your-server.com

# Or using the bash wrapper
./deployment/scripts/tunnel.sh user@your-server.com
```

This creates a tunnel from `localhost:3000` on your laptop to port `3000` on the remote server where the frontend is running.

After running, open your browser to: **<http://localhost:3000>**

### Including Backend API

If you also need to access the backend API:

```bash
python deployment/scripts/ssh_tunnel.py user@your-server.com --include-backend
```

This tunnels:

- Frontend: `localhost:3000` → `remote:3000`
- Backend: `localhost:8000` → `remote:8000`

### Full Stack with Ollama

For complete access including the LLM service:

```bash
python deployment/scripts/ssh_tunnel.py user@your-server.com --include-backend --include-ollama
```

This tunnels:

- Frontend: `localhost:3000` → `remote:3000`
- Backend: `localhost:8000` → `remote:8000`
- Ollama: `localhost:11434` → `remote:11434`

## Common Scenarios

### Using an SSH Key

```bash
python deployment/scripts/ssh_tunnel.py user@server.com -i ~/.ssh/mykey.pem
```

### Custom SSH Port

```bash
python deployment/scripts/ssh_tunnel.py user@server.com --ssh-port 2222
```

### Avoiding Port Conflicts

If you already have services running on the default ports locally:

```bash
python deployment/scripts/ssh_tunnel.py user@server.com \
  --local-frontend 4000 \
  --local-backend 8001 \
  --include-backend
```

Then access at: **<http://localhost:4000>**

### Remote Server with Different Ports

If the remote server runs services on non-standard ports:

```bash
python deployment/scripts/ssh_tunnel.py user@server.com \
  --remote-frontend 3001 \
  --remote-backend 8080 \
  --include-backend
```

## Development Workflow

### Step 1: Start Services on Remote Server

SSH into your server and start the development services:

```bash
# On the remote server
cd /path/to/plAIground

# Terminal 1 - Backend
cd backend && make dev

# Terminal 2 - Frontend
cd frontend && bun dev
```

### Step 2: Create Tunnel from Your Laptop

On your local machine:

```bash
# From your local plAIground directory
python deployment/scripts/ssh_tunnel.py user@your-server.com --include-backend
```

### Step 3: Develop Locally

- Edit code on your laptop using your preferred IDE
- Push changes to the remote server (via git push/pull or rsync)
- View the running application at <http://localhost:3000>
- The tunnel stays active until you press Ctrl+C

## Docker Container Development

If running Docker containers on the remote server:

```bash
# On remote server - start containers
docker-compose up -d

# On your laptop - create tunnels
python deployment/scripts/ssh_tunnel.py user@server.com --include-backend
```

## Troubleshooting

### Connection Refused

If you see "Connection refused" errors:

1. Verify services are running on the remote server:

   ```bash
   # On remote server
   curl http://localhost:3000  # Test frontend
   curl http://localhost:8000  # Test backend
   ```

2. Check firewall rules allow localhost connections

3. Ensure services bind to localhost (0.0.0.0 or 127.0.0.1)

### Port Already in Use

If local ports are already in use:

```bash
# Check what's using the port
lsof -i :3000  # macOS/Linux
netstat -an | grep 3000  # Windows

# Use different local ports
python deployment/scripts/ssh_tunnel.py user@server.com --local-frontend 4000
```

### SSH Key Issues

For SSH key authentication problems:

```bash
# Test SSH connection first
ssh -i ~/.ssh/mykey.pem user@server.com

# Then use the same key for tunnel
python deployment/scripts/ssh_tunnel.py user@server.com -i ~/.ssh/mykey.pem
```

### Keep Connection Alive

The script automatically configures SSH keep-alive settings. If connections still drop:

```bash
# Add custom SSH options
python deployment/scripts/ssh_tunnel.py user@server.com \
  --ssh-args "-o ServerAliveInterval=30 -o TCPKeepAlive=yes"
```

## Advanced Usage

### Multiple Sessions

To tunnel different session containers:

```bash
# Assuming session containers use different ports
python deployment/scripts/ssh_tunnel.py user@server.com \
  --remote-frontend 3001 \
  --local-frontend 3001 \
  --remote-backend 8001 \
  --local-backend 8001 \
  --include-backend
```

### Background Tunnels

To run tunnels in the background (Linux/macOS):

```bash
# Start in background
nohup python deployment/scripts/ssh_tunnel.py user@server.com > tunnel.log 2>&1 &

# Check it's running
ps aux | grep ssh_tunnel

# Stop the tunnel
kill <PID>
```

### Automation with tmux

For persistent sessions:

```bash
# Start new tmux session
tmux new -s tunnel

# Run tunnel script
python deployment/scripts/ssh_tunnel.py user@server.com --include-backend

# Detach with Ctrl+B, then D

# Reattach later
tmux attach -t tunnel
```

## Security Considerations

1. **Only tunnel to trusted servers** - SSH tunnels bypass firewalls
2. **Use SSH keys** instead of passwords when possible
3. **Limit tunnel lifetime** - Don't leave tunnels running indefinitely
4. **Monitor access logs** on the remote server

## Script Options Reference

```
Required Arguments:
  server                    SSH server [user@]hostname or [user@]ip

Service Selection:
  --include-backend         Also tunnel the backend API
  --include-ollama         Also tunnel the Ollama service

Port Configuration:
  --local-frontend PORT     Local port for frontend (default: 3000)
  --local-backend PORT      Local port for backend (default: 8000)
  --local-ollama PORT      Local port for Ollama (default: 11434)
  --remote-frontend PORT    Remote port for frontend (default: 3000)
  --remote-backend PORT     Remote port for backend (default: 8000)
  --remote-ollama PORT     Remote port for Ollama (default: 11434)

SSH Options:
  -i, --identity-file FILE  SSH private key file
  --ssh-port PORT          SSH server port (default: 22)
  --ssh-args ARGS          Additional SSH arguments
```

## Example Configurations

### Development Team Setup

```bash
# Frontend developer (UI only)
./deployment/scripts/tunnel.sh dev@staging.company.com

# Full-stack developer (UI + API)
./deployment/scripts/tunnel.sh dev@staging.company.com --include-backend

# AI researcher (Full stack + LLM)
./deployment/scripts/tunnel.sh dev@staging.company.com --include-backend --include-ollama
```

### Production Debugging

```bash
# Secure production access with specific key and port
python deployment/scripts/ssh_tunnel.py admin@prod.company.com \
  -i ~/.ssh/prod-key.pem \
  --ssh-port 2222 \
  --include-backend \
  --local-frontend 9000 \
  --local-backend 9001
```

## Tips

1. **Save common configurations** as shell aliases:

   ```bash
   alias tunnel-dev="python ~/plAIground/deployment/scripts/ssh_tunnel.py dev@myserver.com --include-backend"
   ```

2. **Use SSH config** for complex setups:

   ```bash
   # ~/.ssh/config
   Host playground-dev
       HostName myserver.com
       User dev
       Port 2222
       IdentityFile ~/.ssh/dev-key.pem

   # Then simply:
   python deployment/scripts/ssh_tunnel.py playground-dev
   ```

3. **Monitor tunnel status** in a separate terminal:

   ```bash
   watch -n 1 'netstat -an | grep -E "3000|8000"'
   ```
