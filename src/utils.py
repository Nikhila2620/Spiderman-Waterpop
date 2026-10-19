"""
Utility helpers for Spider-Man Water Buddy v2.0.
Provides robust resource path resolution, system boot identification, and time helpers.
"""
import sys
import os
import time
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and for PyInstaller bundled executable.
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        # src/ -> parent is project root
        base_path = Path(__file__).resolve().parent.parent
    return base_path / relative_path


def get_boot_id() -> str:
    """
    Returns an identifier for the current system boot.
    On Windows, uses GetTickCount64 to approximate boot time.
    """
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        uptime_ms = kernel32.GetTickCount64()
        boot_timestamp = int((time.time() * 1000 - uptime_ms) / 1000)
        # Round to nearest 10 seconds to allow for minor measurement variance
        rounded_boot = (boot_timestamp // 10) * 10
        return f"win_boot_{rounded_boot}"
    except Exception:
        # Fallback based on monotonic anchor
        anchor = int((time.time() - time.monotonic()) / 10) * 10
        return f"mono_boot_{anchor}"
