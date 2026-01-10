#!/usr/bin/env python3
"""
KiCad MCP Server v3.5.0
AI-assisted PCB design through Model Context Protocol.

This is a compatibility wrapper that imports from the modular package.
For new deployments, use: python -m kicad_mcp_server

Features:
- DRC/ERC checks
- Zone filling
- Board information queries
- Gerber/drill/BOM/position file export
- 3D rendering
- Schematic PDF/SVG export
- Netlist export
- JLCPCB complete package
- FreeRouting auto-routing (async support)
- Secure path validation
- Configurable via environment variables

Environment Variables:
- KICAD_MCP_PROJECTS_BASE: Projects directory (default: /root/pcb/projects)
- KICAD_MCP_TASKS_DIR: Tasks directory (default: /root/pcb/tasks)
- KICAD_MCP_KICAD_CLI: KiCad CLI path (default: kicad-cli)
- KICAD_MCP_FREEROUTING_JAR: FreeRouting JAR path (default: /opt/freerouting.jar)
- KICAD_MCP_DEFAULT_TIMEOUT: Command timeout in seconds (default: 300)
- KICAD_MCP_MAX_FILE_SIZE: Max file size for read_file (default: 10MB)
"""

from kicad_mcp_server.__main__ import main

if __name__ == "__main__":
    main()
