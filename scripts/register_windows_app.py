import os
import sys
import winreg
from pathlib import Path
import subprocess

project_dir = Path(__file__).resolve().parent.parent
icon_path = project_dir / "assets" / "images" / "app_icon.ico"
launcher_bat = project_dir / "START_APP.bat"

appdata = os.environ.get("APPDATA")
start_menu = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"

desktop_candidates = []
onedrive = os.environ.get("OneDrive")
if onedrive and (Path(onedrive) / "Desktop").exists():
    desktop_candidates.append(Path(onedrive) / "Desktop")
userprofile = os.environ.get("USERPROFILE")
if userprofile and (Path(userprofile) / "Desktop").exists():
    desktop_candidates.append(Path(userprofile) / "Desktop")

names = ["Spider-Man Waterpop", "Spider-Man Water Buddy"]


def create_lnk(lnk_path: Path):
    lnk_path.parent.mkdir(parents=True, exist_ok=True)
    esc_lnk = str(lnk_path.resolve()).replace("'", "''")
    esc_target = str(launcher_bat.resolve()).replace("'", "''")
    esc_icon = str(icon_path.resolve()).replace("'", "''")
    esc_workdir = str(project_dir.resolve()).replace("'", "''")

    ps_code = f"""
    $w = New-Object -ComObject WScript.Shell
    $s = $w.CreateShortcut('{esc_lnk}')
    $s.TargetPath = '{esc_target}'
    $s.Arguments = ''
    $s.WorkingDirectory = '{esc_workdir}'
    $s.IconLocation = '{esc_icon}, 0'
    $s.Description = 'Spider-Man Waterpop v2.0 - Desktop Hydration Companion'
    $s.Save()
    """
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_code], capture_output=True)
    print(f"[OK] Shortcut created: {lnk_path}")


for name in names:
    create_lnk(start_menu / f"{name}.lnk")

for d in set(desktop_candidates):
    create_lnk(d / "Spider-Man Waterpop.lnk")

reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\SpiderManWaterpop"
try:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Spider-Man Waterpop")
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "2.0.0")
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Antigravity")
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(icon_path.resolve()))
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(project_dir.resolve()))
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'cmd.exe /c del "{start_menu}\\Spider-Man Waterpop.lnk"')
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    print("[OK] Registered in Windows Installed Apps (Registry)")
except Exception as e:
    print(f"[WARN] Failed to write registry: {e}")

app_paths = r"Software\Microsoft\Windows\CurrentVersion\App Paths\waterpop.exe"
try:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, app_paths) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(launcher_bat.resolve()))
        winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, str(project_dir.resolve()))
    print("[OK] Registered in Windows App Paths (waterpop.exe)")
except Exception:
    pass

print("[DONE] Spider-Man Waterpop successfully registered in Windows!")
