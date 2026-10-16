# Aquatic Liquid Glass UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Spider-Man Water Buddy desktop application into a premium, minimal, smooth, and eye-catching Aquatic Liquid Glass interface inspired by `liquidglassdesign.com`, preserving all existing features, signals, timers, settings persistence, and companion window behavior.

**Architecture:** 
1. Centralize the Aquatic Liquid Glass design system in `src/theme.py` with deep indigo gradients (`#07111E` to `#0C1A2E`), translucent frosted glass cards, subtle cyan borders (`rgba(0, 240, 255, 0.22)`), and luminous Aqua (`#00F0FF`), Azure (`#0A84FF`), and Mint (`#00E699`) accents.
2. Build reusable native PySide6 components in `src/components/`:
   - `LiquidReservoirWidget`: Custom QPainter-rendered fluid reservoir with an animated sine-wave liquid surface, ripple phase oscillation, and hydration percentage.
   - `GlassCard`: Framed container with simulated frosted glass gradient and crisp refraction border.
   - `GlassToggleSwitch`: Smooth animated sliding pill toggle with cyan glow.
3. Overhaul `src/dashboard_window.py` with a sleek custom titlebar, clean left navigation sidebar with 5 distinct sections (Dashboard, General, Reminders, Appearance, Advanced), and interactive quick-log buttons (`+250 ml`, `+500 ml`).
4. Modernize `src/companion_window.py`, `src/wizard_dialog.py`, and `src/popup.py` to match the liquid glass aesthetic without compromising zero-focus-steal or desktop placement.
5. Rebuild production distributables and verify all automated tests pass.

**Tech Stack:** Python 3.11, PySide6 6.12.0 (Qt6), QPainter 2D vector graphics, QPropertyAnimation, PyInstaller 6.22.3.

**Spec:** User prompt requirements and reference design system from `https://liquidglassdesign.com/`.

## Global Constraints
- Target platform: Windows 10/11 x64, 8 GB RAM laptop friendly (lightweight CPU/GPU footprint).
- Strict backward compatibility: Retain all public methods, signal names, settings keys (`settings.json`), and command-line flags (`--minimized`, `--toggle`, `--dashboard`).
- Never introduce web-only frameworks or QtWebEngine; use native PySide6 widgets and QSS.
- Keep companion overlay independent of settings dashboard; preserve top-right desktop placement and `WS_EX_NOACTIVATE` focus protection.
- Liquid animations must pause automatically when the window is hidden or minimized.

## Review Focus
- **Fluid Wave Performance**: Wave rendering timer must shut down completely when the dashboard is hidden or minimized.
- **Quick-Add Logging**: Quick-log buttons (`+250 ml`, `+500 ml`) must update both the reminder engine and `AppSettings` atomically and save to disk immediately.
- **Contrast & Legibility**: Text on frosted translucent backgrounds must maintain high contrast (crisp white `#FFFFFF` for titles, frosted slate `#A8C4D8` for secondary text).
- **Settings Persistence**: All UI changes across all 5 navigation tabs must reliably bind to `ConfigManager` without data loss.
- **Test Integrity**: All existing tests in `tests/test_full_suite.py` must pass at 100%.

---

### Task 1: Aquatic Liquid Glass Theme Tokens & Stylesheets

**Files:**
- Modify: `src/theme.py`
- Test: `tests/test_full_suite.py`

**Interfaces:**
- Consumes: Existing `ThemeTokens`, `get_dashboard_qss()`, `get_companion_card_qss()`, `get_tray_menu_qss()`, `get_dialog_qss()`
- Produces: Updated tokens containing `BG_BASE`, `BG_SURFACE`, `BG_CARD`, `ACCENT_AQUA` (`#00F0FF`), `ACCENT_AZURE` (`#0A84FF`), `ACCENT_MINT` (`#00E699`), `BORDER_GLASS`, `TEXT_PRIMARY`, `TEXT_SECONDARY`, `TEXT_MUTED`

- [ ] **Step 1: Write/Update the test in `tests/test_full_suite.py`**
Verify `TOKENS.ACCENT_AQUA == "#00F0FF"`, `TOKENS.ACCENT_MINT == "#00E699"`, and new aquatic gradient checks.

- [ ] **Step 2: Run test to verify it fails**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_full_suite.py -k test_theme_tokens_and_stylesheets -v`
Expected: FAIL due to missing `ACCENT_AQUA` or new attributes.

- [ ] **Step 3: Implement Aquatic Liquid Glass Tokens & QSS in `src/theme.py`**
Implement deep indigo background (`#07111E` to `#0C1A2E`), translucent cards (`rgba(12, 26, 46, 0.75)`), subtle cyan refraction borders (`rgba(0, 240, 255, 0.22)`), and modern pill tab styles.

- [ ] **Step 4: Run test to verify it passes**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_full_suite.py -k test_theme_tokens_and_stylesheets -v`
Expected: PASS.

- [ ] **Step 5: Commit**
`git commit -m "feat(theme): implement aquatic liquid glass design tokens and QSS engine"`

---

### Task 2: Reusable Liquid Reservoir Widget (`LiquidReservoirWidget`)

**Files:**
- Create: `src/components/__init__.py`
- Create: `src/components/liquid_reservoir.py`
- Test: `tests/test_liquid_reservoir.py`

**Interfaces:**
- Consumes: PySide6 `QWidget`, `QPainter`, `QPainterPath`, `QLinearGradient`, `QTimer`
- Produces: `LiquidReservoirWidget(parent=None)` with methods:
  - `set_values(current_ml: int, goal_ml: int)`
  - `start_animation()` / `stop_animation()`
  - Wave phase physics loop (oscillating sine waves with 30fps timer)
  - Auto-pauses on `hideEvent()` and resumes on `showEvent()`

- [ ] **Step 1: Write test in `tests/test_liquid_reservoir.py`**
Test instantiation, `set_values(500, 2000)`, percentage calculation (25%), wave phase incrementing, and hide/show timer control.

- [ ] **Step 2: Run test to verify failure**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_liquid_reservoir.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement `LiquidReservoirWidget` in `src/components/liquid_reservoir.py`**
Render dual-layer translucent aqua/azure waves (`#00F0FF` and `#0A84FF`), frosted glass capsule border, reflective top highlight, and center percentage text.

