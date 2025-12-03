#!/bin/bash
# Quick start script for Docker deployment

set -e

echo "🚀 buildOS Docker Setup"
echo "========================"

# Check for .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo ""
    echo "Create one with:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env with your ANTHROPIC_API_KEY"
    exit 1
fi

# Check for API key
if ! grep -q "ANTHROPIC_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set in .env"
    echo "   The orchestrator won't work without it."
    echo ""
fi

# Build and start
echo "📦 Building Docker image..."
docker compose build

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "✅ Services started!"
echo ""

# Check if tunnel is configured
if grep -q "CLOUDFLARE_TUNNEL_TOKEN=" .env && grep -v "CLOUDFLARE_TUNNEL_TOKEN=$" .env | grep -q "CLOUDFLARE_TUNNEL_TOKEN"; then
    echo "🌐 Cloudflare Tunnel is configured"
    echo "   Your friend can access via your tunnel URL"
else
    echo "🖥️  Local access only (no tunnel configured)"
    echo "   Access at: http://localhost:4000"
fi

echo ""
echo "📋 Commands:"
echo "   docker compose logs -f    # View logs"
echo "   docker compose down       # Stop"
echo "   docker compose restart    # Restart"
echo ""
