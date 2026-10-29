# Changelog

All notable changes to **Spider-Man Waterpop** will be documented in this file.

## [2.0.0] - 2026-10-29

### Added
- **Interactive Neo-Brutalist Dashboard**: Sunlit comic desk aesthetic featuring dynamic filling glass bottle, animated water meniscus, pill organizer, tactile offset shadows, and live telemetry.
- **Deep Black & Polished Gold Installer**: Redesigned setup wizard, uninstaller, and configuration dialogs with a gold-and-obsidian theme (`#0b0c10` / `#d4af37`).
- **Resilient Shortcut Generator**: Re-engineered PowerShell WScript.Shell shortcut automation with native Windows shell folder detection (OneDrive Desktop redirection compatible).
- **Rate-Limited Exception Handler**: Prevents modal alert dialog spam during unhandled timer errors.
- **Single-Instance Feedback**: Clear user notification when an instance is already running in the background.
- **Fail-Safe Startup**: Direct Windows message box alert if launched via `pythonw` without prerequisites.
- **Project Modernization**: Standardized `pyproject.toml`, CRLF `.bat` launch scripts with Python 3.10+ validation, and clean packaging.

### Fixed
- Fixed PowerShell `-Command` parameter binding failure in `src/installer_gui.py`.
- Fixed desktop shortcut location on machines using Microsoft OneDrive Desktop backup.
- Fixed 5-minute nag loop by resetting reminder timer on notification dismissal.
- Cleaned redundant copy directories and marker files, reducing repository footprint from >4.3 GB to <15 MB pure source.
- Added offline system font fallbacks (`Segoe UI`, `Impact`, `Consolas`, `Segoe Print`) to the HTML dashboard.

## [1.0.0] - 2026-10-15
- Initial release featuring system tray companion, customizable hydration goal, and streak tracking.
