import tempfile
from pathlib import Path
from datetime import date, timedelta
import pytest

from src.config import ConfigManager
from src.streak_tracker import StreakTracker, StreakEvent


def test_initial_state_zero_intake():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        tracker = StreakTracker(cm)

        info = tracker.get_info()
        assert info.current_streak == 0
        assert info.longest_streak == 0
        assert info.today_intake_ml == 0
        assert info.daily_goal_ml == 2000
        assert info.is_completed_today is False
        assert info.progress_percentage == 0


def test_partial_intake_does_not_complete_goal():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        tracker = StreakTracker(cm)

        today = date(2026, 10, 17)
        event = tracker.record_intake(500, current_date=today)
        assert event == StreakEvent.INTAKE_RECORDED

        info = tracker.get_info(current_date=today)
        assert info.today_intake_ml == 500
        assert info.progress_percentage == 25
        assert info.is_completed_today is False
        assert info.current_streak == 0

        event2 = tracker.record_intake(1000, current_date=today)
        assert event2 == StreakEvent.INTAKE_RECORDED
        info2 = tracker.get_info(current_date=today)
        assert info2.today_intake_ml == 1500
        assert info2.progress_percentage == 75
        assert info2.is_completed_today is False
        assert info2.current_streak == 0


def test_reaching_goal_increments_streak_and_celebrates():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        tracker = StreakTracker(cm)

        today = date(2026, 10, 17)
        tracker.record_intake(1500, current_date=today)
        event = tracker.record_intake(500, current_date=today)

        assert event == StreakEvent.GOAL_REACHED_FIRST_TIME
        info = tracker.get_info(current_date=today)
        assert info.today_intake_ml == 2000
        assert info.progress_percentage == 100
        assert info.is_completed_today is True
        assert info.current_streak == 1
        assert info.longest_streak == 1
        assert info.celebrated_today is True


def test_duplicate_intake_on_same_day_does_not_reincrement_streak():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        tracker = StreakTracker(cm)

        today = date(2026, 10, 17)
        tracker.record_intake(2000, current_date=today)

        # Log additional water
        event = tracker.record_intake(500, current_date=today)
        assert event == StreakEvent.INTAKE_RECORDED  # Not a new goal completion

        info = tracker.get_info(current_date=today)
        assert info.today_intake_ml == 2500
        assert info.progress_percentage == 125
        assert info.is_completed_today is True
        assert info.current_streak == 1  # Streak stayed 1, never 2
        assert info.longest_streak == 1


def test_consecutive_days_increments_streak():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        tracker = StreakTracker(cm)

        day1 = date(2026, 10, 15)
        tracker.record_intake(2000, current_date=day1)
        assert tracker.get_info(current_date=day1).current_streak == 1

        day2 = date(2026, 10, 16)
        tracker.check_rollover(current_date=day2)
        # Before logging on day 2, streak is still active from yesterday
        assert tracker.get_info(current_date=day2).current_streak == 1
        assert tracker.get_info(current_date=day2).is_completed_today is False
        assert tracker.get_info(current_date=day2).today_intake_ml == 0

        # Complete day 2
        event = tracker.record_intake(2000, current_date=day2)
        assert event == StreakEvent.GOAL_REACHED_FIRST_TIME
        assert tracker.get_info(current_date=day2).current_streak == 2
        assert tracker.get_info(current_date=day2).longest_streak == 2

        # Complete day 3
        day3 = date(2026, 10, 17)
        tracker.check_rollover(current_date=day3)
        tracker.record_intake(2000, current_date=day3)
        assert tracker.get_info(current_date=day3).current_streak == 3
        assert tracker.get_info(current_date=day3).longest_streak == 3


