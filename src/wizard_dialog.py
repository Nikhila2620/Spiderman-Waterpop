"""
First-Run Setup Wizard for Spider-Man Water Buddy.
Collects personalization, reminder intervals, quiet hours, hydration goal, and explicit Windows startup choice.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QTimeEdit,
    QCheckBox,
    QFrame,
    QWidget,
)
from PySide6.QtGui import QFont, QCursor, QColor
from PySide6.QtCore import QTime

from src.config import ConfigManager, AppSettings
from src.startup_manager import StartupManager
from src.theme import get_dialog_qss, TOKENS


class SetupWizardDialog(QDialog):
    """Multi-step guided setup wizard for first launch."""

    wizardCompleted = Signal(AppSettings)

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.settings = config_manager.settings

        self.setWindowTitle("Spider-Man Water Buddy — Welcome & Setup")
        self.setFixedSize(540, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(get_dialog_qss())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header Title Banner
        header = QHBoxLayout()
        header_title = QLabel("🕷️ SPIDER-MAN WATER BUDDY SETUP")
        header_title.setStyleSheet(f"color: {TOKENS.ACCENT_AQUA}; font-size: 14px; font-weight: 800; letter-spacing: 1.5px;")
        header.addWidget(header_title)
        header.addStretch()
        self.step_label = QLabel("Step 1 of 4")
        self.step_label.setStyleSheet(f"color: {TOKENS.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        header.addWidget(self.step_label)
        layout.addLayout(header)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {TOKENS.BORDER_GLASS};")
        layout.addWidget(divider)

        # Stacked Pages
        self.stack = QStackedWidget()
        self._build_page1_personalization()
        self._build_page2_reminders()
        self._build_page3_startup()
        self._build_page4_summary()
        layout.addWidget(self.stack)

        # Navigation Bar (Back, Next/Finish)
        nav_layout = QHBoxLayout()
        self.btn_back = QPushButton("← Back")
        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(12, 26, 46, 0.8);
                color: {TOKENS.TEXT_SECONDARY};
                border: 1px solid {TOKENS.BORDER_GLASS};
                border-radius: {TOKENS.RADIUS_MD};
                padding: 7px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(16, 36, 64, 0.95);
                color: #ffffff;
            }}
        """)
        self.btn_back.clicked.connect(self._go_back)
        self.btn_back.setEnabled(False)
        nav_layout.addWidget(self.btn_back)

        nav_layout.addStretch()

        self.btn_next = QPushButton("Next →")
        self.btn_next.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #e11d48, stop: 1 #be123c);
                color: #ffffff;
                border: 1px solid #f43f5e;
            }
            QPushButton:hover { background: #f43f5e; }
        """)
        self.btn_next.clicked.connect(self._go_next)
        nav_layout.addWidget(self.btn_next)

        layout.addLayout(nav_layout)

    # PAGE 1: Personalization
    def _build_page1_personalization(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 10, 0, 10)
        vbox.setSpacing(14)

        title = QLabel("Personalize Your Companion")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff;")
        vbox.addWidget(title)

        subtitle = QLabel("Set up how your friendly neighbourhood companion greets you.")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 13px;")
        vbox.addWidget(subtitle)

        # Companion Name
        vbox.addWidget(QLabel("Companion Name:"))
        self.edit_companion_name = QLineEdit(self.settings.companion_name)
        vbox.addWidget(self.edit_companion_name)

        # User Name
        vbox.addWidget(QLabel("Your Preferred Name:"))
        self.edit_user_name = QLineEdit(self.settings.user_name)
        vbox.addWidget(self.edit_user_name)

        # Custom Greeting
        vbox.addWidget(QLabel("Custom Greeting Message (Optional):"))
        self.edit_greeting = QLineEdit(self.settings.custom_greeting)
        vbox.addWidget(self.edit_greeting)

        vbox.addStretch()
        self.stack.addWidget(page)

    # PAGE 2: Reminder Configuration
    def _build_page2_reminders(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 10, 0, 10)
        vbox.setSpacing(12)

        title = QLabel("Water Reminder Settings")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff;")
        vbox.addWidget(title)

        # Interval Presets
        vbox.addWidget(QLabel("Reminder Interval:"))
        preset_box = QHBoxLayout()
        self.preset_group = QButtonGroup(self)
        self.preset_radios = {}

        for mins in (15, 30, 45, 60, 90):
            r = QRadioButton(f"{mins}m")
            if mins == self.settings.reminder_interval_minutes:
                r.setChecked(True)
            self.preset_group.addButton(r)
            self.preset_radios[mins] = r
            preset_box.addWidget(r)

        self.radio_custom = QRadioButton("Custom:")
        self.preset_group.addButton(self.radio_custom)
        preset_box.addWidget(self.radio_custom)

        self.spin_custom_interval = QSpinBox()
        self.spin_custom_interval.setRange(1, 720)
        self.spin_custom_interval.setValue(self.settings.reminder_interval_minutes)
        self.spin_custom_interval.setSuffix(" min")
        preset_box.addWidget(self.spin_custom_interval)
        vbox.addLayout(preset_box)

        # Snooze & Retry
        timing_box = QHBoxLayout()
        # Snooze
        snooze_col = QVBoxLayout()
        snooze_col.addWidget(QLabel("Snooze Duration:"))
        self.spin_snooze = QSpinBox()
        self.spin_snooze.setRange(1, 120)
        self.spin_snooze.setValue(self.settings.snooze_duration_minutes)
        self.spin_snooze.setSuffix(" min")
        snooze_col.addWidget(self.spin_snooze)
        timing_box.addLayout(snooze_col)

        # Retry after NO
        retry_col = QVBoxLayout()
        retry_col.addWidget(QLabel("Retry Interval (if 'Not Yet'):"))
        self.spin_retry = QSpinBox()
        self.spin_retry.setRange(1, 120)
        self.spin_retry.setValue(self.settings.retry_interval_minutes)
        self.spin_retry.setSuffix(" min")
        retry_col.addWidget(self.spin_retry)
        timing_box.addLayout(retry_col)
        vbox.addLayout(timing_box)

        # Quiet Hours
        vbox.addWidget(QLabel("Quiet Hours (Do Not Disturb):"))
        quiet_box = QHBoxLayout()
        self.chk_quiet = QCheckBox("Enable Quiet Hours")
        self.chk_quiet.setChecked(self.settings.quiet_hours_enabled)
        quiet_box.addWidget(self.chk_quiet)

        quiet_box.addWidget(QLabel("From:"))
        self.time_quiet_start = QTimeEdit(QTime.fromString(self.settings.quiet_hours_start, "HH:mm"))
        self.time_quiet_start.setDisplayFormat("HH:mm")
        quiet_box.addWidget(self.time_quiet_start)

        quiet_box.addWidget(QLabel("To:"))
        self.time_quiet_end = QTimeEdit(QTime.fromString(self.settings.quiet_hours_end, "HH:mm"))
        self.time_quiet_end.setDisplayFormat("HH:mm")
        quiet_box.addWidget(self.time_quiet_end)
        vbox.addLayout(quiet_box)

        # Hydration Goal
        goal_box = QHBoxLayout()
        goal_box.addWidget(QLabel("Daily Hydration Goal:"))
        self.spin_goal = QSpinBox()
        self.spin_goal.setRange(500, 8000)
        self.spin_goal.setSingleStep(250)
        self.spin_goal.setValue(self.settings.daily_hydration_goal_ml)
        self.spin_goal.setSuffix(" ml")
        goal_box.addWidget(self.spin_goal)
        vbox.addLayout(goal_box)

        vbox.addStretch()
        self.stack.addWidget(page)

    # PAGE 3: Windows Startup
    def _build_page3_startup(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 10, 0, 10)
        vbox.setSpacing(16)

        title = QLabel("Windows Startup Behavior")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff;")
        vbox.addWidget(title)

        desc = QLabel(
            "Choose whether Spider-Man Water Buddy should launch automatically whenever you log into Windows."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #cbd5e1; font-size: 13px; line-height: 1.4;")
        vbox.addWidget(desc)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1a1626;
                border: 1px solid #332a48;
                border-radius: 12px;
                padding: 14px;
            }
        """)
        card_vbox = QVBoxLayout(card)
        card_vbox.setSpacing(14)

        self.radio_startup_yes = QRadioButton("Yes, start with Windows and run in the background (Recommended)")
        self.radio_startup_yes.setChecked(self.settings.launch_at_startup)
        card_vbox.addWidget(self.radio_startup_yes)

        self.radio_startup_no = QRadioButton("No, launch manually when I want to use it")
        self.radio_startup_no.setChecked(not self.settings.launch_at_startup)
        card_vbox.addWidget(self.radio_startup_no)

        vbox.addWidget(card)

        note = QLabel("ℹ️ You can change this setting at any time from the Settings Dashboard.")
        note.setStyleSheet("color: #94a3b8; font-size: 12px;")
        vbox.addWidget(note)

        vbox.addStretch()
        self.stack.addWidget(page)

    # PAGE 4: Summary & Confirmation
    def _build_page4_summary(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 10, 0, 10)
        vbox.setSpacing(14)

        title = QLabel("Ready to Hydrate!")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff;")
        vbox.addWidget(title)

        desc = QLabel("Review your configuration below. You can go back to make changes, or click Finish.")
        desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        vbox.addWidget(desc)

        self.summary_box = QFrame()
        self.summary_box.setStyleSheet(f"""
            QFrame {{
                background-color: {TOKENS.BG_CARD};
                border: 1.5px solid {TOKENS.BORDER_GLASS_ACTIVE};
                border-radius: {TOKENS.RADIUS_LG};
                padding: 14px;
            }}
            QLabel {{
                font-size: 12.5px;
                color: {TOKENS.TEXT_PRIMARY};
            }}
        """)
        self.summary_layout = QVBoxLayout(self.summary_box)
        self.summary_layout.setSpacing(6)
        vbox.addWidget(self.summary_box)

        vbox.addStretch()
        self.stack.addWidget(page)

    def _update_summary(self):
        """Refreshes summary details on the final page."""
        # Clear existing items
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Gather values
        companion = self.edit_companion_name.text().strip() or "Spider-Man"
        user = self.edit_user_name.text().strip() or "Hero"

        interval = self.spin_custom_interval.value()
        for mins, r in self.preset_radios.items():
            if r.isChecked():
                interval = mins
                break

        snooze = self.spin_snooze.value()
        retry = self.spin_retry.value()
        goal = self.spin_goal.value()
        startup = "Yes (Automatic)" if self.radio_startup_yes.isChecked() else "No (Manual)"
        quiet = "Enabled" if self.chk_quiet.isChecked() else "Disabled"
        q_start = self.time_quiet_start.time().toString("HH:mm")
        q_end = self.time_quiet_end.time().toString("HH:mm")

        rows = [
            f"<b>Companion Name:</b> {companion}",
            f"<b>User Name:</b> {user}",
            f"<b>Reminder Interval:</b> Every {interval} minutes",
            f"<b>Snooze Duration:</b> {snooze} minutes | <b>Retry Interval:</b> {retry} minutes",
            f"<b>Daily Hydration Goal:</b> {goal} ml",
            f"<b>Quiet Hours:</b> {quiet} ({q_start} to {q_end})",
            f"<b>Windows Startup:</b> {startup}",
        ]

        for row in rows:
            lbl = QLabel(row)
            lbl.setTextFormat(Qt.TextFormat.RichText)
            self.summary_layout.addWidget(lbl)

    def _go_next(self):
        idx = self.stack.currentIndex()
        if idx < self.stack.count() - 1:
            self.stack.setCurrentIndex(idx + 1)
            self.step_label.setText(f"Step {idx + 2} of {self.stack.count()}")
            self.btn_back.setEnabled(True)

            if idx + 1 == self.stack.count() - 1:
                self._update_summary()
                self.btn_next.setText("Finish & Save ✨")
                self.btn_next.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 {TOKENS.ACCENT_AZURE}, stop: 1 {TOKENS.ACCENT_AQUA});
                        color: #051324;
                        font-weight: 800;
                        border: none;
                        border-radius: {TOKENS.RADIUS_MD};
                        padding: 8px 16px;
                    }}
                    QPushButton:hover {{
                        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #3b9eff, stop: 1 #4df4ff);
                    }}
                """)
        else:
            self._save_and_finish()

    def _go_back(self):
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
            self.step_label.setText(f"Step {idx} of {self.stack.count()}")
            self.btn_next.setText("Next →")
            self.btn_next.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #e11d48, stop: 1 #be123c);
                    color: #ffffff;
                    border: 1px solid #f43f5e;
                }
                QPushButton:hover { background: #f43f5e; }
            """)
            if idx - 1 == 0:
                self.btn_back.setEnabled(False)

    def _save_and_finish(self):
        """Applies gathered values, sets startup registry, and saves config."""
        s = self.settings
        s.companion_name = self.edit_companion_name.text().strip() or "Spider-Man"
        s.user_name = self.edit_user_name.text().strip() or "Hero"
        s.custom_greeting = self.edit_greeting.text().strip() or s.custom_greeting

        # Interval
        interval = self.spin_custom_interval.value()
        for mins, r in self.preset_radios.items():
            if r.isChecked():
                interval = mins
                break
        s.reminder_interval_minutes = interval
        s.snooze_duration_minutes = self.spin_snooze.value()
        s.retry_interval_minutes = self.spin_retry.value()

        # Quiet hours
        s.quiet_hours_enabled = self.chk_quiet.isChecked()
        s.quiet_hours_start = self.time_quiet_start.time().toString("HH:mm")
        s.quiet_hours_end = self.time_quiet_end.time().toString("HH:mm")

        # Hydration goal
        s.daily_hydration_goal_ml = self.spin_goal.value()

        # Startup
        s.launch_at_startup = self.radio_startup_yes.isChecked()
        StartupManager.set_startup_enabled(s.launch_at_startup)

        # Mark completed
        s.first_run_completed = True

        self.config_manager.save()
        self.wizardCompleted.emit(s)
        self.accept()
