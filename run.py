"""
Spider-Man Water Buddy — Desktop Application Launcher
Launches the standalone application, system tray, companion overlay, and setup wizard.
"""
import sys
import os
import logging
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
log_dir = Path.home() / ".spiderman_water_buddy" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("SpiderManWaterBuddy")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
from src.app import SpiderManWaterBuddyApp


def main():
    # Windows DPI awareness & rendering attributes
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Spider-Man Water Buddy")
    app.setOrganizationName("Antigravity")
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    # App icon
    icon_path = Path(__file__).resolve().parent / "assets" / "images" / "app_icon.png"
    if not icon_path.exists():
        render_path = Path(__file__).resolve().parent / "assets" / "images" / "spidey_3d_render.png"
        if render_path.exists():
            pix = QPixmap(str(render_path)).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pix.save(str(icon_path), "PNG")

    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    controller = SpiderManWaterBuddyApp(app)

    # Check CLI arguments for --minimized
    if "--minimized" in sys.argv:
        logger.info("Launched with --minimized flag (Windows Startup).")
        controller.settings.start_minimized = True

    controller.run()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
