# 🕷️ Spider-Man Waterpop v2.0 — Desktop Hydration Companion

> **A lightweight, standalone desktop hydration companion for Windows.**  
> Features a photorealistic 3D Spider-Man hanging upside down from your screen corner, physics-based swinging, a deterministic reminder engine, an interactive Neo-Brutalist graphic dashboard, and a Deep Black & Polished Gold setup experience.

![Spider-Man Desktop Companion](assets/images/spidey_3d_render.png)

---

## 📖 Table of Contents
1. [Project Overview](#-project-overview)
2. [Beginner's Step-by-Step Architecture Guide](#-beginners-step-by-step-architecture-guide)
   - [How the Desktop Companion Works](#how-the-desktop-companion-works)
   - [Directory & File Roadmap](#directory--file-roadmap)
   - [Hydration Logic & State Engine](#hydration-logic--state-engine)
   - [Character Physics & Animation Engine](#character-physics--animation-engine)
   - [Design Philosophy: Neo-Brutalist Graphic Dashboard & Deep Gold Installer](#design-philosophy)
3. [Task History & Problem-Solving Log](#-task-history--problem-solving-log)
   - [Fix 1: Eliminating Left-Edge Clipping & 270° Cutoff](#fix-1-eliminating-left-edge-clipping--270-cutoff)
   - [Fix 2: Removing the Bent Web Kink & Duplicate Web String](#fix-2-removing-the-bent-web-kink--duplicate-web-string)
   - [Fix 3: Complete Removal of Glassmorphism](#fix-3-complete-removal-of-glassmorphism)
   - [Fix 4: Restoring the v1.0.0 Reminder Hero Section & Trigger Time](#fix-4-restoring-the-v100-reminder-hero-section--trigger-time)
   - [Fix 5: Official Logo, Windows Taskbar Branding & Desktop Shortcuts](#fix-5-official-logo-windows-taskbar-branding--desktop-shortcuts)
   - [Fix 6: Neo-Brutalist Pop-Art Graphic Dashboard & Bidirectional WebBridge](#fix-6-neo-brutalist-pop-art-graphic-dashboard--bidirectional-webbridge)
   - [Fix 7: Deep Black & Polished Gold Installer and Resilient Shortcuts](#fix-7-deep-black--polished-gold-installer-and-resilient-shortcuts)
4. [How to Run & Install (Quick Start)](#-how-to-run--install-quick-start)
5. [Command Line Flags & Controls](#-command-line-flags--controls)
6. [Testing & Quality Assurance](#-testing--quality-assurance)
7. [Configuration, Backups & Privacy](#-configuration-backups--privacy)
8. [Troubleshooting & FAQ](#-troubleshooting--faq)
9. [Legal & Trademark Notice](#-legal--trademark-notice)

---

## 🌟 Project Overview

**Spider-Man Waterpop** is an interactive desktop hydration companion built with Python 3.10+ and PySide6 (Qt 6.7+). It solves a common problem: forgetting to stay hydrated during long work or gaming sessions.

Instead of annoying, generic popups or web notifications, Spider-Man hangs upside down from the corner of your screen by an authentic silk web strand. He periodically checks in with you, swings dynamically across your monitor when you drink water, and tracks your daily hydration goals and streaks in an interactive dashboard.

### Key Highlights
* **Native Desktop Engine:** Powered by PySide6 C++ Qt (~45 MB memory idle companion; ~120 MB when Chromium-based WebEngine dashboard is open).
* **Hardware Click-Through:** Clicks pass straight through to background games and apps (`WS_EX_TRANSPARENT`).
* **Global Hotkey:** Press `Ctrl + Alt + W` anytime system-wide to toggle companion interactivity.
* **Dual Interface:** Interactive Neo-Brutalist Pop-Art Graphic Dashboard (`QWebEngineView`) with synchronized native Qt widgets as fallback.
* **Deterministic Cooldown Engine:** Anti-spam cooldown resilient to reboots, sleep states, and clock adjustments.
* **Single Instance Protection:** Windows Kernel Named Mutex guarantees only one instance runs at a time.
* **Deep Black & Gold Setup:** Polished obsidian and gold setup wizard with OneDrive-compatible shortcut deployment.

---

## 🏗️ Beginner's Step-by-Step Architecture Guide

If you are new to desktop app development or Python GUI programming, this section explains exactly how the codebase is organized and how all pieces fit together.

### How the Desktop Companion Works

```
┌────────────────────────────────────────────────────────┐
│                        Windows OS                      │
│     (Screen Geometry, Kernel Mutex, Win32 Hotkeys)     │
└───────────────────────────▲────────────────────────────┘
                            │
               ┌────────────┴────────────┐
               │         run.py          │ (Entry point, Mutex check, AppUserModelID)
               └────────────┬────────────┘
                            │
               ┌────────────▼────────────┐
               │        src/app.py       │ (Central Coordinator / Controller)
               └──────┬────────────┬─────┘
                      │            │
       ┌──────────────▼─────┐      ┌▼─────────────────────┐
       │src/reminder_engine │      │ src/streak_tracker   │
       │(Timers, States,    │      │ (Daily volume, logs, │
       │ Quiet Hours)       │      │  anti-spam cooldown) │
       └──────┬─────────────┘      └──────────────────────┘
              │
    ┌─────────┴───────────────────────┐
    │                                 │
┌───▼─────────────────────┐   ┌───────▼─────────────────┐
│ src/companion_window.py │   │ src/dashboard_window.py │
│ (Frameless transparent  │   │ (Neo-Brutalist graphic  │
│  desktop overlay)       │   │  dashboard & native HUD,│
│ └── src/character.py    │   │  telemetry, settings,   │
│     (3D Spidey render,  │   │  reminder protocol)     │
│      pendulum physics,  │   └─────────────────────────┘
│      silk web strand)   │
└─────────────────────────┘
```

1. **`run.py` (Startup Guard):**
   - Registers Windows `AppUserModelID` (`SpiderManWaterpop.DesktopApp.2.0`) so the application icon shows up distinctly in the taskbar rather than grouping under generic Python.
   - Enforces a Windows Named Mutex (`Local\SpiderManWaterBuddy_SingleInstance_Mutex`). If an instance is already open, it activates the existing window via an IPC local socket and alerts the user.
   - Handles graceful logging setup with automatic fallback to system temporary directories if APPDATA is locked.
   - Rate-limits error dialogs to prevent modal alert storms.
2. **`src/app.py` (Application Lifecycle):**
   - Coordinates the Reminder Engine, Desktop Companion, Settings Dashboard, and System Tray icon.
   - Handles global signals like `Ctrl + Alt + W` and manages clean shutdown.
3. **`src/companion_window.py` (Desktop Overlay):**
   - A borderless, translucent Qt window (`Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`).
   - Floats anchored to your selected screen corner (top-right by default) without taking focus or appearing in the `Alt + Tab` task switcher.
4. **`src/character.py` (Visual Physics):**
   - Renders the 3D Spider-Man model inside an unclipped 460×420 canvas.
   - Computes pendulum oscillation, mouse dragging, spring recoil, and comic celebration particles.
5. **`src/dashboard_window.py` (Main Control Center):**
   - Houses the Neo-Brutalist graphic dashboard connected via `QWebChannel`, alongside the native widget fallback.

---

### Directory & File Roadmap

```
thalivar_watepop/
├── START_APP.bat              # 1-Click launcher (checks venv and dependencies)
├── SETUP.bat                  # Automated environment setup and pip install
├── INSTALL_APP.bat            # Installer launcher / shortcut configurator
├── INSTALL_SHORTCUTS.bat      # Standalone shortcut installer
├── run.py                     # Main application entry point
├── requirements.txt           # Production dependencies (PySide6)
├── requirements-dev.txt       # Dev dependencies (pytest, pytest-qt, Pillow, PyInstaller)
├── pyproject.toml             # Standard PEP 518/621 project metadata
├── pytest.ini                 # Headless test runner configuration
├── LICENSE                    # MIT License + Trademark Disclaimer
├── CHANGELOG.md               # Version history and upgrade log
├── assets/                    # Application icons, character sprites, and 3D renders
├── src/                       # Core application source code
│   ├── app.py                 # Application controller
│   ├── character.py           # Character rendering and pendulum physics
│   ├── companion_window.py    # Desktop overlay window
│   ├── config.py              # Configuration manager and atomic backup ring
│   ├── dashboard_window.py    # Dual dashboard window and QWebChannel bridge
│   ├── installer_gui.py       # Standalone Deep Black & Gold Setup Wizard
│   ├── uninstaller_gui.py     # Standalone Deep Black & Gold Uninstaller
│   ├── wizard_dialog.py       # First-run guided setup wizard
│   ├── reminder_engine.py     # Deterministic reminder state machine
│   ├── streak_tracker.py      # Hydration streak, goal credit, and cooldown
│   ├── theme.py               # Color tokens and stylesheet generators
│   ├── utils.py               # Resource path helpers and boot telemetry
│   ├── windows_native.py      # Win32 click-through, hotkeys, and mutex
│   └── web/                   # Neo-Brutalist HTML dashboard and assets
└── tests/                     # 60 automated unit and regression tests
```

---

### Design Philosophy

* **Neo-Brutalist Graphic Dashboard (`src/web/dashboard.html`):**
  - **Sunlit Comic Desk:** Warm yellow desktop canvas (`#f5e24f`), deep ink outlines (`#141a3a`), royal blue fluid (`#3350ff`), and tactile offset shadows (`5px 5px 0 #141a3a`).
  - **Dynamic Filling Bottle:** Animated SVG glass bottle with fluid wave physics, rising bubbles, and measurement tick marks.
  - **7-Day Pill Organizer:** Weekly hydration wells that fill and glow green upon achieving daily goals.
  - **Offline Font Fallbacks:** Seamlessly renders with local system typography (`Segoe UI`, `Impact`, `Consolas`, `Segoe Print`) if internet is disconnected.
* **Deep Black & Polished Gold Setup & Dialogs (`src/installer_gui.py`, `src/uninstaller_gui.py`):**
  - High-contrast obsidian surface (`#0b0c10`) with polished gold accents (`#d4af37`), gold progress bars, and gold gradients.
* **Comic Pop-Art Companion Dialogue:**
  - Solid cream comic dialogue card (`#fffef6`) with bold ink borders and Spider-Man action buttons.

---

## 🛠️ Task History & Problem-Solving Log

### Fix 1: Eliminating Left-Edge Clipping & 270° Cutoff
* **The Problem:** When dragging Spider-Man towards the left, his body was sliced in half by a vertical line.
* **The Root Cause:** In early iterations, `SpideyWidget` was clamped to 260px width. Rotating the 175px sprite caused negative coordinates (`x < 0`), triggering Qt clipping.
* **The Solution:** Expanded `SpideyWidget` and `CompanionWindow` to **460×420px** with 142px safety margins on left and right, ensuring butter-smooth motion across full 270° without edge clipping.

### Fix 2: Removing the Bent Web Kink & Duplicate Web String
* **The Problem:** Pulling Spidey revealed two separate web strings pointing in different directions with a sharp elbow kink.
* **The Root Cause:** In `spidey_3d_render.png`, a silk web strand is pre-rendered to Spidey's feet. Drawing a second web line from the screen top without accounting for body tilt produced overlapping lines.
* **The Solution:** Connected an adaptive cubic Bézier curve whose lower tangent vector `(-sin(tilt), -cos(tilt))` perfectly matches the rotated angle of the pre-rendered web.

### Fix 3: Complete Removal of Glassmorphism
* **The Problem:** Translucent glass cards caused readability issues against varying desktop wallpapers and visual blur artifacts.
* **The Solution:** Replaced all translucent tokens with solid opaque surfaces and crisp high-contrast outlines.

### Fix 4: Restoring the v1.0.0 Reminder Hero Section & Trigger Time
* **The Solution:** Restored the primary **"REMINDER PROTOCOL & NEXT PROMPT"** Hero card in the dashboard, featuring live status badges (`🟢 ACTIVE MONITORING`, `⏸️ PAUSED`, `🌙 QUIET HOURS`), scheduled trigger time, and high-contrast countdown.

### Fix 5: Official Logo, Windows Taskbar Branding & Desktop Shortcuts
* **The Solution:** Registered Windows `AppUserModelID` (`SpiderManWaterpop.DesktopApp.2.0`) in `run.py` and built automated shortcut scripts.

### Fix 6: Neo-Brutalist Pop-Art Graphic Dashboard & Bidirectional WebBridge
* **The Solution:** Transitioned the primary dashboard to the sunlit comic desk interface with live bidirectional `QWebChannel` synchronization while preserving 100% of underlying application logic.

### Fix 7: Deep Black & Polished Gold Installer and Resilient Shortcuts
* **The Problem:** Setup wizard failed with `Command 'powershell ... -target ...' returned non-zero exit status 1` due to PowerShell `-Command` parameter binding, and OneDrive Desktop paths were misdirected.
* **The Solution:** Re-engineered `create_windows_shortcut` to embed properly escaped absolute paths, added native shell folder CSIDL detection for OneDrive Desktop, made shortcut creation fail-safe, and styled the entire installer and uninstaller in **Deep Black & Polished Gold** (`#0b0c10` / `#d4af37`).

---

## 🚀 How to Run & Install (Quick Start)

### Option 1: 1-Click Launch (Recommended)
1. Double-click **`SETUP.bat`** on first use to automatically create the Python `.venv` and install dependencies.
2. Double-click **`START_APP.bat`** anytime to launch Spider-Man.

### Option 2: Install Desktop & Start Menu Shortcuts
Double-click **`INSTALL_SHORTCUTS.bat`** (or `INSTALL_APP.bat`).  
A Spider-Man shortcut will be created on your Windows Desktop and Start Menu.

### Option 3: Run from Command Line
```powershell
# 1. Set up virtual environment
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. Run application
.\.venv\Scripts\python.exe run.py
```

---

## 🎮 Command Line Flags & Controls

### CLI Arguments
* **`--minimized`**: Starts the application minimized in the system tray without popping up the companion or dashboard (used for Windows Startup).
* **`--dashboard`**: Opens the Hydration Dashboard immediately upon launching.

### Keyboard & Mouse Controls
* **`Ctrl + Alt + W` (Global Hotkey):** Toggles hardware click-through. Use this anytime system-wide to switch between interacting with Spider-Man and clicking through to background apps.
* **Click Spidey:** Opens the Dashboard when idle, or triggers a fun superhero reaction.
* **Drag Spidey:** Click and drag Spider-Man to stretch his web; release to slingshot him back with spring physics.
* **Right-Click Tray Icon:** Opens the context menu (Quick Log +250ml, Open Dashboard, Pause Reminders, Exit).

---

## 🧪 Testing & Quality Assurance

The application includes an automated test suite containing **60 unit and regression tests**:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/
```

### What the Tests Verify:
* **`test_dashboard_bridge.py`:** Tests bidirectional `WebBridge` dispatching (intake logging, settings synchronization, Spider-Sense status).
* **`test_v2_ui_and_companion.py`:** Tests 460px unclipped bounds, maximum drag displacement, reminder hero cards, and solid theme styles.
* **`test_cinematic_animations.py`:** Tests the 4-phase YES web swing sequence, NO slump sequence, and recoil animations.
* **`test_dashboard_window.py`:** Tests countdown formatting, quiet hours rollover, manual log chips, and streak integration.
* **`test_streak_tracker.py`:** Tests intake math, goal credit, streak continuity, and anti-spam cooldown enforcement.
* **`test_v2_cooldown_and_storage.py`:** Tests corruption recovery, atomic file writes, and rotating backup protection.
* **`test_v2_security_audit.py`:** Audits resource paths, installer safety, and single-instance mutex locks.

---

## 🔒 Configuration, Backups & Privacy

All user settings, logs, and streak history are stored strictly locally on your machine:
```
%APPDATA%\SpiderManWaterBuddy\settings.json
```

### Automatic 5-Generation Backup Ring
Every time settings are saved:
1. The configuration is written atomically to a temporary file (`settings.json.tmp`) and flushed to disk before renaming.
2. The previous version is rotated into a 5-generation backup ring (`settings.backup.1` through `settings.backup.5`).
3. If corruption is ever detected, the app automatically restores from the newest valid backup.

---

## ❓ Troubleshooting & FAQ

### 1. Spider-Man isn't responding to clicks!
- **Reason:** Hardware click-through is enabled (`WS_EX_TRANSPARENT`), allowing clicks to pass straight through to background games or apps.
- **Fix:** Press **`Ctrl + Alt + W`** to toggle interaction mode, or right-click the Spider-Man tray icon (near the clock) and click **Open Dashboard**.

### 2. Can I change Spider-Man's screen corner or size?
- Yes! Open the Dashboard, switch to **Settings**, and adjust the corner position (Top-Right, Top-Left, Bottom-Right, Bottom-Left) and character scale.

### 3. How do I build standalone executables?
- Install build dependencies via `pip install -r requirements-dev.txt`, then run:
  ```powershell
  python scripts/build_dist.py
  ```
  The packaged installer will be generated in `dist/SpiderManWaterBuddy-v2.0.0-Setup.exe`.

---

## ⚖️ Legal & Trademark Notice

**"Spider-Man"**, character names, likeness, and related indicia are trademarks and copyright of Marvel Characters, Inc., Marvel Entertainment, LLC, and The Walt Disney Company.

This project is an unofficial, non-commercial, open-source fan project created solely for personal productivity and educational purposes. It is not affiliated with, endorsed by, sponsored by, or authorized by Marvel Entertainment, Disney, Sony Pictures, or any of their respective affiliates.
