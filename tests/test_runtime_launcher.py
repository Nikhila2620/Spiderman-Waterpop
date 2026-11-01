"""Regression tests for double-click launch (no terminal required)."""
from pathlib import Path

from src.runtime import (
    read_pyvenv_home,
    shortcut_should_target_launcher,
    venv_home_exists,
    venv_is_usable,
)


def test_shortcut_targets_bat_launcher_not_pythonw():
    assert shortcut_should_target_launcher() == "START_APP.bat"


def test_create_shortcuts_script_points_at_start_app():
    script = Path(__file__).resolve().parent.parent / "scripts" / "create_shortcuts.ps1"
    text = script.read_text(encoding="utf-8")
    assert "START_APP.bat" in text
    assert "pythonw.exe" not in text


def test_start_app_does_not_kill_all_pythonw():
    bat = Path(__file__).resolve().parent.parent / "START_APP.bat"
    text = bat.read_text(encoding="utf-8")
    assert "taskkill /f /im pythonw.exe" not in text.lower()
    assert "ensure_runtime.py" in text


def test_register_windows_app_does_not_bind_app_paths_to_pythonw():
    script = Path(__file__).resolve().parent.parent / "scripts" / "register_windows_app.py"
    text = script.read_text(encoding="utf-8")
    assert "START_APP.bat" in text
    assert 'Scripts" / "pythonw.exe"' not in text
    assert ".venv" not in text or "pythonw" not in text


def test_copied_venv_home_is_detected_as_unusable(tmp_path):
    vdir = tmp_path / ".venv"
    vdir.mkdir()
    (vdir / "pyvenv.cfg").write_text(
        "home = Z:\\does-not-exist\\Python311\ninclude-system-site-packages = false\n",
        encoding="utf-8",
    )
    (vdir / "Scripts").mkdir()
    (vdir / "Scripts" / "python.exe").write_bytes(b"not-a-real-python")

    assert read_pyvenv_home(vdir) == Path(r"Z:\does-not-exist\Python311")
    assert venv_home_exists(vdir) is False
    assert venv_is_usable(tmp_path) is False


def test_missing_venv_is_not_usable(tmp_path):
    assert venv_is_usable(tmp_path) is False


def test_installer_gui_adds_project_root_to_syspath():
    source = (Path(__file__).resolve().parent.parent / "src" / "installer_gui.py").read_text(encoding="utf-8")
    assert "sys.path.insert" in source
    assert source.index("sys.path.insert") < source.index("from src.theme")
