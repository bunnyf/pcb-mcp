# KiCad MCP Server

A Model Context Protocol (MCP) server for KiCad 9.x, enabling AI-assisted PCB design through Claude Code or other MCP clients.

[中文文档](./README_CN.md)

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
│  Claude Code    │     MCP      │  MCP Server v3.4    │
│  or MCP Client  │◄────SSH─────►│  kicad-cli + pcbnew │
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
git clone https://github.com/yourusername/pcb-mcp.git
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

## Available Tools (22)

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

## License

MIT License - see [LICENSE](./LICENSE)

## Contributing

Issues and PRs welcome!

## Acknowledgments

- [KiCad](https://www.kicad.org/) - Open source EDA
- [FreeRouting](https://github.com/freerouting/freerouting) - Open source PCB auto-router
- [Anthropic](https://www.anthropic.com/) - Claude AI and MCP protocol
