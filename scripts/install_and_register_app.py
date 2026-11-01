import os
import sys
import winreg
from pathlib import Path
import subprocess
import ctypes

project_dir = Path(__file__).resolve().parent.parent
icon_path = project_dir / "assets" / "images" / "app_icon.ico"
pythonw_exe = project_dir / ".venv" / "Scripts" / "pythonw.exe"
run_py = project_dir / "run.py"
bat_launcher = project_dir / "LAUNCH_APP.bat"

# Target executable and arguments
target_exe = str(pythonw_exe.resolve()) if pythonw_exe.exists() else str(bat_launcher.resolve())
target_args = f'"{run_py.resolve()}"' if pythonw_exe.exists() else ''
work_dir = str(project_dir.resolve())
icon_str = str(icon_path.resolve())

app_user_model_id = "SpiderManWaterpop.DesktopApp.2.0"

# Directories
desktop_dirs = []
onedrive = os.environ.get("OneDrive")
if onedrive and (Path(onedrive) / "Desktop").exists():
    desktop_dirs.append(Path(onedrive) / "Desktop")
userprofile = os.environ.get("USERPROFILE")
if userprofile and (Path(userprofile) / "Desktop").exists():
    desktop_dirs.append(Path(userprofile) / "Desktop")

start_menu_dirs = []
appdata = os.environ.get("APPDATA")
if appdata:
    start_menu_dirs.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
programdata = os.environ.get("ProgramData")
if programdata:
    global_sm = Path(programdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    if global_sm.exists():
        start_menu_dirs.append(global_sm)

def make_shortcut(lnk_path: Path, name: str):
    lnk_path.parent.mkdir(parents=True, exist_ok=True)
    esc_lnk = str(lnk_path.resolve()).replace("'", "''")
    esc_target = target_exe.replace("'", "''")
    esc_args = target_args.replace("'", "''")
    esc_workdir = work_dir.replace("'", "''")
    esc_icon = icon_str.replace("'", "''")

    ps_code = f"""
    $w = New-Object -ComObject WScript.Shell
    $s = $w.CreateShortcut('{esc_lnk}')
    $s.TargetPath = '{esc_target}'
    $s.Arguments = '{esc_args}'
    $s.WorkingDirectory = '{esc_workdir}'
    $s.IconLocation = '{esc_icon}, 0'
    $s.Description = 'Spider-Man Waterpop v2.0 - Desktop Hydration Companion'
    $s.Save()
    """
    res = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_code], capture_output=True)
    if lnk_path.exists():
        print(f"[OK] Created shortcut: {lnk_path}")

# 1. Desktop Shortcuts
for d in set(desktop_dirs):
    make_shortcut(d / "Spider-Man Waterpop.lnk", "Spider-Man Waterpop")

# 2. Start Menu Shortcuts (Creates Spider-Man Waterpop and Waterpop so searching either finds it!)
for sm in set(start_menu_dirs):
    try:
        make_shortcut(sm / "Spider-Man Waterpop.lnk", "Spider-Man Waterpop")
        make_shortcut(sm / "Waterpop.lnk", "Waterpop")
    except Exception as e:
        print(f"[WARN] Could not write to {sm}: {e}")

# 3. Register in Windows Registry (Uninstall & App Paths)
try:
    reg_uninstall = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\SpiderManWaterpop"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_uninstall) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Spider-Man Waterpop")
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "2.0.0")
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Antigravity")
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_str)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, work_dir)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'cmd.exe /c del "{start_menu_dirs[0]}\\Spider-Man Waterpop.lnk"')
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    print("[OK] Registered in Windows Installed Apps (Registry)")
except Exception as e:
    print(f"[WARN] Failed to write Uninstall registry: {e}")

for app_name in ["waterpop.exe", "spidermanwaterpop.exe", "spider.exe"]:
    try:
        reg_app_path = rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{app_name}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_app_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, target_exe)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, work_dir)
        print(f"[OK] Registered App Path: {app_name}")
    except Exception:
        pass

# 4. Notify Windows Shell and refresh Explorer
try:
    # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_FLUSH = 0x1000
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x1000, None, None)
    # SHCNE_UPDATEITEM = 0x00002000
    ctypes.windll.shell32.SHChangeNotify(0x00002000, 0x1000, None, None)
    print("[OK] Refreshed Windows Desktop and Start Menu shell index")
except Exception as e:
    print(f"[WARN] Shell notify: {e}")

print("[DONE] Spider-Man Waterpop shortcut created and registered successfully!")
