# 🕸️ Spider-Man Water Buddy — V2.0 Requirements Analysis & Specification

**Date:** 2026-10-23  
**Document Reference:** `spider_man_water_buddy_v2_0_plan.md`  
**Target Version:** v2.0.0 Desktop  
**Status:** Complete  

---

## 1. Executive Summary & V2.0 Core Objectives

The Spider-Man Water Buddy v2.0 upgrade addresses foundational state-machine, timing, and persistence defects from v1.0, while introducing a professional, distinctive character experience:
1. **State Machine & Persistence Hardening:** Eliminates stats corruption, midnight bleed, and race conditions.
2. **Authoritative Manual Water Logging:** Introduces a manual log mechanism with a strictly enforced backend 30-minute cooldown (resilient to reboots, sleeps, and clock manipulations).
3. **First-Class Streak Tracking System:** Gamifies daily hydration goals with historical retention and goal day credits.
4. **Cinematic Character Motion & Tactical HUD UI:** Replaces generic SaaS gradients with an authentic comic-tech aesthetic (Stark Tech / EDITH HUD), including wide horizontal web swings, fluid physics, and victory celebrations.
5. **Robust Packaging & Native Windows Integration:** Guarantees single-instance stability via Windows Named Mutex, global hotkeys, high-DPI scaling, and multi-monitor resilience.

---

## 2. Structured Functional Breakdown

### 2.1 Existing Features to Retain (Non-Negotiable)
- **Frameless Transparent Desktop Companion:** Spider-Man hanging upside down with pendulum web-swing physics, eye tracking, and speech dialogue.
- **Configurable Reminder Scheduling:** Regular recurring intervals (15–120 minutes), quiet hours, and pause/resume modes.
- **Interactive Snooze & Decline Flow:** Multi-tier snooze options (5, 10, 15, 30 min) and friendly retry intervals upon decline.
- **Desktop Click-Through & Window Dragging:** Toggleable click-through overlay mode with desktop positioning.
- **System Tray Integration:** Quick access to dashboard, reminder toggle, sound toggle, and instant water logging.
- **Zero-Dependency Core / Standalone Windows Operation:** No external cloud services, web servers, or electron bloat; pure Python + PySide6.

### 2.2 New V2.0 Features
- **"YES, I DRANK 💧" Manual Logging Action:**
  - Can be triggered anytime from Dashboard, Tray, or Companion.
  - Adds configured intake amount (default 250 ml; selectable chips 150/250/350/500 ml).
  - Hard minimum cooldown of **30 minutes** (configurable upwards to 45/60/90 min, never below 30 min).
  - Backend-first validation with monotonic clock, wall-clock, and OS boot ID tracking.
- **Streak & Hydration Achievement Engine:**
  - Evaluates consecutive days where intake reaches or exceeds daily goal (default 2,000 ml).
  - Tracks `streak_current`, `streak_best`, `last_goal_date`, and total goal days.
  - One streak credit per calendar day; midnight rollover evaluates streak continuity.
  - Milestone celebrations at 3, 7, 14, 30, and 100 days.
  - Optional Web Shield mechanism (1 shield per 7 days forgiving a missed day).
- **Cinematic 4-Phase Character Animation Engine:**
  - **Phase 1 (Anticipation):** Subtle crouch and web-shoot gesture.
  - **Phase 2 (Wide Horizontal Swing):** Wide sinusoidal arc across the overlay with acceleration and deceleration.
  - **Phase 3 (Victory Celebration):** Energetic celebratory dance / thumbs-up pose with particle effect.
  - **Phase 4 (Smooth Recovery):** Natural damping recovery back to resting pendulum idle.
  - **Expressive Disappointment Reaction:** Gentle head/body slump upon clicking "No / Not Yet".
- **Stark Tech EDITH HUD & Modern Typography:**
  - High-contrast pitch-black (`#050811`), tactical laser lines (`#00E5FF` / `#FFFFFF`), and circular gauge reticle.
  - High-legibility system fonts (Segoe UI, Cascadia Code) with tabular numerals preventing countdown jitter.

### 2.3 Changes to Existing Functionality
- **Split Logging Architecture:** Replaced single insecure entry point with `log_from_reminder(amount)` (state-guarded) and `log_manual(amount)` (cooldown-guarded).
- **Multi-Generation Rotating Backups:** Upgraded single `.bak` file to rotating generational backups (`settings.bak.1`, `settings.bak.2`, `settings.bak.3`) with corrupt file quarantine.
- **Global Win32 Hotkey Registration:** Migrated from focus-bound `QShortcut` to native `RegisterHotKey` in `QAbstractNativeEventFilter`.
- **Pre-Qt Single-Instance Named Mutex:** Mutex is acquired in `run.py` before `QApplication` instantiation to prevent process launch collisions.

