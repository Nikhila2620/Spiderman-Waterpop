"""
Renders a visual screenshot of the Stark Tech / EDITH HUD Dashboard Window
and Companion Overlay directly into the brain artifact directory for inspection.
"""
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap

from src.config import ConfigManager
from src.reminder_engine import ReminderEngine
from src.dashboard_window import DashboardWindow
from src.companion_window import CompanionWindow

ARTIFACT_DIR = Path(r"C:\Users\hp\.gemini\antigravity\brain\29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e")


def capture_preview():
    try:
        app = QApplication.instance() or QApplication(sys.argv)

        cm = ConfigManager()
        cm.settings.today_intake_ml = 1350
        cm.settings.daily_hydration_goal_ml = 2000
        engine = ReminderEngine(cm)

        # 1. Render Dashboard
        dash = DashboardWindow(cm, engine)
        dash.resize(960, 740)
        dash.show()
        app.processEvents()

        # Render dashboard onto pixmap
        dash_pixmap = QPixmap(dash.size())
        dash_pixmap.fill(Qt.GlobalColor.black)
        dash.render(dash_pixmap)

        dash_out = ARTIFACT_DIR / "stark_edith_hud_dashboard.png"
        dash_pixmap.save(str(dash_out))
        print(f"[OK] Saved Stark HUD Dashboard preview to: {dash_out}")

        # 2. Render Companion Window
        comp = CompanionWindow(cm)
        comp.reset_card_ui()
        comp.show()
        app.processEvents()

        comp_pixmap = QPixmap(comp.size())
        comp_pixmap.fill(Qt.GlobalColor.transparent)
        comp.render(comp_pixmap)

        comp_out = ARTIFACT_DIR / "stark_edith_hud_companion.png"
        comp_pixmap.save(str(comp_out))
        print(f"[OK] Saved Stark HUD Companion preview to: {comp_out}")

        dash.close()
        comp.close()
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        with open("preview_error.log", "w") as f:
            f.write(err_msg)
        print("Error during preview:", e)
        sys.exit(1)


if __name__ == "__main__":
    capture_preview()
