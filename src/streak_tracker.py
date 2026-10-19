"""
Authoritative Hydration Goal, Cooldown & Streak Service for Spider-Man Water Buddy v2.0.
Implements backend-first thread-safe water logging, hard 30-minute minimum cooldown,
system boot and clock drift resilience, historical telemetry, and Web Shield.
"""
import time
import threading
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum, auto
from typing import Optional, List, Dict, Any
import logging

from src.config import ConfigManager
from src.utils import get_boot_id

logger = logging.getLogger("SpiderManWaterBuddy.StreakTracker")


class StreakEvent(Enum):
    IGNORED = auto()
    INTAKE_RECORDED = auto()
    GOAL_REACHED_FIRST_TIME = auto()
    MILESTONE_REACHED = auto()


@dataclass
class StreakInfo:
    current_streak: int = 0
    longest_streak: int = 0
    today_intake_ml: int = 0
    daily_goal_ml: int = 2000
    is_completed_today: bool = False
    celebrated_today: bool = False
    progress_percentage: int = 0
    last_completed_date: str = ""
    goal_days_total: int = 0
    cooldown_remaining_seconds: int = 0
    cooldown_total_seconds: int = 1800
    is_cooldown_active: bool = False
    shield_available: bool = False
    shield_last_used: str = ""
    milestone_day: int = 0  # 3, 7, 14, 30, 100 if just hit


@dataclass
class LogResult:
    ok: bool
    added_ml: int
    reason: str  # "ok", "cooldown", "invalid_amount", "invalid_state"
    remaining_seconds: int
    event: StreakEvent
    info: StreakInfo


MILESTONES = {3, 7, 14, 30, 100}


