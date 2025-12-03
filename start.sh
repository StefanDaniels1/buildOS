#!/bin/bash
#
# buildOS Dashboard Startup Script
# Starts the Bun server and Vue frontend
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "========================================"
echo "  buildOS Multi-Agent Dashboard"
echo "========================================"
echo -e "${NC}"

# Check dependencies
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${YELLOW}Warning: $1 not found. Please install it.${NC}"
        return 1
    fi
    return 0
}

echo "Checking dependencies..."

if ! check_command bun; then
    echo "Please install Bun: curl -fsSL https://bun.sh/install | bash"
    exit 1
fi

if ! check_command python3; then
    echo "Please install Python 3"
    exit 1
fi

# Create directories
mkdir -p uploads workspace/.context

# Load environment
if [ -f ".env" ]; then
    echo -e "${GREEN}Loading .env file...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}Warning: ANTHROPIC_API_KEY not set${NC}"
    echo "Set it in .env or export it before running"
fi

# Activate Python venv if exists
if [ -d ".venv" ]; then
    echo -e "${GREEN}Activating Python virtualenv...${NC}"
    source .venv/bin/activate
fi

# Install server dependencies
if [ ! -d "apps/server/node_modules" ]; then
    echo -e "${GREEN}Installing server dependencies...${NC}"
    cd apps/server && bun install && cd "$SCRIPT_DIR"
fi

# Install client dependencies
if [ ! -d "apps/client/node_modules" ]; then
    echo -e "${GREEN}Installing client dependencies...${NC}"
    cd apps/client && bun install && cd "$SCRIPT_DIR"
fi

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
    fi
    if [ ! -z "$CLIENT_PID" ]; then
        kill $CLIENT_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup INT TERM

# Start server
echo -e "${GREEN}Starting server on port 4000...${NC}"
cd apps/server && bun run src/index.ts &
SERVER_PID=$!
cd "$SCRIPT_DIR"

# Wait for server to be ready
sleep 2

# Start client
echo -e "${GREEN}Starting client on port 5173...${NC}"
cd apps/client && bun run dev &
CLIENT_PID=$!
cd "$SCRIPT_DIR"

# Wait for client to be ready
sleep 3

echo ""
echo -e "${GREEN}========================================"
echo "  Dashboard is running!"
echo "========================================${NC}"
echo ""
echo -e "  Frontend:  ${BLUE}http://localhost:5173${NC}"
echo -e "  API:       ${BLUE}http://localhost:4000${NC}"
echo -e "  WebSocket: ${BLUE}ws://localhost:4000/stream${NC}"
echo ""
echo "  Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
