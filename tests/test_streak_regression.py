"""
Regression test suite for Daily Hydration Streak feature.
Verifies the complete end-to-end workflow:
1. Recording water intake updates telemetry and progress.
2. Reaching 2,000 mL marks day as completed and updates streak.
3. New consecutive day completion increments streak exactly once.
4. Logging beyond goal on the same day is idempotent (no duplicate increments).
5. Closing and reopening the application preserves streak visibility and count.
6. Missed days correctly reset the current streak while preserving longest streak.
7. Midnight rollover resets daily intake and allows new streak completion.
"""
import tempfile
from pathlib import Path
from datetime import date, timedelta
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


def test_end_to_end_goal_completion_and_dashboard_refresh(qapp):
    """
    Simulates the exact user scenario:
    User logs intake reaching and exceeding 2,000 mL, ensuring streak
    updates immediately on dashboard and triggers celebration.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.daily_hydration_goal_ml = 2000
        cm.save()

        engine = ReminderEngine(cm)
        dash = DashboardWindow(cm, engine)

        # Baseline: 0 mL logged
        assert cm.settings.streak_current == 0
        assert "0 / 2,000 mL" in dash.streak_card.lbl_intake_numbers.text()
        assert "🔥 0-Day Streak" in dash.streak_card.lbl_streak_count.text()
        assert dash.streak_card.lbl_status.text() == "⏳ In Progress"
        assert dash.streak_card.is_celebration_active is False

        # Step 1: Log 500 mL -> 500 / 2,000 (25%)
        dash._quick_log_water(500)
        assert cm.settings.today_intake_ml == 500
        assert cm.settings.streak_current == 0
        assert "500 / 2,000 mL" in dash.streak_card.lbl_intake_numbers.text()
        assert dash.streak_card.lbl_pct.text() == "25%"
        assert dash.streak_card.is_celebration_active is False

        # Step 2: Log 1,000 mL -> 1,500 / 2,000 (75%)
        engine.on_user_drank_water(1000)
        assert cm.settings.today_intake_ml == 1500
        assert cm.settings.streak_current == 0
        assert "1,500 / 2,000 mL" in dash.streak_card.lbl_intake_numbers.text()
        assert dash.streak_card.lbl_pct.text() == "75%"

        # Step 3: Log 500 mL -> Reaching 2,000 mL (100% Goal Met!)
        # Must immediately update streak to 1 and trigger celebration
        dash._quick_log_water(500)
        assert cm.settings.today_intake_ml == 2000
        assert cm.settings.streak_current == 1
        assert cm.settings.streak_longest == 1
        assert cm.settings.streak_celebrated_today is True
        assert cm.settings.streak_last_completed_date == date.today().isoformat()

        # Check UI components
        assert "2,000 / 2,000 mL" in dash.streak_card.lbl_intake_numbers.text()
        assert dash.streak_card.lbl_pct.text() == "100%"
        assert dash.streak_card.lbl_status.text() == "✨ Goal Completed!"
        assert "🔥 1-Day Streak" in dash.streak_card.lbl_streak_count.text()
        assert dash.streak_card.is_celebration_active is True
        assert "Goal Complete! 🔥 You're on a 1-Day Streak!" in dash.streak_card.lbl_celebration_text.text()

        # Step 4: User logs additional 500 mL (2,500 mL total, matching user screenshot)
        dash._quick_log_water(500)
        assert cm.settings.today_intake_ml == 2500
        assert cm.settings.streak_current == 1  # Streak count MUST remain 1 (no duplicate increment)
        assert "2,500 / 2,000 mL" in dash.streak_card.lbl_intake_numbers.text()
        assert "🔥 1-Day Streak" in dash.streak_card.lbl_streak_count.text()
        assert dash.streak_card.lbl_status.text() == "✨ Goal Completed!"


def test_app_restart_persists_streak(qapp):
    """
    Verifies that closing and reopening the app preserves streak count and completion state.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        
        # Session 1: Complete today's goal
        cm1 = ConfigManager(custom_path=config_path)
        engine1 = ReminderEngine(cm1)
        engine1.on_user_drank_water(2000)
        assert cm1.settings.streak_current == 1
        
        # Simulate app close: engine1 and cm1 discarded
        del engine1
        del cm1

        # Session 2: Fresh app launch from saved config
        cm2 = ConfigManager(custom_path=config_path)
        engine2 = ReminderEngine(cm2)
        dash2 = DashboardWindow(cm2, engine2)

        # Streak and completion must be restored immediately
        assert cm2.settings.streak_current == 1
        assert "🔥 1-Day Streak" in dash2.streak_card.lbl_streak_count.text()
        assert dash2.streak_card.lbl_status.text() == "✨ Goal Completed!"
        assert "2,000 / 2,000 mL" in dash2.streak_card.lbl_intake_numbers.text()


