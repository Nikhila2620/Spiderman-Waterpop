"""
Spider-Man Water Buddy — Desktop Application Launcher
Launches the standalone application, system tray, companion overlay, and setup wizard.
"""
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import threading
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 1. Consolidate logging to %APPDATA%\SpiderManWaterBuddy\logs\app.log
app_data = os.environ.get("APPDATA")
if app_data:
    log_dir = Path(app_data) / "SpiderManWaterBuddy" / "logs"
else:
    log_dir = Path.home() / ".spiderman_water_buddy" / "logs"

log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "app.log"

handlers = [
    RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
]
if sys.stdout is not None:
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=handlers,
)
logger = logging.getLogger("SpiderManWaterBuddy")


# 2. Crash reporting & unhandled exception hooks
def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Unhandled exception encountered:", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_unhandled_exception

if hasattr(threading, "excepthook"):
    def handle_thread_exception(args):
        logger.critical(f"Unhandled thread exception in {args.thread}:", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    threading.excepthook = handle_thread_exception

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtCore import Qt
from src.app import SpiderManWaterBuddyApp


def main():
    # Modern Qt 6 High-DPI rounding policy
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Spider-Man Water Buddy")
    app.setOrganizationName("Antigravity")
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    # App icon from existing assets
    icon_path = Path(__file__).resolve().parent / "assets" / "images" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    controller = SpiderManWaterBuddyApp(app)

    # Transient runtime flag for --minimized without permanently mutating saved settings
    minimized_override = False
    if "--minimized" in sys.argv:
        logger.info("Launched with --minimized flag (Windows Startup).")
        minimized_override = True

    controller.run(start_minimized_override=minimized_override)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

