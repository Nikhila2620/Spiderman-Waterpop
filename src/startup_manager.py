"""
Windows Startup Manager for Spider-Man Water Buddy.
Interacts with HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run safely without requiring admin privileges.
"""
import sys
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("SpiderManWaterBuddy.Startup")

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "SpiderManWaterBuddy"


class StartupManager:
    """Manages launch-at-startup configuration via Windows User Registry."""

    @staticmethod
    def get_executable_command() -> str:
        """Determines the appropriate command to launch the app on startup."""
        if getattr(sys, "frozen", False):
            # Running as compiled PyInstaller executable
            return f'"{sys.executable}" --minimized'
        else:
            # Running from source in Python
            python_exe = sys.executable
            # If python.exe is a console app, pythonw.exe can be used to run silently without terminal
            pythonw_exe = Path(python_exe).with_name("pythonw.exe")
            target_python = str(pythonw_exe) if pythonw_exe.exists() else python_exe
            script_path = Path(__file__).resolve().parent.parent / "run.py"
            return f'"{target_python}" "{script_path}" --minimized'

    @classmethod
    def is_startup_enabled(cls) -> bool:
        """Queries the Windows registry to verify whether startup launch is registered."""
        if sys.platform != "win32":
            return False

        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, APP_NAME)
                return bool(val)
        except (FileNotFoundError, OSError):
            return False

    @classmethod
    def set_startup_enabled(cls, enable: bool) -> bool:
        """Enables or disables automatic startup registration in HKCU Run key."""
        if sys.platform != "win32":
            logger.warning("Startup registration is only supported on Windows.")
            return False

        import winreg
        cmd = cls.get_executable_command()

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                    logger.info(f"Registered startup command: {cmd}")
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                        logger.info("Unregistered startup command.")
                    except FileNotFoundError:
                        pass
            
            # Verify the state
            current = cls.is_startup_enabled()
            return current == enable
        except Exception as e:
            logger.error(f"Failed to update startup registry: {e}")
            return False
