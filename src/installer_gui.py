"""
Standalone Windows Installer for Spider-Man Water Buddy.
Installs to %LOCALAPPDATA%\\Programs\\SpiderManWaterBuddy without requiring administrator privileges.
Creates Start Menu and Desktop shortcuts and registers Windows Add/Remove Programs uninstaller.
"""
import sys
import os
import shutil
import zipfile
import subprocess
import winreg
from pathlib import Path
import time

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QProgressBar,
    QFileDialog,
    QMessageBox,
)

from src.theme import get_dialog_qss, TOKENS

APP_NAME = "Spider-Man Water Buddy"
VERSION = "1.0.0"
PUBLISHER = "Antigravity"
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\SpiderManWaterBuddy"


def create_windows_shortcut(target_exe: Path, shortcut_path: Path, icon_path: Path):
    """Creates a Windows .lnk shortcut natively via PowerShell WScript.Shell."""
    ps_cmd = f"""
    $WshShell = New-Object -ComObject WScript.Shell;
    $Shortcut = $WshShell.CreateShortcut('{shortcut_path}');
    $Shortcut.TargetPath = '{target_exe}';
    $Shortcut.IconLocation = '{icon_path}, 0';
    $Shortcut.WorkingDirectory = '{target_exe.parent}';
    $Shortcut.Save();
    """
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True, creationflags=subprocess.CREATE_NO_WINDOW)


