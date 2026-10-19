# 🕸️ Spider-Man Water Buddy — v2.0 Plan

> "With great hydration comes great productivity."

**Status:** Draft, written without access to `src/`.  
**Verification legend:** ✅ Confirmed in visible files · 🟡 Reported in tracker, not yet verified in code · ⬜ Not started · ☑ Done

---

## 1. Goals of v2.0

1. Fix the state-machine and persistence bugs that corrupt hydration stats.
2. Add manual water logging with a hard 30-minute cooldown.
3. Add a first-class Streak system.
4. Replace the dashboard look with a distinctive, restrained design.
5. Ship with a real test suite and a clean, versioned build.

Non-goals: rewriting the app, adding a web server, adding Electron-style background processes.

---

## 2. Bug Register

### 2.1 Critical

| ID | Problem | Source | Status |
|---|---|---|---|
| CRIT-01 | State guard in `reminder_engine.py:184` is a `pass`, so hydration can be logged in any state | Tracker | 🟡 ⬜ |
| CRIT-02 | Drink amount hardcoded to 250 ml (`app.py:157`) | Tracker | 🟡 ⬜ |
| CRIT-03 | Clicking NO never notifies the engine, which freezes in `WAITING` | Tracker | 🟡 ⬜ |
| CRIT-04 | "Remind Me Now" fails silently if a reminder is already showing | Tracker | 🟡 ⬜ |
| CRIT-05 | Single-instance socket race on fast double launch (`app.py:70`) | Tracker | 🟡 ⬜ |

**Design conflict to resolve before fixing CRIT-01.** The tracker's fix only allows logging in `REMINDER_ACTIVE` or `SNOOZED`. The manual button (Section 3) must work at any time. Resolution: split logging into two entry points.

- `log_from_reminder(amount)` validates engine state.
- `log_manual(amount)` bypasses the state check but enforces the cooldown.

Both write through the same single persistence function.

### 2.2 High

| ID | Problem | Source | Status |
|---|---|---|---|
| HIGH-01 | Stats bleed across midnight after sleep/wake (`reminder_engine.py:55`) | Tracker | 🟡 ⬜ |
| HIGH-02 | Manual triggers inflate `today_reminders_completed` | Tracker | 🟡 ⬜ |
| HIGH-03 | Corrupt config silently resets to defaults (`config.py:158`) | Tracker | 🟡 ⬜ |
| HIGH-04 | Single backup file is overwritten right after restore (`config.py:216`) | Tracker | 🟡 ⬜ |

### 2.3 Medium

| ID | Problem | Source | Status |
|---|---|---|---|
| MED-01 | Tray says "Hide Companion" after the window was closed with X | Tracker | 🟡 ⬜ |
| MED-02 | `app.py` reads private `_in_reminder_mode` and calls `_on_auto_close()` | Tracker | 🟡 ⬜ |
| MED-03 | `Ctrl+Alt+W` only works with window focus | Tracker | 🟡 ⬜ |
| MED-04 | Dragged position is lost on reposition or settings change | Tracker | 🟡 ⬜ |
| MED-05 | Auto-close timer keeps running after dismiss | Tracker | 🟡 ⬜ |

### 2.4 Low / Cleanup

| ID | Problem | Source | Status |
|---|---|---|---|
| CLEAN-01 | Delete dead `popup.py` (381 lines) | Tracker | 🟡 ⬜ |
| CLEAN-02 | `sound_effects_enabled` is unused | Tracker | 🟡 ⬜ |
| CLEAN-03 | `mouse_follow_enabled` is unused | Tracker | 🟡 ⬜ |
| CLEAN-04 | `character_scale` is unused | Tracker | 🟡 ⬜ |
| CLEAN-05 | `daily_active_hours` is not enforced | Tracker | 🟡 ⬜ |
| CLEAN-06 | Dead variable `_previous_click_through` | Tracker | 🟡 ⬜ |

### 2.5 Additional problems found in visible files

