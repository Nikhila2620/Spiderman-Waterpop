"""Create or repair the local venv so double-click launch works on a friend's PC."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.runtime import (  # noqa: E402
    interpreter_can_import_pyside,
    project_root,
    resolve_launch_pythonw,
    venv_dir,
    venv_home_exists,
    venv_is_usable,
    venv_python,
)


def _fail(message: str, code: int = 1) -> int:
    print(f"[ERROR] {message}")
    return code


def _run(cmd, **kwargs) -> subprocess.CompletedProcess:
    print(f"[INFO] {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, cwd=str(ROOT), **kwargs)


def ensure_venv() -> Path:
    root = project_root()
    vdir = venv_dir(root)
    py = venv_python(root)

    if py.exists() and not venv_home_exists(vdir):
        print("[WARN] Existing .venv points at another computer's Python. Recreating it...")
        shutil.rmtree(vdir, ignore_errors=True)

    if not py.exists():
        print("[INFO] Creating virtual environment in .venv ...")
        result = _run([sys.executable, "-m", "venv", str(vdir)])
        if result.returncode != 0 or not py.exists():
            raise RuntimeError("Failed to create .venv. Install Python 3.10+ and tick 'Add Python to PATH'.")

    if interpreter_can_import_pyside(py):
        return py

    req = root / "requirements.txt"
    print("[INFO] Installing dependencies (PySide6)...")
    _run([str(py), "-m", "pip", "install", "--upgrade", "pip"], capture_output=True)
    result = _run([str(py), "-m", "pip", "install", "-r", str(req)])
    if result.returncode != 0 or not interpreter_can_import_pyside(py):
        raise RuntimeError("Could not install PySide6. Check your internet connection and try again.")
    return py


def main() -> int:
    try:
        ensure_venv()
    except Exception as exc:
        return _fail(str(exc))

    root = project_root()
    if not venv_is_usable(root):
        return _fail("Virtual environment is still not usable after setup.")

    launch = resolve_launch_pythonw(root)
    if launch is None:
        return _fail("Could not locate pythonw.exe / python.exe in .venv.")

    marker = root / ".runtime_python"
    marker.write_text(str(launch), encoding="utf-8")
    print(f"[OK] Runtime ready: {launch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
