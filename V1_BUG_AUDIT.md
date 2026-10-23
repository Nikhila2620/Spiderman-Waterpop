# 🕷️ Spider-Man Water Buddy — V1.0 Bug Audit & Codebase Assessment

**Date:** 2026-10-23  
**Auditor:** Senior Software Engineer & Security Auditor  
**Target Codebase:** Spider-Man Water Buddy v1.0.0 Baseline (Git commit `8700a13` / `9e262c4`)  
**Status:** Audit Complete — All Findings Verified in Code and Test Fixtures  

---

## 1. Project Architecture & Technical Profile

| Component | Specification |
|---|---|
| **Primary Language** | Python 3.11+ |
| **GUI Framework** | PySide6 6.7+ (Qt for Python / QtCore, QtGui, QtWidgets, QtNetwork) |
| **Native Integration** | Windows Win32 API via `ctypes` (`user32.dll`, `kernel32.dll`), Windows Named Mutex, Registry (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`) |
| **Entry Point** | `run.py` (executes `src/app.py:SpiderManWaterBuddyApp`) |
| **Data Storage** | Local atomic JSON at `%APPDATA%\SpiderManWaterBuddy\settings.json` + `settings.bak` |
| **Logging** | Rotating file handler at `%APPDATA%\SpiderManWaterBuddy\logs\app.log` (1 MB max, 3 backups) |
| **Packaging & Build** | PyInstaller 6.6+ via `scripts/build_dist.py` with standalone and installer specs |
| **Test Framework** | `pytest` 8.0+ / `pytest-qt` |

### Core Modules Directory Structure
- `run.py`: Application launcher, mutex acquisition, exception logging, and splash/bootstrap.
- `src/app.py`: Application lifecycle orchestrator, QLocalServer single-instance management, tray icon, hotkey wiring, and window coordination.
- `src/config.py`: `AppSettings` dataclass, JSON persistence, validation, and backup recovery.
- `src/reminder_engine.py`: State machine (`ReminderState`), 1-second QTimer heartbeat, quiet hours logic, and hydration statistics.
- `src/companion_window.py`: Frameless, transparent, always-on-top companion overlay (`SpideyCompanionWindow`) with web-swing pendulum canvas and speech bubble dialogue.
- `src/character.py`: `SpideyWidget` character rendering, pendulum angle physics, sprite drawing, and eye tracking.
- `src/dashboard_window.py`: Main settings, telemetry, schedule tuning, and history viewer.
- `src/installer_gui.py` & `src/uninstaller_gui.py`: Setup and teardown wizards with desktop shortcut creation and startup registration.
- `src/startup_manager.py`: Windows registry autorun manager.
- `src/windows_native.py`: Win32 native event filter (`WM_HOTKEY`, `WM_POWERBROADCAST`), Named Mutex guard, and DPI awareness.
- `src/popup.py`: Deprecated legacy notification dialog (381 lines of dead code).

---

## 2. Bug Register & Detailed Findings

Findings are categorized and assigned unique IDs matching the project specification:
- **Critical (CRIT)**: Data corruption, race conditions, or complete workflow breakdown.
- **High (HIGH)**: State desynchronization, silent data loss, or calculation drift.
- **Medium (MED)**: UI/UX state disconnects, hotkey capture failures, layout drift.
- **Low / Cleanup (CLEAN / NEW)**: Dead code, build pipeline gaps, configuration hygiene.
- **Security (SEC)**: Path traversal, file locks, privilege/sandbox integrity.

---

### 2.1 Critical Severity (CRIT)

#### [CRIT-01] State Guard in `reminder_engine.py` is a `pass` Statement
- **Module & Line:** `src/reminder_engine.py` (`on_user_drank_water()`)
- **Severity:** Critical
- **Status:** CONFIRMED in baseline `8700a13`
- **Description:** In the reminder response handler, the state check `if self.state != ReminderState.WAITING_FOR_RESPONSE:` had a no-op `pass` block instead of returning or validating state. As a result, intake could be logged from any arbitrary state (such as during quiet hours or paused state) without validation.
- **Steps to Reproduce:**
  1. Trigger `engine.on_user_drank_water(250)` while `engine.state == ReminderState.PAUSED` or `IDLE`.
  2. Observe `today_intake_ml` increments regardless of state.
- **Expected vs Actual Behavior:**
  - *Expected:* Reminder-driven hydration should only register when an active reminder or snooze is pending.
  - *Actual:* Any external trigger increments water intake indiscriminately.
- **Proposed Fix:** Split hydration logging into two explicit pathways: `log_from_reminder()` (strictly validated against `WAITING_FOR_RESPONSE` or `SNOOZED`) and `log_manual()` (governed by an authoritative cooldown timer).
- **Verification Method:** Unit test verifying `log_from_reminder()` raises or returns false when state is `IDLE`.

---

#### [CRIT-02] Drink Amount Hardcoded to 250 ml in `app.py`
- **Module & Line:** `src/app.py:157` (`_setup_signals()`)
- **Severity:** Critical
- **Status:** CONFIRMED in baseline `8700a13`
- **Description:** The signal connection was hardcoded as:
  `self.companion.waterDrank.connect(lambda: self.engine.on_user_drank_water(250))`
  Users with custom glass/bottle capacities (e.g. 150ml, 350ml, 500ml) could not have their configured `drink_amount_ml` honored.
- **Steps to Reproduce:**
  1. Change `drink_amount_ml` in settings to 500 ml.
  2. Click "Yes, I drank" in companion.
  3. Notice only 250 ml is credited in `today_intake_ml`.
- **Expected vs Actual Behavior:**
  - *Expected:* Uses `self.settings.drink_amount_ml` dynamically or accepts amount payload from signal.
  - *Actual:* Hardcoded `250` ml passed via lambda.
- **Proposed Fix:** Pass dynamic intake capacity from `self.settings.drink_amount_ml` or support parameterized amount chips (150/250/350/500 ml).
- **Verification Method:** Pytest setting `drink_amount_ml = 350` and asserting `today_intake_ml == 350`.

---

#### [CRIT-03] Companion Window Rejection / Dismiss Freezes Reminder Engine in `WAITING`
- **Module & Line:** `src/companion_window.py` & `src/reminder_engine.py`
- **Severity:** Critical
- **Status:** CONFIRMED in baseline `8700a13`
- **Description:** When the user closes the companion dialog via window close (X) or if the dialogue times out without explicit snooze selection, the engine remains in `ReminderState.WAITING_FOR_RESPONSE`. While stuck in this state, recurring interval timers never reschedule, freezing hydration alerts indefinitely.
- **Steps to Reproduce:**
  1. Wait for reminder to appear (`WAITING_FOR_RESPONSE`).
  2. Click close (X) on window or allow auto-close to expire without clicking Yes/No/Snooze.
  3. Check `engine.state`.
- **Expected vs Actual Behavior:**
  - *Expected:* Auto-close or dismiss transitions engine to `RETRY_SCHEDULED` or reschedules next interval.
  - *Actual:* Engine stays stuck in `WAITING_FOR_RESPONSE`, halting future reminders.
- **Proposed Fix:** Connect companion `dismissed` signal to `engine.on_user_declined()` or a dedicated fallback reschedule method.
- **Verification Method:** Simulate companion dismissal and verify engine transitions to `RETRY_SCHEDULED` with a positive countdown target.

---

#### [CRIT-04] "Remind Me Now" Fails Silently If Reminder Is Already Showing
- **Module & Line:** `src/reminder_engine.py:trigger_now()`
- **Severity:** Critical
- **Status:** CONFIRMED in baseline `8700a13`
- **Description:** Calling manual reminder trigger when the companion is already rendered returns early without refocusing the window or giving user feedback.
- **Steps to Reproduce:**
  1. Trigger reminder.
  2. From Dashboard or Tray, click "Remind Me Now".
  3. Companion is obscured behind full-screen window; nothing happens.
- **Expected vs Actual Behavior:**
  - *Expected:* Shake or flash companion window, bring it to front, and play audio prompt.
  - *Actual:* Silent no-op.
- **Proposed Fix:** In `trigger_now()`, if companion is already active, call `companion.raise_()`, `companion.activateWindow()`, and trigger Spidey attention wiggle.
- **Verification Method:** Test calling `trigger_now()` when companion is visible raises companion.

---

#### [CRIT-05] Single-Instance Socket Race on Fast Double Launch
- **Module & Line:** `src/app.py:_check_single_instance()`
- **Severity:** Critical
- **Status:** CONFIRMED in baseline `8700a13`
- **Description:** V1.0 relied solely on `QLocalServer` / `QLocalSocket`. When two instances are launched in rapid succession (e.g., fast double-click on `.exe`), both can execute `socket.connectToServer()` before either has finished calling `server.listen()`. Both instances believe they are the primary instance, leading to dual tray icons, conflicting JSON writes, and duplicate reminders.
- **Steps to Reproduce:**
  1. Execute two instances of `python run.py` simultaneously within 5ms.
  2. Both processes acquire distinct local sockets and run concurrently.
- **Expected vs Actual Behavior:**
  - *Expected:* OS-level mutual exclusion guarantees exactly one process runs.
  - *Actual:* Multiple active GUI processes conflicting on `settings.json`.
- **Proposed Fix:** Pre-empt Qt initialization in `run.py` by acquiring a Win32 Kernel Named Mutex (`CreateMutexW(None, False, "Local\\SpiderManWaterBuddy_SingleInstance_Mutex")`). If `GetLastError() == ERROR_ALREADY_EXISTS`, immediately forward the `ACTIVATE` message to `QLocalSocket` and terminate.
- **Verification Method:** Concurrent process launch test validating only 1 PID persists.

---

### 2.2 High Severity (HIGH)

#### [HIGH-01] Daily Hydration Stats Bleed Across Midnight After Sleep/Wake
- **Module & Line:** `src/reminder_engine.py:_check_daily_date_reset()`
- **Severity:** High
- **Status:** CONFIRMED in baseline `8700a13`
- **Description:** The date rollover check only checked `if now.date() > self.last_recorded_date`. If a user put their computer to sleep on Friday at 23:30 and resumed Saturday at 08:00, the 1-second QTimer tick would execute after wake, but if a log was queued during resume, stats could be written with the previous date's stamp. Furthermore, historical daily totals were overwritten rather than archived.
- **Steps to Reproduce:**
  1. Set system clock past midnight or simulate sleep resume.
  2. Check `today_intake_ml` persistence.
- **Expected vs Actual Behavior:**
  - *Expected:* Clean rollover to 0 ml at local midnight, archiving previous day to history.
  - *Actual:* Stats can retain yesterday's intake until next heartbeat or trigger.
- **Proposed Fix:** Authoritative midnight roll check on heartbeat, sleep resume (`WM_POWERBROADCAST`), and before every read/write.
- **Verification Method:** Fake clock jump past midnight verifying intake rolls to 0 and history record is created.

---

#### [HIGH-02] Manual Triggers Inflate `today_reminders_completed`
- **Module & Line:** `src/reminder_engine.py:on_user_drank_water()`
- **Severity:** High
- **Status:** CONFIRMED in baseline `8700a13`
- **Description:** `today_reminders_completed` was incremented every time water was logged, regardless of whether it came from a scheduled reminder or a manual dashboard button. This distorted compliance telemetry (e.g. 15 completed reminders when only 6 were scheduled).
- **Proposed Fix:** Separate `today_reminders_completed` from `today_manual_logs`.
- **Verification Method:** Manual log increments `today_manual_logs` and leaves `today_reminders_completed` unchanged.

---

#### [HIGH-03] Corrupted Settings File Silently Resets to Defaults
- **Module & Line:** `src/config.py:load()`
- **Severity:** High
- **Status:** CONFIRMED in baseline `8700a13`
- **Description:** If `settings.json` encountered a `JSONDecodeError` and `settings.bak` was also invalid, the method silently instantiated `AppSettings()`, called `self.save()`, and completely destroyed the user's custom settings and historical records without notification or quarantining the broken file.
- **Proposed Fix:** Quarantine corrupted file to `settings.json.corrupt.<timestamp>`, attempt recovery from rotating backups, and alert the user with a diagnostic notice.
- **Verification Method:** Corrupt `settings.json` with malformed JSON; verify backup is preserved and corrupt file is quarantined.

---

#### [HIGH-04] Single Backup File Overwritten Immediately After Restore
- **Module & Line:** `src/config.py:load()` and `save()`
- **Severity:** High
- **Status:** CONFIRMED in baseline `8700a13`
- **Description:** When `load()` successfully recovered from `settings.bak`, it immediately invoked `self.save()`. In `save()`, `shutil.copy2(self.settings_file, self.backup_file)` executed, meaning if an error occurred during subsequent writes, the backup was overwritten with partial or unverified data.
- **Proposed Fix:** Maintain an N-generation rotating backup queue (`settings.bak.1`, `settings.bak.2`, `settings.bak.3`) with CRC/size validation.
- **Verification Method:** Multiple successive corruptions recover from secondary backup generations.

---

### 2.3 Medium Severity (MED)

#### [MED-01] Tray Menu Displays "Hide Companion" When Window Was Closed via X
- **Module & Line:** `src/app.py:_update_tray_menu()`
- **Severity:** Medium
- **Status:** CONFIRMED
- **Description:** Tray action text is not synchronized with the companion window's `closeEvent` / `hideEvent`.
- **Proposed Fix:** Connect companion `visibilityChanged` signal directly to tray action text update.

#### [MED-02] `app.py` Directly Accesses Private Companion Attributes
- **Module & Line:** `src/app.py:168`
- **Severity:** Medium
- **Status:** CONFIRMED
- **Description:** `app.py` called `self.companion._in_reminder_mode` and `self.companion._on_auto_close()`, violating module encapsulation.
- **Proposed Fix:** Expose public API methods `is_reminder_active()` and `dismiss_reminder()`.

#### [MED-03] `Ctrl+Alt+W` Hotkey Only Works When App Has Window Focus
- **Module & Line:** `src/app.py:_setup_shortcuts()`
- **Severity:** Medium
- **Status:** CONFIRMED
- **Description:** V1.0 configured hotkeys using `QShortcut(QKeySequence("Ctrl+Alt+W"), self.companion)`. Qt shortcuts only trigger when a top-level window has active desktop keyboard focus. A user playing a game or typing in Word could not toggle or trigger reminders.
- **Proposed Fix:** Register global hotkey via Win32 `RegisterHotKey(hWnd, HOTKEY_ID, MOD_CONTROL | MOD_ALT, 'W')` within a `QAbstractNativeEventFilter`.

#### [MED-04] Dragged Companion Screen Position Lost on Settings Change or Screen Resize
- **Module & Line:** `src/companion_window.py:mouseReleaseEvent()`
- **Severity:** Medium
- **Status:** CONFIRMED
- **Description:** Dragged X/Y coordinates were saved as absolute pixels. On multi-monitor setups or DPI changes, the window was clipped or repositioned to default top-right corner.
- **Proposed Fix:** Store position as normalized corner offsets (e.g. `anchor_corner = "TOP_RIGHT"`, `offset_x = 24`, `offset_y = 24`) and clamp against active screen `availableGeometry()`.

#### [MED-05] Auto-Close Timer Keeps Running After User Dismisses Notification
- **Module & Line:** `src/companion_window.py`
- **Severity:** Medium
- **Status:** CONFIRMED
- **Description:** `_auto_close_timer` was not explicitly stopped on button click, potentially firing a late auto-dismiss during user interaction.
- **Proposed Fix:** Stop `_auto_close_timer.stop()` immediately at the start of any response handler.

---

### 2.4 Security & Packaging Findings (SEC / NEW)

#### [SEC-01] Potential Zip Path Traversal in Installer Payload Extraction
- **Module & Line:** `src/installer_gui.py:extract_payload()`
- **Severity:** High (Security)
- **Status:** CONFIRMED in early v1.0, hardened in v1.0-patch
- **Description:** `ZipFile.extractall()` without path sanitization allows maliciously crafted zip archives containing `../../` entries to overwrite arbitrary system files.
- **Proposed Fix:** Implement `_safe_extract()` verifying `os.path.commonpath([target_dir, extracted_path]) == target_dir`.

#### [SEC-02] Uninstaller File Lock and Self-Deletion Race
- **Module & Line:** `src/uninstaller_gui.py`
- **Severity:** Medium
- **Status:** CONFIRMED
- **Description:** When uninstaller attempts to remove its own directory while running, Windows file locking raises `PermissionError (WinError 32)`.
- **Proposed Fix:** Spawn a detached batch cleaner via `cmd.exe /c timeout 2 & rmdir /s /q ...` and exit immediately.

#### [NEW-01 to NEW-10] Configuration, Dependency, and Asset Gaps
- **NEW-01:** Version string `v1.0.0` hardcoded across batch files, README, and specs. -> Centralized in `src/version.py`.
- **NEW-02:** `dist/` gitignored, causing fresh clones to fail install. -> Automated build scripts added.
- **NEW-06:** `run.py` missing pre-Qt mutex check. -> Added `NamedMutexGuard`.
- **NEW-07:** `pytest-qt` missing from requirements. -> Added to `requirements-dev.txt`.
- **NEW-09:** Asset resolution used `Path(__file__)`, failing in PyInstaller one-dir mode. -> Added `resource_path()` supporting `sys._MEIPASS`.

---

## 3. Bug Classification Summary Matrix

| ID | Module | Title | Severity | Status |
|---|---|---|---|---|
| **CRIT-01** | `reminder_engine.py` | State guard pass allows hydration logging anywhere | Critical | CONFIRMED |
| **CRIT-02** | `app.py` | Drink amount hardcoded to 250 ml | Critical | CONFIRMED |
| **CRIT-03** | `companion_window.py` | Window close/dismiss freezes engine in WAITING | Critical | CONFIRMED |
| **CRIT-04** | `reminder_engine.py` | Remind Me Now silent failure during active display | Critical | CONFIRMED |
| **CRIT-05** | `app.py` / `run.py` | Single-instance socket race on fast double-launch | Critical | CONFIRMED |
| **HIGH-01** | `reminder_engine.py` | Stats bleed across midnight / sleep resume | High | CONFIRMED |
| **HIGH-02** | `reminder_engine.py` | Manual logging distorts reminder compliance metrics | High | CONFIRMED |
| **HIGH-03** | `config.py` | Corrupted JSON resets silently with data loss | High | CONFIRMED |
| **HIGH-04** | `config.py` | Single backup file overwritten right after restore | High | CONFIRMED |
| **MED-01** | `app.py` | Tray menu out-of-sync with companion close | Medium | CONFIRMED |
| **MED-02** | `app.py` | Direct access to companion private state | Medium | CONFIRMED |
| **MED-03** | `app.py` | Non-global Ctrl+Alt+W hotkey | Medium | CONFIRMED |
| **MED-04** | `companion_window.py` | Position lost on DPI / multi-monitor changes | Medium | CONFIRMED |
| **MED-05** | `companion_window.py` | Dangling auto-close timer on response | Medium | CONFIRMED |
| **SEC-01** | `installer_gui.py` | Zip path traversal protection | High (Sec) | CONFIRMED |
| **SEC-02** | `uninstaller_gui.py`| File lock on self-deletion | Medium | CONFIRMED |
| **CLEAN-01**| `popup.py` | 381 lines of dead legacy popup code | Low | CONFIRMED |

---
*Report generated and verified against local repository state.*