| ID | Problem | Fix | Status |
|---|---|---|---|
| NEW-01 | `v1.0.0` is hardcoded in `INSTALL_APP.bat`, README and build outputs | One `VERSION` constant, read by the build script, bat files and About screen | ✅ ⬜ |
| NEW-02 | `dist/` is gitignored, so `INSTALL_APP.bat` fails on a fresh clone | Download from GitHub Releases, or call `scripts/build_dist.py` first | ✅ ⬜ |
| NEW-03 | README presents `Ctrl+Alt+W` as global, which conflicts with MED-03 | Fix MED-03, then keep README wording | ✅ ⬜ |
| NEW-04 | README performance numbers have no stated method | Add measurement method and machine specs, or remove | ✅ ⬜ |
| NEW-05 | Unhandled exceptions are logged but invisible to the user | Show one small "Something went wrong. Open log" dialog; keep the app alive when safe | ✅ ⬜ |
| NEW-06 | `run.py` has no single-instance guard of its own | Acquire the lock before building any window (ties to CRIT-05) | ✅ ⬜ |
| NEW-07 | `pytest-qt` missing from `requirements-dev.txt` | Add it | ✅ ⬜ |
| NEW-08 | Pillow is a runtime dependency; may be unused | Audit imports; drop it if unused (smaller installer) | ✅ ⬜ |
| NEW-09 | Icon and asset lookup uses `Path(__file__)` | Add a `resource_path()` helper that handles `sys._MEIPASS` | ✅ ⬜ |
| NEW-10 | `setOrganizationName("Antigravity")` affects `QSettings` location | Freeze the value, or confirm nothing uses `QSettings` | ✅ ⬜ |

---

## 3. Feature: Manual Water Log ("YES, I DRANK 💧")

### 3.1 Rules

- Button label: **YES, I DRANK 💧**.
- Each valid click adds exactly **250 ml** (v1.1 behaviour; see 3.6 for v2.0 chips).
- Cooldown between successful logs: **30 minutes by default; the minimum is 30**.
- First entry is allowed immediately, including right after first install.
- Daily goal stays **2,000 ml**. Daily total resets at **local midnight**.
- The cooldown is **independent of the daily reset**. A log at 23:50 still blocks a click at 00:05.

### 3.2 Backend-first validation

The UI is never the gatekeeper. One function owns the decision:

```text
log_water(amount=250) -> LogResult(ok, added_ml, reason, remaining_seconds)
```

Steps, all inside one lock:

1. Normalize the current day (local date). If it changed, roll the daily total over.
2. Compute `remaining` from the stored last-success data (see 3.3).
3. If `remaining > 0`: return `ok=False, reason="cooldown", remaining_seconds=remaining`. Nothing is written.
4. Add 250 ml, set the new last-success stamp, evaluate streak (Section 4).
5. Persist everything in one atomic write (3.4).
6. Emit a single `intake_changed` signal. All UI listens to that signal only.

Because the lock covers steps 1–6, a rapid double-click, a keyboard shortcut and a tray action racing each other produce exactly one success.

### 3.3 Cooldown across restarts, sleep and clock changes

Store with each successful log:

- `last_log_wall_utc` (UTC wall-clock timestamp)
- `last_log_mono` (monotonic reading)
- `boot_id` (identifies the current system boot, for example boot time rounded)

Remaining-time rules:

| Situation | How remaining is computed |
|---|---|
| Same app run, same boot | `cooldown - (mono_now - last_log_mono)`. Monotonic is immune to clock edits. |
| App restarted, same boot | Same monotonic rule if the stored `boot_id` matches. |
| New boot (monotonic reset) | Use wall clock: `cooldown - (wall_now - last_log_wall_utc)`. |
| Sleep / hibernate | Wall clock is authoritative after resume. Monotonic may pause during sleep on some systems, so take the **smaller** of the two remaining values only when both are trustworthy; otherwise trust wall clock. |
| Wall clock moved backwards | Elapsed would be negative. Clamp elapsed to `0` and do not extend the cooldown beyond the configured value. |
| Wall clock moved far forward | Treat as time passing. Accepted limitation; log a warning if the jump exceeds 24 h. |
| Corrupt or missing stamp | Treat as no previous log, and log a warning. |

Never lock a user out for more than the configured cooldown. Whatever happens, `remaining <= cooldown`.

### 3.4 Atomic persistence

- Write the full state to `data.json.tmp`, call `flush()` and `os.fsync()`, then `os.replace()` onto `data.json`.
- Keep the last N versions as rotating backups (also fixes HIGH-04).
- On load failure: rename the bad file to `data.json.corrupt.<timestamp>`, log it, show a notice, and restore from the newest valid backup. Never silently reset (also fixes HIGH-03).

### 3.5 UI behaviour

