#!/bin/bash
# KiCad MCP Server Installation Script
# For Ubuntu 22.04+ / Debian 12+

set -e

echo "=========================================="
echo "KiCad MCP Server Installer"
echo "=========================================="

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./install.sh)"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    echo "Cannot detect OS"
    exit 1
fi

echo "Detected: $OS $VERSION"

# Install dependencies
echo ""
echo "[1/6] Installing system dependencies..."
apt update
apt install -y wget curl software-properties-common xvfb

# Install KiCad 9
echo ""
echo "[2/6] Installing KiCad 9..."
if [ "$OS" = "ubuntu" ]; then
    add-apt-repository -y ppa:kicad/kicad-9.0-releases
    apt update
    apt install -y kicad
elif [ "$OS" = "debian" ]; then
    echo "deb http://deb.debian.org/debian bookworm-backports main" > /etc/apt/sources.list.d/backports.list
    apt update
    apt install -y -t bookworm-backports kicad
else
    echo "Unsupported OS: $OS"
    exit 1
fi

# Verify KiCad
echo ""
echo "KiCad version:"
kicad-cli --version

# Install Java for FreeRouting
echo ""
echo "[3/6] Installing Java 17..."
apt install -y openjdk-17-jre

# Install FreeRouting
echo ""
echo "[4/6] Installing FreeRouting..."
FREEROUTING_VERSION="1.9.0"
FREEROUTING_URL="https://github.com/freerouting/freerouting/releases/download/v${FREEROUTING_VERSION}/freerouting-${FREEROUTING_VERSION}.jar"
wget -q "$FREEROUTING_URL" -O /opt/freerouting.jar
echo "FreeRouting installed: /opt/freerouting.jar"

# Setup directories
echo ""
echo "[5/6] Setting up directories..."
mkdir -p /root/pcb/{mcp,projects,tasks}

# Copy MCP server
echo ""
echo "[6/6] Installing MCP Server..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/../kicad_mcp_server.py" /root/pcb/mcp/
chmod +x /root/pcb/mcp/kicad_mcp_server.py

# Create run script
cat > /root/pcb/mcp/run_mcp.sh << 'EOF'
#!/bin/bash
exec python3 -u /root/pcb/mcp/kicad_mcp_server.py
EOF
chmod +x /root/pcb/mcp/run_mcp.sh

# Verify installation
echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Versions:"
echo "  KiCad:       $(kicad-cli --version 2>/dev/null | head -1)"
echo "  Python:      $(python3 --version)"
echo "  Java:        $(java --version 2>&1 | head -1)"
echo "  FreeRouting: /opt/freerouting.jar"
echo ""
echo "Directories:"
echo "  MCP Server:  /root/pcb/mcp/kicad_mcp_server.py"
echo "  Projects:    /root/pcb/projects/"
echo "  Tasks:       /root/pcb/tasks/"
echo ""
echo "Test MCP Server:"
echo "  python3 /root/pcb/mcp/kicad_mcp_server.py"
echo ""
echo "Claude Code config example:"
echo '  {"mcpServers": {"kicad": {"command": "ssh", "args": ["your-vps", "python3 /root/pcb/mcp/kicad_mcp_server.py"]}}}'
echo ""
