# 🕸️ Spider-Man Water Buddy v2.0

A lightweight, standalone, installable Windows desktop companion featuring a photorealistic 3D Spider-Man hanging upside down from your desktop corner with Stark Tech EDITH Tactical HUD telemetry, 4-phase cinematic web swing animations, and gamified hydration streak tracking.

![Spider-Man Desktop Companion](assets/images/spidey_3d_render.png)

---

## ✨ Key Features (v2.0)

### 🕷️ Cinematic 3D Superhero Companion
- **Corner Web-Hang**: Spider-Man hangs upside down by a glowing web strand anchored to your screen corner/bezel.
- **4-Phase Cinematic Web Swing**: Clicking "YES, I DRANK" triggers Anticipation -> Wide Horizontal Web Swing -> Victory Celebration Dance -> Smooth Damped Recovery.
- **Expressive Disappointment Reaction**: Clicking "NO" triggers a funny slump reaction without recording water intake.
- **True Transparency & Hardware Click-Through**: Completely transparent frameless overlay using Windows extended styles (`WS_EX_TRANSPARENT | WS_EX_LAYERED`). Clicks pass straight through to your games and desktop work.
- **Global Interaction Hotkey**: Press **`Ctrl + Alt + W`** anytime (system-wide) to toggle click-through and interact directly with Spider-Man.
- **Physical Pendulum & Elastic Recoil**: Natural physics-based swinging on the web strand, and elastic mouse drag-and-release with realistic spring recoil.

### 💧 Deterministic Hydration & Streak Engine
- **Manual "YES, I DRANK 💧" Action**: Authoritative 30-minute hard minimum cooldown resilient to system reboots, sleep/hibernate, and clock tampering.
- **First-Class Streak System**: Daily goal tracking (default 2,000 ml) with streak counting, milestones (3, 7, 14, 30, 100 days), and configurable Web Shield forgiveness.
- **Configurable Intervals**: Quick presets (15, 30, 45, 60, 90 mins) or custom intervals in minutes.
- **Independent Snooze & Retry**: Snooze options (5m, 10m, 15m) and automatic gentle retry if no response is given.
- **Quiet Hours with Midnight-Crossing**: Configure non-intrusive periods (e.g., 22:00 to 07:00) during which reminders are gracefully suppressed.

### 🎨 Stark Tech EDITH Tactical HUD Dashboard
- **Tactical Reticle Hero**: High-contrast pitch-black (`#050811`) and white laser line aesthetic replacing generic SaaS templates.
- **Modern Typography**: Bundled high-legibility Segoe UI and Cascadia Code typography with tabular numerals preventing countdown jitter.
- **Pre-Qt Named Mutex**: Windows Kernel Named Mutex guarantees single-instance execution on fast double-clicks.
- **Atomic Generational Backups**: 3-generation rotating backup ring (`.bak.1`, `.bak.2`, `.bak.3`) with corrupt file quarantine.
- **Auto-Startup Registration**: Safe Windows startup registration via `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` without requiring administrator privileges.

---

## ⚡ Performance & Efficiency
Unlike heavy Electron-based desktop companions, Spider-Man Water Buddy is powered by native PySide6 (Qt 6.7) with zero external background processes:

| Metric | Measured Result |
| :--- | :--- |
| **Startup Memory** | **~34.0 MB** |
| **Idle Memory (Steady State)** | **~44.0 MB** |
| **Peak Working Set** | **~65.0 MB** |
| **Idle CPU Usage** | **< 0.2%** |
| **Animation CPU Usage** | **< 2.1%** |
| **Admin Rights Required** | **None (User-space)** |

---

## 🚀 Installation & Running

### 1. Standalone Installer (Recommended)
Download and run:
```
dist\SpiderManWaterBuddy-v2.0.0-Setup.exe
```
Or double-click `INSTALL_APP.bat`.
- Installs to `%LOCALAPPDATA%\Programs\SpiderManWaterBuddy`.
- Automatically generates Desktop and Start Menu shortcuts.
- Registers in Windows *Installed Apps* / *Add or Remove Programs*.

### 2. Portable Edition
Extract:
```
dist\SpiderManWaterBuddy-v2.0.0-Portable.zip
```
Double-click `SpiderManWaterBuddy.exe` or `START_APP.bat` to run instantly from any folder or USB drive.

### 3. Uninstalling
- Launch from Windows *Installed Apps / Settings*, or run `uninstall.exe` in the application directory.
- The uninstaller safely cleans shortcuts, startup registry entries, and program binaries.
- **User Privacy Choice**: Explicitly prompts whether you want to delete or retain your personal settings and hydration records in `%APPDATA%\SpiderManWaterBuddy`.

---

## 🛠️ Development & Building from Source

### Prerequisites
- Windows 10 / 11 (64-bit)
- Python 3.11+
- Virtual environment with dependencies:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt -r requirements-dev.txt
  ```

### Running Tests
Execute the full 55-test automated regression suite:
```powershell
.\.venv\Scripts\python.exe -m pytest
```

### Running Locally
```powershell
.\.venv\Scripts\python.exe run.py
```

### Running Automated Test Suite
- Comprehensive 55-test suite covering state machine, security, cooldown, streak, animations, and UI:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest
  ```

### Building Distributables (Automated)
Run the automated packaging script to compile the onedir application, uninstaller, portable zip, and single-file setup installer:
```powershell
.\.venv\Scripts\python.exe scripts/build_dist.py
```
Outputs are placed directly in `dist/`:
- `dist/SpiderManWaterBuddy/` (portable onedir folder)
- `dist/SpiderManWaterBuddy-v2.0.0-Portable.zip`
- `dist/SpiderManWaterBuddy-v2.0.0-Setup.exe`

---

## 📜 License
MIT License.
