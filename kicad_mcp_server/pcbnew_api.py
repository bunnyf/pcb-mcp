"""
KiCad pcbnew API wrapper.

Provides safe access to the pcbnew Python API with fallback handling.
"""

from __future__ import annotations

from typing import Any, Optional

# Try to import pcbnew
try:
    import pcbnew as _pcbnew
    HAS_PCBNEW = True
except ImportError:
    _pcbnew = None
    HAS_PCBNEW = False


def get_pcbnew() -> Any:
    """
    Get the pcbnew module.

    Returns:
        The pcbnew module

    Raises:
        RuntimeError: If pcbnew is not available
    """
    if not HAS_PCBNEW:
        raise RuntimeError("pcbnew module is not available")
    return _pcbnew


def is_available() -> bool:
    """
    Check if pcbnew API is available.

    Returns:
        True if pcbnew can be imported
    """
    return HAS_PCBNEW
