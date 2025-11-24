#!/bin/bash
# BIM AI CO2 Analysis System - Setup Script

echo "🚀 Setting up BIM AI CO2 Analysis System"
echo "========================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ uv found"

# Create virtual environment and install dependencies
echo ""
echo "📦 Installing dependencies with uv..."
uv sync

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Set your API key:"
echo "     export ANTHROPIC_API_KEY='your-api-key-here'"
echo ""
echo "  2. Run the orchestrator:"
echo "     uv run python orchestrator.py model.ifc"
echo ""
echo "  3. Or use the example:"
echo "     uv run python example_usage.py"
echo ""