def test_consecutive_days_increment_and_missed_day_reset():
    """
    Simulates consecutive day tracking and missed day reset across date boundaries.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        
        d1 = date(2026, 10, 15)
        d2 = date(2026, 10, 16)
        d3 = date(2026, 10, 17)
        d5 = date(2026, 10, 19)  # Missed d4 (Oct 18)

        # Day 1: complete goal
        tracker = cm.settings
        from src.streak_tracker import StreakTracker, StreakEvent
        st = StreakTracker(cm)
        ev1 = st.record_intake(2000, current_date=d1)
        assert ev1 == StreakEvent.GOAL_REACHED_FIRST_TIME
        assert cm.settings.streak_current == 1

        # Day 2: consecutive completion -> streak becomes 2
        ev2 = st.record_intake(2000, current_date=d2)
        assert ev2 == StreakEvent.GOAL_REACHED_FIRST_TIME
        assert cm.settings.streak_current == 2

        # Day 3: consecutive completion -> streak becomes 3
        ev3 = st.record_intake(2000, current_date=d3)
        assert ev3 == StreakEvent.GOAL_REACHED_FIRST_TIME
        assert cm.settings.streak_current == 3
        assert cm.settings.streak_longest == 3

        # Day 5 (Oct 19): Reopening after missing Oct 18
        st.check_rollover(current_date=d5)
        assert cm.settings.streak_current == 0  # Reset due to missed day
        assert cm.settings.streak_longest == 3  # Longest streak preserved!

        # Completing Day 5 restarts streak at 1
        ev5 = st.record_intake(2000, current_date=d5)
        assert ev5 == StreakEvent.GOAL_REACHED_FIRST_TIME
        assert cm.settings.streak_current == 1
        assert cm.settings.streak_longest == 3


def test_reset_to_defaults_propagates_to_running_engine_and_streak():
    """Verifies that reset_to_defaults immediately updates running ReminderEngine and StreakTracker."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.reminder_interval_minutes = 99
        cm.settings.daily_hydration_goal_ml = 5000
        cm.save()

        engine = ReminderEngine(cm)
        assert engine.settings.reminder_interval_minutes == 99
        assert engine.streak_tracker.settings.daily_hydration_goal_ml == 5000

        # Reset to defaults
        cm.reset_to_defaults()
        assert cm.settings.reminder_interval_minutes == 45
        assert cm.settings.daily_hydration_goal_ml == 2000

        # Live engine and streak tracker must immediately see new values
        assert engine.settings.reminder_interval_minutes == 45
        assert engine.streak_tracker.settings.daily_hydration_goal_ml == 2000


def test_dismiss_companion_guarantees_idle_and_reschedules():
    """Verifies that dismissing the companion window always clears waiting states and reschedules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.reminder_interval_minutes = 45
        cm.save()

        from src.reminder_engine import ReminderState
        engine = ReminderEngine(cm)
        engine._set_state(ReminderState.WAITING_FOR_RESPONSE)
        engine._target_time = None

        engine.on_user_dismissed()
        assert engine.state == ReminderState.IDLE
        assert engine._target_time is not None
        assert engine.get_seconds_remaining() > 0
