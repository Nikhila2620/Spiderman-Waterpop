"""
Spider-Man Water Buddy v2.0 — Desktop Application Launcher
Launches the standalone application, system tray, companion overlay, and settings dashboard.
"""
import sys
import os
import atexit
import logging
from logging.handlers import RotatingFileHandler
import threading
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.version import FULL_NAME
from src.utils import resource_path
from src.windows_native import NamedMutexGuard

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


# 2. Crash reporting & unhandled exception hooks (NEW-05)
def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Unhandled exception encountered:", exc_info=(exc_type, exc_value, exc_traceback))
    try:
        from PySide6.QtWidgets import QMessageBox, QApplication
        if QApplication.instance():
            QMessageBox.warning(
                None,
                "Spider-Man Water Buddy — Alert",
                f"An unexpected error occurred.\n\nA diagnostic report was saved to:\n{log_file}",
            )
    except Exception:
        pass


sys.excepthook = handle_unhandled_exception

if hasattr(threading, "excepthook"):
    def handle_thread_exception(args):
        logger.critical(f"Unhandled thread exception in {args.thread}:", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    threading.excepthook = handle_thread_exception

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtCore import Qt
from PySide6.QtNetwork import QLocalSocket
from src.app import SpiderManWaterBuddyApp


def main():
    # Modern Qt 6 High-DPI rounding policy
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 3. Named Mutex Single-Instance Guard (CRIT-05 / NEW-06)
    mutex_guard = NamedMutexGuard("Local\\SpiderManWaterBuddy_SingleInstance_Mutex")
    if not mutex_guard.acquire():
        logger.info("Another instance is already running (Named Mutex held). Notifying and activating existing instance...")
        app_dummy = QApplication.instance() or QApplication(sys.argv)
        socket = QLocalSocket()
        socket.connectToServer("SpiderManWaterBuddy_SingleInstance_Pipe")
        if socket.waitForConnected(800):
            socket.write(b"ACTIVATE")
            socket.waitForBytesWritten(800)
            socket.disconnectFromServer()
        sys.exit(0)

    atexit.register(mutex_guard.release)

    app = QApplication(sys.argv)
    app.setApplicationName("Spider-Man Water Buddy")
    app.setOrganizationName("Antigravity")
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    # App icon from resource path (NEW-09)
    icon_path = resource_path("assets/images/app_icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    controller = SpiderManWaterBuddyApp(app)

    # Transient runtime flags: standard launch opens Dashboard immediately
    minimized_override = False
    show_dashboard_flag = True
    if "--minimized" in sys.argv:
        logger.info("Launched with --minimized flag (Windows Startup).")
        minimized_override = True
        show_dashboard_flag = False
    if "--dashboard" in sys.argv:
        show_dashboard_flag = True

    controller.run(start_minimized_override=minimized_override, show_dashboard=show_dashboard_flag)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
