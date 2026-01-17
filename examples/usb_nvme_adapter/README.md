# USB NVMe Adapter - Example Project

A complete PCB design example created entirely using **KiCad MCP Server** through Claude Code, demonstrating AI-assisted hardware design workflow.

## Project Overview

**USB-C to M.2 NVMe Adapter** - A compact 4-layer PCB that enables connecting M.2 NVMe SSDs via USB-C interface.

### Key Specifications

- **Form Factor**: M.2 2230 compatible
- **Interface**: USB Type-C (USB 3.2 Gen2) → PCIe Gen3 x2 NVMe
- **PCB Layers**: 4-layer stackup
- **Dimensions**: ~40mm x 25mm (optimized for portability)
- **Power**: USB-C powered with onboard 3.3V regulation

### Main Components

| Component | Part Number | Function |
|-----------|-------------|----------|
| Bridge Controller | ASM2362 | USB 3.2 Gen2 to PCIe Gen3 x2 bridge |
| DC-DC Converter | TPS62913 | 5V to 3.3V step-down (3A) |
| USB ESD Protection | USBLC6-2SC6 + TPD4S012 | USB 2.0/3.0 protection |
| Connector | USB Type-C 16-pin | Power + data interface |
| M.2 Connector | Key-M 2230 | NVMe SSD socket |

## Design Workflow (AI-Assisted)

This project was designed using **KiCad MCP Server** with Claude Code, demonstrating a fully remote, AI-assisted PCB design workflow:

### 1. Schematic Design
```
User: "Create USB-C to NVMe adapter schematic"
AI: [Generated component placement, connections via KiCad]
```

### 2. PCB Layout
```
User: "Optimize PCB layout for compact size"
AI: [Used auto-routing and manual optimization]
```

### 3. Design Verification
```
User: "Run DRC and ERC checks"
AI: [Executed design rule checks, fixed violations]
```

### 4. Manufacturing Output
```
User: "Generate JLCPCB manufacturing files"
AI: [Exported Gerber, BOM, position files]
```

## Generated Outputs

All files in this directory were generated using MCP tools:

### 3D Renders
Generated with `export_3d` tool:
- `3d/pcb_top.png` - Top view (318KB)
- `3d/pcb_bottom.png` - Bottom view (296KB)
- `3d/pcb_iso.png` - Isometric view (423KB)
- `3d/pcb.step` - STEP 3D model (11KB)

### Documentation
Generated with `export_pdf` and `export_sch_pdf` tools:
- `docs/schematic.pdf` - Schematic diagram
- `docs/pcb_all.pdf` - PCB layout documentation

### Manufacturing Files
Generated with `export_svg` tool:
- `images/pcb_top.svg` - Top layer SVG
- `images/pcb_bottom.svg` - Bottom layer SVG
- `images/usb_nvme_adapter.svg` - Schematic SVG

### Bill of Materials
Generated with `export_bom` tool:
- `bom.csv` - Complete component list with part numbers

## MCP Tools Used

This project utilized the following KiCad MCP Server tools:

| Tool | Purpose | Usage Count |
|------|---------|-------------|
| `get_board_info` | Check PCB dimensions and stats | Multiple times |
| `fill_zones` | Fill copper zones | Before each export |
| `run_drc` | Design rule check | Multiple iterations |
| `run_erc` | Electrical rule check | During schematic design |
| `export_3d` | Generate 3D renders | Final documentation |
| `export_pdf` | Create documentation PDFs | Final deliverables |
| `export_svg` | Export layer images | Review and documentation |
| `export_bom` | Generate bill of materials | Manufacturing |
| `export_gerber` | Gerber files for fabrication | Manufacturing |
| `export_jlcpcb` | Complete JLCPCB package | Manufacturing |

## Design Features

### Hardware Highlights

1. **USB Type-C Power Delivery**
   - CC1/CC2 resistors (5.1kΩ) for proper USB-C negotiation
   - PTC fuse protection (2A)
   - Comprehensive ESD protection on all USB lines

2. **Power Management**
   - Efficient 3A buck converter (TPS62913)
   - 2.2µH power inductor
   - Proper input/output capacitor placement
   - Feedback network for stable 3.3V output

