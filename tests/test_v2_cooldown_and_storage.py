"""
Unit and integration tests for Spider-Man Water Buddy v2.0:
- Manual water logging with hard 30-minute minimum cooldown
- Monotonic, wall-clock, and boot ID tracking
- Clock tampering resilience (backwards/forwards jumps)
- Thread-safe concurrent logging race conditions
- Atomic writes, rotating backups, and corruption recovery
- Clamping of hand-edited cooldowns below 30
"""
import tempfile
import time
import json
import threading
from pathlib import Path
from datetime import date, timedelta
import pytest

from src.config import ConfigManager, AppSettings
from src.streak_tracker import StreakTracker, StreakEvent, LogResult
from src.reminder_engine import ReminderEngine, ReminderState


def test_first_click_accepted_immediately():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        st = StreakTracker(cm)

        # Fresh install: remaining cooldown must be 0
        assert st.get_cooldown_remaining() == 0

        res = st.log_water(250, is_manual=True)
        assert res.ok is True
        assert res.added_ml == 250
        assert res.reason == "ok"
        assert res.remaining_seconds == 30 * 60
        assert cm.settings.today_intake_ml == 250
        assert cm.settings.today_manual_logs == 1
        assert cm.settings.today_reminders_completed == 0


def test_second_click_before_30_min_rejected():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        st = StreakTracker(cm)

        now_w = 1000000.0
        now_m = 50000.0

        # Log 1 at t=0
        res1 = st.log_water(250, is_manual=True, now_wall=now_w, now_mono=now_m)
        assert res1.ok is True

        # Log 2 at t=15 minutes (900 seconds) -> Rejected!
        res2 = st.log_water(250, is_manual=True, now_wall=now_w + 900, now_mono=now_m + 900)
        assert res2.ok is False
        assert res2.reason == "cooldown"
        assert res2.added_ml == 0
        assert res2.remaining_seconds == 900  # Exactly 15 min remaining
        assert cm.settings.today_intake_ml == 250
        assert cm.settings.today_manual_logs == 1


def test_click_at_30_min_accepted():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        st = StreakTracker(cm)

        now_w = 1000000.0
        now_m = 50000.0

        st.log_water(250, is_manual=True, now_wall=now_w, now_mono=now_m)

        # Log 2 at exactly 30:00 (1800 seconds) -> Accepted!
        res2 = st.log_water(250, is_manual=True, now_wall=now_w + 1800, now_mono=now_m + 1800)
        assert res2.ok is True
        assert res2.added_ml == 250
        assert cm.settings.today_intake_ml == 500
        assert cm.settings.today_manual_logs == 2


def test_rapid_concurrent_clicks_exactly_one_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(custom_path=Path(tmpdir) / "settings.json")
        st = StreakTracker(cm)

        results = []
        threads = []

        def worker():
            res = st.log_water(250, is_manual=True)
            results.append(res)

        # Launch 10 threads concurrently racing to log water
        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r for r in results if r.ok]
        rejections = [r for r in results if not r.ok]

        assert len(successes) == 1, "Exactly one thread must succeed in a concurrent race"
        assert len(rejections) == 9
        assert cm.settings.today_intake_ml == 250


def test_restart_during_cooldown_preserves_cooldown():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "settings.json"
        now_w = 2000000.0
        now_m = 10000.0

        # Session 1: log water at t=0
        cm1 = ConfigManager(custom_path=cfg)
        st1 = StreakTracker(cm1)
        st1.log_water(250, is_manual=True, now_wall=now_w, now_mono=now_m)
        assert cm1.settings.today_intake_ml == 250

        # Session 2: App restarted 10 minutes later (600s) on same boot
        cm2 = ConfigManager(custom_path=cfg)
        st2 = StreakTracker(cm2)
        rem = st2.get_cooldown_remaining(now_wall=now_w + 600, now_mono=now_m + 600)
        assert rem == 1200  # 20 minutes remaining

        # Attempt to log is rejected
        res = st2.log_water(250, is_manual=True, now_wall=now_w + 600, now_mono=now_m + 600)
        assert res.ok is False
        assert res.reason == "cooldown"
        assert res.remaining_seconds == 1200


def test_midnight_during_cooldown_resets_total_but_enforces_cooldown():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=cfg)
        st = StreakTracker(cm)

        # Log at 23:50 on Day 1
        d1 = date(2026, 10, 15)
        now_w = 1000000.0
        now_m = 50000.0
        st.log_water(250, is_manual=True, current_date=d1, now_wall=now_w, now_mono=now_m)
        assert cm.settings.today_intake_ml == 250

        # Attempt log at 00:05 on Day 2 (15 minutes later = 900 seconds)
        d2 = date(2026, 10, 16)
        res = st.log_water(250, is_manual=True, current_date=d2, now_wall=now_w + 900, now_mono=now_m + 900)

        # Must be rejected because 15 minutes of cooldown remain
        assert res.ok is False
        assert res.reason == "cooldown"
        assert res.remaining_seconds == 900
        # Daily total reset for the new day
        assert cm.settings.today_intake_ml == 0
        # Yesterday archived in history
        assert len(cm.settings.daily_history) == 1
        assert cm.settings.daily_history[0]["total_ml"] == 250


def test_cooldown_hard_minimum_30_clamped_on_load_and_save():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "settings.json"
        
        # User tries to hand-edit cooldown to 5 minutes
        bad_json = {
            "schema_version": 2,
            "cooldown_minutes": 5,
            "daily_hydration_goal_ml": 2000,
        }
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump(bad_json, f)

        cm = ConfigManager(custom_path=cfg)
        assert cm.settings.cooldown_minutes == 30, "Cooldown must be clamped to 30 on load"

        # User tries to set cooldown to 10 via settings object
        cm.settings.cooldown_minutes = 10
        cm.save()

        # Reload from disk
        cm2 = ConfigManager(custom_path=cfg)
        assert cm2.settings.cooldown_minutes == 30, "Cooldown must be clamped to 30 on save"


def test_clock_moved_backwards_does_not_extend_beyond_cooldown():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=cfg)
        st = StreakTracker(cm)

        now_w = 1000000.0
        now_m = 50000.0
        st.log_water(250, is_manual=True, now_wall=now_w, now_mono=now_m)

        # Clock jumped 1 hour into the past (wall clock goes from 1,000,000 to 996,400)
        # Monotonic time advances normally (+300s = 5 minutes)
        rem = st.get_cooldown_remaining(now_wall=now_w - 3600, now_mono=now_m + 300)
        # Must not extend beyond 30 min (1800s); in fact, monotonic gives 25 min (1500s)
        assert rem <= 1800
        assert rem == 1500


def test_corrupt_config_restores_from_rotating_backups():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=cfg)
        cm.settings.user_name = "Peter Parker"
        cm.settings.daily_hydration_goal_ml = 2500
        cm.save()  # Creates backup.1

        # Corrupt settings.json with invalid bytes
        with open(cfg, "w", encoding="utf-8") as f:
            f.write("GARBAGE DATA {{{ NOT JSON")

        cm_recovered = ConfigManager(custom_path=cfg)
        assert cm_recovered.corruption_detected is True
        assert cm_recovered.recovered_from_backup is True
        assert cm_recovered.settings.user_name == "Peter Parker"
        assert cm_recovered.settings.daily_hydration_goal_ml == 2500

        # Corrupt file must be preserved
        corrupt_files = list(Path(tmpdir).glob("settings.json.corrupt.*"))
        assert len(corrupt_files) == 1