class InstallWorker(QThread):
    progressUpdated = Signal(int, str)
    finishedSuccess = Signal(Path)
    failed = Signal(str)

    def __init__(self, target_dir: Path, desktop_shortcut: bool, start_menu: bool, launch_after: bool):
        super().__init__()
        self.target_dir = target_dir
        self.desktop_shortcut = desktop_shortcut
        self.start_menu = start_menu
        self.launch_after = launch_after

    def run(self):
        try:
            self.progressUpdated.emit(5, "Closing running instances of Spider-Man Water Buddy...")
            # Terminate running instances so executables can be cleanly overwritten
            if sys.platform == "win32":
                for proc_name in ["SpiderManWaterBuddy.exe", "uninstall.exe"]:
                    subprocess.run(
                        ["taskkill", "/f", "/im", proc_name],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                time.sleep(0.5)

            self.progressUpdated.emit(10, "Preparing installation directory...")
            
            # If target directory already exists, ensure clean slate or rotate away if files are locked
            if self.target_dir.exists():
                has_locked_files = False
                for item in list(self.target_dir.iterdir()):
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        try:
                            try:
                                os.chmod(item, 0o777)
                            except Exception:
                                pass
                            item.unlink()
                        except Exception:
                            has_locked_files = True

                # If any locked file remains in target_dir, rename the directory out of the way
                if has_locked_files or any(self.target_dir.iterdir()):
                    try:
                        backup_dir = self.target_dir.parent / f"{self.target_dir.name}_old_{int(time.time())}"
                        self.target_dir.rename(backup_dir)
                        shutil.rmtree(backup_dir, ignore_errors=True)
                    except Exception as ex:
                        print(f"[WARN] Target directory rotation warning: {ex}")

            self.target_dir.mkdir(parents=True, exist_ok=True)

            # Locate payload zip or compiled source files
            source_dir = Path(__file__).resolve().parent.parent / "dist" / "SpiderManWaterBuddy"
            payload_zip = Path(__file__).resolve().parent.parent / "dist" / "SpiderManWaterBuddy-v1.0.0-Portable.zip"

            if getattr(sys, "frozen", False):
                # When bundled as onefile installer, extraction payload is in sys._MEIPASS
                meipass = getattr(sys, "_MEIPASS", None)
                if meipass:
                    meipass_path = Path(meipass)
                    candidates = [
                        meipass_path / "SpiderManWaterBuddy-v1.0.0-Portable.zip",
                        meipass_path / "payload.zip",
                    ] + [p for p in meipass_path.glob("*.zip") if "base_library" not in p.name.lower()]
                    for c in candidates:
                        if c.exists():
                            payload_zip = c
                            break

            if payload_zip.exists():
                self.progressUpdated.emit(25, "Extracting application package...")
                resolved_target = self.target_dir.resolve()
                with zipfile.ZipFile(payload_zip, "r") as zf:
                    names = zf.namelist()
                    if "SpiderManWaterBuddy.exe" not in names:
                        raise RuntimeError(f"Package {payload_zip.name} does not contain SpiderManWaterBuddy.exe")
                    
                    # Security: Validate all entries against Zip-Slip path traversal before extracting
                    for name in names:
                        entry_dest = (self.target_dir / name).resolve()
                        if not str(entry_dest).startswith(str(resolved_target)):
                            raise SecurityError(f"Security error: Archive entry '{name}' attempts path traversal outside target directory.")

                    total_files = len(names)
                    for idx, name in enumerate(names):
                        dest_file = self.target_dir / name
                        extracted = False
                        for attempt in range(4):
                            try:
                                if dest_file.exists():
                                    try:
                                        os.chmod(dest_file, 0o777)
                                    except Exception:
                                        pass
                                zf.extract(name, self.target_dir)
                                extracted = True
                                break
                            except PermissionError:
                                if sys.platform == "win32":
                                    subprocess.run(
                                        ["taskkill", "/f", "/im", "SpiderManWaterBuddy.exe"],
                                        capture_output=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW,
                                    )
                                    subprocess.run(
                                        ["taskkill", "/f", "/im", "uninstall.exe"],
                                        capture_output=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW,
                                    )
                                time.sleep(0.5)

                                # Try renaming locked file away
                                if dest_file.exists():
                                    try:
                                        renamed_old = dest_file.parent / f"{dest_file.name}.old.{int(time.time())}"
                                        dest_file.rename(renamed_old)
                                        try:
                                            renamed_old.unlink()
                                        except Exception:
                                            pass
                                    except Exception:
                                        pass

                        if not extracted:
                            # If it is uninstall.exe and existing binary is present, keep existing rather than aborting
                            if name == "uninstall.exe" and dest_file.exists():
                                print("[INFO] Kept existing uninstaller.")
                            else:
                                zf.extract(name, self.target_dir)

                        pct = 25 + int((idx / total_files) * 50)
                        self.progressUpdated.emit(pct, f"Installing {Path(name).name}...")
            elif source_dir.exists():
                self.progressUpdated.emit(30, "Copying application binaries...")
                shutil.copytree(source_dir, self.target_dir, dirs_exist_ok=True)
            else:
                raise FileNotFoundError("Could not find installation payload.")

            target_exe = self.target_dir / "SpiderManWaterBuddy.exe"
            if not target_exe.exists():
                raise FileNotFoundError(f"Installation failed: {target_exe} was not found after extraction.")
            icon_path = self.target_dir / "assets" / "images" / "app_icon.ico"
            if not icon_path.exists():
                icon_path = self.target_dir / "_internal" / "assets" / "images" / "app_icon.ico"
            if not icon_path.exists():
                icon_path = target_exe

            self.progressUpdated.emit(80, "Creating Windows shortcuts...")
            # Desktop shortcut
            if self.desktop_shortcut:
                desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
                ds_path = desktop / f"{APP_NAME}.lnk"
                create_windows_shortcut(target_exe, ds_path, icon_path)

            # Start Menu shortcut
            if self.start_menu:
                appdata = Path(os.environ.get("APPDATA", ""))
                sm_path = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / f"{APP_NAME}.lnk"
                create_windows_shortcut(target_exe, sm_path, icon_path)

            self.progressUpdated.emit(90, "Registering Windows uninstaller...")
            uninstaller_exe = self.target_dir / "uninstall.exe"
            # If uninstaller isn't separate, register PowerShell uninstall command
            uninstall_cmd = f'"{uninstaller_exe}"' if uninstaller_exe.exists() else f'cmd /c start "" "{self.target_dir}\\uninstall.bat"'

            # Write Windows Add/Remove Programs registry entry in HKCU
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
                    winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
                    winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
                    winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
                    winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(icon_path))
                    winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(self.target_dir))
                    winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
                    winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            except Exception as re:
                print(f"[WARN] Failed to write ARP registry: {re}")

            self.progressUpdated.emit(100, "Installation completed!")
            self.finishedSuccess.emit(target_exe)
        except Exception as e:
            self.failed.emit(str(e))


class InstallerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Setup Wizard")
        self.setFixedSize(520, 380)
        self.setStyleSheet(get_dialog_qss())

        local_app = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        self.default_install_dir = local_app / "Programs" / "SpiderManWaterBuddy"
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel(f"🕷️ Install {APP_NAME}")
        title.setStyleSheet(f"font-size: 19px; font-weight: 900; color: {TOKENS.ACCENT_RED};")
        layout.addWidget(title)

        desc = QLabel("Install your friendly neighbourhood desktop companion.")
        desc.setStyleSheet(f"color: {TOKENS.TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(desc)

        # Destination Folder
        layout.addWidget(QLabel("Installation Directory:"))
        path_box = QHBoxLayout()
        self.edit_path = QLineEdit(str(self.default_install_dir))
        path_box.addWidget(self.edit_path)

        btn_browse = QPushButton("Browse...")
        btn_browse.setStyleSheet(f"background-color: {TOKENS.BG_CARD}; color: {TOKENS.TEXT_SECONDARY}; border: 1px solid {TOKENS.BORDER_DEFAULT};")
        btn_browse.clicked.connect(self._browse_dir)
        path_box.addWidget(btn_browse)
        layout.addLayout(path_box)

        # Shortcuts checkboxes
        self.chk_desktop = QCheckBox("Create Desktop Shortcut")
        self.chk_desktop.setChecked(True)
        layout.addWidget(self.chk_desktop)

        self.chk_start_menu = QCheckBox("Create Start Menu Shortcut")
        self.chk_start_menu.setChecked(True)
        layout.addWidget(self.chk_start_menu)

        self.chk_launch = QCheckBox("Launch Spider-Man Water Buddy when setup finishes")
        self.chk_launch.setChecked(True)
        layout.addWidget(self.chk_launch)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setFixedHeight(18)
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {TOKENS.ACCENT_RED_HOVER}; font-size: 12px; font-weight: 600;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Action Buttons
        btn_box = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(f"background-color: {TOKENS.BG_CARD}; color: {TOKENS.TEXT_SECONDARY}; border: 1px solid {TOKENS.BORDER_DEFAULT};")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        btn_box.addStretch()

        self.btn_install = QPushButton("Install Now ⚡")
        self.btn_install.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 {TOKENS.ACCENT_RED}, stop: 1 {TOKENS.ACCENT_RED_ACTIVE});
                color: #ffffff;
                border: 1px solid {TOKENS.ACCENT_RED_HOVER};
            }}
            QPushButton:hover {{ background: {TOKENS.ACCENT_RED_HOVER}; }}
        """)
        self.btn_install.clicked.connect(self._start_install)
        btn_box.addWidget(self.btn_install)

        layout.addLayout(btn_box)

    def _browse_dir(self):
        chosen = QFileDialog.getExistingDirectory(self, "Select Installation Directory", self.edit_path.text())
        if chosen:
            self.edit_path.setText(str(Path(chosen) / "SpiderManWaterBuddy"))

    def _start_install(self):
        target_str = self.edit_path.text().strip()
        invalid_roots = {"c:\\", "c:\\windows", "c:\\windows\\system32", "c:\\program files", "c:\\program files (x86)"}
        
        if not target_str or len(target_str) < 3 or not Path(target_str).is_absolute() or target_str.lower().rstrip("\\") in invalid_roots:
            target = self.default_install_dir
            self.edit_path.setText(str(target))
        else:
            target = Path(target_str)
        self.btn_install.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)

        self.worker = InstallWorker(
            target_dir=target,
            desktop_shortcut=self.chk_desktop.isChecked(),
            start_menu=self.chk_start_menu.isChecked(),
            launch_after=self.chk_launch.isChecked(),
        )
        self.worker.progressUpdated.connect(self._on_progress)
        self.worker.finishedSuccess.connect(self._on_success)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_progress(self, val: int, msg: str):
        self.progress.setValue(val)
        self.status_label.setText(msg)

    def _on_success(self, target_exe: Path):
        if self.chk_launch.isChecked():
            subprocess.Popen([str(target_exe)], creationflags=subprocess.CREATE_NO_WINDOW)

        QMessageBox.information(
            self,
            "Installation Complete",
            "Spider-Man Water Buddy has been successfully installed on your computer!\n\nYou can launch it from your Desktop or Start Menu anytime.",
        )
        self.accept()

    def _on_failed(self, error: str):
        QMessageBox.critical(self, "Installation Failed", f"An error occurred: {error}")
        self.btn_install.setEnabled(True)
        self.btn_cancel.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = InstallerWindow()
    window.exec()


if __name__ == "__main__":
    main()
