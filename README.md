# 🕸️ Spider-Man Water Buddy

A lightweight, standalone, installable Windows desktop companion featuring a photorealistic 3D Spider-Man hanging upside down from your desktop corner to keep you hydrated and focused.

![Spider-Man Desktop Companion](assets/images/spidey_3d_render.png)

---

## ✨ Key Features

### 🕷️ Photorealistic 3D Superhero Companion
- **Corner Web-Hang**: Spider-Man hangs upside down by a glowing web strand anchored to your screen corner/bezel.
- **True Transparency & Hardware Click-Through**: Completely transparent frameless overlay using Windows extended styles (`WS_EX_TRANSPARENT | WS_EX_LAYERED`). Clicks pass straight through to your games and desktop work.
- **Global Interaction Hotkey**: Press **`Ctrl + Alt + S`** anytime to toggle click-through and interact directly with Spider-Man.
- **Physical Pendulum & Elastic Recoil**: Natural physics-based swinging on the web strand, and elastic mouse drag-and-release with realistic spring recoil.
- **Expressive Reactions**: Eye-lens expansion and web-wave on mouse hover, thumbs-up celebration on **YES**, and funny slumped disappointment on **NO**.

### 💧 Deterministic Hydration & Reminder Engine
- **Configurable Intervals**: Quick presets (15, 30, 45, 60, 90 mins) or custom intervals in minutes.
- **Independent Snooze & Retry**: Snooze options (5m, 10m, 15m) and automatic gentle retry if no response is given.
- **Quiet Hours with Midnight-Crossing**: Configure non-intrusive periods (e.g., 22:00 to 07:00) during which reminders are gracefully suppressed.
- **Daily Goal Tracking**: Set your daily hydration goal (in ml) with automatic 24-hour resets and historical daily statistics.

### 🎨 Superhero Dark Dashboard & Setup Wizard
- **First-Run Setup Wizard**: 4-step onboarding wizard to personalize your companion name, greeting message, reminder preferences, and startup behavior.
- **Control Dashboard**: Tabbed interface (Overview, Reminders, Appearance, Diagnostics) with Spider-Man crimson and midnight-indigo theme.
- **System Tray Integration**: Background tray icon with right-click menu: *Show/Hide Companion*, *Open Dashboard*, *Pause/Resume Reminders*, *Remind Me Now*, *Toggle Click-Through*, and *Exit*.
- **Auto-Startup Registration**: Safe Windows startup registration via `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` without requiring administrator privileges.

---

## ⚡ Performance & Efficiency
Unlike heavy Electron-based desktop companions, Spider-Man Water Buddy is powered by native PySide6 (Qt 6.12) with zero external background processes:

| Metric | Measured Result |
| :--- | :--- |
| **Startup Memory** | **~122.9 MB** |
| **Peak Working Set** | **~138.6 MB** |
| **Idle CPU Usage** | **0.00%** |
| **Animation CPU Usage** | **< 1.0%** |
| **Admin Rights Required** | **None (User-space)** |

---

## 🚀 Installation & Running

### 1. Standalone Installer (Recommended)
Download and run:
```
dist\SpiderManWaterBuddy-v1.0.0-Setup.exe
```
- Installs to `%LOCALAPPDATA%\Programs\SpiderManWaterBuddy`.
- Automatically generates Desktop and Start Menu shortcuts.
- Registers in Windows *Installed Apps* / *Add or Remove Programs*.

### 2. Portable Edition
Extract:
```
dist\SpiderManWaterBuddy-v1.0.0-Portable.zip
```
Double-click `SpiderManWaterBuddy.exe` to run instantly from any folder or USB drive.

### 3. Uninstalling
- Launch from Windows *Installed Apps / Settings*, or run `uninstall.exe` in the application directory.
- The uninstaller safely cleans shortcuts, startup registry entries, and program binaries.
- **User Privacy Choice**: Explicitly prompts whether you want to delete or retain your personal settings and hydration records in `%APPDATA%\SpiderManWaterBuddy`.

---

## 🛠️ Development & Building from Source

### Prerequisites
- Windows 10 / 11 (64-bit)
- Python 3.11+
- Virtual environment with PySide6:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

### Running Locally
```powershell
.\.venv\Scripts\python.exe run.py
```

### Running Automated Test Suite
- Comprehensive unit and state-machine tests:
  ```powershell
  .\.venv\Scripts\python.exe tests\test_full_suite.py
  ```
- Resource profiling and memory benchmark:
  ```powershell
  .\.venv\Scripts\python.exe tests\profile_resources.py
  ```

### Building Distributables
1. **Compile Application Executable**:
   ```powershell
   .\.venv\Scripts\pyinstaller.exe --onedir --noconsole --name "SpiderManWaterBuddy" --icon "assets/images/app_icon.ico" --add-data "assets;assets" run.py
   ```
2. **Compile Uninstaller**:
   ```powershell
   .\.venv\Scripts\pyinstaller.exe --onefile --noconsole --name "uninstall" --distpath "dist/SpiderManWaterBuddy" --icon "assets/images/app_icon.ico" src/uninstaller_gui.py
   ```
3. **Generate Portable Zip**:
   ```powershell
   Compress-Archive -Path ".\dist\SpiderManWaterBuddy\*" -DestinationPath ".\dist\SpiderManWaterBuddy-v1.0.0-Portable.zip" -Force
   ```
4. **Compile Setup Installer**:
   ```powershell
   .\.venv\Scripts\pyinstaller.exe --onefile --noconsole --name "SpiderManWaterBuddy-v1.0.0-Setup" --icon "assets/images/app_icon.ico" --add-data "dist/SpiderManWaterBuddy-v1.0.0-Portable.zip;." src/installer_gui.py
   ```

---

## 📜 License
MIT License. Created with Antigravity.
