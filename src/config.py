"""
Configuration management for Spider-Man Water Buddy v2.0.
Provides atomic persistence, rotating backups, schema validation, corruption recovery,
and backward-compatible migration from v1.
"""
import os
import sys
import json
import time
import logging
import shutil
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger("SpiderManWaterBuddy.Config")

MAX_BACKUPS = 5


@dataclass
class AppSettings:
    schema_version: int = 2

    # First-run state
    first_run_completed: bool = False

    # Personalization
    companion_name: str = "Spider-Man"
    user_name: str = "Hero"
    custom_greeting: str = "Hey web-slinger! Take a cozy sip of water ☕💧"
    message_yes: str = "Thwip! Super hydrated! Your spider-sense is at 100%! 🌟"
    message_no: str = "Even superheroes need H2O... Snooze for a bit? 🕷️"
    message_snooze: str = "Snoozed for {minutes} min! Web-slinging back soon. ⏱️"

    # Reminder intervals (in minutes)
    reminder_interval_minutes: int = 45
    snooze_duration_minutes: int = 10
    retry_interval_minutes: int = 5
    reminders_enabled: bool = True
    reminders_paused: bool = False

    # Quiet hours & Daily schedule
    quiet_hours_enabled: bool = True
    quiet_hours_start: str = "22:00"  # 24h format HH:MM
    quiet_hours_end: str = "08:00"
    daily_active_hours_enabled: bool = False
    daily_active_start: str = "09:00"
    daily_active_end: str = "21:00"

    # Hydration tracking & Streak
    daily_hydration_goal_ml: int = 2000
    today_reminders_completed: int = 0
    today_manual_logs: int = 0
    today_intake_ml: int = 0
    last_tracking_date: str = ""
    streak_current: int = 0
    streak_longest: int = 0
    streak_last_completed_date: str = ""
    streak_celebrated_today: bool = False
    goal_days_total: int = 0
    shield_available: bool = False
    shield_last_used: str = ""
    daily_history: List[Dict[str, Any]] = field(default_factory=list)

    # Manual log cooldown (v2.0 requirement: hard minimum 30 minutes)
    cooldown_minutes: int = 30
    last_log_wall_utc: float = 0.0
    last_log_mono: float = 0.0
    boot_id: str = ""

    # Appearance & Window behavior
    corner_position: str = "top-right"  # "top-right", "top-left", "bottom-right", "bottom-left"
    window_offset_x: int = 0
    window_offset_y: int = 0
    character_scale: float = 1.0  # 0.75 to 1.5
    always_on_top: bool = True
    click_through_enabled: bool = False
    interaction_mode_shortcut: str = "Ctrl+Alt+W"
    animation_enabled: bool = True
    mouse_follow_enabled: bool = True
    performance_mode: bool = False
    sound_effects_enabled: bool = True

    # Windows Integration
    launch_at_startup: bool = False
    start_minimized: bool = False
    companion_visible: bool = True

    def validate(self) -> None:
        """Sanitizes and enforces strict validation boundaries on all settings."""
        if not self.companion_name or not self.companion_name.strip():
            self.companion_name = "Spider-Man"
        if not self.user_name or not self.user_name.strip():
            self.user_name = "Hero"

        # Constrain reminder intervals
        self.reminder_interval_minutes = max(1, min(720, int(self.reminder_interval_minutes)))
        self.snooze_duration_minutes = max(1, min(120, int(self.snooze_duration_minutes)))
        self.retry_interval_minutes = max(1, min(120, int(self.retry_interval_minutes)))

        # Enforce HARD MINIMUM 30 minutes for cooldown
        self.cooldown_minutes = max(30, int(self.cooldown_minutes or 30))

        # Goal and intake boundaries
        self.daily_hydration_goal_ml = max(100, min(10000, int(self.daily_hydration_goal_ml)))
        self.today_intake_ml = max(0, int(self.today_intake_ml))
        self.today_reminders_completed = max(0, int(self.today_reminders_completed))
        self.today_manual_logs = max(0, int(self.today_manual_logs))
        self.streak_current = max(0, int(self.streak_current))
        self.streak_longest = max(0, int(self.streak_longest))
        if self.streak_current > self.streak_longest:
            self.streak_longest = self.streak_current
        self.goal_days_total = max(0, int(self.goal_days_total))

        if not isinstance(self.streak_last_completed_date, str):
            self.streak_last_completed_date = ""
        elif self.streak_last_completed_date:
            try:
                date.fromisoformat(self.streak_last_completed_date)
            except Exception:
                self.streak_last_completed_date = ""
        self.streak_celebrated_today = bool(self.streak_celebrated_today)

        # Constrain scale
        self.character_scale = max(0.5, min(2.0, float(self.character_scale)))

        # Validate corner position
        valid_corners = {"top-right", "top-left", "bottom-right", "bottom-left"}
        if self.corner_position not in valid_corners:
            self.corner_position = "top-right"

        # Ensure valid time formats
        for time_field in ("quiet_hours_start", "quiet_hours_end", "daily_active_start", "daily_active_end"):
            val = getattr(self, time_field)
            if not isinstance(val, str) or len(val) != 5 or val[2] != ":":
                setattr(self, time_field, "00:00")
            else:
                try:
                    h, m = int(val[:2]), int(val[3:])
                    if not (0 <= h <= 23 and 0 <= m <= 59):
                        setattr(self, time_field, "00:00")
                except ValueError:
                    setattr(self, time_field, "00:00")

        if not isinstance(self.daily_history, list):
            self.daily_history = []