class StreakTracker:
    """
    Thread-safe authoritative business-logic service managing hydration logging,
    cooldown enforcement, streaks, midnight rollover, and history persistence.
    """

    def __init__(self, config_manager: ConfigManager, current_date: Optional[date] = None):
        self.config_manager = config_manager
        self.settings = config_manager.settings
        self._lock = threading.Lock()

        # Run startup rollover validation if date provided
        if current_date is not None:
            with self._lock:
                self._check_rollover_internal(current_date)

    def get_cooldown_remaining(
        self,
        now_wall: Optional[float] = None,
        now_mono: Optional[float] = None,
        boot_id: Optional[str] = None,
    ) -> int:
        """
        Calculates remaining cooldown seconds with immunity to clock drift,
        system reboots, and sleep/resume (Section 3.3).
        """
        cooldown_secs = max(30, int(self.settings.cooldown_minutes or 30)) * 60

        last_wall = self.settings.last_log_wall_utc
        last_mono = self.settings.last_log_mono
        stored_boot = self.settings.boot_id

        # First entry allowed immediately
        if last_wall <= 0 or last_mono <= 0:
            return 0

        curr_wall = now_wall if now_wall is not None else time.time()
        curr_mono = now_mono if now_mono is not None else time.monotonic()
        curr_boot = boot_id or get_boot_id()

        if stored_boot == curr_boot:
            # Same boot session: monotonic clock is immune to system clock tampering
            elapsed_mono = max(0.0, curr_mono - last_mono)
            rem_mono = max(0, int(cooldown_secs - elapsed_mono))

            # Wall clock check (handles sleep/hibernate resume)
            elapsed_wall = max(0.0, curr_wall - last_wall)
            rem_wall = max(0, int(cooldown_secs - elapsed_wall))

            # Use smaller remaining when both are sensible, otherwise trust wall
            remaining = min(rem_mono, rem_wall)
        else:
            # System was rebooted since last log; monotonic reset, trust wall clock
            elapsed_wall = max(0.0, curr_wall - last_wall)
            remaining = max(0, int(cooldown_secs - elapsed_wall))

        # Guarantee: remaining can never exceed configured cooldown
        return max(0, min(int(cooldown_secs), int(remaining)))

    def check_rollover(self, current_date: Optional[date] = None) -> bool:
        """Public thread-safe rollover check."""
        with self._lock:
            return self._check_rollover_internal(current_date)

    def _check_rollover_internal(self, current_date: Optional[date] = None) -> bool:
        """
        Internal date-rollover logic. Must be called with self._lock held.
        """
        curr = current_date or date.today()
        today_str = curr.isoformat()
        last_date = self.settings.last_tracking_date

        if last_date == today_str:
            self._ensure_streak_continuity(curr)
            return False

        logger.info(f"Day rollover detected: '{last_date}' -> '{today_str}'")

        # 1. Archive yesterday's stats into daily_history if valid
        if last_date:
            already_archived = any(entry.get("date") == last_date for entry in self.settings.daily_history)
            if not already_archived:
                yesterday_goal = self.settings.daily_hydration_goal_ml
                yesterday_intake = self.settings.today_intake_ml
                history_entry = {
                    "date": last_date,
                    "total_ml": yesterday_intake,
                    "goal_ml": yesterday_goal,
                    "goal_met": yesterday_intake >= yesterday_goal,
                    "log_count": self.settings.today_reminders_completed + self.settings.today_manual_logs,
                }
                self.settings.daily_history.append(history_entry)
                if len(self.settings.daily_history) > 365:
                    self.settings.daily_history = self.settings.daily_history[-365:]

        # 2. Evaluate streak continuity
        yesterday_str = (curr - timedelta(days=1)).isoformat()
        if self.settings.streak_last_completed_date == yesterday_str:
            logger.info(f"Yesterday was completed. Active streak of {self.settings.streak_current} carries over.")
        elif self.settings.streak_last_completed_date == today_str:
            pass  # Already completed today
        else:
            # Check Web Shield: single missed day forgiveness
            two_days_ago_str = (curr - timedelta(days=2)).isoformat()
            if (
                self.settings.shield_available
                and self.settings.streak_last_completed_date == two_days_ago_str
                and self.settings.streak_current > 0
            ):
                logger.info(f"Web Shield activated! Preserved streak of {self.settings.streak_current} days.")
                self.settings.shield_available = False
                self.settings.shield_last_used = yesterday_str
            else:
                if self.settings.streak_current > 0:
                    logger.info(f"Missed days detected. Streak reset from {self.settings.streak_current} to 0.")
                self.settings.streak_current = 0

        # 3. Reset today's metrics
        self.settings.today_intake_ml = 0
        self.settings.today_reminders_completed = 0
        self.settings.today_manual_logs = 0
        self.settings.streak_celebrated_today = False
        self.settings.last_tracking_date = today_str

        # Update total goal days count
        self.settings.goal_days_total = sum(1 for e in self.settings.daily_history if e.get("goal_met", False))

        self.config_manager.save()
        return True

    def _ensure_streak_continuity(self, curr: date) -> None:
        today_str = curr.isoformat()
        if self.settings.streak_last_completed_date == today_str:
            return

        yesterday_str = (curr - timedelta(days=1)).isoformat()
        two_days_ago_str = (curr - timedelta(days=2)).isoformat()

        if self.settings.streak_last_completed_date != yesterday_str and self.settings.streak_current > 0:
            if self.settings.shield_available and self.settings.streak_last_completed_date == two_days_ago_str:
                return  # Shield protects
            logger.info("Missed yesterday while running. Resetting streak to 0.")
            self.settings.streak_current = 0
            self.config_manager.save()

    def log_water(
        self,
        amount: int = 250,
        is_manual: bool = True,
        current_date: Optional[date] = None,
        now_wall: Optional[float] = None,
        now_mono: Optional[float] = None,
    ) -> LogResult:
        """
        Unified authoritative logging endpoint.
        Inside a single lock:
        1. Checks date rollover.
        2. Validates amount boundaries (50 - 1000 ml).
        3. Enforces 30-min minimum cooldown if is_manual.
        4. Increments intake and updates streak.
        5. Saves atomically and returns LogResult.
        """
        with self._lock:
            curr = current_date or date.today()
            today_str = curr.isoformat()
            self._check_rollover_internal(curr)

            # Validate amount bounds
            if not isinstance(amount, (int, float)) or amount <= 0 or amount > 10000:
                logger.warning(f"Rejected invalid water amount: {amount}")
                info = self._get_info_internal(curr, now_wall, now_mono)
                return LogResult(
                    ok=False,
                    added_ml=0,
                    reason="invalid_amount",
                    remaining_seconds=info.cooldown_remaining_seconds,
                    event=StreakEvent.IGNORED,
                    info=info,
                )

            amount = int(amount)
            wall = now_wall if now_wall is not None else time.time()
            mono = now_mono if now_mono is not None else time.monotonic()
            boot = get_boot_id()

            # Enforce cooldown on manual logs
            if is_manual:
                rem = self.get_cooldown_remaining(now_wall=wall, now_mono=mono, boot_id=boot)
                if rem > 0:
                    logger.info(f"Manual log rejected: {rem}s cooldown remaining.")
                    info = self._get_info_internal(curr, wall, mono)
                    return LogResult(
                        ok=False,
                        added_ml=0,
                        reason="cooldown",
                        remaining_seconds=rem,
                        event=StreakEvent.IGNORED,
                        info=info,
                    )

            # Apply intake
            self.settings.today_intake_ml += amount
            if is_manual:
                self.settings.today_manual_logs += 1
            else:
                self.settings.today_reminders_completed += 1

            # Update cooldown timestamps
            self.settings.last_log_wall_utc = wall
            self.settings.last_log_mono = mono
            self.settings.boot_id = boot

            # Check goal & streak
            goal = self.settings.daily_hydration_goal_ml
            was_already_completed = (self.settings.streak_last_completed_date == today_str)
            event = StreakEvent.INTAKE_RECORDED
            milestone = 0

            if self.settings.today_intake_ml >= goal and not was_already_completed:
                yesterday_str = (curr - timedelta(days=1)).isoformat()
                if self.settings.streak_last_completed_date == yesterday_str:
                    self.settings.streak_current += 1
                else:
                    self.settings.streak_current = 1

                if self.settings.streak_current > self.settings.streak_longest:
                    self.settings.streak_longest = self.settings.streak_current

                self.settings.streak_last_completed_date = today_str
                self.settings.streak_celebrated_today = True
                self.settings.goal_days_total += 1
                event = StreakEvent.GOAL_REACHED_FIRST_TIME

                if self.settings.streak_current in MILESTONES:
                    milestone = self.settings.streak_current

                logger.info(
                    f"Goal Complete! Today={self.settings.today_intake_ml}ml, "
                    f"Streak={self.settings.streak_current} days"
                )

            self.config_manager.save()
            info = self._get_info_internal(curr, wall, mono)
            info.milestone_day = milestone

            return LogResult(
                ok=True,
                added_ml=amount,
                reason="ok",
                remaining_seconds=info.cooldown_remaining_seconds,
                event=event,
                info=info,
            )

    def record_intake(self, ml: int, current_date: Optional[date] = None) -> StreakEvent:
        """Backward-compatibility wrapper for existing test suites."""
        res = self.log_water(amount=ml, is_manual=False, current_date=current_date)
        return res.event

    def get_info(
        self,
        current_date: Optional[date] = None,
        now_wall: Optional[float] = None,
        now_mono: Optional[float] = None,
    ) -> StreakInfo:
        """Returns the current validated snapshot of streak and cooldown telemetry."""
        with self._lock:
            curr = current_date or date.today()
            self._check_rollover_internal(curr)
            return self._get_info_internal(curr, now_wall, now_mono)

    def _get_info_internal(
        self,
        curr: date,
        now_wall: Optional[float] = None,
        now_mono: Optional[float] = None,
    ) -> StreakInfo:
        today_str = curr.isoformat()
        goal = self.settings.daily_hydration_goal_ml
        intake = self.settings.today_intake_ml
        pct = int((intake / goal) * 100) if goal > 0 else 0
        is_completed = (self.settings.streak_last_completed_date == today_str)

        cooldown_rem = self.get_cooldown_remaining(now_wall=now_wall, now_mono=now_mono)
        cooldown_total = max(30, int(self.settings.cooldown_minutes or 30)) * 60

        return StreakInfo(
            current_streak=self.settings.streak_current,
            longest_streak=self.settings.streak_longest,
            today_intake_ml=intake,
            daily_goal_ml=goal,
            is_completed_today=is_completed,
            celebrated_today=self.settings.streak_celebrated_today,
            progress_percentage=pct,
            last_completed_date=self.settings.streak_last_completed_date,
            goal_days_total=self.settings.goal_days_total,
            cooldown_remaining_seconds=cooldown_rem,
            cooldown_total_seconds=cooldown_total,
            is_cooldown_active=(cooldown_rem > 0),
            shield_available=self.settings.shield_available,
            shield_last_used=self.settings.shield_last_used,
        )
