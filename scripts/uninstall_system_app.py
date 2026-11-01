import os
import shutil
import winreg
import subprocess
from pathlib import Path

print("============================================================")
print("  CLEANING / UNINSTALLING SPIDER-MAN WATERPOP FROM SYSTEM")
print("============================================================")

# 1. Kill any running app processes
print("[1/5] Terminating any running application instances...")
subprocess.run(["taskkill", "/f", "/im", "SpiderManWaterBuddy.exe"], capture_output=True)
subprocess.run(["taskkill", "/f", "/im", "uninstall.exe"], capture_output=True)
subprocess.run([
    "powershell", "-NoProfile", "-Command",
    "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run.py*' } | Stop-Process -Force -ErrorAction SilentlyContinue"
], capture_output=True)

# 2. Delete Shortcuts from Desktop & Start Menu
print("[2/5] Removing Desktop and Start Menu shortcuts...")
shortcut_targets = []
appdata = os.environ.get("APPDATA")
if appdata:
    sm = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    shortcut_targets.extend([
        sm / "Spider-Man Waterpop.lnk",
        sm / "Spider-Man Water Buddy.lnk",
    ])

userprofile = os.environ.get("USERPROFILE")
if userprofile:
    d = Path(userprofile) / "Desktop"
    shortcut_targets.extend([
        d / "Spider-Man Waterpop.lnk",
        d / "Spider-Man Water Buddy.lnk",
    ])

onedrive = os.environ.get("OneDrive")
if onedrive:
    d_od = Path(onedrive) / "Desktop"
    shortcut_targets.extend([
        d_od / "Spider-Man Waterpop.lnk",
        d_od / "Spider-Man Water Buddy.lnk",
    ])

for sc in set(shortcut_targets):
    if sc.exists():
        try:
            sc.unlink()
            print(f"  - Deleted shortcut: {sc}")
        except Exception as e:
            print(f"  - Could not delete {sc}: {e}")

# 3. Remove Windows Registry entries
print("[3/5] Cleaning Windows Registry keys...")
reg_keys_to_delete = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\SpiderManWaterpop"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\SpiderManWaterBuddy"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\waterpop.exe"),
]
for root_key, subkey in reg_keys_to_delete:
    try:
        winreg.DeleteKey(root_key, subkey)
        print(f"  - Deleted registry key: {subkey}")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"  - Could not delete registry key {subkey}: {e}")

# Check Run startup entry
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
        try:
            winreg.DeleteValue(key, "SpiderManWaterBuddy")
            print("  - Removed startup entry from Run key")
        except FileNotFoundError:
            pass
except Exception:
    pass

# 4. Remove installed program files from LocalAppData
print("[4/5] Removing installed binaries from LocalAppData...")
local_app = os.environ.get("LOCALAPPDATA")
if local_app:
    install_dir = Path(local_app) / "Programs" / "SpiderManWaterBuddy"
    if install_dir.exists():
        try:
            shutil.rmtree(install_dir, ignore_errors=True)
            print(f"  - Removed installed folder: {install_dir}")
        except Exception as e:
            print(f"  - Could not remove {install_dir}: {e}")

# 5. Remove AppData settings & logs
print("[5/5] Removing app runtime configuration & logs...")
if appdata:
    app_data_dir = Path(appdata) / "SpiderManWaterBuddy"
    if app_data_dir.exists():
        try:
            shutil.rmtree(app_data_dir, ignore_errors=True)
            print(f"  - Removed AppData directory: {app_data_dir}")
        except Exception as e:
            print(f"  - Could not remove {app_data_dir}: {e}")

print("============================================================")
print("[SUCCESS] Application has been cleanly uninstalled from your PC!")
print("============================================================")
