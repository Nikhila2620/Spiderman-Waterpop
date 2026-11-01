"""
Launch-time runtime checks for Spider-Man Waterpop.

Friends often copy this folder (including a .venv built on someone else's PC)
and then double-click a shortcut. That venv's pyvenv.cfg still points at the
original machine's Python, so pythonw.exe exits immediately with no window.
Running `python run.py` from a terminal uses a working interpreter, which is
why the app appears to "only work from the terminal."
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def venv_dir(root: Optional[Path] = None) -> Path:
    return (root or project_root()) / ".venv"


def venv_python(root: Optional[Path] = None) -> Path:
    return venv_dir(root) / "Scripts" / "python.exe"


def venv_pythonw(root: Optional[Path] = None) -> Path:
    return venv_dir(root) / "Scripts" / "pythonw.exe"


def read_pyvenv_home(venv_path: Path) -> Optional[Path]:
    cfg = venv_path / "pyvenv.cfg"
    if not cfg.exists():
        return None
    try:
        for line in cfg.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("home"):
                _, _, value = line.partition("=")
                home = value.strip().strip('"')
                return Path(home) if home else None
    except OSError:
        return None
    return None


def venv_home_exists(venv_path: Path) -> bool:
    """False when the venv was copied from another PC and its base Python is gone."""
    home = read_pyvenv_home(venv_path)
    if home is None:
        return True
    return (home / "python.exe").exists() or (home / "python3.exe").exists()


def interpreter_can_import_pyside(python_exe: Path, timeout: int = 45) -> bool:
    if not python_exe.exists():
        return False
    try:
        result = subprocess.run(
            [str(python_exe), "-c", "from PySide6.QtWidgets import QApplication"],
            capture_output=True,
            timeout=timeout,
            cwd=str(python_exe.parent),
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def venv_is_usable(root: Optional[Path] = None) -> bool:
    root = root or project_root()
    py = venv_python(root)
    if not py.exists():
        return False
    if not venv_home_exists(venv_dir(root)):
        return False
    return interpreter_can_import_pyside(py)


def shortcut_should_target_launcher() -> str:
    """Desktop/Start Menu shortcuts must invoke the .bat launcher, never a raw venv pythonw."""
    return "START_APP.bat"


def resolve_launch_pythonw(root: Optional[Path] = None) -> Optional[Path]:
    root = root or project_root()
    if not venv_is_usable(root):
        return None
    pyw = venv_pythonw(root)
    if pyw.exists():
        return pyw
    py = venv_python(root)
    return py if py.exists() else None