- States: **Ready**, **Cooling down**, **Just logged** (a one-second success state).
- Countdown text: `Next water log in 29:59`, updated by **one** shared 1-second timer. It does not create a second timer. Reuse the engine's existing tick if there is one.
- The countdown shows the *backend's* remaining value, not its own counter, so it cannot drift.
- Re-enables itself at zero even if the dashboard stays open.
- Success toast: `Awesome! +250 ml logged 🕷️`.
- Early-click rejection: `Easy there, hero. Next sip in 12:41` (no water added).
- The same button state appears on the dashboard, the tray menu item and the companion overlay, all fed by `intake_changed`.
- Keyboard: Enter/Space on the focused button goes through the same `log_water()`. Auto-repeat key events are ignored.

### 3.6 Settings

- `cooldown_minutes`, default `30`, **hard minimum 30**.
- Values below 30 are clamped to 30 on save *and* on load, in the backend. A hand-edited config file cannot go below 30.
- Control: a stepper or segmented chips (30 / 45 / 60 / 90 / custom), with a line such as "Minimum 30 min".
- Changing the cooldown applies to the *next* calculation, using the stored last-log stamp. It never refunds an active cooldown.

### 3.7 v2.0 amount chips and the cooldown

The tracker's CRIT-02 adds 150 / 250 / 350 / 500 ml chips. Decision:

- The cooldown applies to **any** manual amount, not per chip.
- The default chip is 250 ml.
- Custom amount is capped (for example 50–1000 ml) and validated in the backend.

---

## 4. Feature: Streak System (new)

### 4.1 Definition

- A day is a **goal day** when its total reaches the daily goal (default 2,000 ml).
- **Streak** = number of consecutive local calendar days that were goal days, ending today or yesterday.
- At most **one streak credit per calendar day**, however many clicks follow.

### 4.2 State stored

```text
streak_current, streak_best, last_goal_date,
goal_days_total, shield_available, shield_last_used
```

Daily history keeps one record per date: `date, total_ml, goal_ml, goal_met, log_count`. Historical records are never deleted at midnight.

### 4.3 Update rules

On the log that moves today's total from below goal to at-or-above goal:

1. If `last_goal_date == today`: do nothing (credit already given).
2. If `last_goal_date == yesterday`: `streak_current += 1`.
3. Else: `streak_current = 1` (a break, unless a shield applies).
4. Set `last_goal_date = today`; update `streak_best`.
5. Emit `streak_changed` with the new value, so the UI updates immediately.

On app start and on every midnight roll: if `last_goal_date` is older than yesterday, show the streak as broken (current = 0) without touching history.

### 4.4 Optional: Web Shield

- One shield per 7 days lets a single missed day be forgiven.
- Shows as a small shield icon beside the streak count.
- Off by default; configurable. It is a v2.1 candidate if scope is tight.

### 4.5 Surfaces

- Dashboard: flame-free streak badge, "7-day streak", best streak beneath it.
- Tray tooltip and icon badge: current streak count.
- Companion: "Suit Upgraded!" animation the moment the goal is reached (once per day).
- Milestones at 3, 7, 14, 30, 100 days give a one-time celebration.

### 4.6 Edge cases to test

