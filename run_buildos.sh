#!/bin/bash

# buildOS Orchestrator with Dashboard Integration
# This script runs the IFC analysis with full observability

echo "🏗️  buildOS - IFC CO2 Analysis with Observability"
echo "=================================================="
echo ""
echo "📊 Dashboard: http://localhost:5173"
echo "🔌 Server: http://localhost:4000"
echo ""

# Check if dashboard is running
if ! curl -s http://localhost:4000 > /dev/null 2>&1; then
    echo "⚠️  Dashboard server not running!"
    echo ""
    echo "Starting dashboard..."
    echo ""
    cd claude-code-hooks-multi-agent-observability
    export PATH="$HOME/.bun/bin:$PATH"
    ./scripts/start-system.sh &
    DASHBOARD_PID=$!
    cd ..

    echo "Waiting for server to start..."
    sleep 3

    if ! curl -s http://localhost:4000 > /dev/null 2>&1; then
        echo "❌ Failed to start dashboard. Starting anyway..."
    else
        echo "✅ Dashboard started!"
    fi
    echo ""
fi

# Check if IFC file was provided
if [ -z "$1" ]; then
    echo "Usage: ./run_buildos.sh <ifc_file>"
    echo ""
    echo "Example: ./run_buildos.sh Small_condo.ifc"
    exit 1
fi

echo "Starting analysis with observability..."
echo ""

# Run with dashboard integration
python run_with_dashboard.py "$1"

echo ""
echo "✅ Complete!"
echo "📊 Review the timeline at http://localhost:5173"
