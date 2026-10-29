import tempfile
import json
from pathlib import Path
from datetime import date
from PySide6.QtWidgets import QApplication
import pytest

from src.config import ConfigManager
from src.reminder_engine import ReminderEngine
from src.dashboard_window import DashboardWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_dashboard_web_bridge_actions(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.daily_hydration_goal_ml = 2000
        cm.settings.today_intake_ml = 300
        cm.settings.last_tracking_date = date.today().isoformat()
        cm.save()

        engine = ReminderEngine(cm)
        dash = DashboardWindow(cm, engine)

        # 1. Test WebBridge log_water dispatch
        payload = json.dumps({"amount": 250})
        dash._handle_web_action("log_water", payload)

        assert cm.settings.today_intake_ml == 550
        assert dash.reservoir_widget.current_ml == 550

        # 2. Test WebBridge save_settings dispatch
        settings_payload = json.dumps({
            "companion_name": "Peter Parker",
            "user_name": "Miles",
            "daily_goal": 2500,
            "interval_mins": 45,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "23:00",
            "quiet_hours_end": "07:30",
            "sound_effects_enabled": False,
            "corner_position": "bottom-right",
            "click_through_enabled": True,
            "animation_enabled": False,
            "performance_mode": True,
        })
        dash._handle_web_action("save_settings", settings_payload)

        assert cm.settings.companion_name == "Peter Parker"
        assert cm.settings.user_name == "Miles"
        assert cm.settings.daily_hydration_goal_ml == 2500
        assert cm.settings.reminder_interval_minutes == 45
        assert cm.settings.quiet_hours_start == "23:00"
        assert cm.settings.quiet_hours_end == "07:30"
        assert cm.settings.sound_effects_enabled is False
        assert cm.settings.corner_position == "bottom-right"
        assert cm.settings.click_through_enabled is True
        assert cm.settings.animation_enabled is False
        assert cm.settings.performance_mode is True

        # 3. Test WebBridge toggle_spider_sense dispatch
        prior_pause = cm.settings.reminders_paused
        dash._handle_web_action("toggle_spider_sense", "{}")
        assert cm.settings.reminders_paused != prior_pause

        # 4. Test View Mode Toggle
        dash.show()
        assert dash.web_view.isVisible()
        dash.toggle_view_mode()
        assert not dash.web_view.isVisible()
        assert dash._native_container.isVisible()
        dash.toggle_view_mode()
        assert dash.web_view.isVisible()
