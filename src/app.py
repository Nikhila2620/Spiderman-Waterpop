"""
Central Application Controller for Spider-Man Water Buddy.
Orchestrates single-instance enforcement, system tray integration, window lifecycle,
global interaction shortcuts, and clean process shutdown.
"""
import sys
import os
import logging
from pathlib import Path

from PySide6.QtCore import Qt, QObject, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QMessageBox,
)
from PySide6.QtGui import QIcon, QPixmap, QAction, QKeySequence, QShortcut
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from src.config import ConfigManager
from src.startup_manager import StartupManager
from src.reminder_engine import ReminderEngine, ReminderState
from src.companion_window import CompanionWindow
from src.dashboard_window import DashboardWindow
from src.wizard_dialog import SetupWizardDialog
from src.theme import get_tray_menu_qss

logger = logging.getLogger("SpiderManWaterBuddy.App")
SINGLE_INSTANCE_KEY = "SpiderManWaterBuddySingleInstanceServer_v1"


class SpiderManWaterBuddyApp(QObject):
    """
    Main Application Controller managing lifecycle, windows, and system tray.
    """

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.settings

        self._local_server = None
        self._check_single_instance()

        # Initialize core components
        self.engine = ReminderEngine(self.config_manager, self)
        self.companion = CompanionWindow(self.config_manager)
        self.dashboard = DashboardWindow(self.config_manager, self.engine)

        self._setup_tray_icon()
        self._setup_shortcuts()
        self._wire_signals()

    def _check_single_instance(self):
        """Enforces single application instance via QLocalServer."""
        socket = QLocalSocket()
        socket.connectToServer(SINGLE_INSTANCE_KEY)
        if socket.waitForConnected(500):
            # Another instance is already running
            logger.info("Another instance is already running. Notifying and exiting.")
            socket.write(b"ACTIVATE")
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            sys.exit(0)

        # Start server to listen for subsequent instances
        self._local_server = QLocalServer(self)
        self._local_server.removeServer(SINGLE_INSTANCE_KEY)
        self._local_server.newConnection.connect(self._on_new_instance_connection)
        self._local_server.listen(SINGLE_INSTANCE_KEY)

    def _on_new_instance_connection(self):
        client = self._local_server.nextPendingConnection()
        if client:
            client.readyRead.connect(lambda: self._handle_client_message(client))

    def _handle_client_message(self, client: QLocalSocket):
        msg = client.readAll().data().decode("utf-8")
        if msg == "ACTIVATE":
            self.show_dashboard()
            self.show_companion()
        client.disconnectFromServer()

    def _setup_tray_icon(self):
        """Builds Windows System Tray icon with quick action menu."""
        self.tray_icon = QSystemTrayIcon(self)

        # Load or generate icon
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "images" / "app_icon.png"
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            # Fallback to character 3D render or vector icon
            render_path = Path(__file__).resolve().parent.parent / "assets" / "images" / "spidey_3d_render.png"
            if render_path.exists():
                pix = QPixmap(str(render_path)).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.tray_icon.setIcon(QIcon(pix))
            else:
                self.tray_icon.setIcon(self.app.style().standardIcon(self.app.style().StandardPixmap.SP_ComputerIcon))

        tray_menu = QMenu()
        tray_menu.setStyleSheet(get_tray_menu_qss())

        # Open Dashboard Action
        act_dashboard = QAction("📊 Open Settings & Dashboard", self)
        act_dashboard.triggered.connect(self.show_dashboard)
        tray_menu.addAction(act_dashboard)

        # Remind Me Now
        act_remind = QAction("💧 Remind Me Now", self)
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

        # Toggle Interaction Mode (Click-Through)
        self.act_toggle_clickthrough = QAction("🖱️ Toggle Click-Through Mode", self)
        self.act_toggle_clickthrough.triggered.connect(self._toggle_click_through)
        tray_menu.addAction(self.act_toggle_clickthrough)

        tray_menu.addSeparator()

        # Exit
        act_exit = QAction("✕ Exit", self)
        act_exit.triggered.connect(self.exit_app)
        tray_menu.addAction(act_exit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("Spider-Man Water Buddy")
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _setup_shortcuts(self):
        """Window shortcut to toggle interaction mode (configurable, default Ctrl+Alt+W)."""
        key_seq = self.settings.interaction_mode_shortcut or "Ctrl+Alt+W"
        self.shortcut = QShortcut(QKeySequence(key_seq), self.companion)
        self.shortcut.activated.connect(self._toggle_click_through)

    def _wire_signals(self):
        # Engine events to Companion
        self.engine.reminderTriggered.connect(self._on_reminder_triggered)
        self.engine.stateChanged.connect(self._on_state_changed)

        # Companion events to Engine
        self.companion.waterDrank.connect(lambda: self.engine.on_user_drank_water(250))
        self.companion.snoozeRequested.connect(self.engine.on_user_snoozed)
        self.companion.declined.connect(self.engine.on_user_declined)

        # Dashboard settings updates to Companion
        self.dashboard.settingsChanged.connect(self._on_settings_updated)
        self.dashboard.triggerReminderRequested.connect(self._remind_now)
        self.dashboard.testAnimationRequested.connect(self._on_test_animation)

    def run(self, start_minimized_override: bool = False):
        """Launches the application, showing wizard if first run."""
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
        # Start minimized or show companion
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
        # Show tray notification if companion was hidden
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

        if state == ReminderState.QUIET_HOURS and self.companion._in_reminder_mode:
            self.companion._on_auto_close()

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
        if self._local_server:
            self._local_server.close()
        self.engine._heartbeat.stop()
        self.companion.close()
        self.dashboard.close()
        self.app.quit()