Goal reached at 23:59 then more clicks at 00:01 (new day, new total). Clock moved backwards. Two clicks racing over the 2,000 ml boundary. App closed over midnight. Goal changed mid-day (do not retro-revoke today's credit).

---

## 5. UI/UX Direction (not "default AI dashboard")

The usual AI look is purple-blue gradients, blur on every surface, rounded cards everywhere, and emoji as decoration. v2.0 avoids that with a few deliberate choices.

### 5.1 Concept

A **comic-panel night-city** feel: flat, confident panels, one hot accent, and web-line motifs used sparingly. It reads as Spider-Man, not as a SaaS template.

### 5.2 Palette (kept from your tracker, with roles tightened)

| Role | Hex | Use |
|---|---|---|
| Obsidian Night | `#0B0E14` | App background |
| Midnight Panel | `#121824` | Panels (solid in the dashboard) |
| Web Mist stroke | `rgba(255,255,255,0.08)` | 1px borders |
| Crimson Spider | `#FF3355` | **One** primary action per screen, streak badge |
| Web Fluid Blue | `#00D2FF` | Water, progress only |
| Bio-Venom Cyan | `#00F5A0` | Success confirmations only |
| Silk Amber | `#FFB800` | Cooldown, snooze, quiet hours |
| Frost White | `#F3F4F6` | Primary text |
| Stealth Gray | `#9CA3AF` | Secondary text |

Rule: crimson and blue never fill large areas at the same time. Use at most one accent per card.

### 5.3 Where glass is used, and where it is not

- Real backdrop blur is **not** what `QGraphicsBlurEffect` does. It blurs the widget's own content, not what is behind it.
- For true backdrop blur on Windows 10/11, use the DWM acrylic or Mica window attribute on the **companion popup only**.
- The dashboard uses **solid panels** with fine borders. It is faster, sharper and avoids the overused glass look.
- Provide a fallback to a solid panel when acrylic is unavailable (older Windows, remote desktop, power-saving mode).

### 5.4 Layout

- 8 px spacing grid. Corner radius: 14 px panels, 10 px buttons, full pill for the water gauge.
- Dashboard hero: a large **water gauge**, not a progress bar. A tall glass-pill with a wave surface that settles as the level rises.
- Left of the gauge: big numerals for `ml / goal`, `remaining`, `% complete`.
- Beneath: the **YES, I DRANK 💧** button as the single crimson element, with the cooldown ring around or under it.
- Right rail: streak badge, last log time, next reminder.
- Tabs reduce to: **Today · Reminders · Look & Feel · Diagnostics**.

### 5.5 Typography

Bundle two fonts so the look does not depend on what Windows has installed.

- Display numerals and headings: a condensed bold face (for example Bebas Neue or Barlow Condensed).
- Body and UI: a clean grotesque (for example Inter or Space Grotesk).
- Tabular numerals for all countdowns so digits do not jitter.
- Check licences before bundling.

### 5.6 Motion (all under 300 ms except ambient)

| Element | Motion |
|---|---|
| Button hover | 2 px lift, 120 ms ease-out |
| Button press | 0.97 scale, 80 ms |
| Successful log | Water rises in 450 ms with a short overshoot; a subtle ripple from the click point |
| Cooldown ring | Smooth depletion, one update per second |
| Goal reached | Short web-burst behind the gauge, Spider-Man "suit upgraded" pose, once per day |
| Ambient wave | 6–8 s loop, paused when the window is hidden or minimized (keeps idle CPU near 0) |

Respect Windows "reduce animations": if set, skip the overshoot, ripple and burst.

### 5.7 Companion overlay

- Pendulum physics stay. Add damping so it settles instead of swinging forever.
- Eye-lens look-at: limit to a few pixels of travel; update on a throttled timer, not every mouse event.
- The overlay mirrors the button state: a small water-drop above Spider-Man shows Ready vs a clock when cooling down.
- Respect `character_scale` (0.75×–1.5×) and persist the dragged position as an offset from the screen corner (MED-04).

### 5.8 Accessibility

Contrast at least 4.5:1 for body text, visible focus rings, full keyboard navigation, no state conveyed by colour alone (cooldown also shows text), and scalable text for high-DPI.

---

## 6. Other Problems and Better Solutions

| # | Problem | Better solution |
|---|---|---|
| 1 | Reminder timing can drift or double-fire when several `QTimer`s exist | One scheduler object owns every deadline. Use `QTimer` with `Qt.PreciseTimer` plus absolute-time deadlines; recompute after wake. Skip adding `schedule` as a new dependency. Qt timers already cover this. |
| 2 | Sleep/wake handling is ad hoc | Listen for the Windows power broadcast (`WM_POWERBROADCAST`) through a native event filter, and also run a 60 s heartbeat that compares the date and elapsed time. Heartbeat is the safety net. |
| 3 | Hotkey depends on window focus | `RegisterHotKey` through `ctypes`, handled in a `QAbstractNativeEventFilter`. Unregister on exit. Report a clear error if another app holds the combo, and let the user rebind it. |
| 4 | Single-instance race | Named mutex (`CreateMutexW`) acquired at the top of `run.py`, plus a `QLocalServer` to tell the first instance to show its window. Second launch sends "show" and exits. |
| 5 | Everything saved in one JSON | Split settings, daily history and runtime state into separate files, each with a `schema_version` and a migration function. v1 data must load in v2 without loss. |
| 6 | Data migration risk v1 → v2 | On first v2 launch, copy the v1 folder to a timestamped backup before migrating. Offer rollback instructions in the log. |
| 7 | Time zone / DST changes | Store dates as local ISO dates, timestamps as UTC. Day rollover uses the local date from the OS each check. |
| 8 | Tray state desync | One `AppState` object with signals. Tray, dashboard and overlay only read from it and never keep their own copies. |
| 9 | Click-through trap: user cannot reach Spider-Man | Show a clear tray tip when click-through is on, and a temporary un-click-through while the cursor holds a modifier key (for example Ctrl). |
| 10 | Multi-monitor and DPI changes | Listen for `screenAdded`, `screenRemoved` and geometry changes. Clamp the saved offset into the nearest visible screen. |
| 11 | Notification overload | Respect quiet hours, `daily_active_hours`, and full-screen detection (do not interrupt games or presentations). Use a gentle retry cap. |
| 12 | Installer size (131 MB) | Exclude unused Qt modules in the PyInstaller spec, audit Pillow, compress textures, and consider UPX only if antivirus false positives stay low. |
| 13 | Antivirus false positives on unsigned `.exe` | Code-sign if possible; at minimum publish SHA-256 hashes with each release. |
| 14 | Audio feature without assets | Ship two short royalty-free or self-made sounds (thwip, chime), preload them, keep volume low and offer a mute toggle. Remove the setting if not built (CLEAN-02). |
| 15 | Untested UI logic | Move logic (cooldown, streak, reset) into plain Python classes with no Qt imports, so they are testable with plain `pytest`. Use `pytest-qt` only for widget wiring. Inject a fake clock into those classes. |
| 16 | Privacy wording | Keep the "no admin rights, no network" promise explicit in README and verify the app makes no network calls. |
| 17 | Log growth and support | Keep the rotating log; add a "Copy diagnostics" button in the Diagnostics tab. |

---

## 7. Test Plan

All time-dependent tests use an injected fake clock (never `time.sleep`).

### 7.1 Manual log and cooldown

| # | Test | Expected |
|---|---|---|
| 1 | First click on a fresh install | +250 ml accepted immediately |
| 2 | Second click before 30 min | Rejected, no water added, remaining time returned |
| 3 | Click at exactly 30:00 | Accepted, +250 ml |
| 4 | Rapid double-click (concurrent calls) | Exactly one success |
| 5 | Restart during cooldown | Cooldown continues from the stored stamp |
| 6 | Sleep and resume during cooldown | Remaining computed correctly from elapsed time |
| 7 | Midnight during cooldown | Daily total resets, cooldown still enforced |
| 8 | Reaching 2,000 ml | Streak updates exactly once |
| 9 | Configure 29 min or less | Clamped to 30 (UI, backend and config load) |
| 10 | Existing reminders, snooze, animations, dashboard, saved data | Still work (regression) |

### 7.2 Extra cases

Clock moved backwards (remaining never exceeds cooldown). Clock moved far forward. Corrupt data file triggers backup restore. Config hand-edited to a cooldown of 5. Cooldown raised to 60 while a 30-minute cooldown is active. Keyboard auto-repeat. Tray action and button clicked at the same moment. Atomic write interrupted (simulate a crash between temp write and replace).

### 7.3 Streak

Consecutive days, a gap day, a shield (if enabled), goal changed mid-day, multiple clicks after the goal, and midnight rollover with an open dashboard.

### 7.4 Reporting rule

A release note may list a test as passing **only** if it was actually run and passed on the release commit. Record the command, date and result.

---

## 8. Implementation Phases

| Phase | Scope | Exit criteria |
|---|---|---|
| 0 | Inspect code, confirm each bug in 2.x, record file and line | Register updated: ✅ or ❌ per item |
| 1 | Engine fixes: state machine, single instance, midnight and wake reset, atomic persistence, backups | CRIT and HIGH items closed with tests |
| 2 | Manual log + cooldown + settings + streak backend | Tests 7.1 and 7.3 pass |
| 3 | New dashboard UI, water gauge, button states, streak badge | Visual review on 100%, 125%, 150% DPI |
| 4 | Companion polish: native hotkey, drag persistence, look-at, scale | MED items closed |
| 5 | Audio, cleanup, packaging, README refresh, versioning | Clean build; installer and portable verified on a fresh Windows profile |

---

## 9. Release Checklist

- [ ] `VERSION` bumped in one place
- [ ] README numbers re-measured or removed
- [ ] v1 → v2 migration tested with a real v1 data folder
- [ ] Full test suite run and results recorded
- [ ] Installer and uninstaller tested on a clean machine
- [ ] SHA-256 hashes published
- [ ] Known issues listed honestly

---

## 10. Open Questions

1. Should the manual button be available while a reminder popup is showing? (Recommended: yes, and it should also dismiss that reminder.)
2. Should custom amounts share the 30-minute cooldown? (Recommended: yes.)
3. Is the Web Shield in v2.0 or v2.1?
4. Does any code use `QSettings` (relevant to NEW-10)?