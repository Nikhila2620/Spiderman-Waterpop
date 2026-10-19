import tempfile
from pathlib import Path
from datetime import date
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
import pytest

from src.config import ConfigManager
from src.reminder_engine import ReminderEngine
from src.dashboard_window import DashboardWindow
from src.companion_window import CompanionWindow
from src.character import SpideyWidget


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_companion_scale_and_offset_persistence(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.character_scale = 1.2
        cm.settings.corner_position = "top-right"
        cm.save()

        companion = CompanionWindow(cm)
        assert companion.spidey._character_scale == 1.2

        # Check drag release persists offset
        base_x, base_y = companion._get_base_corner_pos()
        companion.move(base_x - 50, base_y + 30)
        
        # Simulate drag release
        companion._drag_start_pos = QPoint(10, 10)
        class DummyEvent:
            pass
        companion.mouseReleaseEvent(DummyEvent())

        assert cm.settings.window_offset_x == -50
        assert cm.settings.window_offset_y == 30

        # Create another instance and verify offset was respected on reposition
        companion2 = CompanionWindow(cm)
        assert companion2.x() == base_x - 50
        assert companion2.y() == base_y + 30


def test_companion_clean_dismiss(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        companion = CompanionWindow(cm)

        companion.trigger_reminder_mode()
        assert companion.is_in_reminder_mode() is True

        dismissed_calls = []
        companion.dismissed.connect(lambda: dismissed_calls.append(True))
        companion.dismiss()

        assert companion.is_in_reminder_mode() is False
        assert len(dismissed_calls) == 1
        assert not companion._auto_close_timer.isActive()


def test_dashboard_hero_drink_and_chips(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.today_intake_ml = 0
        cm.settings.daily_hydration_goal_ml = 2000
        cm.settings.last_tracking_date = date.today().isoformat()
        cm.save()

        engine = ReminderEngine(cm)
        dash = DashboardWindow(cm, engine)

        assert dash.btn_hero_drink.isEnabled()
        assert "250 ml" in dash.btn_hero_drink.text()

        # Select 500 ml chip
        dash._select_amount(500)
        assert dash._selected_amount == 500
        assert "500 ml" in dash.btn_hero_drink.text()

        # Click hero drink button
        dash.btn_hero_drink.click()

        # Check intake updated
        assert cm.settings.today_intake_ml == 500
        assert dash.reservoir_widget.current_ml == 500

        # Cooldown should now be active
        assert not dash.btn_hero_drink.isEnabled()
        assert "Next log in" in dash.btn_hero_drink.text()
        assert "Cooldown active" in dash.lbl_cooldown_status.text()
