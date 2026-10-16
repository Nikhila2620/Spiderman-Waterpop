import tempfile
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


def test_dashboard_window_initialization_and_telemetry(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.daily_hydration_goal_ml = 2000
        cm.settings.today_intake_ml = 500
        cm.settings.last_tracking_date = date.today().isoformat()
        cm.save()

        engine = ReminderEngine(cm)
        dash = DashboardWindow(cm, engine)

        # Verify components initialized
        assert dash.reservoir_widget.current_ml == 500
        assert dash.reservoir_widget.goal_ml == 2000
        assert dash.reservoir_widget.percentage == 25

        # Verify quick log
        dash._quick_log_water(250)
        assert cm.settings.today_intake_ml == 750
        assert dash.reservoir_widget.current_ml == 750
        assert dash.reservoir_widget.percentage == 37

        # Verify nav switching
        dash._switch_nav(2)
        assert dash.stack.currentIndex() == 2
        dash._switch_nav(0)
        assert dash.stack.currentIndex() == 0


def test_dashboard_countdown_formatting(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.quiet_hours_end = "08:00"
        cm.save()

        engine = ReminderEngine(cm)
        dash = DashboardWindow(cm, engine)

        from src.reminder_engine import ReminderState

        # 1. Normal countdown under 1 hour (e.g. 45 min = 2700s)
        engine.state = ReminderState.IDLE
        dash._on_timer_tick(2700)
        assert dash.lbl_countdown.text() == "45:00"
        assert dash.card_timer.lbl_subtitle.text() == "Countdown to hydration prompt"

        # 2. Normal countdown over 1 hour (e.g. 90 min = 5400s)
        dash._on_timer_tick(5400)
        assert dash.lbl_countdown.text() == "01:30:00"

        # 3. Quiet Hours: 34,387 seconds (approx 9h 33m) should NEVER show garbage '573:07'
        engine.state = ReminderState.QUIET_HOURS
        dash._on_timer_tick(34387)
        assert "573" not in dash.lbl_countdown.text()
        assert "Resumes 8:00 AM" in dash.lbl_countdown.text()
        assert "Sleeping • Resumes in 9h 33m" == dash.card_timer.lbl_subtitle.text()

        # 4. Due now (0 seconds)
        engine.state = ReminderState.IDLE
        dash._on_timer_tick(0)
        assert dash.lbl_countdown.text() == "DUE NOW!"

        # 5. Paused
        dash._on_timer_tick(-1)
        assert dash.lbl_countdown.text() == "Paused"