- [ ] **Step 4: Run test to verify pass**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_liquid_reservoir.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**
`git commit -m "feat(components): add animated liquid reservoir widget"`

---

### Task 3: Reusable Glass Components (`GlassCard` & `GlassToggleSwitch`)

**Files:**
- Create: `src/components/glass_card.py`
- Create: `src/components/toggle_switch.py`
- Test: `tests/test_components.py`

**Interfaces:**
- Consumes: PySide6 `QFrame`, `QAbstractButton`, `QPropertyAnimation`
- Produces:
  - `GlassCard(title: str = "", subtitle: str = "", parent=None)`
  - `GlassToggleSwitch(checked: bool = False, parent=None)` with signal `toggled(bool)`

- [ ] **Step 1: Write test in `tests/test_components.py`**
Test `GlassCard` hierarchy and `GlassToggleSwitch` state toggling & animation properties.

- [ ] **Step 2: Run test to verify failure**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_components.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `GlassCard` and `GlassToggleSwitch`**
Build translucent frosted glass frame with top gloss reflection line and smooth sliding pill toggle switch.

- [ ] **Step 4: Run test to verify pass**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_components.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**
`git commit -m "feat(components): add reusable glass card and animated toggle switch"`

---

### Task 4: Redesign Dashboard Settings Window (`DashboardWindow`)

**Files:**
- Modify: `src/dashboard_window.py`
- Test: `tests/test_full_suite.py`

**Interfaces:**
- Consumes: `LiquidReservoirWidget`, `GlassCard`, `GlassToggleSwitch`, `ConfigManager`, `ReminderEngine`
- Produces: Refactored `DashboardWindow` with:
  - Custom aquatic liquid glass titlebar with icon badge, title, minimize & close buttons.
  - Left navigation sidebar with 5 clean tabs: Dashboard, General, Reminders, Appearance, Advanced.
  - Interactive hydration reservoir with live wave animation.
  - Quick-add buttons (`+250 ml`, `+500 ml`) connected directly to `ReminderEngine.log_intake()`.
  - Full settings management across all 5 sections.

- [ ] **Step 1: Update dashboard verification test in `tests/test_full_suite.py`**
Verify quick-log water intake, tab switching, and window lifecycle.

- [ ] **Step 2: Implement redesign in `src/dashboard_window.py`**
Replace purple/crimson styles with liquid glass sidebar layout, mount `LiquidReservoirWidget`, integrate quick-add buttons, and connect all controls.

- [ ] **Step 3: Run full test suite**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_full_suite.py -v`
Expected: 8/8 PASS.

- [ ] **Step 4: Commit**
`git commit -m "feat(ui): redesign main dashboard with aquatic liquid glass sidebar and fluid reservoir"`

---

### Task 5: Redesign Desktop Companion Overlay & Wizard Dialog

**Files:**
- Modify: `src/companion_window.py`
- Modify: `src/wizard_dialog.py`
- Modify: `src/character.py`

**Interfaces:**
- Consumes: `ThemeTokens`, `SpideyWidget`
- Produces:
  - Frosted translucent liquid glass companion card with subtle cyan glow border.
  - Glowing Mint `💧 YES, DRANK!` button and sleek translucent `⏳ NOT YET` button.
  - Liquid glass styled First-Run Wizard with step progression and summary cards.
  - Character reaction overlays updated to aquatic glint & golden celebration.

- [ ] **Step 1: Update `src/companion_window.py` with liquid glass styling**
Translucent glass card (`rgba(7, 17, 30, 0.90)`), cyan refraction border (`rgba(0, 240, 255, 0.28)`), mint celebration feedback.

- [ ] **Step 2: Update `src/wizard_dialog.py` with liquid glass styling**
Aquatic header, translucent page containers, and azure/aqua "Finish & Save" button.

- [ ] **Step 3: Run full automated tests**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_full_suite.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**
`git commit -m "feat(ui): apply aquatic liquid glass theme to companion overlay and setup wizard"`

---

### Task 6: Build Standalone Distributables & End-to-End Verification

**Files:**
- Modify/Run: `scripts/build_dist.py`
- Output: `dist/SpiderManWaterBuddy-v1.0.0-Setup.exe`, `dist/SpiderManWaterBuddy-v1.0.0-Portable.zip`

- [ ] **Step 1: Run complete test suite**
Run: `.\.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 2: Run automated build pipeline**
Run: `.\.venv\Scripts\python.exe scripts/build_dist.py`
Verify compilation of standalone onedir, portable zip, and setup installer.

- [ ] **Step 3: Verify portable archive integrity**
Extract to temp directory and verify executable launches and logs without errors.

- [ ] **Step 4: Commit and finalize**
`git commit -m "chore(release): package aquatic liquid glass v1.0.0 desktop release"`