def test_missed_day_resets_streak_to_zero():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        tracker = StreakTracker(cm)

        day1 = date(2026, 10, 15)
        tracker.record_intake(2000, current_date=day1)
        assert tracker.get_info(current_date=day1).current_streak == 1

        # Day 2: incomplete (only 500 mL)
        day2 = date(2026, 10, 16)
        tracker.check_rollover(current_date=day2)
        tracker.record_intake(500, current_date=day2)

        # Day 3: Day 2 was not completed, so streak must be reset to 0
        day3 = date(2026, 10, 17)
        tracker.check_rollover(current_date=day3)
        info = tracker.get_info(current_date=day3)
        assert info.current_streak == 0
        assert info.longest_streak == 1  # Longest streak preserved

        # Completing Day 3 starts a new streak of 1
        tracker.record_intake(2000, current_date=day3)
        assert tracker.get_info(current_date=day3).current_streak == 1
        assert tracker.get_info(current_date=day3).longest_streak == 1


def test_multiple_missed_days_while_app_closed():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        tracker = StreakTracker(cm)

        # Completed on Monday
        monday = date(2026, 10, 12)
        tracker.record_intake(2000, current_date=monday)
        assert tracker.get_info(current_date=monday).current_streak == 1

        # Reopened on Friday (3 full days missed)
        friday = date(2026, 10, 16)
        tracker.check_rollover(current_date=friday)
        info = tracker.get_info(current_date=friday)
        assert info.current_streak == 0
        assert info.today_intake_ml == 0
        assert info.is_completed_today is False


def test_persistence_across_app_restarts():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        
        # Session 1: complete goal
        today = date(2026, 10, 17)
        cm1 = ConfigManager(custom_path=config_path)
        tracker1 = StreakTracker(cm1)
        tracker1.record_intake(2000, current_date=today)
        assert tracker1.get_info(current_date=today).current_streak == 1

        # Session 2: fresh instance loads from disk
        cm2 = ConfigManager(custom_path=config_path)
        tracker2 = StreakTracker(cm2)
        info2 = tracker2.get_info(current_date=today)
        assert info2.current_streak == 1
        assert info2.today_intake_ml == 2000
        assert info2.is_completed_today is True
        assert info2.celebrated_today is True


def test_invalid_and_corrupted_data_recovery():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        # Force negative / corrupt values
        cm.settings.today_intake_ml = -500
        cm.settings.streak_current = -10
        cm.settings.streak_longest = -5
        cm.settings.streak_last_completed_date = "invalid-date-string"
        cm.save()

        tracker = StreakTracker(cm)
        info = tracker.get_info()
        assert info.today_intake_ml == 0
        assert info.current_streak == 0
        assert info.longest_streak == 0


def test_input_validation_rejects_negative_or_zero_intake():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        tracker = StreakTracker(cm)

        assert tracker.record_intake(0) == StreakEvent.IGNORED
        assert tracker.record_intake(-250) == StreakEvent.IGNORED
        assert tracker.get_info().today_intake_ml == 0


def test_web_shield_protects_single_missed_day():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        t0 = date(2026, 10, 1)
        tracker = StreakTracker(cm, current_date=t0)

        # Day 1: reach goal
        res = tracker.log_water(2000, is_manual=False, current_date=t0)
        assert res.info.current_streak == 1

        # Enable Web Shield
        cm.settings.shield_available = True
        cm.save()

        # Day 2: skipped completely
        # Day 3: rollover check
        t2 = date(2026, 10, 3)
        tracker.check_rollover(current_date=t2)

        # Shield should have preserved streak=1
        info = tracker.get_info(current_date=t2)
        assert info.current_streak == 1
        assert cm.settings.shield_available is False
        assert cm.settings.shield_last_used == date(2026, 10, 2).isoformat()


def test_web_shield_does_not_protect_two_missed_days():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        t0 = date(2026, 10, 1)
        tracker = StreakTracker(cm, current_date=t0)

        # Day 1: reach goal
        res = tracker.log_water(2000, is_manual=False, current_date=t0)
        assert res.info.current_streak == 1

        cm.settings.shield_available = True
        cm.save()

        # Day 2 & 3 skipped -> Day 4
        t3 = date(2026, 10, 4)
        tracker.check_rollover(current_date=t3)

        info = tracker.get_info(current_date=t3)
        assert info.current_streak == 0
