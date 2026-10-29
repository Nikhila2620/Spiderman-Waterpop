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
import time
import tempfile
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.version import FULL_NAME
from src.utils import resource_path
from src.windows_native import NamedMutexGuard

# 1. Consolidate logging with robust directory creation and fallback
app_data = os.environ.get("APPDATA")
candidates = []
if app_data:
    candidates.append(Path(app_data) / "SpiderManWaterBuddy" / "logs")
candidates.append(Path.home() / ".spiderman_water_buddy" / "logs")
candidates.append(Path(tempfile.gettempdir()) / "SpiderManWaterBuddy" / "logs")

log_dir = None
for cand in candidates:
    try:
        cand.mkdir(parents=True, exist_ok=True)
        log_dir = cand
        break
    except Exception:
        continue

if log_dir is None:
    log_dir = Path(".")

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


# 2. Crash reporting & rate-limited unhandled exception hooks (prevents dialog storms)
_last_error_dialog_time = 0.0

def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    global _last_error_dialog_time
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Unhandled exception encountered:", exc_info=(exc_type, exc_value, exc_traceback))

    # Rate-limit modal dialogs: max 1 per 30 seconds
    now = time.time()
    if now - _last_error_dialog_time < 30.0:
        logger.warning("Suppressed consecutive error dialog within rate limit window.")
        return
    _last_error_dialog_time = now

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


# 3. Safe PySide6 imports with native fallback if launched directly under pythonw without dependencies
try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtGui import QIcon, QGuiApplication
    from PySide6.QtCore import Qt, QCoreApplication
    from PySide6.QtNetwork import QLocalSocket
    # Preload QtWebEngineWidgets if available before QApplication instantiation
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
    except Exception:
        pass
except ImportError:
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            "PySide6 is not installed.\nPlease run SETUP.bat in the application folder to install required dependencies.",
            "Spider-Man Water Buddy",
            0x10,
        )
    sys.exit(1)

from src.app import SpiderManWaterBuddyApp


def main():
    # Explicit Windows AppUserModelID for crisp Taskbar and Alt-Tab branding
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SpiderManWaterpop.DesktopApp.2.0")
        except Exception:
            pass

    # Modern Qt 6 High-DPI rounding policy
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 4. Named Mutex Single-Instance Guard
    mutex_guard = NamedMutexGuard("Local\\SpiderManWaterBuddy_SingleInstance_Mutex")
    if not mutex_guard.acquire():
        logger.info("Another instance is already running (Named Mutex held). Notifying and activating existing instance...")
        app_dummy = QApplication.instance() or QApplication(sys.argv)
        socket = QLocalSocket()
        connected = False
        for _ in range(5):
            socket.connectToServer("SpiderManWaterBuddy_SingleInstance_Pipe")
            if socket.waitForConnected(600):
                connected = True
                socket.write(b"ACTIVATE")
                socket.waitForBytesWritten(600)
                socket.disconnectFromServer()
                break
            time.sleep(0.3)
        if not connected:
            logger.info("Existing instance mutex held; pipe connection was not received. Informing user.")
            try:
                QMessageBox.information(
                    None,
                    "Spider-Man Water Buddy",
                    "Spider-Man Water Buddy is already running in the background.\nCheck your system tray (near the clock) or press Ctrl+Alt+W.",
                )
            except Exception:
                pass
        sys.exit(0)

    atexit.register(mutex_guard.release)

    app = QApplication(sys.argv)
    app.setApplicationName("Spider-Man Waterpop")
    app.setApplicationDisplayName(FULL_NAME)
    app.setOrganizationName("SpiderManWaterpop")
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    # App icon from resource path (ICO for Windows taskbar + PNG)
    ico_path = resource_path("assets/images/app_icon.ico")
    png_path = resource_path("assets/images/app_icon.png")
    app_icon = None
    if ico_path.exists():
        app_icon = QIcon(str(ico_path))
    elif png_path.exists():
        app_icon = QIcon(str(png_path))
    if app_icon and not app_icon.isNull():
        app.setWindowIcon(app_icon)

    controller = SpiderManWaterBuddyApp(app)

    # Transient runtime flags: standard launch shows perched companion; dashboard opens on click or --dashboard
    minimized_override = False
    show_dashboard_flag = False
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
