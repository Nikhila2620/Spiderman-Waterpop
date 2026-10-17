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


def test_dashboard_streak_card_integration(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.daily_hydration_goal_ml = 2000
        cm.settings.today_intake_ml = 1500
        cm.settings.last_tracking_date = date.today().isoformat()
        cm.save()

        engine = ReminderEngine(cm)
        dash = DashboardWindow(cm, engine)

        # 1. Initial State: 1500 / 2000 mL (75%), In Progress
        assert hasattr(dash, "streak_card"), "Dashboard must contain streak_card component"
        assert "1,500 / 2,000 mL" in dash.streak_card.lbl_intake_numbers.text()
        assert dash.streak_card.lbl_pct.text() == "75%"
        assert dash.streak_card.lbl_status.text() == "⏳ In Progress"
        assert dash.streak_card.is_celebration_active is False

        # 2. Log +500 mL to reach exactly 2,000 mL (Goal reached!)
        dash._quick_log_water(500)

        assert cm.settings.today_intake_ml == 2000
        assert cm.settings.streak_current == 1
        assert "2,000 / 2,000 mL" in dash.streak_card.lbl_intake_numbers.text()
        assert dash.streak_card.lbl_pct.text() == "100%"
        assert dash.streak_card.lbl_status.text() == "✨ Goal Completed!"
        assert "🔥 1-Day Streak" in dash.streak_card.lbl_streak_count.text()
        assert dash.streak_card.is_celebration_active is True
        assert "Goal Complete! 🔥 You're on a 1-Day Streak!" in dash.streak_card.lbl_celebration_text.text()

        # 3. Log an additional +250 mL (2,250 mL): Streak should remain 1 and not re-trigger celebration
        dash._quick_log_water(250)
        assert cm.settings.today_intake_ml == 2250
        assert cm.settings.streak_current == 1
        assert "2,250 / 2,000 mL" in dash.streak_card.lbl_intake_numbers.text()
        assert "🔥 1-Day Streak" in dash.streak_card.lbl_streak_count.text()


def test_streak_card_component_unit(qapp):
    from src.components.streak_card import StreakCardWidget
    from src.streak_tracker import StreakInfo

    card = StreakCardWidget()
    assert card.title == "Daily Hydration Streak"

    # Simulate info update with in-progress state
    info = StreakInfo(
        current_streak=3,
        longest_streak=7,
        today_intake_ml=1000,
        daily_goal_ml=2000,
        is_completed_today=False,
        celebrated_today=False,
        progress_percentage=50,
        last_completed_date="",
    )
    card.update_info(info)
    assert card.lbl_streak_count.text() == "🔥 3-Day Streak"
    assert card.lbl_longest_streak.text() == "Personal Best: 7 days"
    assert card.lbl_pct.text() == "50%"
    assert card.progress_bar.value() == 50
    assert card.lbl_status.text() == "⏳ In Progress"
    assert card.is_celebration_active is False

    # Simulate celebration trigger
    card.trigger_celebration("Goal Complete! 🔥 You're on a 4-Day Streak!")
    assert card.is_celebration_active is True
    assert "4-Day Streak" in card.lbl_celebration_text.text()