3. **Signal Integrity**
   - 4-layer PCB with dedicated ground planes
   - Controlled impedance for USB 3.0 differential pairs
   - PCIe Gen3 trace routing with proper termination
   - Minimized trace lengths for high-speed signals

4. **Thermal Management**
   - Thermal vias under ASM2362 controller
   - Copper pour for heat dissipation
   - Optimized component placement

### PCB Statistics

```
Board Information:
├── Dimensions: ~40mm × 25mm
├── Area: ~1000 mm²
├── Layers: 4 (Signal/GND/PWR/Signal)
├── Components: 20 total
│   ├── SMD: 18
│   └── Through-hole: 2 (connectors)
├── Nets: 45
├── Zones: 6 copper pours
└── Vias: 120+
```

## Manufacturing Notes

### JLCPCB Fabrication Parameters
- **PCB Thickness**: 1.6mm
- **Copper Weight**: 1oz (outer), 0.5oz (inner)
- **Surface Finish**: HASL / ENIG
- **Silkscreen**: White on green solder mask
- **Min Track/Space**: 0.15mm/0.15mm
- **Min Hole Size**: 0.3mm

### Assembly Considerations
- **Component Placement**: All SMD on top layer
- **Stencil Required**: Yes (for paste application)
- **Reflow Profile**: Standard lead-free (SAC305)
- **Special Notes**:
  - QFN packages require thermal via stencil apertures
  - M.2 connector requires precise alignment

## AI-Assisted Design Benefits

This project demonstrates several advantages of AI-assisted PCB design:

1. **No Local EDA Software Required**
   - Entire design created on MacBook without KiCad installed
   - All processing done on remote VPS via MCP

2. **Rapid Iteration**
   - Quick DRC/ERC checks
   - Instant 3D visualization
   - Automated export generation

3. **Knowledge Assistance**
   - Component selection guidance
   - Layout optimization suggestions
   - Design rule clarification

4. **Manufacturing Ready**
   - One-command JLCPCB package generation
   - Complete documentation auto-generated
   - BOM with manufacturer part numbers

## File Structure

```
usb_nvme_adapter/
├── README.md              # This file
├── bom.csv                # Bill of materials
├── 3d/                    # 3D renders and models
│   ├── pcb_top.png       # Top view render
│   ├── pcb_bottom.png    # Bottom view render
│   ├── pcb_iso.png       # Isometric render
│   ├── pcb.step          # STEP 3D model
│   └── pcb.glb           # GLB 3D model
├── docs/                  # Documentation PDFs
│   ├── schematic.pdf     # Schematic diagram
│   └── pcb_all.pdf       # PCB layout
└── images/                # SVG exports
    ├── pcb_top.svg       # Top layer
    ├── pcb_bottom.svg    # Bottom layer
    └── usb_nvme_adapter.svg  # Schematic
```

## Lessons Learned

### Design Process
- AI assistance accelerated component selection and placement
- Automated DRC checking caught issues early
- 3D visualization helped identify mechanical conflicts

### MCP Workflow
- Async auto-routing handled complex routing tasks
- Remote execution eliminated local resource constraints
- Automated export generation ensured consistency

### Future Improvements
- Add USB PD negotiation for higher power
- Support M.2 2242/2280 form factors
- Add activity LED feedback
- Consider thermal pad on controller

## Replication Guide

To use this example as a starting point:

1. **Upload to VPS**
   ```bash
   rsync -avz examples/usb_nvme_adapter/ your-vps:/root/pcb/projects/usb_nvme_adapter/
   ```

2. **Verify with MCP**
   ```
   User: "List projects"
   AI: [Shows usb_nvme_adapter]

   User: "Get board info for usb_nvme_adapter"
   AI: [Returns PCB statistics]
   ```

3. **Generate Fresh Outputs**
   ```
   User: "Export all files for usb_nvme_adapter"
   AI: [Regenerates all manufacturing files]
   ```

## License

This example project is provided as educational reference under GPL-3.0 license.

## Credits

- **Design**: Created with Claude Code + KiCad MCP Server v3.5.0
- **EDA**: KiCad 9.0.6
- **Bridge IC**: ASMedia ASM2362 (datasheet referenced)
- **DC-DC**: Texas Instruments TPS62913 (reference design)

---

**Note**: This is a demonstration project. For production use, perform thorough testing and validation according to USB-IF and PCIe specifications.
