"""
Settings & Hydration Dashboard Window for Spider-Man Water Buddy.
Provides comprehensive graphical configuration across General, Reminders, Appearance,
and real-time Daily Hydration tracking.
"""
from datetime import datetime
from PySide6.QtCore import Qt, QTime, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QComboBox,
    QTimeEdit,
    QProgressBar,
    QFrame,
    QScrollArea,
    QMessageBox,
)
from PySide6.QtGui import QFont, QCursor, QColor

from src.config import ConfigManager, AppSettings
from src.startup_manager import StartupManager
from src.reminder_engine import ReminderEngine, ReminderState


class DashboardWindow(QWidget):
    """
    Comprehensive graphical dashboard and settings window.
    """

    settingsChanged = Signal()
    triggerReminderRequested = Signal()
    testAnimationRequested = Signal(str)

    def __init__(self, config_manager: ConfigManager, reminder_engine: ReminderEngine, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.settings = config_manager.settings
        self.engine = reminder_engine

        self.setWindowTitle("Spider-Man Water Buddy — Dashboard & Settings")
        self.setMinimumSize(640, 580)
        self.resize(680, 620)

        self._init_ui()
        self._connect_engine_signals()
        self.load_values_from_settings()

    def _init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #110e1c;
                color: #f1f5f9;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #2e2646;
                background-color: #161224;
                border-radius: 12px;
                top: -1px;
            }
            QTabBar::tab {
                background: #110e1c;
                color: #94a3b8;
                border: 1px solid #2e2646;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 18px;
                margin-right: 4px;
                font-weight: 700;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: #1e1832;
                color: #38bdf8;
                border-color: #38bdf8;
            }
            QTabBar::tab:hover {
                color: #ffffff;
            }
            QLineEdit, QSpinBox, QTimeEdit, QComboBox {
                background-color: #1e1830;
                color: #ffffff;
                border: 1.5px solid #3d335c;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus, QTimeEdit:focus, QComboBox:focus {
                border-color: #38bdf8;
            }
            QCheckBox {
                color: #cbd5e1;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QPushButton {
                font-weight: 700;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 12.5px;
            }
            QProgressBar {
                background-color: #1b162a;
                border: 1px solid #362d52;
                border-radius: 8px;
                text-align: center;
                color: #ffffff;
                font-weight: 700;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #0284c7, stop: 1 #38bdf8);
                border-radius: 7px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Top Banner
        banner = QHBoxLayout()
        logo_lbl = QLabel("🕷️ SPIDER-MAN WATER BUDDY")
        logo_lbl.setStyleSheet("font-size: 15px; font-weight: 900; color: #38bdf8; letter-spacing: 1.5px;")
        banner.addWidget(logo_lbl)
        banner.addStretch()

        self.btn_remind_now_top = QPushButton("💧 Remind Me Now")
        self.btn_remind_now_top.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #0284c7, stop: 1 #0369a1);
                color: #ffffff;
                border: 1px solid #38bdf8;
            }
            QPushButton:hover { background: #38bdf8; }
        """)
        self.btn_remind_now_top.clicked.connect(self._on_remind_now_clicked)
        banner.addWidget(self.btn_remind_now_top)
        main_layout.addLayout(banner)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_dashboard_tab(), "📊 Dashboard")
        self.tabs.addTab(self._build_general_tab(), "⚙️ General")
        self.tabs.addTab(self._build_reminders_tab(), "⏱️ Reminders")
        self.tabs.addTab(self._build_appearance_tab(), "🎨 Appearance")
        main_layout.addWidget(self.tabs)

        # Bottom Save Bar
        bottom_bar = QHBoxLayout()
        self.status_save_label = QLabel("Settings up to date.")
        self.status_save_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        bottom_bar.addWidget(self.status_save_label)
        bottom_bar.addStretch()

        self.btn_apply = QPushButton("Apply & Save")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #e11d48, stop: 1 #be123c);
                color: #ffffff;
                border: 1px solid #f43f5e;
            }
            QPushButton:hover { background: #f43f5e; }
        """)
        self.btn_apply.clicked.connect(self.save_and_apply)
        bottom_bar.addWidget(self.btn_apply)

        main_layout.addLayout(bottom_bar)

    # TAB 1: Real-time Dashboard & Hydration Tracking
    def _build_dashboard_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Companion Status Badge Card
        status_card = QFrame()
        status_card.setStyleSheet("background-color: #1a152b; border: 1px solid #31284a; border-radius: 12px; padding: 14px;")
        sc_layout = QHBoxLayout(status_card)

        status_left = QVBoxLayout()
        self.lbl_companion_status_title = QLabel("Companion Status")
        self.lbl_companion_status_title.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 700;")
        status_left.addWidget(self.lbl_companion_status_title)

        self.lbl_companion_status = QLabel("🟢 ACTIVE")
        self.lbl_companion_status.setStyleSheet("font-size: 18px; font-weight: 800; color: #34d399;")
        status_left.addWidget(self.lbl_companion_status)
        sc_layout.addLayout(status_left)

        sc_layout.addStretch()

        time_right = QVBoxLayout()
        time_right.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_next = QLabel("Next Reminder In:")
        lbl_next.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 700;")
        time_right.addWidget(lbl_next)

        self.lbl_countdown = QLabel("--:--")
        self.lbl_countdown.setStyleSheet("font-size: 20px; font-weight: 800; color: #38bdf8;")
        time_right.addWidget(self.lbl_countdown)
        sc_layout.addLayout(time_right)

        layout.addWidget(status_card)

        # Daily Hydration Goal Card
        hydro_card = QFrame()
        hydro_card.setStyleSheet("background-color: #1a152b; border: 1px solid #31284a; border-radius: 12px; padding: 14px;")
        hc_layout = QVBoxLayout(hydro_card)
        hc_layout.setSpacing(10)

        hc_header = QHBoxLayout()
        hc_title = QLabel("Today's Hydration Progress")
        hc_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #ffffff;")
        hc_header.addWidget(hc_title)
        hc_header.addStretch()
        self.lbl_hydro_stats = QLabel("0 / 2000 ml (0%)")
        self.lbl_hydro_stats.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 13px;")
        hc_header.addWidget(self.lbl_hydro_stats)
        hc_layout.addLayout(hc_header)

        self.progress_hydro = QProgressBar()
        self.progress_hydro.setFixedHeight(18)
        self.progress_hydro.setValue(0)
        hc_layout.addWidget(self.progress_hydro)

        # Completed Reminders Counter
        rem_count_box = QHBoxLayout()
        self.lbl_reminders_completed = QLabel("Completed Reminders Today: 0")
        self.lbl_reminders_completed.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600;")
        rem_count_box.addWidget(self.lbl_reminders_completed)
        rem_count_box.addStretch()
        hc_layout.addLayout(rem_count_box)

        # Quick Log Water Buttons
        log_box = QHBoxLayout()
        log_box.addWidget(QLabel("Quick Log Water Intake:"))
        log_box.addStretch()

        btn_log_250 = QPushButton("+250 ml (Glass)")
        btn_log_250.setStyleSheet("background-color: #261f3d; color: #38bdf8; border: 1px solid #3b315c;")
        btn_log_250.clicked.connect(lambda: self._quick_log_water(250))
        log_box.addWidget(btn_log_250)

        btn_log_500 = QPushButton("+500 ml (Bottle)")
        btn_log_500.setStyleSheet("background-color: #261f3d; color: #38bdf8; border: 1px solid #3b315c;")
        btn_log_500.clicked.connect(lambda: self._quick_log_water(500))
        log_box.addWidget(btn_log_500)

        hc_layout.addLayout(log_box)
        layout.addWidget(hydro_card)

        # Quick Control Actions
        ctrl_card = QFrame()
        ctrl_card.setStyleSheet("background-color: #1a152b; border: 1px solid #31284a; border-radius: 12px; padding: 14px;")
        cc_layout = QHBoxLayout(ctrl_card)

        self.btn_pause_toggle = QPushButton("⏸️ Pause Reminders")
        self.btn_pause_toggle.setStyleSheet("background-color: #2c2242; color: #facc15; border: 1px solid #524075;")
        self.btn_pause_toggle.clicked.connect(self._on_toggle_pause_clicked)
        cc_layout.addWidget(self.btn_pause_toggle)

        self.btn_visibility_toggle = QPushButton("👁️ Hide Companion")
        self.btn_visibility_toggle.setStyleSheet("background-color: #2c2242; color: #cbd5e1; border: 1px solid #524075;")
        self.btn_visibility_toggle.clicked.connect(self._on_toggle_visibility_clicked)
        cc_layout.addWidget(self.btn_visibility_toggle)

        layout.addWidget(ctrl_card)
        layout.addStretch()
        return widget

    # TAB 2: General Settings
    def _build_general_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Identity
        id_card, id_vbox = self._create_card("Personalization")
        id_vbox.addWidget(QLabel("Companion Name:"))
        self.edit_comp_name = QLineEdit()
        id_vbox.addWidget(self.edit_comp_name)

        id_vbox.addWidget(QLabel("Your Preferred Name:"))
        self.edit_user_name = QLineEdit()
        id_vbox.addWidget(self.edit_user_name)
        layout.addWidget(id_card)

        # Windows Integration
        win_card, win_vbox = self._create_card("Windows Integration & Behavior")

        self.chk_startup = QCheckBox("Launch automatically when Windows starts")
        win_vbox.addWidget(self.chk_startup)

        self.chk_start_minimized = QCheckBox("Start minimized to system tray")
        win_vbox.addWidget(self.chk_start_minimized)

        self.chk_always_on_top = QCheckBox("Keep companion Always-On-Top of other windows")
        win_vbox.addWidget(self.chk_always_on_top)
        layout.addWidget(win_card)

        # Backup & Recovery
        bak_card, bak_vbox = self._create_card("Configuration Backup & Reset")
        bak_layout = QHBoxLayout()

        btn_restore_bak = QPushButton("Restore Backup Settings")
        btn_restore_bak.setStyleSheet("background-color: #241c38; color: #38bdf8; border: 1px solid #3c2f5a;")
        btn_restore_bak.clicked.connect(self._restore_backup)
        bak_layout.addWidget(btn_restore_bak)

        btn_reset_defaults = QPushButton("Reset to Defaults")
        btn_reset_defaults.setStyleSheet("background-color: #241c38; color: #f87171; border: 1px solid #5a2f3a;")
        btn_reset_defaults.clicked.connect(self._reset_defaults)
        bak_layout.addWidget(btn_reset_defaults)
        bak_vbox.addLayout(bak_layout)
        layout.addWidget(bak_card)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    # TAB 3: Reminder Settings
    def _build_reminders_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Intervals
        sched_card, s_layout = self._create_card("Reminder Intervals")
        s_layout.setSpacing(10)

        self.chk_reminders_enabled = QCheckBox("Enable Water Reminders")
        s_layout.addWidget(self.chk_reminders_enabled)

        int_row = QHBoxLayout()
        int_row.addWidget(QLabel("Recurring Reminder Interval:"))
        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["15 min", "30 min", "45 min", "60 min", "90 min", "Custom"])
        self.combo_interval.currentIndexChanged.connect(self._on_combo_interval_changed)
        int_row.addWidget(self.combo_interval)

        self.spin_interval_custom = QSpinBox()
        self.spin_interval_custom.setRange(1, 720)
        self.spin_interval_custom.setSuffix(" min")
        int_row.addWidget(self.spin_interval_custom)
        s_layout.addLayout(int_row)

        snooze_row = QHBoxLayout()
        snooze_row.addWidget(QLabel("Snooze Duration:"))
        self.spin_snooze = QSpinBox()
        self.spin_snooze.setRange(1, 120)
        self.spin_snooze.setSuffix(" min")
        snooze_row.addWidget(self.spin_snooze)

        snooze_row.addWidget(QLabel("Retry Interval (if 'Not Yet'):"))
        self.spin_retry = QSpinBox()
        self.spin_retry.setRange(1, 120)
        self.spin_retry.setSuffix(" min")
        snooze_row.addWidget(self.spin_retry)
        s_layout.addLayout(snooze_row)
        layout.addWidget(sched_card)

        # Quiet Hours
        quiet_card, q_layout = self._create_card("Quiet Hours (Do Not Disturb)")

        self.chk_quiet = QCheckBox("Enable Quiet Hours")
        q_layout.addWidget(self.chk_quiet)

        q_row = QHBoxLayout()
        q_row.addWidget(QLabel("From:"))
        self.time_q_start = QTimeEdit()
        self.time_q_start.setDisplayFormat("HH:mm")
        q_row.addWidget(self.time_q_start)

        q_row.addWidget(QLabel("To:"))
        self.time_q_end = QTimeEdit()
        self.time_q_end.setDisplayFormat("HH:mm")
        q_row.addWidget(self.time_q_end)
        q_row.addStretch()
        q_layout.addLayout(q_row)
        layout.addWidget(quiet_card)

        # Personalized Messages
        msg_card, m_layout = self._create_card("Custom Messages (Use '[Name]' for your name)")

        m_layout.addWidget(QLabel("Reminder Prompt Message:"))
        self.edit_msg_prompt = QLineEdit()
        m_layout.addWidget(self.edit_msg_prompt)

        m_layout.addWidget(QLabel("Success Confirmation Message (YES):"))
        self.edit_msg_yes = QLineEdit()
        m_layout.addWidget(self.edit_msg_yes)

        m_layout.addWidget(QLabel("Disappointment Message (NO):"))
        self.edit_msg_no = QLineEdit()
        m_layout.addWidget(self.edit_msg_no)

        btn_restore_msgs = QPushButton("Restore Default Messages")
        btn_restore_msgs.setStyleSheet("background-color: #241c38; color: #cbd5e1; border: 1px solid #3c2f5a;")
        btn_restore_msgs.clicked.connect(self._restore_default_messages)
        m_layout.addWidget(btn_restore_msgs)
        layout.addWidget(msg_card)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    # TAB 4: Appearance & Interaction
    def _build_appearance_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Desktop Placement
        pos_card, pos_vbox = self._create_card("Desktop Screen Placement")
        p_layout = QHBoxLayout()
        p_layout.addWidget(QLabel("Anchor Corner:"))
        self.combo_corner = QComboBox()
        self.combo_corner.addItems(["top-right", "top-left", "bottom-right", "bottom-left"])
        p_layout.addWidget(self.combo_corner)
        p_layout.addStretch()
        pos_vbox.addLayout(p_layout)
        layout.addWidget(pos_card)

        # Interaction & Mouse Follow
        act_card, a_layout = self._create_card("Interaction & Click-Through")

        self.chk_click_through = QCheckBox("Enable Click-Through (Clicks pass through companion to background apps)")
        a_layout.addWidget(self.chk_click_through)

        lbl_hint = QLabel("💡 Press 'Ctrl+Alt+W' or use the System Tray to toggle interaction mode anytime.")
        lbl_hint.setStyleSheet("color: #94a3b8; font-size: 11.5px;")
        a_layout.addWidget(lbl_hint)

        self.chk_mouse_follow = QCheckBox("Mouse Awareness (Spider-Man reacts when pointer approaches)")
        a_layout.addWidget(self.chk_mouse_follow)

        self.chk_animation = QCheckBox("Enable Pendulum Web Swinging")
        a_layout.addWidget(self.chk_animation)

        self.chk_perf_mode = QCheckBox("Performance Mode (Minimizes CPU/GPU load for battery saving)")
        a_layout.addWidget(self.chk_perf_mode)

        self.chk_sound = QCheckBox("Sound Effects")
        a_layout.addWidget(self.chk_sound)
        layout.addWidget(act_card)

        # Animation Preview
        anim_card, anim_vbox = self._create_card("Animation Previews")
        an_layout = QHBoxLayout()

        btn_test_happy = QPushButton("🎉 Test Happy Celebration")
        btn_test_happy.setStyleSheet("background-color: #241c38; color: #34d399; border: 1px solid #3c2f5a;")
        btn_test_happy.clicked.connect(lambda: self.testAnimationRequested.emit("happy"))
        an_layout.addWidget(btn_test_happy)

        btn_test_sad = QPushButton("🕷️ Test Disappointed Reaction")
        btn_test_sad.setStyleSheet("background-color: #241c38; color: #f87171; border: 1px solid #3c2f5a;")
        btn_test_sad.clicked.connect(lambda: self.testAnimationRequested.emit("disappointed"))
        an_layout.addWidget(btn_test_sad)
        anim_vbox.addLayout(an_layout)
        layout.addWidget(anim_card)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def _create_card(self, title: str):
        card = QFrame()
        card.setStyleSheet("background-color: #1a152b; border: 1px solid #31284a; border-radius: 12px; padding: 12px;")
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #38bdf8; margin-bottom: 4px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(lbl)
        return card, layout

    def _connect_engine_signals(self):
        self.engine.timerTick.connect(self._on_timer_tick)
        self.engine.stateChanged.connect(self._on_state_changed)
        self.engine.statsUpdated.connect(self._on_stats_updated)

    def _on_timer_tick(self, seconds: int):
        if seconds < 0 or self.settings.reminders_paused or not self.settings.reminders_enabled:
            self.lbl_countdown.setText("Paused")
            self.lbl_countdown.setStyleSheet("font-size: 20px; font-weight: 800; color: #facc15;")
        elif seconds == 0:
            self.lbl_countdown.setText("DUE NOW!")
            self.lbl_countdown.setStyleSheet("font-size: 20px; font-weight: 800; color: #f43f5e;")
        else:
            mins, secs = divmod(seconds, 60)
            self.lbl_countdown.setText(f"{mins:02d}:{secs:02d}")
            self.lbl_countdown.setStyleSheet("font-size: 20px; font-weight: 800; color: #38bdf8;")

    def _on_state_changed(self, state: ReminderState):
        if state == ReminderState.PAUSED:
            self.lbl_companion_status.setText("⏸️ PAUSED")
            self.lbl_companion_status.setStyleSheet("font-size: 18px; font-weight: 800; color: #facc15;")
            self.btn_pause_toggle.setText("▶️ Resume Reminders")
        elif state == ReminderState.QUIET_HOURS:
            self.lbl_companion_status.setText("🌙 QUIET HOURS")
            self.lbl_companion_status.setStyleSheet("font-size: 18px; font-weight: 800; color: #94a3b8;")
        elif state == ReminderState.WAITING_FOR_RESPONSE:
            self.lbl_companion_status.setText("💧 REMINDER ACTIVE")
            self.lbl_companion_status.setStyleSheet("font-size: 18px; font-weight: 800; color: #38bdf8;")
        else:
            self.lbl_companion_status.setText("🟢 ACTIVE")
            self.lbl_companion_status.setStyleSheet("font-size: 18px; font-weight: 800; color: #34d399;")
            self.btn_pause_toggle.setText("⏸️ Pause Reminders")

    def _on_stats_updated(self, count: int, ml: int):
        self.lbl_reminders_completed.setText(f"Completed Reminders Today: {count}")
        goal = self.settings.daily_hydration_goal_ml
        pct = min(100, int((ml / goal) * 100)) if goal > 0 else 0
        self.lbl_hydro_stats.setText(f"{ml} / {goal} ml ({pct}%)")
        self.progress_hydro.setValue(pct)

    def _quick_log_water(self, ml: int):
        self.engine.on_user_drank_water(ml)
        self.status_save_label.setText(f"Logged +{ml} ml of water! Great job.")

    def _on_toggle_pause_clicked(self):
        new_state = not self.settings.reminders_paused
        self.engine.pause_reminders(new_state)

    def _on_toggle_visibility_clicked(self):
        self.settings.companion_visible = not self.settings.companion_visible
        self.config_manager.save()
        if self.settings.companion_visible:
            self.btn_visibility_toggle.setText("👁️ Hide Companion")
        else:
            self.btn_visibility_toggle.setText("👁️ Show Companion")
        self.settingsChanged.emit()

    def _on_remind_now_clicked(self):
        self.engine.trigger_now()
        self.triggerReminderRequested.emit()

    def _on_combo_interval_changed(self, index: int):
        is_custom = (self.combo_interval.currentText() == "Custom")
        self.spin_interval_custom.setEnabled(is_custom)

    def load_values_from_settings(self):
        s = self.settings
        # Identity
        self.edit_comp_name.setText(s.companion_name)
        self.edit_user_name.setText(s.user_name)

        # Windows
        self.chk_startup.setChecked(s.launch_at_startup)
        self.chk_start_minimized.setChecked(s.start_minimized)
        self.chk_always_on_top.setChecked(s.always_on_top)

        # Reminders
        self.chk_reminders_enabled.setChecked(s.reminders_enabled)
        matching_idx = -1
        preset_map = {15: 0, 30: 1, 45: 2, 60: 3, 90: 4}
        if s.reminder_interval_minutes in preset_map:
            self.combo_interval.setCurrentIndex(preset_map[s.reminder_interval_minutes])
            self.spin_interval_custom.setEnabled(False)
        else:
            self.combo_interval.setCurrentIndex(5)  # Custom
            self.spin_interval_custom.setEnabled(True)
        self.spin_interval_custom.setValue(s.reminder_interval_minutes)

        self.spin_snooze.setValue(s.snooze_duration_minutes)
        self.spin_retry.setValue(s.retry_interval_minutes)

        self.chk_quiet.setChecked(s.quiet_hours_enabled)
        self.time_q_start.setTime(QTime.fromString(s.quiet_hours_start, "HH:mm"))
        self.time_q_end.setTime(QTime.fromString(s.quiet_hours_end, "HH:mm"))

        # Messages
        self.edit_msg_prompt.setText(s.custom_greeting)
        self.edit_msg_yes.setText(s.message_yes)
        self.edit_msg_no.setText(s.message_no)

        # Appearance
        idx = self.combo_corner.findText(s.corner_position)
        if idx >= 0:
            self.combo_corner.setCurrentIndex(idx)
        self.chk_click_through.setChecked(s.click_through_enabled)
        self.chk_mouse_follow.setChecked(s.mouse_follow_enabled)
        self.chk_animation.setChecked(s.animation_enabled)
        self.chk_perf_mode.setChecked(s.performance_mode)
        self.chk_sound.setChecked(s.sound_effects_enabled)

        # Initial dashboard stats update
        self._on_stats_updated(s.today_reminders_completed, s.today_intake_ml)

    def save_and_apply(self):
        s = self.settings
        s.companion_name = self.edit_comp_name.text().strip() or "Spider-Man"
        s.user_name = self.edit_user_name.text().strip() or "Hero"

        # Windows
        if s.launch_at_startup != self.chk_startup.isChecked():
            s.launch_at_startup = self.chk_startup.isChecked()
            StartupManager.set_startup_enabled(s.launch_at_startup)

        s.start_minimized = self.chk_start_minimized.isChecked()
        s.always_on_top = self.chk_always_on_top.isChecked()

        # Reminders
        s.reminders_enabled = self.chk_reminders_enabled.isChecked()
        if self.combo_interval.currentText() == "Custom":
            s.reminder_interval_minutes = self.spin_interval_custom.value()
        else:
            text = self.combo_interval.currentText().replace(" min", "")
            s.reminder_interval_minutes = int(text)

        s.snooze_duration_minutes = self.spin_snooze.value()
        s.retry_interval_minutes = self.spin_retry.value()

        s.quiet_hours_enabled = self.chk_quiet.isChecked()
        s.quiet_hours_start = self.time_q_start.time().toString("HH:mm")
        s.quiet_hours_end = self.time_q_end.time().toString("HH:mm")

        # Messages
        s.custom_greeting = self.edit_msg_prompt.text().strip() or s.custom_greeting
        s.message_yes = self.edit_msg_yes.text().strip() or s.message_yes
        s.message_no = self.edit_msg_no.text().strip() or s.message_no

        # Appearance
        s.corner_position = self.combo_corner.currentText()
        s.click_through_enabled = self.chk_click_through.isChecked()
        s.mouse_follow_enabled = self.chk_mouse_follow.isChecked()
        s.animation_enabled = self.chk_animation.isChecked()
        s.performance_mode = self.chk_perf_mode.isChecked()
        s.sound_effects_enabled = self.chk_sound.isChecked()

        self.config_manager.save()
        self.engine.reset_schedule()
        self.settingsChanged.emit()

        self.status_save_label.setText(f"Settings saved successfully at {datetime.now().strftime('%H:%M:%S')}")

    def _restore_default_messages(self):
        defaults = AppSettings()
        self.edit_msg_prompt.setText(defaults.custom_greeting)
        self.edit_msg_yes.setText(defaults.message_yes)
        self.edit_msg_no.setText(defaults.message_no)

    def _reset_defaults(self):
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults? Your current settings will be backed up.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager.reset_to_defaults()
            self.load_values_from_settings()
            self.engine.reset_schedule()
            self.settingsChanged.emit()

    def _restore_backup(self):
        if self.config_manager.restore_backup():
            self.load_values_from_settings()
            self.engine.reset_schedule()
            self.settingsChanged.emit()
            QMessageBox.information(self, "Backup Restored", "Settings have been restored from the last backup.")
        else:
            QMessageBox.warning(self, "No Backup", "No valid backup file was found.")
