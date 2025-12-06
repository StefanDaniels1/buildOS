# Share buildOS with Cloudflare Tunnel

Quick guide to share your local buildOS dashboard with a friend via Cloudflare Tunnel.

## Prerequisites

1. **Docker** installed on your machine
2. **Cloudflare account** (free)
3. Your **Anthropic API key** in `.env` file

## Step 1: Create Cloudflare Tunnel (One-time Setup)

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Click **Networks** → **Tunnels** → **Create a tunnel**
3. Choose **Cloudflared** connector
4. Name it: `buildos-demo`
5. Copy the **tunnel token** (starts with `eyJ...`)
6. Configure public hostname:
   - Subdomain: `buildos` (or anything you want)
   - Domain: your Cloudflare domain
   - Service: `http://app:4000`

## Step 2: Configure Environment

Create/update your `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Cloudflare Tunnel Token (from step 1)
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoixxxx...
```

## Step 3: Build & Run

```bash
# Build the Docker image
docker compose build

# Start the services
docker compose up -d

# Check logs
docker compose logs -f
```

## Step 4: Share the URL

Your friend can now access:
```
https://buildos.yourdomain.com
```

They can:
1. Upload an IFC file via the sidebar
2. Ask questions about the model
3. See the AI orchestrator work in real-time

## Quick Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f app

# Rebuild after changes
docker compose build --no-cache && docker compose up -d
```

## Without Cloudflare Tunnel

If you just want to test locally with Docker:

```bash
# Comment out the tunnel service in docker-compose.yml
# Then run:
docker compose up -d

# Access at http://localhost:4000
```

## Troubleshooting

### Tunnel not connecting
- Check token is correct in `.env`
- Verify tunnel is active in Cloudflare dashboard

### File upload not working
- Check `uploads/` directory has write permissions
- View logs: `docker compose logs app`

### API errors
- Ensure `ANTHROPIC_API_KEY` is set
- Check Python dependencies in logs

## Files Created

- `Dockerfile` - Multi-stage build for the app
- `docker-compose.yml` - Docker services config
- `.env` - Your secrets (not committed to git)

## Security Notes

- The tunnel is secure (HTTPS enforced by Cloudflare)
- API key stays on your machine
- Files uploaded are stored locally in `uploads/`
- Consider adding Cloudflare Access for authentication if sharing publicly
