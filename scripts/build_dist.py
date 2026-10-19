"""
Automated Build & Packaging Pipeline for Spider-Man Water Buddy.
Builds the standalone onedir executable, uninstaller, portable zip, and single-file setup installer.
"""
import sys
import os
import shutil
import zipfile
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.version import VERSION, APP_NAME

DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
PACKAGING_DIR = ROOT_DIR / "packaging"


def run_cmd(cmd, description):
    print(f"\n[BUILD STEP] {description}...")
    result = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if result.returncode != 0:
        print(f"[ERROR] Failed during: {description}")
        sys.exit(result.returncode)
    print(f"[SUCCESS] {description} completed.")


def build_all():
    print("==================================================")
    print(f" {APP_NAME} v{VERSION} — Production Build Suite")
    print("==================================================")

    # 0. Gracefully terminate any running instances
    try:
        for proc in ["SpiderManWaterBuddy.exe", "uninstall.exe", f"SpiderManWaterBuddy-v{VERSION}-Setup.exe"]:
            subprocess.run(["taskkill", "/F", "/IM", proc], capture_output=True)
    except Exception:
        pass

    # 1. Build main application onedir package
    spec_main = PACKAGING_DIR / "SpiderManWaterBuddy.spec"
    run_cmd([sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec_main)], "Compiling SpiderManWaterBuddy (onedir)")

    # 2. Build uninstaller single-file executable
    spec_uninst = PACKAGING_DIR / "uninstall.spec"
    run_cmd([sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec_uninst)], "Compiling uninstaller")

    # 3. Copy uninstaller into application directory
    src_uninst = DIST_DIR / "uninstall.exe"
    dest_uninst = DIST_DIR / "SpiderManWaterBuddy" / "uninstall.exe"
    if src_uninst.exists():
        shutil.copy2(src_uninst, dest_uninst)
        src_uninst.unlink()
        print(f"[INFO] Integrated uninstaller into {dest_uninst}")

    # 4. Generate portable zip archive
    app_folder = DIST_DIR / "SpiderManWaterBuddy"
    portable_zip = DIST_DIR / f"SpiderManWaterBuddy-v{VERSION}-Portable.zip"
    print(f"\n[BUILD STEP] Creating portable archive: {portable_zip.name}...")

    with zipfile.ZipFile(portable_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for file_path in app_folder.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(app_folder)
                zf.write(file_path, arcname=str(rel_path))

    size_mb = portable_zip.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Created portable zip ({size_mb:.2f} MB).")

    # 5. Build onefile setup installer
    spec_setup = PACKAGING_DIR / f"SpiderManWaterBuddy-v{VERSION}-Setup.spec"
    if not spec_setup.exists():
        spec_setup = PACKAGING_DIR / "SpiderManWaterBuddy-Setup.spec"
    run_cmd([sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec_setup)], "Compiling Setup Installer")

    installer_exe = DIST_DIR / f"SpiderManWaterBuddy-v{VERSION}-Setup.exe"
    inst_size_mb = installer_exe.stat().st_size / (1024 * 1024) if installer_exe.exists() else 0

    print("\n==================================================")
    print(f" BUILD PIPELINE COMPLETED SUCCESSFULLY (v{VERSION})!")
    print(f" 1. Portable Folder:  {app_folder}")
    print(f" 2. Portable Zip:     {portable_zip} ({size_mb:.2f} MB)")
    print(f" 3. Windows Setup:    {installer_exe} ({inst_size_mb:.2f} MB)")
    print("==================================================")


if __name__ == "__main__":
    build_all()
