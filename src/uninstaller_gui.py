"""
Standalone Graphical Uninstaller for Spider-Man Water Buddy.
Removes shortcuts, startup registration, Add/Remove Programs entry, and program files.
Asks the user explicitly whether to retain or delete personal settings.
"""
import sys
import os
import shutil
import winreg
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QProgressBar,
)

from src.installer_gui import get_windows_special_folder

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\SpiderManWaterBuddy"


class UninstallerDialog(QDialog):
    def __init__(self, install_dir: Path, parent=None):
        super().__init__(parent)
        self.install_dir = install_dir
        self.setWindowTitle("Spider-Man Water Buddy — Uninstaller")
        self.setFixedSize(480, 260)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0c10;
                color: #f5f6f9;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QLabel { color: #f5f6f9; }
            QCheckBox { color: #c5bfab; font-size: 13px; spacing: 8px; font-weight: 600; }
            QCheckBox::indicator {
                width: 17px;
                height: 17px;
                border: 1.5px solid #4a3e1b;
                border-radius: 4px;
                background-color: #12141a;
            }
            QCheckBox::indicator:hover { border-color: #d4af37; }
            QCheckBox::indicator:checked { background-color: #d4af37; border: 1.5px solid #f5d77f; }
            QPushButton {
                font-weight: 700;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Uninstall Spider-Man Water Buddy")
        title.setStyleSheet("font-size: 17px; font-weight: 900; color: #d4af37; letter-spacing: 0.5px;")
        layout.addWidget(title)

        desc = QLabel("Are you sure you want to remove Spider-Man Water Buddy from your computer?")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #c5bfab; font-size: 13px;")
        layout.addWidget(desc)

        self.chk_delete_settings = QCheckBox("Also delete my personal settings and hydration history")
        self.chk_delete_settings.setChecked(False)
        layout.addWidget(self.chk_delete_settings)

        layout.addStretch()

        btn_box = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #181b24;
                color: #dcd8cc;
                border: 1px solid #4a3e1b;
                border-radius: 8px;
                padding: 9px 18px;
            }
            QPushButton:hover {
                border-color: #d4af37;
                background-color: #222633;
                color: #ffffff;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        btn_box.addStretch()

        self.btn_uninstall = QPushButton("Uninstall Now")
        self.btn_uninstall.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #d4af37, stop: 1 #b89326);
                color: #0b0c10;
                font-weight: 900;
                font-size: 13px;
                border: 1px solid #f5d77f;
                border-radius: 8px;
                padding: 9px 20px;
            }
            QPushButton:hover {
                background: #e8c459;
                border-color: #ffe394;
            }
        """)
        self.btn_uninstall.clicked.connect(self._do_uninstall)
        btn_box.addWidget(self.btn_uninstall)

        layout.addLayout(btn_box)

    def _do_uninstall(self):
        try:
            # 1. Remove Startup registry if present
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, "SpiderManWaterBuddy")
            except Exception:
                pass

            # 2. Remove Uninstall registry entry
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
            except Exception:
                pass

            # 3. Remove Desktop shortcut
            desktop = get_windows_special_folder("desktop")
            ds_link = desktop / "Spider-Man Water Buddy.lnk"
            if ds_link.exists():
                ds_link.unlink()

            # 4. Remove Start Menu shortcut
            start_menu = get_windows_special_folder("programs") / "Spider-Man Water Buddy.lnk"
            if start_menu.exists():
                start_menu.unlink()

            # 5. Delete personal settings if requested
            if self.chk_delete_settings.isChecked():
                settings_dir = appdata / "SpiderManWaterBuddy"
                if settings_dir.exists():
                    shutil.rmtree(settings_dir, ignore_errors=True)

            QMessageBox.information(
                self,
                "Uninstall Complete",
                "Spider-Man Water Buddy has been successfully removed from your computer.",
            )

            # 6. Schedule self-deletion of installation directory with safety validation
            resolved_install = self.install_dir.resolve()
            win_dir = Path(os.environ.get("WINDIR", "C:\\Windows")).resolve()
            is_safe = (
                resolved_install.exists()
                and resolved_install.is_dir()
                and resolved_install.parent != resolved_install
                and not resolved_install.is_relative_to(win_dir)
                and "spidermanwaterbuddy" in resolved_install.name.lower()
            )

            if is_safe:
                install_path = str(resolved_install).replace('"', '')
                cmd = f'cmd /c "for /l %i in (1,1,5) do ( ping 127.0.0.1 -n 2 > nul & rmdir /s /q \"{install_path}\" & if not exist \"{install_path}\" exit )"'
                import subprocess
                subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                print(f"[SECURITY] Skipped rmdir on invalid or unsafe install_dir: {resolved_install}")

            self.accept()
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Uninstall encountered an issue: {e}")
            self.reject()


def main():
    app = QApplication(sys.argv)
    if getattr(sys, "frozen", False):
        install_dir = Path(sys.executable).resolve().parent
    else:
        install_dir = Path(__file__).resolve().parent.parent

    dialog = UninstallerDialog(install_dir)
    dialog.exec()


if __name__ == "__main__":
    main()