class ConfigManager:
    """
    Authoritative configuration and state manager for Spider-Man Water Buddy v2.0.
    Handles atomic writes, rotating backups, corruption recovery, and migration.
    """

    def __init__(self, custom_path: Optional[Path] = None):
        if custom_path:
            self.settings_dir = custom_path.parent
            self.settings_file = custom_path
        else:
            app_data = os.environ.get("APPDATA")
            if app_data:
                self.settings_dir = Path(app_data) / "SpiderManWaterBuddy"
            else:
                self.settings_dir = Path.home() / ".spiderman_water_buddy"
            self.settings_file = self.settings_dir / "settings.json"

        self.backup_file = self.settings_dir / "settings.backup.1"
        self.settings = AppSettings()
        self.corruption_detected = False
        self.recovered_from_backup = False
        self.ensure_directory()
        self.load()

    def ensure_directory(self) -> None:
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create settings directory {self.settings_dir}: {e}")

    def _get_backup_path(self, index: int) -> Path:
        return self.settings_dir / f"settings.backup.{index}"

    def _rotate_backups(self) -> None:
        """Rotates backup files up to MAX_BACKUPS."""
        try:
            # Delete oldest backup if it exists
            oldest = self._get_backup_path(MAX_BACKUPS)
            if oldest.exists():
                oldest.unlink()

            # Shift backups downwards: backup.4 -> backup.5, etc.
            for i in range(MAX_BACKUPS - 1, 0, -1):
                src = self._get_backup_path(i)
                dst = self._get_backup_path(i + 1)
                if src.exists():
                    shutil.move(src, dst)

            # Copy current settings.json to backup.1
            if self.settings_file.exists():
                shutil.copy2(self.settings_file, self._get_backup_path(1))
        except Exception as e:
            logger.warning(f"Error rotating backups: {e}")

    def load(self) -> AppSettings:
        """Loads settings from file with automatic fallback, migration, and rotating backup recovery."""
        if not self.settings_file.exists():
            logger.info("No settings file found, using defaults.")
            self.settings = AppSettings()
            return self.settings

        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("Settings file root is not a JSON object")

            # Check if this is a v1 format without schema_version
            if "schema_version" not in data or data.get("schema_version", 1) < 2:
                self._migrate_v1_to_v2(data)
                return self.settings

            valid_keys = {f.name for f in AppSettings.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            self.settings = AppSettings(**filtered)
            self.settings.validate()
            logger.info("Settings successfully loaded.")
            return self.settings
        except Exception as e:
            logger.error(f"Error reading {self.settings_file.name} ({e}). Recovering from rotating backups...")
            self.corruption_detected = True

            # Preserve corrupted file for diagnostics
            try:
                corrupt_copy = self.settings_dir / f"settings.json.corrupt.{int(time.time())}"
                shutil.copy2(self.settings_file, corrupt_copy)
                logger.warning(f"Preserved corrupted settings file as {corrupt_copy.name}")
            except Exception:
                pass

            # Try restoring from rotating backups 1..MAX_BACKUPS
            for i in range(1, MAX_BACKUPS + 1):
                bp = self._get_backup_path(i)
                if bp.exists():
                    try:
                        with open(bp, "r", encoding="utf-8") as f:
                            bdata = json.load(f)
                        if isinstance(bdata, dict):
                            valid_keys = {f.name for f in AppSettings.__dataclass_fields__.values()}
                            filtered = {k: v for k, v in bdata.items() if k in valid_keys}
                            self.settings = AppSettings(**filtered)
                            self.settings.validate()
                            logger.info(f"Successfully recovered settings from {bp.name}.")
                            self.recovered_from_backup = True
                            self.save()
                            return self.settings
                    except Exception as be:
                        logger.warning(f"Backup {bp.name} was also unreadable: {be}")

            # Legacy backup file fallback
            legacy_bak = self.settings_dir / "settings.bak"
            if legacy_bak.exists():
                try:
                    with open(legacy_bak, "r", encoding="utf-8") as f:
                        bdata = json.load(f)
                    valid_keys = {f.name for f in AppSettings.__dataclass_fields__.values()}
                    filtered = {k: v for k, v in bdata.items() if k in valid_keys}
                    self.settings = AppSettings(**filtered)
                    self.settings.validate()
                    self.recovered_from_backup = True
                    self.save()
                    return self.settings
                except Exception:
                    pass

            logger.error("All backups exhausted. Initializing safe defaults.")
            self.settings = AppSettings()
            self.save()
            return self.settings

    def _migrate_v1_to_v2(self, v1_data: dict) -> None:
        """Migrates v1 configuration to v2 while preserving a pre-migration backup."""
        logger.info("Migrating v1 settings schema to v2...")
        try:
            v1_backup = self.settings_dir / f"settings.v1.backup.{int(time.time())}.json"
            shutil.copy2(self.settings_file, v1_backup)
            logger.info(f"Created pre-migration backup: {v1_backup.name}")
        except Exception as e:
            logger.warning(f"Could not create pre-migration backup: {e}")

        valid_keys = {f.name for f in AppSettings.__dataclass_fields__.values()}
        filtered = {k: v for k, v in v1_data.items() if k in valid_keys}
        filtered["schema_version"] = 2
        # Ensure default cooldown is 30
        if "cooldown_minutes" not in filtered:
            filtered["cooldown_minutes"] = 30

        self.settings = AppSettings(**filtered)
        self.settings.validate()
        self.save()
        logger.info("v1 -> v2 schema migration complete.")

    def save(self) -> bool:
        """Performs atomic file write with fsync and rotating backups."""
        self.ensure_directory()
        self.settings.validate()
        data = asdict(self.settings)

        temp_file = self.settings_dir / "settings.json.tmp"
        try:
            # 1. Write to temp file and flush to disk
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            # 2. Rotate backups before replacing current settings
            self._rotate_backups()

            # 3. Atomic replace
            os.replace(temp_file, self.settings_file)

            # 4. Ensure at least backup.1 exists
            backup1 = self._get_backup_path(1)
            if not backup1.exists() and self.settings_file.exists():
                shutil.copy2(self.settings_file, backup1)

            return True

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False

    def reset_to_defaults(self) -> None:
        """Resets all configuration values to defaults while keeping rotating backups."""
        self._rotate_backups()
        self.settings = AppSettings()
        self.settings.first_run_completed = True
        self.save()
