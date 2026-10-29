"""
Authoritative Water Reminder Engine for Spider-Man Water Buddy v2.0.
Implements a strict finite-state machine with independent snooze, retry, quiet hours,
manual log cooldown integration, sleep/wake resilience, and midnight rollover.
"""
from enum import Enum, auto
from datetime import datetime, time, date, timedelta
import logging
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal
from src.config import ConfigManager, AppSettings
from src.streak_tracker import StreakTracker, StreakEvent, StreakInfo, LogResult

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
    cooldownTick = Signal(int)  # seconds remaining in manual log cooldown
    statsUpdated = Signal(int, int)  # reminders completed count, total ml logged
    streakUpdated = Signal(object)  # StreakInfo
    goalCelebrated = Signal(str)  # Celebration message
    intakeChanged = Signal(object)  # LogResult

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.settings = config_manager.settings
        self.streak_tracker = StreakTracker(self.config_manager)

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
        """Resets today's stats and updates streak continuity if calendar date changed."""
        rolled_over = self.streak_tracker.check_rollover()
        if rolled_over:
            self.statsUpdated.emit(0, 0)
            info = self.streak_tracker.get_info()
            self.streakUpdated.emit(info)

    def on_system_wake(self) -> None:
        """Called upon system resume from sleep or hibernate (WM_POWERBROADCAST)."""
        logger.info("System wake event received. Re-evaluating date and scheduler...")
        self._check_daily_date_reset()
        now = datetime.now()
        if self._target_time and now >= self._target_time:
            self._trigger_reminder()
        else:
            self.reset_schedule()

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
            return start_t <= current_time < end_t
        else:
            return current_time >= start_t or current_time < end_t

    def get_seconds_until_quiet_hours_end(self, dt: Optional[datetime] = None) -> int:
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
        """Calculates next reminder deadline based on settings and state."""
        self._check_daily_date_reset()

        if self.settings.reminders_paused or not self.settings.reminders_enabled:
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
        logger.info(f"Next recurring reminder scheduled for: {self._target_time.strftime('%H:%M:%S')}")

    def _set_state(self, new_state: ReminderState) -> None:
        if self.state != new_state:
            self.state = new_state
            logger.info(f"ReminderEngine state -> {new_state.name}")
            self.stateChanged.emit(new_state)

    def _on_heartbeat(self) -> None:
        """Authoritative 1-second tick: checks rollover, countdowns, and cooldowns."""
        self._check_daily_date_reset()

        # Emit cooldown tick for manual water logging
        cooldown_rem = self.streak_tracker.get_cooldown_remaining()
        self.cooldownTick.emit(cooldown_rem)

        if self.state == ReminderState.PAUSED or not self.settings.reminders_enabled:
            self.timerTick.emit(-1)
            return

        now = datetime.now()

        # Check quiet hours transition
        if self.is_in_quiet_hours(now) and self.state in (
            ReminderState.IDLE,
            ReminderState.SNOOZED,
            ReminderState.RETRY_SCHEDULED,
            ReminderState.WAITING_FOR_RESPONSE,
        ):
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
    def on_user_drank_water(self, ml: Optional[int] = None, from_reminder: bool = False) -> bool:
        """
        User clicked YES or logged water intake.
        If from_reminder is True, strictly validates reminder window (CRIT-01).
        """
        if from_reminder and self.state not in (ReminderState.WAITING_FOR_RESPONSE, ReminderState.REMINDER_DUE):
            logger.warning("on_user_drank_water called from reminder outside response window.")
            return False

        self._check_daily_date_reset()
        amount = ml if (ml is not None and ml > 0) else 250
        res = self.streak_tracker.log_water(amount=amount, is_manual=False)

        self.statsUpdated.emit(self.settings.today_reminders_completed, self.settings.today_intake_ml)
        self.streakUpdated.emit(res.info)
        self.intakeChanged.emit(res)

        if res.event == StreakEvent.GOAL_REACHED_FIRST_TIME:
            msg = f"Goal Complete! 🔥 You're on a {res.info.current_streak}-Day Streak!"
            self.goalCelebrated.emit(msg)

        # Reset schedule for next recurring interval
        self.reset_schedule()
        return True

    def log_from_reminder(self, amount: int = 250) -> bool:
        """Explicit entry point for reminder responses (CRIT-01)."""
        return self.on_user_drank_water(amount, from_reminder=True)


    def log_manual(self, amount: int = 250) -> LogResult:
        """
        User clicked YES, I DRANK 💧 manual button on dashboard, companion, or tray.
        Enforces 30-minute minimum cooldown. Dismisses active reminder if present.
        """
        self._check_daily_date_reset()
        res = self.streak_tracker.log_water(amount=amount, is_manual=True)

        if res.ok:
            # If an active reminder was waiting, manual drinking satisfies it
            if self.state == ReminderState.WAITING_FOR_RESPONSE:
                self._set_state(ReminderState.IDLE)

            self.statsUpdated.emit(self.settings.today_reminders_completed, self.settings.today_intake_ml)
            self.streakUpdated.emit(res.info)
            self.intakeChanged.emit(res)

            if res.event in (StreakEvent.GOAL_REACHED_FIRST_TIME, StreakEvent.MILESTONE_REACHED):
                msg = f"Goal Complete! 🔥 You're on a {res.info.current_streak}-Day Streak!"
                self.goalCelebrated.emit(msg)

            # Reset next recurring reminder from now
            self.reset_schedule()

        return res

    def get_streak_info(self) -> StreakInfo:
        return self.streak_tracker.get_info()

    def on_user_snoozed(self, custom_minutes: Optional[int] = None) -> None:
        """User clicked Snooze."""
        mins = custom_minutes or self.settings.snooze_duration_minutes
        mins = max(1, min(120, mins))

        now = datetime.now()
        self._target_time = now + timedelta(minutes=mins)
        self._set_state(ReminderState.SNOOZED)
        logger.info(f"Snoozed for {mins} minutes (Target: {self._target_time.strftime('%H:%M:%S')})")

    def on_user_declined(self) -> None:
        """User clicked NO / Not Yet (CRIT-03)."""
        mins = max(1, min(120, self.settings.retry_interval_minutes))
        now = datetime.now()
        self._target_time = now + timedelta(minutes=mins)
        self._set_state(ReminderState.RETRY_SCHEDULED)
        logger.info(f"Retry scheduled in {mins} minutes (Target: {self._target_time.strftime('%H:%M:%S')})")

    def on_user_dismissed(self) -> None:
        """User closed popup or reminder auto-closed without response (MED-05)."""
        if self.state in (ReminderState.WAITING_FOR_RESPONSE, ReminderState.RETRY_SCHEDULED):
            # User dismissed the reminder. Respect user focus and prevent the irritating 5-minute nag loop
            # by scheduling the next reminder for the full configured reminder interval.
            mins = max(1, min(720, self.settings.reminder_interval_minutes))
            now = datetime.now()
            self._target_time = now + timedelta(minutes=mins)
            self._set_state(ReminderState.IDLE)
            logger.info(f"Reminder dismissed. Next reminder scheduled in {mins}m.")

    def pause_reminders(self, pause: bool = True) -> None:
        self.settings.reminders_paused = pause
        self.config_manager.save()
        if pause:
            self._set_state(ReminderState.PAUSED)
            self._target_time = None
        else:
            self.reset_schedule()

    def trigger_now(self) -> None:
        """Forces immediate reminder or re-surfaces active reminder (CRIT-04)."""
        if self.state in (ReminderState.WAITING_FOR_RESPONSE, ReminderState.REMINDER_DUE):
            logger.info("Remind Me Now called while already active; re-emitting reminderTriggered.")
            self.reminderTriggered.emit()
            return
        self._trigger_reminder()

    def get_seconds_remaining(self) -> int:
        if not self._target_time or self.state == ReminderState.PAUSED:
            return -1
        rem = int((self._target_time - datetime.now()).total_seconds())
        return max(0, rem)
