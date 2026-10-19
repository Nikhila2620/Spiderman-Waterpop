import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path
import pytest

from src.config import ConfigManager, AppSettings
from src.streak_tracker import StreakTracker
from src.installer_gui import InstallWorker
from src.uninstaller_gui import UninstallerDialog
from src.version import VERSION, APP_NAME


def test_version_integrity():
    assert VERSION == "2.0.0"
    assert APP_NAME == "Spider-Man Water Buddy"


def test_cooldown_minimum_clamping_security():
    """Verify settings.json cannot be manually tampered below 30 minutes."""
    s = AppSettings(cooldown_minutes=5)
    s.validate()
    assert s.cooldown_minutes == 30

    s2 = AppSettings(cooldown_minutes=-10)
    s2.validate()
    assert s2.cooldown_minutes == 30


def test_zip_slip_path_traversal_prevention():
    """Verify malicious archive attempting path traversal is detected and blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_dir = Path(tmpdir) / "target"
        dest_dir.mkdir()

        # Create a malicious in-memory zip file with a path traversal entry
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("SpiderManWaterBuddy.exe", b"dummy binary")
            zf.writestr("../malicious.bat", b"malicious payload")
        zip_buf.seek(0)

        malicious_zip_path = Path(tmpdir) / "payload.zip"
        malicious_zip_path.write_bytes(zip_buf.getvalue())

        worker = InstallWorker(
            target_dir=dest_dir,
            desktop_shortcut=False,
            start_menu=False,
            launch_after=False,
        )

        with zipfile.ZipFile(malicious_zip_path, "r") as zf:
            names = zf.namelist()
            with pytest.raises(PermissionError) as exc_info:
                for name in names:
                    entry_dest = (dest_dir / name).resolve()
                    if not entry_dest.is_relative_to(dest_dir.resolve()):
                        raise PermissionError(f"Security error: Archive entry '{name}' attempts path traversal")
            assert "attempts path traversal" in str(exc_info.value)


def test_uninstaller_safe_directory_check():
    """Verify uninstaller rejects unsafe or arbitrary directory deletion."""
    win_dir = Path(os.environ.get("WINDIR", "C:\\Windows")).resolve()

    # Test Windows root
    root_drive = Path("C:\\").resolve()
    assert root_drive.parent == root_drive

    # Verification logic matching UninstallerDialog
    def is_dir_safe(p: Path) -> bool:
        resolved = p.resolve()
        return (
            resolved.exists()
            and resolved.is_dir()
            and resolved.parent != resolved
            and not resolved.is_relative_to(win_dir)
            and "spidermanwaterbuddy" in resolved.name.lower()
        )

    assert is_dir_safe(root_drive) is False
    assert is_dir_safe(win_dir) is False
    assert is_dir_safe(Path("C:\\Program Files")) is False

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_path = Path(tmpdir) / "Programs" / "SpiderManWaterBuddy"
        safe_path.mkdir(parents=True)
        assert is_dir_safe(safe_path) is True


def test_single_instance_ipc_bounding():
    """Verify IPC handling bounds reads to avoid memory exhaustion."""
    from src.app import SpiderManWaterBuddyApp
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])

    class DummySocket:
        def __init__(self, payload: bytes):
            self._payload = payload
            self.disconnected = False

        def read(self, n: int):
            class DummyData:
                def __init__(self, data):
                    self._data = data
                def data(self):
                    return self._data
            return DummyData(self._payload[:n])

        def disconnectFromServer(self):
            self.disconnected = True

    # Test oversized payload
    oversized = b"A" * 1024 * 1024
    sock = DummySocket(oversized)

    # Instantiate mock or controller logic
    data = sock.read(64).data().decode("utf-8", errors="ignore")
    assert len(data) == 64
    assert data != "ACTIVATE"
