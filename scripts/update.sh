#!/bin/bash
# Update KiCad MCP Server
# Run on VPS to update to latest version

set -e

echo "Updating KiCad MCP Server..."

# Backup current version
if [ -f /root/pcb/mcp/kicad_mcp_server.py ]; then
    cp /root/pcb/mcp/kicad_mcp_server.py /root/pcb/mcp/kicad_mcp_server.py.bak
    echo "Backed up current version"
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Copy new version
if [ -f "$SCRIPT_DIR/../kicad_mcp_server.py" ]; then
    cp "$SCRIPT_DIR/../kicad_mcp_server.py" /root/pcb/mcp/
    chmod +x /root/pcb/mcp/kicad_mcp_server.py
    echo "Updated MCP Server"
else
    echo "Error: kicad_mcp_server.py not found"
    exit 1
fi

# Show version
echo ""
echo "New version installed."
echo ""
echo "✅ Update complete"
echo "Restart Claude Code to use new version"
