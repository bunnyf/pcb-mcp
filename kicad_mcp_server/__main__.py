"""
Main entry point for KiCad MCP Server.

This module provides the main() function that starts the MCP server,
reading JSON-RPC requests from stdin and writing responses to stdout.
"""

from __future__ import annotations

import json
import os
import signal
import sys
from typing import NoReturn

from . import __version__
from .config import get_config
from .protocol import handle_request
from .utils import setup_logging, get_logger
from .pcbnew_api import HAS_PCBNEW


# Flag for graceful shutdown
_shutdown_requested = False


def _signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    logger = get_logger()
    logger.info(f"Received signal {signum}, shutting down...")
    _shutdown_requested = True


def _setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown."""
    # Handle SIGTERM (kill) and SIGINT (Ctrl+C)
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # Handle SIGHUP on Unix systems (terminal closed)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, _signal_handler)


def main() -> NoReturn:
    """
    Main entry point for the MCP server.

    Reads JSON-RPC requests from stdin and writes responses to stdout.
    Logs are written to stderr to keep stdout clean for protocol messages.
    """
    global _shutdown_requested

    # Set up logging
    setup_logging()
    logger = get_logger()

    # Set up signal handlers
    _setup_signal_handlers()

    # Get configuration
    config = get_config()

    # Log startup information
    logger.info(f"KiCad MCP Server v{__version__} starting (KiCad 9.x)")
    logger.info(f"pcbnew API: {'available' if HAS_PCBNEW else 'not available'}")
    logger.info(
        f"FreeRouting: {'available' if os.path.exists(config.freerouting_jar) else 'not available'}"
    )
    logger.info(f"Projects directory: {config.projects_base}")
    logger.info(f"Tasks directory: {config.tasks_dir}")

    # Main request loop
    try:
        for line in sys.stdin:
            if _shutdown_requested:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                response = handle_request(request)

                if response is not None:
                    print(json.dumps(response), flush=True)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {e}"},
                }
                print(json.dumps(error_response), flush=True)

            except Exception as e:
                logger.error(f"Request handling error: {e}")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

    logger.info("Server shutdown complete")
    sys.exit(0)


if __name__ == "__main__":
    main()
