"""
Comprehensive Automated Test Suite for Spider-Man Water Buddy.
Covers Configuration, Validation, Corruption Recovery, Reminder Engine State Machine,
Quiet Hours (including midnight-crossing), Hydration Tracking, and Desktop Positioning.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, date, time, timedelta

import logging
logging.basicConfig(level=logging.CRITICAL)

# Set headless environment for Qt tests
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.config import ConfigManager, AppSettings
from src.reminder_engine import ReminderEngine, ReminderState
from src.companion_window import CompanionWindow
from src.startup_manager import StartupManager

app = QApplication.instance() or QApplication(sys.argv)


def test_config_validation_and_recovery():
    print("[TEST] Running Config Validation & Recovery...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)

        # 1. Validation boundaries
        cm.settings.reminder_interval_minutes = 99999
        cm.settings.snooze_duration_minutes = -50
        cm.settings.character_scale = 10.0
        cm.settings.corner_position = "invalid-corner"
        cm.settings.quiet_hours_start = "bad-time"
        cm.save()

        # Reload and verify clamped values
        cm.load()
        assert cm.settings.reminder_interval_minutes == 720, "Interval should be clamped to 720"
        assert cm.settings.snooze_duration_minutes == 1, "Snooze should be clamped to 1"
        assert cm.settings.character_scale == 2.0, "Scale should be clamped to 2.0"
        assert cm.settings.corner_position == "top-right", "Corner should fallback to top-right"
        assert cm.settings.quiet_hours_start == "00:00", "Bad time should fallback to 00:00"

        # 2. Corruption recovery
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON CORRUPTED DATA !!!")
        
        # Reloading should automatically recover from backup or safe defaults
        recovered = cm.load()
        assert recovered.companion_name == "Spider-Man", "Should recover valid settings or defaults"
        print("  -> Config Validation & Recovery: PASSED [OK]")


def test_reminder_engine_lifecycle():
    print("[TEST] Running Reminder Engine Lifecycle...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.reminder_interval_minutes = 30
        cm.settings.snooze_duration_minutes = 10
        cm.settings.retry_interval_minutes = 5
        cm.settings.quiet_hours_enabled = False
        cm.save()

        engine = ReminderEngine(cm)

        # Initial state: IDLE
        assert engine.state == ReminderState.IDLE, "Initial state must be IDLE"
        assert engine.get_seconds_remaining() > 0, "Remaining seconds must be positive"

        # Trigger reminder
        triggered = []
        engine.reminderTriggered.connect(lambda: triggered.append(True))
        engine.trigger_now()

        assert len(triggered) == 1, "reminderTriggered must be emitted"
        assert engine.state == ReminderState.WAITING_FOR_RESPONSE, "State must be WAITING_FOR_RESPONSE"

        # User clicks SNOOZE
        engine.on_user_snoozed(custom_minutes=15)
        assert engine.state == ReminderState.SNOOZED, "State must transition to SNOOZED"
        assert engine.get_seconds_remaining() > 800, "Snooze target must be around 15 minutes"

        # Trigger again and user clicks NO (retry)
        engine.trigger_now()
        engine.on_user_declined()
        assert engine.state == ReminderState.RETRY_SCHEDULED, "State must transition to RETRY_SCHEDULED"
        assert engine.get_seconds_remaining() <= 300, "Retry target must be around 5 minutes"

        # Trigger again and user clicks YES (water drank)
        stats = []
        engine.statsUpdated.connect(lambda count, ml: stats.append((count, ml)))
        engine.trigger_now()
        engine.on_user_drank_water(ml=300)

        assert engine.settings.today_reminders_completed == 1, "Completed reminders must increment"
        assert engine.settings.today_intake_ml == 300, "Intake ml must increment"
        assert engine.state == ReminderState.IDLE, "State must reset to IDLE after YES"

        # Pause and resume
        engine.pause_reminders(True)
        assert engine.state == ReminderState.PAUSED, "State must be PAUSED"
        assert engine.get_seconds_remaining() == -1, "Paused countdown should return -1"

        engine.pause_reminders(False)
        assert engine.state == ReminderState.IDLE, "State must be IDLE after resume"

        print("  -> Reminder Engine Lifecycle: PASSED [OK]")


def test_quiet_hours_midnight_crossing():
    print("[TEST] Running Quiet Hours (Midnight Crossing)...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.quiet_hours_enabled = True
        cm.settings.quiet_hours_start = "22:00"
        cm.settings.quiet_hours_end = "08:00"
        cm.save()

        engine = ReminderEngine(cm)

        # 23:30 (during quiet hours)
        dt_night = datetime(2026, 10, 15, 23, 30)
        assert engine.is_in_quiet_hours(dt_night) is True, "23:30 must be in quiet hours"

        # 04:15 (during quiet hours next morning)
        dt_morning = datetime(2026, 10, 16, 4, 15)
        assert engine.is_in_quiet_hours(dt_morning) is True, "04:15 must be in quiet hours"

        # 14:00 (outside quiet hours)
        dt_afternoon = datetime(2026, 10, 15, 14, 0)
        assert engine.is_in_quiet_hours(dt_afternoon) is False, "14:00 must NOT be in quiet hours"

        print("  -> Quiet Hours Midnight Crossing: PASSED [OK]")


def test_companion_window_and_placement():
    print("[TEST] Running Companion Window & Placement...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        win = CompanionWindow(cm)
        win.show()

        flags = win.windowFlags()
        assert bool(flags & Qt.WindowType.FramelessWindowHint), "Must be frameless"
        assert bool(flags & Qt.WindowType.WindowStaysOnTopHint), "Must be always on top"
        assert win.testAttribute(Qt.WA_TranslucentBackground), "Must be translucent"

        # Test placement calculations for corners
        for corner in ("top-right", "top-left", "bottom-right", "bottom-left"):
            cm.settings.corner_position = corner
            win.reposition()
            assert win.x() >= 0 and win.y() >= 0, f"Position for {corner} must be within screen"

        # Test click-through toggle
        win.apply_click_through(True)
        win.apply_click_through(False)

        print("  -> Companion Window & Placement: PASSED [OK]")


def run_all_tests():
    test_config_validation_and_recovery()
    test_reminder_engine_lifecycle()
    test_quiet_hours_midnight_crossing()
    test_companion_window_and_placement()
    print("\n=======================================================")
    print(" ALL AUTOMATED ARCHITECTURE & ENGINE TESTS PASSED! [OK]")
    print("=======================================================")


if __name__ == "__main__":
    run_all_tests()
    sys.exit(0)
