"""
Main Application Controller for Spider-Man Water Buddy v2.0.
Coordinates windows, system tray, native hotkeys, sleep/wake power events,
and single-instance communication.
"""
import sys
import logging
from pathlib import Path
from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QAction, QKeySequence, QShortcut
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from src.config import ConfigManager
from src.reminder_engine import ReminderEngine, ReminderState
from src.companion_window import CompanionWindow
from src.dashboard_window import DashboardWindow
from src.wizard_dialog import SetupWizardDialog
from src.theme import get_tray_menu_qss
from src.utils import resource_path
from src.windows_native import WindowsNativeEventFilter

logger = logging.getLogger("SpiderManWaterBuddy.App")

SINGLE_INSTANCE_KEY = "SpiderManWaterBuddy_SingleInstance_Pipe"


class SpiderManWaterBuddyApp(QObject):
    """
    Core Controller managing application lifecycle and subsystem communication.
    """

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self._local_server = None
        self._native_filter = None

        self._check_single_instance()

        # Core subsystems
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.settings

        self.engine = ReminderEngine(self.config_manager)
        self.companion = CompanionWindow(self.config_manager)
        self.dashboard = DashboardWindow(self.config_manager, self.engine)

        self._setup_tray_icon()
        self._setup_native_integration()
        self._wire_signals()

    def _check_single_instance(self):
        """Starts local server to listen for subsequent launch attempts."""
        self._local_server = QLocalServer(self)
        self._local_server.removeServer(SINGLE_INSTANCE_KEY)
        self._local_server.newConnection.connect(self._on_new_instance_connection)
        if not self._local_server.listen(SINGLE_INSTANCE_KEY):
            logger.warning(f"Failed to listen on single instance server pipe: {self._local_server.errorString()}")

    def _on_new_instance_connection(self):
        client = self._local_server.nextPendingConnection()
        if client:
            client.readyRead.connect(lambda: self._handle_client_message(client))

    def _handle_client_message(self, client: QLocalSocket):
        try:
            data = client.read(64).data().decode("utf-8", errors="ignore")
            if data.strip() == "ACTIVATE":
                self.show_dashboard()
                self.show_companion()
        except Exception as e:
            logger.warning(f"Error reading single instance client message: {e}")
        finally:
            client.disconnectFromServer()

    def _setup_native_integration(self):
        """Installs native Windows event filter for system-wide hotkeys and wake detection."""
        try:
            self._native_filter = WindowsNativeEventFilter(self)
            self.app.installNativeEventFilter(self._native_filter)
            self._native_filter.register_global_hotkey()
            self._native_filter.hotkeyActivated.connect(self._toggle_click_through)
            self._native_filter.systemResumed.connect(self.engine.on_system_wake)
        except Exception as e:
            logger.warning(f"Could not install native event filter: {e}")

        # Local fallback shortcut
        key_seq = self.settings.interaction_mode_shortcut or "Ctrl+Alt+W"
        self.shortcut = QShortcut(QKeySequence(key_seq), self.companion)
        self.shortcut.activated.connect(self._toggle_click_through)

    def _setup_tray_icon(self):
        """Builds Windows System Tray icon with quick action menu and cooldown indicator."""
        self.tray_icon = QSystemTrayIcon(self)

        icon_path = resource_path("assets/images/app_icon.png")
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(self.app.style().standardIcon(self.app.style().StandardPixmap.SP_ComputerIcon))

        tray_menu = QMenu()
        tray_menu.setStyleSheet(get_tray_menu_qss())

        # Manual Log Action: YES, I DRANK 💧
        self.act_manual_drink = QAction("💧 YES, I DRANK (+250 ml)", self)
        self.act_manual_drink.triggered.connect(self._on_tray_manual_drink)
        tray_menu.addAction(self.act_manual_drink)

        tray_menu.addSeparator()

        # Open Dashboard Action
        act_dashboard = QAction("📊 Open Settings & Dashboard", self)
        act_dashboard.triggered.connect(self.show_dashboard)
        tray_menu.addAction(act_dashboard)

        # Remind Me Now
        act_remind = QAction("⏰ Remind Me Now", self)
        act_remind.triggered.connect(self._remind_now)
        tray_menu.addAction(act_remind)

        tray_menu.addSeparator()

        # Toggle Companion
        self.act_toggle_comp = QAction("👁️ Hide Companion", self)
        self.act_toggle_comp.triggered.connect(self._toggle_companion_visibility)
        tray_menu.addAction(self.act_toggle_comp)

        # Toggle Pause
        self.act_toggle_pause = QAction("⏸️ Pause Reminders", self)
        self.act_toggle_pause.triggered.connect(self._toggle_pause)
        tray_menu.addAction(self.act_toggle_pause)

        # Toggle Click-Through Mode
        self.act_toggle_clickthrough = QAction("🖱️ Toggle Click-Through Mode", self)
        self.act_toggle_clickthrough.triggered.connect(self._toggle_click_through)
        tray_menu.addAction(self.act_toggle_clickthrough)

        tray_menu.addSeparator()

        # Exit
        act_exit = QAction("✕ Exit", self)
        act_exit.triggered.connect(self.exit_app)
        tray_menu.addAction(act_exit)

        self.tray_icon.setContextMenu(tray_menu)
        self._update_tray_tooltip()
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_manual_drink(self):
        res = self.engine.log_manual(250)
        if res.ok:
            self.tray_icon.showMessage(
                "Spider-Man Water Buddy",
                f"Awesome! +250 ml logged 🕷️\nStreak: {res.info.current_streak} days",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
        else:
            mins, secs = divmod(res.remaining_seconds, 60)
            self.tray_icon.showMessage(
                "Spider-Man Water Buddy",
                f"Easy there, hero! Next sip in {mins:02d}:{secs:02d}",
                QSystemTrayIcon.MessageIcon.Warning,
                2000,
            )

    def _update_tray_tooltip(self):
        info = self.engine.get_streak_info()
        cooldown_str = "Ready"
        if info.is_cooldown_active:
            m, s = divmod(info.cooldown_remaining_seconds, 60)
            cooldown_str = f"Cooldown: {m:02d}:{s:02d}"

        tip = (
            f"Spider-Man Water Buddy v2.0\n"
            f"Streak: 🔥 {info.current_streak} days (Best: {info.longest_streak})\n"
            f"Today: {info.today_intake_ml:,} / {info.daily_goal_ml:,} mL ({info.progress_percentage}%)\n"
            f"Manual Log: {cooldown_str}"
        )
        self.tray_icon.setToolTip(tip)

    def _wire_signals(self):
        # Engine events to Companion
        self.engine.reminderTriggered.connect(self._on_reminder_triggered)
        self.engine.stateChanged.connect(self._on_state_changed)
        self.engine.cooldownTick.connect(self._on_cooldown_tick)
        self.engine.streakUpdated.connect(lambda info: self._update_tray_tooltip())

        # Companion events to Engine
        self.companion.waterDrank.connect(lambda: self.engine.log_from_reminder(250))
        self.companion.snoozeRequested.connect(self.engine.on_user_snoozed)
        self.companion.declined.connect(self.engine.on_user_declined)
        self.companion.dismissed.connect(self.engine.on_user_dismissed)

        # Dashboard settings updates to Companion
        self.dashboard.settingsChanged.connect(self._on_settings_updated)
        self.dashboard.triggerReminderRequested.connect(self._remind_now)
        self.dashboard.testAnimationRequested.connect(self._on_test_animation)

    def _on_cooldown_tick(self, rem_seconds: int):
        if rem_seconds > 0:
            mins, secs = divmod(rem_seconds, 60)
            self.act_manual_drink.setText(f"⏳ Cooling down ({mins:02d}:{secs:02d})")
            self.act_manual_drink.setEnabled(False)
        else:
            self.act_manual_drink.setText("💧 YES, I DRANK (+250 ml)")
            self.act_manual_drink.setEnabled(True)

    def run(self, start_minimized_override: bool = False):
        if not self.settings.first_run_completed:
            wizard = SetupWizardDialog(self.config_manager)
            wizard.wizardCompleted.connect(self._on_wizard_completed)
            wizard.exec()
        else:
            self._start_main_workflow(minimized=start_minimized_override or self.settings.start_minimized)

    def _on_wizard_completed(self, new_settings):
        logger.info("First run wizard completed successfully.")
        self.dashboard.load_values_from_settings()
        self._start_main_workflow(minimized=self.settings.start_minimized)

    def _start_main_workflow(self, minimized: bool = False):
        if minimized:
            self.companion.hide()
            self.act_toggle_comp.setText("👁️ Show Companion")
            logger.info("Application started minimized to system tray.")
        elif self.settings.companion_visible:
            self.show_companion()
        else:
            self.companion.hide()
            self.act_toggle_comp.setText("👁️ Show Companion")

    def show_companion(self):
        self.settings.companion_visible = True
        self.config_manager.save()
        self.companion.reposition()
        self.companion.show()
        self.act_toggle_comp.setText("👁️ Hide Companion")

    def hide_companion(self):
        self.settings.companion_visible = False
        self.config_manager.save()
        self.companion.hide()
        self.act_toggle_comp.setText("👁️ Show Companion")

    def show_dashboard(self):
        self.dashboard.load_values_from_settings()
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_dashboard()

    def _remind_now(self):
        self.engine.trigger_now()

    def _on_reminder_triggered(self):
        if not self.settings.companion_visible:
            self.tray_icon.showMessage(
                "Spider-Man Water Buddy",
                f"Time for a water break, {self.settings.user_name}! 💧",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        self.companion.trigger_reminder_mode()

    def _on_state_changed(self, state: ReminderState):
        if state == ReminderState.PAUSED:
            self.act_toggle_pause.setText("▶️ Resume Reminders")
        else:
            self.act_toggle_pause.setText("⏸️ Pause Reminders")

        is_reminding = getattr(self.companion, "is_in_reminder_mode", lambda: False)()
        if state == ReminderState.QUIET_HOURS and is_reminding:
            self.companion.dismiss()

    def _toggle_companion_visibility(self):
        if self.companion.isVisible():
            self.hide_companion()
        else:
            self.show_companion()

    def _toggle_pause(self):
        new_pause = not self.settings.reminders_paused
        self.engine.pause_reminders(new_pause)

    def _toggle_click_through(self):
        self.settings.click_through_enabled = not self.settings.click_through_enabled
        self.config_manager.save()
        self.companion.apply_click_through(self.settings.click_through_enabled)
        state_str = "ENABLED" if self.settings.click_through_enabled else "DISABLED"
        shortcut = self.settings.interaction_mode_shortcut or "Ctrl+Alt+W"
        self.tray_icon.showMessage(
            "Spider-Man Water Buddy",
            f"Click-through mode {state_str}. (Press {shortcut} to toggle)",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _on_settings_updated(self):
        self.companion.badge.setText(f"🕸️ {self.settings.companion_name.upper()} WATER BUDDY")
        self.companion.spidey.set_animation_enabled(self.settings.animation_enabled)
        self.companion.spidey.set_performance_mode(self.settings.performance_mode)
        self.companion.reposition()
        self.companion.apply_click_through(self.settings.click_through_enabled)
        if self.settings.companion_visible:
            self.companion.show()
        else:
            self.companion.hide()

    def _on_test_animation(self, anim_type: str):
        self.show_companion()
        self.companion.spidey.set_state(anim_type)

    def exit_app(self):
        logger.info("Clean shutdown initiated.")
        if self._native_filter:
            self._native_filter.unregister_all()
        if self._local_server:
            self._local_server.close()
        self.engine._heartbeat.stop()
        self.companion.close()
        self.dashboard.close()
        self.app.quit()
