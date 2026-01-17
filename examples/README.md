# Examples

This directory contains example configurations and complete project demonstrations for KiCad MCP Server.

## Configuration Examples

### Claude Code MCP Configuration

[`claude_code_config.json`](./claude_code_config.json) - Sample MCP server configuration for Claude Code.

Add this to your `~/.claude/claude_desktop_config.json`:

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

Replace `your-vps-host` with your actual VPS hostname or IP address.

## Complete Project Examples

### USB NVMe Adapter

[`usb_nvme_adapter/`](./usb_nvme_adapter/) - **Complete PCB design created entirely with AI assistance**

A production-ready USB-C to M.2 NVMe adapter demonstrating:
- ✅ Full PCB design workflow using MCP tools
- ✅ Professional 4-layer board design
- ✅ Manufacturing-ready outputs (Gerber, BOM, 3D models)
- ✅ Comprehensive documentation

**Highlights:**
- Bridge IC: ASMedia ASM2362 (USB 3.2 Gen2 to PCIe Gen3 x2)
- Power: USB-C powered with TPS62913 buck converter
- Form factor: M.2 2230 compatible
- All design, verification, and export done via Claude Code + MCP

See the [project README](./usb_nvme_adapter/README.md) for detailed documentation.

## What These Examples Demonstrate

### MCP-Powered Workflow
1. **No Local EDA Software** - Entire design process on MacBook without KiCad installed
2. **AI-Assisted Design** - Component selection, layout, and optimization with AI guidance
3. **Automated Verification** - DRC/ERC checks, 3D visualization, manufacturing outputs
4. **Remote Execution** - All processing on VPS, results synced back

### Tools Showcased
- `get_board_info` - PCB statistics and dimensions
- `fill_zones` - Copper pour management
- `run_drc` / `run_erc` - Design validation
- `export_3d` - Photorealistic 3D renders
- `export_gerber` - Manufacturing files
- `export_jlcpcb` - Complete fabrication package
- `export_bom` - Component list generation

### Key Benefits
- **Speed**: Rapid iteration with instant feedback
- **Quality**: Professional results with automated checks
- **Accessibility**: Hardware design without expensive software licenses
- **Documentation**: Auto-generated outputs for manufacturing

## Adding Your Own Examples

To contribute an example project:

1. Create a new directory under `examples/`
2. Include your KiCad project files (or outputs only)
3. Add a comprehensive README.md explaining:
   - What the project does
   - Which MCP tools were used
   - Key design decisions
   - Manufacturing notes
4. Include representative outputs:
   - 3D renders (PNG)
   - Documentation (PDF)
   - Manufacturing files (Gerber/BOM)

## License

Examples are provided under GPL-3.0 license for educational and reference purposes.