---

## 3. Data Model & Storage Specifications

### 3.1 Extended Settings Schema (`AppSettings`)
```python
@dataclass
class AppSettings:
    # Hydration Goals & Intake
    daily_goal_ml: int = 2000
    drink_amount_ml: int = 250
    today_intake_ml: int = 0
    today_manual_logs: int = 0
    today_reminders_completed: int = 0
    last_log_date: str = ""                # ISO YYYY-MM-DD
    
    # Cooldown & Clock Integrity
    cooldown_minutes: int = 30              # Minimum clamped to 30
    last_log_wall_utc: float = 0.0          # Time of last log (UTC epoch seconds)
    last_log_mono: float = 0.0              # Monotonic time of last log
    boot_id: str = ""                       # Unique identifier for OS boot session
    
    # Streak Engine
    streak_current: int = 0
    streak_best: int = 0
    last_goal_date: str = ""
    goal_days_total: int = 0
    shield_available: bool = False
    shield_last_used: str = ""
    daily_history: Dict[str, Dict] = field(default_factory=dict)
    
    # UI, Theme, & Motion
    theme_mode: str = "edith_hud"           # edith_hud / obsidian / liquid_glass
    animation_enabled: bool = True
    performance_mode: bool = False
    character_scale: float = 1.0            # 0.75 to 1.5
    anchor_corner: str = "TOP_RIGHT"
    offset_x: int = 24
    offset_y: int = 24
```

### 3.2 Atomic Write Protocol
1. Format payload to UTF-8 JSON.
2. Write to temporary file (`settings.json.tmp.<pid>`).
3. Flush and call `os.fsync()` to ensure disk commitment.
4. Rotate existing valid `settings.json` into generational backup ring.
5. Atomically rename temporary file onto `settings.json` via `os.replace()`.
6. On JSON decode exception during load: quarantine damaged file to `settings.json.corrupt.<timestamp>` and roll back to newest valid backup.

---

## 4. Requirements Traceability Matrix

| Requirement ID | Specification Area | Target Module | Verification / Acceptance Criteria |
|---|---|---|---|
| **REQ-MAN-01** | Manual Log Trigger | `src/streak_tracker.py`, `src/dashboard_window.py` | First click accepts +250ml immediately. |
| **REQ-MAN-02** | Cooldown Enforcement | `src/streak_tracker.py` | Subsequent click within 30 min returns `ok=False`, `reason="cooldown"`. |
| **REQ-MAN-03** | Clock Tampering Resilience | `src/streak_tracker.py` | System clock rollback does not extend cooldown past configured limit. |
| **REQ-MAN-04** | Reboot / Sleep Handling | `src/streak_tracker.py`, `src/windows_native.py` | Cooldown persists across app restart and sleep resume. |
| **REQ-STRK-01**| Daily Streak Evaluation | `src/streak_tracker.py` | Crossing daily goal increments streak; maximum 1 credit per calendar day. |
| **REQ-STRK-02**| Streak Break Rollover | `src/streak_tracker.py` | Missed day resets current streak to 0 while preserving `streak_best`. |
| **REQ-ANIM-01**| Wide Web Swing | `src/character.py` | 4-phase animation completes smoothly with no layout jitter or window clipping. |
| **REQ-ANIM-02**| Disappointment Reaction | `src/character.py` | Clicking "No" triggers slump reaction without recording water intake. |
| **REQ-HUD-01** | EDITH HUD Theme | `src/theme.py`, `src/components/` | Pitch black background, crisp typography, circular reticle widget. |
| **REQ-MUTEX-01**| Named Mutex Single Instance | `run.py`, `src/windows_native.py` | Fast double-launch terminates second instance and activates primary. |
| **REQ-HOTKEY-01**| Native Global Hotkey | `src/windows_native.py`, `src/app.py` | `Ctrl+Alt+W` activates reminder regardless of window focus. |

---

## 5. Ambiguities & Edge-Case Decisions

1. **Manual Logging During Active Reminder Display:**  
   *Decision:* Manual log is permitted while a reminder is showing. A successful manual log also completes and dismisses the active reminder, avoiding double-prompts.
2. **Custom Intake Amounts Cooldown Policy:**  
   *Decision:* The 30-minute cooldown applies globally to the manual action regardless of selected amount (150, 250, 350, or 500 ml).
3. **Web Shield Scope:**  
   *Decision:* Web shield logic is fully architected in `StreakTracker` and disabled by default, available as an optional toggle in Diagnostics/Settings.
4. **Font Fallback Strategy:**  
   *Decision:* System fonts Segoe UI and Cascadia Code are prioritized with fallback to sans-serif / monospace. Nested font-family quotes in QSS are eliminated to ensure zero tofu boxes (□□□).

---
*Requirements Analysis approved for implementation planning.*
