<!-- mcp-name: io.github.bunnyf/kicad-mcp-server -->

# KiCad MCP Server

A Model Context Protocol (MCP) server for KiCad 9.x, enabling AI-assisted PCB design through Claude Code or other MCP clients.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![KiCad 9.x](https://img.shields.io/badge/KiCad-9.x-orange.svg)](https://www.kicad.org/)

[中文文档](./README_CN.md)

## ✨ What's New in v3.5.0

- **🏗️ Modular Architecture** - Refactored from 987-line monolithic script to clean package structure
- **🔒 Security Hardening** - Path validation, injection prevention, restricted file access
- **⚙️ Environment Configuration** - All settings configurable via environment variables
- **🧹 Task Cleanup** - New `cleanup_tasks` tool for managing old async tasks
- **✅ Unit Tests** - 55 comprehensive tests covering core functionality
- **📝 Type Annotations** - Full type hints throughout codebase
- **📊 Proper Logging** - Structured logging framework replacing stderr prints

## Features

- **DRC/ERC Check** - Design Rule Check and Electrical Rule Check
- **Zone Fill** - Automatic copper zone filling
- **Auto-routing** - FreeRouting integration with async support (bypass 10-min timeout)
- **3D Rendering** - Native KiCad 9 3D render (top/bottom/iso views)
- **Export** - Gerber, Drill, BOM, Netlist, PDF, SVG, STEP
- **JLCPCB Package** - Complete manufacturing files for JLCPCB/PCBWay

## Architecture

```
Local Machine                    VPS (KiCad 9.x)
┌─────────────────┐              ┌─────────────────────┐
│  Claude Code    │     MCP      │  MCP Server v3.5.0  │
│  or MCP Clients │◄────SSH─────►│  kicad-cli + pcbnew │
└─────────────────┘              │  + FreeRouting      │
                                 └─────────────────────┘
```

## Requirements

### VPS
- Ubuntu 22.04+ or Debian 12+
- KiCad 9.0.6+
- Python 3.10+
- Java 17+ (for FreeRouting)
- xvfb (for headless rendering)

### Local
- Claude Code with MCP support
- SSH access to VPS

## Quick Install

### On VPS

```bash
# Clone repository
git clone https://github.com/bunnyf/pcb-mcp.git
cd pcb-mcp

# Run install script
chmod +x scripts/install.sh
./scripts/install.sh
```

Or manual install:

```bash
# Install KiCad 9
sudo add-apt-repository ppa:kicad/kicad-9.0-releases -y
sudo apt update
sudo apt install kicad xvfb -y

# Install FreeRouting
sudo apt install openjdk-17-jre -y
sudo wget -q https://github.com/freerouting/freerouting/releases/download/v1.9.0/freerouting-1.9.0.jar -O /opt/freerouting.jar

# Setup MCP Server
mkdir -p /root/pcb/{mcp,projects,tasks}
cp kicad_mcp_server.py /root/pcb/mcp/
chmod +x /root/pcb/mcp/kicad_mcp_server.py
```

### Claude Code Configuration

Add to your Claude Code MCP settings (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "kicad": {
      "command": "ssh",
      "args": [
        "your-vps-host",
        "python3 /root/pcb/mcp/kicad_mcp_server.py"
      ]
    }
  }
}
```

## Available Tools (23)

### Check
| Tool | Description |
|------|-------------|
| `run_drc` | PCB Design Rule Check |
| `run_erc` | Schematic Electrical Rule Check |

### Operations
| Tool | Description |
|------|-------------|
| `fill_zones` | Fill all copper zones |
| `auto_route` | Auto-routing with FreeRouting (async) |

### Async Tasks
| Tool | Description |
|------|-------------|
| `get_task_status` | Query async task status |
| `list_tasks` | List all async tasks |
| `cleanup_tasks` | Clean up old completed/failed tasks |

### Info
| Tool | Description |
|------|-------------|
| `list_projects` | List all projects |
| `get_board_info` | Board dimensions, layers, components |
| `get_output_files` | List output files |
| `get_version` | Version info |

### PCB Export
| Tool | Description |
|------|-------------|
| `export_gerber` | Gerber + Drill files |
| `export_3d` | 3D render (top/bottom/iso/all) |
| `export_svg` | PCB SVG images |
| `export_pdf` | PCB PDF |
| `export_step` | STEP 3D model |

### Schematic Export
| Tool | Description |
|------|-------------|
| `export_bom` | Bill of Materials (CSV) |
| `export_netlist` | Netlist (KiCad XML/SPICE) |
| `export_sch_pdf` | Schematic PDF |
| `export_sch_svg` | Schematic SVG |

### Manufacturing
| Tool | Description |
|------|-------------|
| `export_jlcpcb` | Complete JLCPCB package |
| `export_all` | Export all files |

### File
| Tool | Description |
|------|-------------|
| `read_file` | Read file content |

## Complete Example Project

### 🎯 USB NVMe Adapter

A **production-ready PCB design** created entirely using KiCad MCP Server + Claude Code:

- **Design**: USB-C to M.2 NVMe adapter (4-layer PCB)
- **Workflow**: 100% AI-assisted design, no local EDA software
- **Components**: ASM2362 bridge, TPS62913 DC-DC, USB-C connector
- **Outputs**: Manufacturing files, 3D renders, complete documentation

See the complete example: [examples/usb_nvme_adapter](./examples/usb_nvme_adapter/)

![3D Render](./examples/usb_nvme_adapter/3d/pcb_iso.png)

## Usage Examples

### Basic Workflow

```
User: List projects
AI: [calls list_projects]

