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
