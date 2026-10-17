"""
Daily Hydration Goal & Streak Tracker Service for Spider-Man Water Buddy.
Implements robust date-based streak logic, midnight rollover detection,
idempotent goal completion, and persistence via ConfigManager.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum, auto
from typing import Optional
import logging

from src.config import ConfigManager

logger = logging.getLogger("SpiderManWaterBuddy.StreakTracker")


class StreakEvent(Enum):
    IGNORED = auto()
    INTAKE_RECORDED = auto()
    GOAL_REACHED_FIRST_TIME = auto()


@dataclass
class StreakInfo:
    current_streak: int
    longest_streak: int
    today_intake_ml: int
    daily_goal_ml: int
    is_completed_today: bool
    celebrated_today: bool
    progress_percentage: int
    last_completed_date: str


class StreakTracker:
    """
    Business-logic service managing hydration goal verification,
    consecutive-day streaks, missed days, and celebration triggering.
    """

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.settings = config_manager.settings
        # Run startup validation & rollover check
        self.check_rollover()

    def check_rollover(self, current_date: Optional[date] = None) -> bool:
        """
        Detects if local calendar date has rolled over and handles
        streak continuity vs. streak expiration.
        Returns True if a date rollover occurred.
        """
        curr = current_date or date.today()
        today_str = curr.isoformat()
        last_date = self.settings.last_tracking_date

        if last_date == today_str:
            # Same day: ensure streak is still valid if user hasn't completed today
            self._ensure_streak_continuity(curr)
            return False

        logger.info(f"Day rollover detected: '{last_date}' -> '{today_str}'")

        # Check if yesterday was completed
        yesterday_str = (curr - timedelta(days=1)).isoformat()
        if self.settings.streak_last_completed_date == yesterday_str:
            # Streak carries over into today unbroken
            logger.info(f"Yesterday was completed. Active streak of {self.settings.streak_current} carries over.")
        elif self.settings.streak_last_completed_date == today_str:
            # Already completed today (edge case)
            pass
        else:
            # Yesterday or more days were missed: reset current streak
            if self.settings.streak_current > 0:
                logger.info(f"Missed days detected. Streak reset from {self.settings.streak_current} to 0.")
            self.settings.streak_current = 0

        # Reset today's transient metrics
        self.settings.today_intake_ml = 0
        self.settings.today_reminders_completed = 0
        self.settings.streak_celebrated_today = False
        self.settings.last_tracking_date = today_str

        self.config_manager.save()
        return True

    def _ensure_streak_continuity(self, curr: date) -> None:
        """Verifies that an uncompleted today hasn't inherited an expired streak."""
        today_str = curr.isoformat()
        if self.settings.streak_last_completed_date == today_str:
            return  # Already completed today

        yesterday_str = (curr - timedelta(days=1)).isoformat()
        if self.settings.streak_last_completed_date != yesterday_str and self.settings.streak_current > 0:
            logger.info("Missed yesterday while app was running. Resetting streak to 0.")
            self.settings.streak_current = 0
            self.config_manager.save()

    def record_intake(self, ml: int, current_date: Optional[date] = None) -> StreakEvent:
        """
        Validates and records water intake volume, calculates goal attainment,
        and safely increments the streak.
        """
        if not isinstance(ml, int) or ml <= 0:
            logger.warning(f"Rejected invalid water intake amount: {ml}")
            return StreakEvent.IGNORED

        curr = current_date or date.today()
        today_str = curr.isoformat()

        # Ensure date rollover is processed first
        self.check_rollover(curr)

        self.settings.today_intake_ml += ml
        goal = self.settings.daily_hydration_goal_ml
        was_already_completed = (self.settings.streak_last_completed_date == today_str)

        if self.settings.today_intake_ml >= goal and not was_already_completed:
            # First time reaching the goal today!
            yesterday_str = (curr - timedelta(days=1)).isoformat()
            if self.settings.streak_last_completed_date == yesterday_str:
                self.settings.streak_current += 1
            else:
                self.settings.streak_current = 1

            if self.settings.streak_current > self.settings.streak_longest:
                self.settings.streak_longest = self.settings.streak_current

            self.settings.streak_last_completed_date = today_str
            self.settings.streak_celebrated_today = True

            logger.info(
                f"Daily Goal Complete! Today={self.settings.today_intake_ml}ml, "
                f"Streak={self.settings.streak_current} days"
            )
            self.config_manager.save()
            return StreakEvent.GOAL_REACHED_FIRST_TIME

        self.config_manager.save()
        return StreakEvent.INTAKE_RECORDED

    def get_info(self, current_date: Optional[date] = None) -> StreakInfo:
        """Returns the current validated snapshot of streak telemetry."""
        curr = current_date or date.today()
        today_str = curr.isoformat()
        self.check_rollover(curr)

        goal = self.settings.daily_hydration_goal_ml
        intake = self.settings.today_intake_ml
        pct = int((intake / goal) * 100) if goal > 0 else 0
        is_completed = (self.settings.streak_last_completed_date == today_str)

        return StreakInfo(
            current_streak=self.settings.streak_current,
            longest_streak=self.settings.streak_longest,
            today_intake_ml=intake,
            daily_goal_ml=goal,
            is_completed_today=is_completed,
            celebrated_today=self.settings.streak_celebrated_today,
            progress_percentage=pct,
            last_completed_date=self.settings.streak_last_completed_date,
        )