User: Run DRC on my_board
AI: [calls run_drc with project="my_board"]

User: Generate 3D renders
AI: [calls export_3d with project="my_board", view="all"]

User: Export for JLCPCB
AI: [calls export_jlcpcb with project="my_board"]
```

### Auto-routing (Async)

```
User: Auto-route my_board
AI: [calls auto_route] 
    → Returns task_id: "route_my_board_20241231_101530"

User: Check routing status
AI: [calls get_task_status with task_id]
    → {"status": "started", "log_tail": "..."}

# After completion:
AI: [calls get_task_status]
    → {"status": "completed", "message": "Auto-routing complete!"}
```

## Output Directory Structure

```
project/output/
├── gerber/      # Gerber + Drill files
├── bom/         # BOM CSV
├── netlist/     # Netlist files
├── 3d/          # 3D renders (PNG) + STEP model
├── images/      # SVG images
├── docs/        # PDF documents
├── reports/     # DRC/ERC reports (JSON)
├── jlcpcb/      # Complete JLCPCB package
└── backup/      # Pre-autoroute backups
```

## Project Sync

Use rsync to sync projects between local and VPS:

```bash
# Upload to VPS
rsync -avz ~/pcb/my_board/ vps:/root/pcb/projects/my_board/

# Download from VPS
rsync -avz vps:/root/pcb/projects/my_board/output/ ~/pcb/my_board/output/
```

## Configuration

All server settings can be configured via environment variables. See [`.env.example`](./.env.example) for details.

### Key Environment Variables

```bash
# Base directories
KICAD_MCP_PROJECTS_BASE=/root/pcb/projects
KICAD_MCP_TASKS_DIR=/root/pcb/tasks

# External tools
KICAD_MCP_KICAD_CLI=kicad-cli
KICAD_MCP_FREEROUTING_JAR=/opt/freerouting.jar

# Timeouts (seconds)
KICAD_MCP_DEFAULT_TIMEOUT=300
KICAD_MCP_AUTOROUTE_TIMEOUT=600

# File limits
KICAD_MCP_MAX_FILE_SIZE=10485760  # 10MB

# Render settings
KICAD_MCP_RENDER_WIDTH=1920
KICAD_MCP_RENDER_HEIGHT=1080

# Task cleanup
KICAD_MCP_TASK_MAX_AGE_DAYS=7
```

## Security Features

v3.5.0 includes comprehensive security hardening:

- **Path Validation** - Prevents directory traversal attacks
- **Restricted File Access** - `read_file` tool limited to projects/tasks directories
- **Shell Injection Prevention** - Uses `shlex.quote()` for all dynamic script generation
- **Input Validation** - Project names sanitized to prevent path manipulation
- **Safe Command Execution** - Proper subprocess handling with timeout protection

## Development

### Running Tests

```bash
# Install dev dependencies
pip3 install -r requirements.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=kicad_mcp_server --cov-report=html
```

### Code Quality

```bash
# Type checking
mypy kicad_mcp_server/

# Linting
ruff check kicad_mcp_server/
```

## License

GNU General Public License v3.0 or later - see [LICENSE](./LICENSE)

## Contributing

Issues and PRs welcome!

## Acknowledgments

- [KiCad](https://www.kicad.org/) - Open source EDA
- [FreeRouting](https://github.com/freerouting/freerouting) - Open source PCB auto-router
- [Anthropic](https://www.anthropic.com/) - Claude AI and MCP protocol
