# Deploying buildOS Dashboard on Dokploy (Hetzner)

This guide walks you through deploying the buildOS Dashboard on Dokploy running on a Hetzner VPS.

## Prerequisites

1. **Hetzner VPS** - Recommended: CX21 (2 vCPU, 4GB RAM) or higher
2. **Dokploy** installed on your VPS
3. **Domain** pointing to your VPS (e.g., `agents.bimai.nl`)
4. **Anthropic API Key** from https://console.anthropic.com/

## Quick Start

### Step 1: Set Up Hetzner VPS

1. Create a new VPS on [Hetzner Cloud](https://console.hetzner.cloud/)
   - Recommended: CX21 (€4.51/month) or CX31 for heavier usage
   - Location: Choose nearest to your users
   - OS: Ubuntu 22.04

2. Point your domain to the VPS IP:
   ```
   A record: agents.bimai.nl → YOUR_VPS_IP
   ```

### Step 2: Install Dokploy

SSH into your VPS and run:

```bash
curl -sSL https://dokploy.com/install.sh | sh
```

Access Dokploy at `http://YOUR_VPS_IP:3000` and complete the setup.

### Step 3: Connect GitHub Repository

1. In Dokploy, go to **Settings** → **Git Providers**
2. Connect your GitHub account
3. Grant access to your repository

### Step 4: Create Application

1. Click **Create Project** → Name it "buildOS"
2. Click **Add Application**
3. Select **Docker Compose**
4. Choose your repository
5. Set the compose file path: `docker-compose.production.yml`

### Step 5: Configure Environment Variables

In the application settings, add these environment variables:

| Variable | Value | Required |
|----------|-------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | ✅ Yes |
| `DOMAIN` | agents.bimai.nl | ✅ Yes |
| `DASHBOARD_URL` | https://agents.bimai.nl | ✅ Yes |
| `SERVER_PORT` | 4000 | Optional |

### Step 6: Configure Domain

1. Go to **Domains** tab in your application
2. Add domain: `agents.bimai.nl`
3. Enable HTTPS (Let's Encrypt)
4. Port: 4000

### Step 7: Deploy

Click **Deploy** and wait for the build to complete.

---

## Alternative: Docker Compose Direct Deployment

If you prefer to deploy directly without Dokploy:

### 1. Clone the Repository

```bash
ssh root@YOUR_VPS_IP
git clone https://github.com/YOUR_USERNAME/agent_system5.git
cd agent_system5
```

### 2. Create Environment File

```bash
cp .env.example .env
nano .env
# Add your ANTHROPIC_API_KEY
```

### 3. Deploy with Docker Compose

```bash
docker compose -f docker-compose.production.yml up -d
```

### 4. Set Up Reverse Proxy (Caddy)

Install Caddy for automatic HTTPS:

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install caddy
```

Create Caddyfile:

```bash
cat > /etc/caddy/Caddyfile << 'EOF'
agents.bimai.nl {
    reverse_proxy localhost:4000
    
    # WebSocket support
    @websocket {
        header Connection *Upgrade*
        header Upgrade websocket
    }
    reverse_proxy @websocket localhost:4000
}
EOF

systemctl reload caddy
```

---

## Updating the Application

### With Dokploy
1. Push changes to your repository
2. Dokploy auto-deploys or click **Redeploy**

### Manual Update
```bash
cd agent_system5
git pull
docker compose -f docker-compose.production.yml up -d --build
```

---

## Monitoring & Logs

### View Logs
```bash
# With Docker Compose
docker compose -f docker-compose.production.yml logs -f

# Specific service
docker compose -f docker-compose.production.yml logs -f app
```

### Check Status
```bash
docker compose -f docker-compose.production.yml ps
```

### Health Check
```bash
curl https://agents.bimai.nl/events/recent?limit=1
```

---

## Backup & Restore

### Backup Volumes
```bash
# Create backup directory
mkdir -p ~/backups

# Backup uploads, logs, and workspace
docker run --rm \
  -v agent_system5_uploads_data:/data/uploads \
  -v agent_system5_logs_data:/data/logs \
  -v agent_system5_workspace_data:/data/workspace \
  -v ~/backups:/backup \
  alpine tar czf /backup/buildos-backup-$(date +%Y%m%d).tar.gz /data
```

### Restore Volumes
```bash
docker run --rm \
  -v agent_system5_uploads_data:/data/uploads \
  -v agent_system5_logs_data:/data/logs \
  -v agent_system5_workspace_data:/data/workspace \
  -v ~/backups:/backup \
  alpine tar xzf /backup/buildos-backup-YYYYMMDD.tar.gz -C /
```

---

## Troubleshooting

### Application Not Starting
```bash
# Check container logs
docker compose -f docker-compose.production.yml logs app

# Check if port is in use
lsof -i :4000
```

### WebSocket Not Connecting
- Ensure your reverse proxy supports WebSocket upgrades
- Check CORS headers in the application

### SSL Certificate Issues
```bash
# With Caddy, check certificate status
caddy validate --config /etc/caddy/Caddyfile

# Restart Caddy
systemctl restart caddy
```

### Out of Memory
Upgrade your Hetzner plan or add swap:
```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

---

## Security Recommendations

1. **Firewall**: Only allow ports 22 (SSH), 80, 443
   ```bash
   ufw allow 22
   ufw allow 80
   ufw allow 443
   ufw enable
   ```

2. **SSH Key Only**: Disable password authentication
   ```bash
   # In /etc/ssh/sshd_config
   PasswordAuthentication no
   ```

3. **Keep Updated**:
   ```bash
   apt update && apt upgrade -y
   ```

4. **API Key Security**: Use environment variables, never commit to git

---

## Resource Recommendations

| Usage Level | Hetzner Plan | RAM | vCPU |
|-------------|--------------|-----|------|
| Light (1-5 users) | CX11 | 2GB | 1 |
| Medium (5-20 users) | CX21 | 4GB | 2 |
| Heavy (20+ users) | CX31 | 8GB | 2 |

---

## Support

- **Dokploy Docs**: https://docs.dokploy.com/
- **Hetzner Docs**: https://docs.hetzner.com/
- **Issues**: Create an issue in the repository
