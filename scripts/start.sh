#!/usr/bin/env bash
set -e
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "================================================================="
echo "   NEXORA — Android Automation & Personal Knowledge Platform    "
echo "================================================================="

# Register MCP Server in Antigravity configurations if not already present
"$PYTHON_BIN" -m nexora.mcp.configurator

# Start the local dashboard
exec "$PYTHON_BIN" -m nexora.cli start --port "${1:-8080}"
