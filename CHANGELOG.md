# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.5.0] - 2026-01-17

### Added
- **Modular Architecture**: Refactored from 987-line monolithic script to clean package structure
  - Separated into 18 Python modules (`tools/`, `utils/`, `config.py`, `protocol.py`)
  - Added proper Python packaging with `pyproject.toml`
- **Security Features**:
  - Path validation to prevent directory traversal attacks
  - Restricted file access (`read_file` limited to projects/tasks directories)
  - Shell injection prevention using `shlex.quote()`
  - Input validation for project names
- **Configuration System**:
  - Environment variable configuration (`.env.example`)
  - All settings configurable via `KICAD_MCP_*` variables
- **Task Management**:
  - New `cleanup_tasks` tool for managing old async tasks
  - Automatic cleanup of completed/failed tasks older than configurable age
- **Testing**:
  - 55 comprehensive unit tests with pytest
  - Test coverage for config, paths, tasks, protocol, and file operations
- **Type Safety**:
  - Full type annotations throughout codebase
  - `py.typed` marker file for PEP 561 compliance
- **Logging**:
  - Proper logging framework with structured logs
  - Replaced stderr prints with logging module
- **Documentation**:
  - Complete USB NVMe adapter example project
  - Enhanced README with badges, security features, and configuration sections
  - Added examples directory with detailed documentation

### Changed
- **License**: Changed from MIT to GPL-3.0-or-later
- **Entry Point**: Main entry via `python -m kicad_mcp_server` (legacy `kicad_mcp_server.py` still works)
- **Comments**: All comments and docstrings standardized to English
- **Error Handling**: Consistent error handling patterns across all modules
- **Code Quality**: Extracted magic numbers to named constants

### Fixed
- Graceful shutdown with signal handlers (SIGTERM/SIGINT/SIGHUP)
- Repository URLs updated to correct GitHub location
- Version synchronization across all files

### Security
- Path validation prevents directory traversal
- File read access restricted to safe directories
- Shell script generation uses proper quoting
- Input sanitization for all user-provided data

## [3.4.0] - 2024-12-31

### Added
- Initial KiCad 9.x support
- 22 MCP tools for PCB design workflow
- Async auto-routing with FreeRouting
- 3D rendering with multiple view angles
- JLCPCB complete manufacturing package export
- DRC/ERC checking
- Zone filling
- Multiple export formats (Gerber, BOM, PDF, SVG, STEP)

### Features
- pcbnew Python API integration
- Async task system for long-running operations
- Task status tracking with log tailing
- Comprehensive export capabilities

## Links

- [3.5.0]: https://github.com/bunnyf/pcb-mcp/compare/v3.4.0...v3.5.0
- [3.4.0]: https://github.com/bunnyf/pcb-mcp/releases/tag/v3.4.0
