"""
Configuration management for Spider-Man Water Buddy.
Provides atomic persistence, schema validation, automatic backup, and corruption recovery.
"""
import os
import sys
import json
import logging
import shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("SpiderManWaterBuddy.Config")


@dataclass
class AppSettings:
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

    # Hydration tracking
    daily_hydration_goal_ml: int = 2000
    today_reminders_completed: int = 0
    today_intake_ml: int = 0
    last_tracking_date: str = ""

    # Appearance & Window behavior
    corner_position: str = "top-right"  # "top-right", "top-left", "bottom-right", "bottom-left"
    character_scale: float = 1.0  # 0.7 to 1.5
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
        self.daily_hydration_goal_ml = max(100, min(10000, int(self.daily_hydration_goal_ml)))

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


class ConfigManager:
    """Handles loading, saving, backup, and atomic recovery of AppSettings."""

    def __init__(self, custom_path: Optional[Path] = None):
        if custom_path:
            self.settings_dir = custom_path.parent
            self.settings_file = custom_path
        else:
            # Standard Windows AppData directory
            app_data = os.environ.get("APPDATA")
            if app_data:
                self.settings_dir = Path(app_data) / "SpiderManWaterBuddy"
            else:
                self.settings_dir = Path.home() / ".spiderman_water_buddy"
            self.settings_file = self.settings_dir / "settings.json"

        self.backup_file = self.settings_dir / "settings.bak"
        self.settings = AppSettings()
        self.ensure_directory()
        self.load()

    def ensure_directory(self) -> None:
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create settings directory {self.settings_dir}: {e}")

    def load(self) -> AppSettings:
        """Loads settings from file with automatic fallback and backup recovery."""
        if not self.settings_file.exists():
            logger.info("No settings file found, using defaults.")
            self.settings = AppSettings()
            return self.settings

        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Filter and merge into dataclass
            valid_keys = {f.name for f in AppSettings.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            self.settings = AppSettings(**filtered)
            self.settings.validate()
            logger.info("Settings successfully loaded.")
            return self.settings
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Error reading settings.json ({e}). Attempting backup recovery...")
            if self.backup_file.exists():
                try:
                    with open(self.backup_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    valid_keys = {f.name for f in AppSettings.__dataclass_fields__.values()}
                    filtered = {k: v for k, v in data.items() if k in valid_keys}
                    self.settings = AppSettings(**filtered)
                    self.settings.validate()
                    logger.info("Successfully recovered settings from backup.")
                    self.save()
                    return self.settings
                except Exception as be:
                    logger.error(f"Backup file was also unreadable: {be}")

            logger.error("Using safe defaults due to settings corruption.")
            self.settings = AppSettings()
            self.save()
            return self.settings

    def save(self) -> bool:
        """Performs atomic file write to prevent corruption and maintains a backup."""
        self.ensure_directory()
        self.settings.validate()
        data = asdict(self.settings)

        temp_file = self.settings_dir / "settings.json.tmp"
        try:
            # Write to temp file first
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Create backup of current settings if valid
            if self.settings_file.exists():
                shutil.copy2(self.settings_file, self.backup_file)

            # Atomic replace
            os.replace(temp_file, self.settings_file)
            logger.info("Settings saved atomically.")
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
        """Resets all configuration values to defaults while keeping backup."""
        if self.settings_file.exists():
            shutil.copy2(self.settings_file, self.backup_file)
        self.settings = AppSettings()
        self.settings.first_run_completed = True
        self.save()

    def restore_backup(self) -> bool:
        """Restores the last known valid backup if available."""
        if not self.backup_file.exists():
            return False
        try:
            with open(self.backup_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid_keys = {f.name for f in AppSettings.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            self.settings = AppSettings(**filtered)
            self.settings.validate()
            self.save()
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
