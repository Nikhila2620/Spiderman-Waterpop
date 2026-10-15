"""
Deterministic Water Reminder Engine for Spider-Man Water Buddy.
Implements an authoritative state machine with independent snooze, retry, quiet hours,
midnight-crossing schedules, and daily hydration tracking.
"""
from enum import Enum, auto
from datetime import datetime, time, date, timedelta
import logging
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal
from src.config import ConfigManager, AppSettings

logger = logging.getLogger("SpiderManWaterBuddy.ReminderEngine")


class ReminderState(Enum):
    IDLE = auto()
    REMINDER_DUE = auto()
    WAITING_FOR_RESPONSE = auto()
    SNOOZED = auto()
    RETRY_SCHEDULED = auto()
    QUIET_HOURS = auto()
    PAUSED = auto()


class ReminderEngine(QObject):
    """
    Authoritative water reminder scheduler and lifecycle manager.
    """

    # Signals
    reminderTriggered = Signal()
    stateChanged = Signal(ReminderState)
    timerTick = Signal(int)  # seconds remaining until next reminder
    statsUpdated = Signal(int, int)  # completed count, total ml logged

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.settings = config_manager.settings

        self.state = ReminderState.IDLE
        self._target_time: Optional[datetime] = None

        # Precision 1-second heartbeat timer
        self._heartbeat = QTimer(self)
        self._heartbeat.setInterval(1000)
        self._heartbeat.timeout.connect(self._on_heartbeat)

        self._check_daily_date_reset()
        self.reset_schedule()
        self._heartbeat.start()

    def _check_daily_date_reset(self) -> None:
        """Resets today's stats if the calendar date changed."""
        today_str = date.today().isoformat()
        if self.settings.last_tracking_date != today_str:
            self.settings.last_tracking_date = today_str
            self.settings.today_reminders_completed = 0
            self.settings.today_intake_ml = 0
            self.config_manager.save()
            self.statsUpdated.emit(0, 0)

    def is_in_quiet_hours(self, dt: Optional[datetime] = None) -> bool:
        """Determines if the specified datetime (or now) is within quiet hours."""
        if not self.settings.quiet_hours_enabled:
            return False

        dt = dt or datetime.now()
        current_time = dt.time()

        try:
            sh, sm = map(int, self.settings.quiet_hours_start.split(":"))
            eh, em = map(int, self.settings.quiet_hours_end.split(":"))
            start_t = time(sh, sm)
            end_t = time(eh, em)
        except Exception:
            return False

        if start_t == end_t:
            return False

        if start_t < end_t:
            # Same day interval (e.g. 13:00 to 15:00)
            return start_t <= current_time < end_t
        else:
            # Midnight crossing interval (e.g. 22:00 to 08:00)
            return current_time >= start_t or current_time < end_t

    def get_seconds_until_quiet_hours_end(self, dt: Optional[datetime] = None) -> int:
        """Calculates seconds until quiet hours expire."""
        dt = dt or datetime.now()
        try:
            eh, em = map(int, self.settings.quiet_hours_end.split(":"))
        except Exception:
            return 60

        target_dt = datetime.combine(dt.date(), time(eh, em))
        if target_dt <= dt:
            target_dt += timedelta(days=1)
        return max(1, int((target_dt - dt).total_seconds()))

    def reset_schedule(self) -> None:
        """Calculates the next reminder time based on current settings and state."""
        self._check_daily_date_reset()

        if self.settings.reminders_paused:
            self._set_state(ReminderState.PAUSED)
            self._target_time = None
            return

        if not self.settings.reminders_enabled:
            self._set_state(ReminderState.PAUSED)
            self._target_time = None
            return

        now = datetime.now()
        if self.is_in_quiet_hours(now):
            self._set_state(ReminderState.QUIET_HOURS)
            secs = self.get_seconds_until_quiet_hours_end(now)
            self._target_time = now + timedelta(seconds=secs)
            return

        # Normal recurring reminder
        interval_secs = self.settings.reminder_interval_minutes * 60
        self._target_time = now + timedelta(seconds=interval_secs)
        self._set_state(ReminderState.IDLE)
        logger.info(f"Scheduled next recurring reminder for: {self._target_time.strftime('%H:%M:%S')}")

    def _set_state(self, new_state: ReminderState) -> None:
        if self.state != new_state:
            self.state = new_state
            logger.info(f"ReminderEngine state -> {new_state.name}")
            self.stateChanged.emit(new_state)

    def _on_heartbeat(self) -> None:
        """Runs every second to evaluate state and time triggers."""
        self._check_daily_date_reset()

        if self.state == ReminderState.PAUSED or not self.settings.reminders_enabled:
            self.timerTick.emit(-1)
            return

        now = datetime.now()

        # If in quiet hours, make sure state reflects it
        if self.is_in_quiet_hours(now) and self.state in (ReminderState.IDLE, ReminderState.SNOOZED, ReminderState.RETRY_SCHEDULED):
            self._set_state(ReminderState.QUIET_HOURS)
            secs = self.get_seconds_until_quiet_hours_end(now)
            self._target_time = now + timedelta(seconds=secs)

        if not self._target_time:
            self.timerTick.emit(-1)
            return

        remaining = int((self._target_time - now).total_seconds())
        if remaining > 0:
            self.timerTick.emit(remaining)
        else:
            self.timerTick.emit(0)
            self._trigger_reminder()

    def _trigger_reminder(self) -> None:
        """Fires the reminder notification."""
        if self.state in (ReminderState.WAITING_FOR_RESPONSE, ReminderState.REMINDER_DUE):
            return

        now = datetime.now()
        if self.is_in_quiet_hours(now):
            self.reset_schedule()
            return

        self._set_state(ReminderState.WAITING_FOR_RESPONSE)
        self._target_time = None
        self.reminderTriggered.emit()

    # User response handlers
    def on_user_drank_water(self, ml: Optional[int] = None) -> None:
        """User clicked YES."""
        if self.state != ReminderState.WAITING_FOR_RESPONSE:
            # Allow manual trigger or celebration even if outside exact window
            pass

        self._check_daily_date_reset()
        self.settings.today_reminders_completed += 1
        if ml is not None and ml > 0:
            self.settings.today_intake_ml += ml

        self.config_manager.save()
        self.statsUpdated.emit(self.settings.today_reminders_completed, self.settings.today_intake_ml)

        # Reset schedule for next recurring interval
        self.reset_schedule()

    def on_user_snoozed(self, custom_minutes: Optional[int] = None) -> None:
        """User clicked Snooze."""
        mins = custom_minutes or self.settings.snooze_duration_minutes
        mins = max(1, min(120, mins))

        now = datetime.now()
        self._target_time = now + timedelta(minutes=mins)
        self._set_state(ReminderState.SNOOZED)
        logger.info(f"Snoozed for {mins} minutes (Target: {self._target_time.strftime('%H:%M:%S')})")

    def on_user_declined(self) -> None:
        """User clicked NO / Not Yet."""
        mins = max(1, min(120, self.settings.retry_interval_minutes))
        now = datetime.now()
        self._target_time = now + timedelta(minutes=mins)
        self._set_state(ReminderState.RETRY_SCHEDULED)
        logger.info(f"Retry scheduled in {mins} minutes (Target: {self._target_time.strftime('%H:%M:%S')})")

    def pause_reminders(self, pause: bool = True) -> None:
        """Pauses or resumes reminder schedule."""
        self.settings.reminders_paused = pause
        self.config_manager.save()
        if pause:
            self._set_state(ReminderState.PAUSED)
            self._target_time = None
        else:
            self.reset_schedule()

    def trigger_now(self) -> None:
        """Forces an immediate reminder trigger for testing."""
        self._trigger_reminder()

    def get_seconds_remaining(self) -> int:
        if not self._target_time or self.state == ReminderState.PAUSED:
            return -1
        rem = int((self._target_time - datetime.now()).total_seconds())
        return max(0, rem)
