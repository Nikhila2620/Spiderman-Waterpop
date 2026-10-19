"""
Settings & Hydration Dashboard Window for Spider-Man Water Buddy.
Implements a premium Aquatic Liquid Glass user interface with custom left navigation sidebar,
animated liquid reservoir widget, translucent glass cards, and real-time hydration telemetry.
"""
from datetime import datetime
from pathlib import Path
import os
from PySide6.QtCore import Qt, QTime, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
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
    QButtonGroup,
)
from PySide6.QtGui import QFont, QCursor, QColor

from src.config import ConfigManager, AppSettings
from src.startup_manager import StartupManager
from src.reminder_engine import ReminderEngine, ReminderState
from src.theme import get_dashboard_qss, TOKENS
from src.components.glass_card import GlassCard
from src.components.liquid_reservoir import LiquidReservoirWidget
from src.components.streak_card import StreakCardWidget
from src.streak_tracker import StreakInfo


class DashboardWindow(QWidget):
    """
    Comprehensive graphical dashboard and settings window styled in Aquatic Liquid Glass.
    """

    settingsChanged = Signal()
    triggerReminderRequested = Signal()
    testAnimationRequested = Signal(str)

    def __init__(self, config_manager: ConfigManager, reminder_engine: ReminderEngine, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.settings = config_manager.settings
        self.engine = reminder_engine

        self._selected_amount = 250
        self._chip_buttons = []

        self.setObjectName("mainDashboard")
        self.setWindowTitle("Spider-Man Water Buddy v2.0 — Comic Night-City Edition")
        self.setMinimumSize(820, 640)
        self.resize(880, 680)

        self._init_ui()
        self._connect_engine_signals()
        self.load_values_from_settings()

    def _init_ui(self):
        self.setStyleSheet(get_dashboard_qss())

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Sleek Top Header Bar
        top_bar = QFrame()
        top_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(11, 14, 20, 0.95);
                border-bottom: 1px solid {TOKENS.BORDER_GLASS};
                padding: 10px 20px;
            }}
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(18, 12, 18, 12)
        top_layout.setSpacing(14)

        logo_title = QLabel("🕸️ SPIDER-MAN WATER BUDDY v2.0")
        logo_title.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 900;
            color: {TOKENS.ACCENT_AQUA};
            letter-spacing: 1.5px;
        """)
        top_layout.addWidget(logo_title)

        subtitle_badge = QLabel("COMIC NIGHT-CITY EDITION")
        subtitle_badge.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 800;
            color: {TOKENS.ACCENT_RED};
            background-color: rgba(255, 51, 85, 0.12);
            border: 1px solid rgba(255, 51, 85, 0.3);
            border-radius: 4px;
            padding: 3px 6px;
        """)
        top_layout.addWidget(subtitle_badge)
        top_layout.addStretch()

        self.btn_remind_now_top = QPushButton("💧 Remind Me Now")
        self.btn_remind_now_top.setProperty("class", "primaryBtn")
        self.btn_remind_now_top.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_remind_now_top.clicked.connect(self._on_remind_now_clicked)
        top_layout.addWidget(self.btn_remind_now_top)

        root_layout.addWidget(top_bar)

        # 2. Main Body Split: Left Sidebar + Right Stacked Content
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left Sidebar
        sidebar = QWidget()
        sidebar.setObjectName("sidebarContainer")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 18, 12, 18)
        sidebar_layout.setSpacing(6)

        self.nav_buttons = []
        nav_items = [
            ("📊  Dashboard", 0),
            ("⚙️  General", 1),
            ("⏱️  Reminders", 2),
            ("🎨  Appearance", 3),
            ("🛠️  Advanced", 4),
        ]

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "navBtn")
            btn.setCheckable(True)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            if index == 0:
                btn.setChecked(True)
                btn.setProperty("selected", "true")
            else:
                btn.setProperty("selected", "false")
            btn.clicked.connect(lambda chk=False, idx=index: self._switch_nav(idx))
            self.nav_group.addButton(btn, index)
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        body_layout.addWidget(sidebar)

        # Right Stacked Content Pages
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_dashboard_tab())
        self.stack.addWidget(self._build_general_tab())
        self.stack.addWidget(self._build_reminders_tab())
        self.stack.addWidget(self._build_appearance_tab())
        self.stack.addWidget(self._build_advanced_tab())
        body_layout.addWidget(self.stack)

        root_layout.addLayout(body_layout)

        # 3. Bottom Save & Status Bar
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(7, 17, 30, 0.95);
                border-top: 1px solid {TOKENS.BORDER_GLASS};
                padding: 10px 20px;
            }}
        """)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(18, 10, 18, 10)

        self.status_save_label = QLabel("Settings up to date.")
        self.status_save_label.setStyleSheet(f"color: {TOKENS.TEXT_SECONDARY}; font-size: 12px;")
        bottom_layout.addWidget(self.status_save_label)
        bottom_layout.addStretch()

        self.btn_apply = QPushButton("Apply & Save ✨")
        self.btn_apply.setProperty("class", "primaryBtn")
        self.btn_apply.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_apply.clicked.connect(self.save_and_apply)
        bottom_layout.addWidget(self.btn_apply)

        root_layout.addWidget(bottom_bar)

    def _switch_nav(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            is_active = (i == index)
            btn.setProperty("selected", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # PAGE 1: Aquatic Dashboard & Liquid Reservoir
    def _build_dashboard_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 1. Top Telemetry Row: Status & Next Countdown
        telemetry_row = QHBoxLayout()
        telemetry_row.setSpacing(14)

        card_status = GlassCard("Companion Status", "Current desktop presence")
        cs_box = QHBoxLayout()
        self.lbl_companion_status = QLabel("🟢 ACTIVE")
        self.lbl_companion_status.setStyleSheet(f"font-size: 17px; font-weight: 800; color: {TOKENS.STATUS_SUCCESS};")
        cs_box.addWidget(self.lbl_companion_status)
        card_status.content_layout.addLayout(cs_box)
        telemetry_row.addWidget(card_status)

        self.card_timer = GlassCard("Next Reminder", "Countdown to hydration prompt")
        ct_box = QHBoxLayout()
        self.lbl_countdown = QLabel("--:--")
        self.lbl_countdown.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {TOKENS.ACCENT_AQUA};")
        ct_box.addWidget(self.lbl_countdown)
        self.card_timer.content_layout.addLayout(ct_box)
        telemetry_row.addWidget(self.card_timer)

        layout.addLayout(telemetry_row)

        # 2. Main Fluid Hydration Reservoir Card
        reservoir_card = GlassCard("Daily Hydration Reservoir", "Live simulated fluid dynamics and progress tracking")
        res_layout = QVBoxLayout()
        res_layout.setSpacing(14)

        # Animated Liquid Reservoir Widget
        self.reservoir_widget = LiquidReservoirWidget()
        res_layout.addWidget(self.reservoir_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # Hero Water Intake Controls & Amount Chips
        hero_log_box = QVBoxLayout()
        hero_log_box.setSpacing(10)

        # Chips row
        chip_box = QHBoxLayout()
        chip_box.setSpacing(8)

        lbl_chip_prompt = QLabel("Select Intake:")
        lbl_chip_prompt.setStyleSheet(f"color: {TOKENS.TEXT_SECONDARY}; font-weight: 700; font-size: 12px;")
        chip_box.addWidget(lbl_chip_prompt)

        self._chip_buttons = []
        amounts = [(150, "150 ml (Cup)"), (250, "250 ml (Glass)"), (350, "350 ml (Mug)"), (500, "500 ml (Bottle)")]
        for amt, label in amounts:
            chip = QPushButton(label)
            chip.setProperty("class", "chipBtn")
            chip.setProperty("amount", amt)
            chip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            if amt == self._selected_amount:
                chip.setProperty("selected", "true")
            else:
                chip.setProperty("selected", "false")
            chip.clicked.connect(lambda chk=False, a=amt: self._select_amount(a))
            chip_box.addWidget(chip)
            self._chip_buttons.append(chip)

        chip_box.addStretch()
        hero_log_box.addLayout(chip_box)

        # Big Hero Manual Drink Button
        self.btn_hero_drink = QPushButton("💧 YES, I DRANK (250 ml)")
        self.btn_hero_drink.setProperty("class", "heroDrinkBtn")
        self.btn_hero_drink.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_hero_drink.clicked.connect(self._on_hero_drink_clicked)
        hero_log_box.addWidget(self.btn_hero_drink)

        # Cooldown & Spacing Label
        self.lbl_cooldown_status = QLabel("Ready to log hydration")
        self.lbl_cooldown_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cooldown_status.setStyleSheet(f"font-size: 11.5px; font-weight: 600; color: {TOKENS.ACCENT_MINT};")
        hero_log_box.addWidget(self.lbl_cooldown_status)

        res_layout.addLayout(hero_log_box)

        # Legacy Quick Log Buttons (Kept for compatibility with test suites & quick shortcuts)
        self.btn_log_250 = QPushButton("💧 +250 ml")
        self.btn_log_250.setVisible(False)
        self.btn_log_250.clicked.connect(lambda: self._quick_log_water(250))
        self.btn_log_500 = QPushButton("🌊 +500 ml")
        self.btn_log_500.setVisible(False)
        self.btn_log_500.clicked.connect(lambda: self._quick_log_water(500))
        res_layout.addWidget(self.btn_log_250)
        res_layout.addWidget(self.btn_log_500)

        # Fallback hidden labels for compatibility
        self.lbl_hydro_stats = QLabel("0 / 2000 ml (0%)")
        self.lbl_hydro_stats.setVisible(False)
        self.progress_hydro = QProgressBar()
        self.progress_hydro.setVisible(False)
        self.lbl_reminders_completed = QLabel("Completed Reminders Today: 0")
        self.lbl_reminders_completed.setStyleSheet(f"color: {TOKENS.TEXT_MUTED}; font-size: 12.5px; font-weight: 600;")
        res_layout.addWidget(self.lbl_reminders_completed)

        reservoir_card.content_layout.addLayout(res_layout)
        layout.addWidget(reservoir_card)

        # 3. Daily Hydration Goal & Streak Tracker Card
        self.streak_card = StreakCardWidget()
        layout.addWidget(self.streak_card)

        # 4. Quick Action Controls Card
        ctrl_card = GlassCard("Companion Quick Controls", "Pause or hide desktop overlay")
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(12)

        self.btn_pause_toggle = QPushButton("⏸️ Pause Reminders")
        self.btn_pause_toggle.setProperty("class", "secondaryBtn")
        self.btn_pause_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pause_toggle.clicked.connect(self._on_toggle_pause_clicked)
        ctrl_layout.addWidget(self.btn_pause_toggle)

        self.btn_visibility_toggle = QPushButton("👁️ Hide Companion")
        self.btn_visibility_toggle.setProperty("class", "secondaryBtn")
        self.btn_visibility_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_visibility_toggle.clicked.connect(self._on_toggle_visibility_clicked)
        ctrl_layout.addWidget(self.btn_visibility_toggle)

        ctrl_layout.addStretch()
        ctrl_card.content_layout.addLayout(ctrl_layout)
        layout.addWidget(ctrl_card)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    # PAGE 2: General Settings
    def _build_general_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Personalization
        id_card = GlassCard("Personalization", "Custom greetings and companion identity")
        id_card.content_layout.addWidget(QLabel("Companion Name:"))
        self.edit_comp_name = QLineEdit()
        id_card.content_layout.addWidget(self.edit_comp_name)

        id_card.content_layout.addWidget(QLabel("Your Preferred Name:"))
        self.edit_user_name = QLineEdit()
        id_card.content_layout.addWidget(self.edit_user_name)
        layout.addWidget(id_card)

        # Daily Hydration Goal
        goal_card = GlassCard("Hydration Target", "Daily target in milliliters (ml)")
        goal_row = QHBoxLayout()
        goal_row.addWidget(QLabel("Daily Goal (ml):"))
        self.spin_daily_goal = QSpinBox()
        self.spin_daily_goal.setRange(500, 10000)
        self.spin_daily_goal.setSingleStep(250)
        self.spin_daily_goal.setSuffix(" ml")
        goal_row.addWidget(self.spin_daily_goal)
        goal_row.addStretch()
        goal_card.content_layout.addLayout(goal_row)
        layout.addWidget(goal_card)

        # Windows Integration
        win_card = GlassCard("Windows Integration & System Behavior", "Configure startup and window layering")
        self.chk_startup = QCheckBox("Launch automatically when Windows starts")
        win_card.content_layout.addWidget(self.chk_startup)

        self.chk_start_minimized = QCheckBox("Start minimized in background tray")
        win_card.content_layout.addWidget(self.chk_start_minimized)

        self.chk_always_on_top = QCheckBox("Keep companion Always-On-Top of other windows")
        win_card.content_layout.addWidget(self.chk_always_on_top)
        layout.addWidget(win_card)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    # PAGE 3: Reminder Scheduling
    def _build_reminders_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Reminder Intervals
        sched_card = GlassCard("Reminder Timing & Recurrence", "Intervals between prompts and snoozes")
        self.chk_reminders_enabled = QCheckBox("Enable Automatic Water Reminders")
        sched_card.content_layout.addWidget(self.chk_reminders_enabled)

        int_row = QHBoxLayout()
        int_row.addWidget(QLabel("Recurring Interval:"))
        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["15 min", "30 min", "45 min", "60 min", "90 min", "Custom"])
        self.combo_interval.currentIndexChanged.connect(self._on_combo_interval_changed)
        int_row.addWidget(self.combo_interval)

        self.spin_interval_custom = QSpinBox()
        self.spin_interval_custom.setRange(1, 720)
        self.spin_interval_custom.setSuffix(" min")
        int_row.addWidget(self.spin_interval_custom)
        int_row.addStretch()
        sched_card.content_layout.addLayout(int_row)

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
        snooze_row.addStretch()
        sched_card.content_layout.addLayout(snooze_row)
        layout.addWidget(sched_card)

        # Quiet Hours
        quiet_card = GlassCard("Quiet Hours (Do Not Disturb)", "Prevent notifications during sleep or focus hours")
        self.chk_quiet = QCheckBox("Enable Quiet Hours")
        quiet_card.content_layout.addWidget(self.chk_quiet)

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
        quiet_card.content_layout.addLayout(q_row)
        layout.addWidget(quiet_card)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    # PAGE 4: Appearance & Motion
    def _build_appearance_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Desktop Placement
        pos_card = GlassCard("Desktop Screen Placement", "Corner anchoring for Spider-Man web hang")
        p_layout = QHBoxLayout()
        p_layout.addWidget(QLabel("Anchor Corner:"))
        self.combo_corner = QComboBox()
        self.combo_corner.addItems(["top-right", "top-left", "bottom-right", "bottom-left"])
        p_layout.addWidget(self.combo_corner)
        p_layout.addStretch()
        pos_card.content_layout.addLayout(p_layout)
        layout.addWidget(pos_card)

        # Interaction & Motion
        act_card = GlassCard("Interaction, Motion & Physics", "Configure web swinging and hover awareness")
        self.chk_click_through = QCheckBox("Enable Click-Through (Clicks pass through companion to apps below)")
        act_card.content_layout.addWidget(self.chk_click_through)

        lbl_hint = QLabel("💡 Press 'Ctrl+Alt+W' or use the System Tray to toggle interaction mode anytime.")
        lbl_hint.setStyleSheet(f"color: {TOKENS.TEXT_MUTED}; font-size: 11.5px;")
        act_card.content_layout.addWidget(lbl_hint)

        self.chk_mouse_follow = QCheckBox("Spider-Sense Awareness (Reacts when pointer approaches)")
        act_card.content_layout.addWidget(self.chk_mouse_follow)

        self.chk_animation = QCheckBox("Enable Natural Pendulum Web Swinging")
        act_card.content_layout.addWidget(self.chk_animation)

        self.chk_perf_mode = QCheckBox("Performance Mode (Minimizes CPU/GPU draw on battery)")
        act_card.content_layout.addWidget(self.chk_perf_mode)

        self.chk_sound = QCheckBox("Play Audio Cues on Reminders")
        act_card.content_layout.addWidget(self.chk_sound)
        layout.addWidget(act_card)

        # Animation Preview
        anim_card = GlassCard("Animation & Reaction Previews", "Trigger character state reactions")
        an_layout = QHBoxLayout()
        an_layout.setSpacing(12)

        btn_test_happy = QPushButton("🎉 Test Happy Celebration")
        btn_test_happy.setProperty("class", "secondaryBtn")
        btn_test_happy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_test_happy.clicked.connect(lambda: self.testAnimationRequested.emit("happy"))
        an_layout.addWidget(btn_test_happy)

        btn_test_sad = QPushButton("🕷️ Test Disappointed Reaction")
        btn_test_sad.setProperty("class", "secondaryBtn")
        btn_test_sad.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_test_sad.clicked.connect(lambda: self.testAnimationRequested.emit("disappointed"))
        an_layout.addWidget(btn_test_sad)
        an_layout.addStretch()

        anim_card.content_layout.addLayout(an_layout)
        layout.addWidget(anim_card)

        # Custom Messages
        msg_card = GlassCard("Custom Dialogue Messages", "Use '[Name]' to dynamically insert your name")
        msg_card.content_layout.addWidget(QLabel("Reminder Prompt:"))
        self.edit_msg_prompt = QLineEdit()
        msg_card.content_layout.addWidget(self.edit_msg_prompt)

        msg_card.content_layout.addWidget(QLabel("Celebration (YES):"))
        self.edit_msg_yes = QLineEdit()
        msg_card.content_layout.addWidget(self.edit_msg_yes)

        msg_card.content_layout.addWidget(QLabel("Postponed (NO):"))
        self.edit_msg_no = QLineEdit()
        msg_card.content_layout.addWidget(self.edit_msg_no)

        btn_restore_msgs = QPushButton("Restore Default Dialogue")
        btn_restore_msgs.setProperty("class", "secondaryBtn")
        btn_restore_msgs.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_restore_msgs.clicked.connect(self._restore_default_messages)
        msg_card.content_layout.addWidget(btn_restore_msgs)
        layout.addWidget(msg_card)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    # PAGE 5: Advanced & About
    def _build_advanced_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # About & Diagnostics
        info_card = GlassCard("Application Information & Diagnostics", "Technical telemetry and system paths")
        info_rows = [
            ("Version:", "1.0.0 (Aquatic Liquid Glass Edition)"),
            ("Framework:", "PySide6 (Qt 6.12) / Python 3.11"),
            ("Rendering Engine:", "Hardware Accelerated 2D Vector & PBR Alpha Blending"),
            ("Config Path:", str(self.config_manager.settings_file)),
            ("Log Path:", str(Path(os.environ.get("APPDATA", "")) / "SpiderManWaterBuddy" / "logs" / "app.log")),
        ]
        for label, val in info_rows:
            row = QHBoxLayout()
            lbl_k = QLabel(label)
            lbl_k.setStyleSheet(f"color: {TOKENS.TEXT_MUTED}; font-weight: 700; width: 120px;")
            lbl_v = QLabel(val)
            lbl_v.setStyleSheet(f"color: {TOKENS.TEXT_PRIMARY}; font-size: 12px;")
            row.addWidget(lbl_k)
            row.addWidget(lbl_v)
            row.addStretch()
            info_card.content_layout.addLayout(row)
        layout.addWidget(info_card)

        # Configuration Recovery & Reset
        bak_card = GlassCard("Configuration Backup & Safety", "Revert changes or restore defaults")
        bak_layout = QHBoxLayout()
        bak_layout.setSpacing(12)

        btn_restore_bak = QPushButton("🔄 Restore Settings Backup")
        btn_restore_bak.setProperty("class", "secondaryBtn")
        btn_restore_bak.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_restore_bak.clicked.connect(self._restore_backup)
        bak_layout.addWidget(btn_restore_bak)

        btn_reset_defaults = QPushButton("⚠️ Reset All Defaults")
        btn_reset_defaults.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(239, 68, 68, 0.15);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: {TOKENS.RADIUS_MD};
                padding: 8px 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #ef4444;
                color: #ffffff;
            }}
        """)
        btn_reset_defaults.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_reset_defaults.clicked.connect(self._reset_defaults)
        bak_layout.addWidget(btn_reset_defaults)
        bak_layout.addStretch()

        bak_card.content_layout.addLayout(bak_layout)
        layout.addWidget(bak_card)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def _connect_engine_signals(self):
        self.engine.timerTick.connect(self._on_timer_tick)
        self.engine.stateChanged.connect(self._on_state_changed)
        self.engine.statsUpdated.connect(self._on_stats_updated)
        self.engine.streakUpdated.connect(self._on_streak_updated)
        self.engine.goalCelebrated.connect(self._on_goal_celebrated)
        self.engine.cooldownTick.connect(self._on_cooldown_tick)

    def _select_amount(self, amount: int):
        self._selected_amount = amount
        for chip in getattr(self, "_chip_buttons", []):
            is_active = (chip.property("amount") == amount)
            chip.setProperty("selected", "true" if is_active else "false")
            chip.style().unpolish(chip)
            chip.style().polish(chip)
        rem = self.engine.streak_tracker.get_cooldown_remaining()
        if rem <= 0 and hasattr(self, "btn_hero_drink"):
            self.btn_hero_drink.setText(f"💧 YES, I DRANK ({amount} ml)")

    def _on_hero_drink_clicked(self):
        res = self.engine.log_manual(self._selected_amount)
        if res.ok:
            self.status_save_label.setText(f"Logged +{res.added_ml} ml of water! Hero status: Hydrated! 💧")
            self._on_cooldown_tick(res.remaining_seconds)
        else:
            mins, secs = divmod(res.remaining_seconds, 60)
            self.status_save_label.setText(f"Cooldown active: please wait {mins}m {secs:02d}s before logging again.")
            self._on_cooldown_tick(res.remaining_seconds)

    def _on_cooldown_tick(self, rem_secs: int):
        if not hasattr(self, "btn_hero_drink"):
            return
        if rem_secs > 0:
            mins, secs = divmod(rem_secs, 60)
            self.btn_hero_drink.setEnabled(False)
            self.btn_hero_drink.setText(f"⏳ Next log in {mins:02d}:{secs:02d}")
            self.lbl_cooldown_status.setText(f"Cooldown active: {mins}m {secs:02d}s remaining (minimum 30m spacing)")
            self.lbl_cooldown_status.setStyleSheet(f"font-size: 11.5px; font-weight: 700; color: {TOKENS.STATUS_WARNING};")
            for chip in getattr(self, "_chip_buttons", []):
                chip.setEnabled(False)
        else:
            self.btn_hero_drink.setEnabled(True)
            self.btn_hero_drink.setText(f"💧 YES, I DRANK ({self._selected_amount} ml)")
            self.lbl_cooldown_status.setText("Ready to log hydration")
            self.lbl_cooldown_status.setStyleSheet(f"font-size: 11.5px; font-weight: 600; color: {TOKENS.ACCENT_MINT};")
            for chip in getattr(self, "_chip_buttons", []):
                chip.setEnabled(True)

    def _on_streak_updated(self, info: StreakInfo):
        if hasattr(self, "streak_card"):
            self.streak_card.update_info(info)

    def _on_goal_celebrated(self, msg: str):
        if hasattr(self, "streak_card"):
            self.streak_card.trigger_celebration(msg)

    def _on_timer_tick(self, seconds: int):
        if self.engine.state == ReminderState.QUIET_HOURS:
            end_time_str = self.settings.quiet_hours_end
            try:
                t = datetime.strptime(end_time_str, "%H:%M")
                formatted_end = t.strftime("%I:%M %p").lstrip("0")
            except Exception:
                formatted_end = end_time_str

            hrs, rem = divmod(max(0, seconds), 3600)
            mins, secs = divmod(rem, 60)

            self.lbl_countdown.setText(f"Resumes {formatted_end}")
            self.lbl_countdown.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {TOKENS.ACCENT_AQUA};")
            if hasattr(self, "card_timer"):
                self.card_timer.lbl_subtitle.setText(f"Sleeping • Resumes in {hrs}h {mins:02d}m")
            self.lbl_countdown.setToolTip(
                f"Quiet Hours are active ({self.settings.quiet_hours_start} to {self.settings.quiet_hours_end}).\n"
                f"Hydration reminders will automatically resume at {formatted_end} (in {hrs}h {mins:02d}m {secs:02d}s)."
            )
            return

        if hasattr(self, "card_timer"):
            self.card_timer.lbl_subtitle.setText("Countdown to hydration prompt")

        if seconds < 0 or self.settings.reminders_paused or not self.settings.reminders_enabled:
            self.lbl_countdown.setText("Paused")
            self.lbl_countdown.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {TOKENS.STATUS_WARNING};")
            self.lbl_countdown.setToolTip("Reminders are currently paused.")
        elif seconds == 0:
            self.lbl_countdown.setText("DUE NOW!")
            self.lbl_countdown.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {TOKENS.ACCENT_MINT};")
            self.lbl_countdown.setToolTip("Hydration reminder is due right now!")
        else:
            hrs, rem = divmod(seconds, 3600)
            mins, secs = divmod(rem, 60)
            if hrs > 0:
                self.lbl_countdown.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")
            else:
                self.lbl_countdown.setText(f"{mins:02d}:{secs:02d}")
            self.lbl_countdown.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {TOKENS.ACCENT_AQUA};")
            self.lbl_countdown.setToolTip(
                f"Next reminder in {hrs}h {mins}m {secs}s" if hrs > 0 else f"Next reminder in {mins}m {secs}s"
            )

    def _on_state_changed(self, state: ReminderState):
        if state == ReminderState.PAUSED:
            self.lbl_companion_status.setText("⏸️ PAUSED")
            self.lbl_companion_status.setStyleSheet(f"font-size: 17px; font-weight: 800; color: {TOKENS.STATUS_WARNING};")
            self.btn_pause_toggle.setText("▶️ Resume Reminders")
        elif state == ReminderState.QUIET_HOURS:
            self.lbl_companion_status.setText("🌙 QUIET HOURS")
            self.lbl_companion_status.setStyleSheet(f"font-size: 17px; font-weight: 800; color: {TOKENS.TEXT_MUTED};")
            rem_secs = self.engine.get_seconds_remaining()
            if rem_secs > 0:
                self._on_timer_tick(rem_secs)
        elif state == ReminderState.WAITING_FOR_RESPONSE:
            self.lbl_companion_status.setText("💧 REMINDER ACTIVE")
            self.lbl_companion_status.setStyleSheet(f"font-size: 17px; font-weight: 800; color: {TOKENS.ACCENT_AQUA};")
        else:
            self.lbl_companion_status.setText("🟢 ACTIVE")
            self.lbl_companion_status.setStyleSheet(f"font-size: 17px; font-weight: 800; color: {TOKENS.STATUS_SUCCESS};")
            self.btn_pause_toggle.setText("⏸️ Pause Reminders")
            if hasattr(self, "card_timer"):
                self.card_timer.lbl_subtitle.setText("Countdown to hydration prompt")

    def _on_stats_updated(self, count: int, ml: int):
        self.lbl_reminders_completed.setText(f"Completed Reminders Today: {count}")
        goal = self.settings.daily_hydration_goal_ml
        pct = min(100, int((ml / goal) * 100)) if goal > 0 else 0
        self.lbl_hydro_stats.setText(f"{ml} / {goal} ml ({pct}%)")
        self.progress_hydro.setValue(pct)
        # Update animated fluid reservoir
        self.reservoir_widget.set_values(ml, goal)

    def _quick_log_water(self, ml: int, is_manual: bool = False):
        if is_manual:
            res = self.engine.log_manual(ml)
            if res.ok:
                self.status_save_label.setText(f"Logged +{res.added_ml} ml of water! Hero status: Hydrated! 💧")
                self._on_cooldown_tick(res.remaining_seconds)
            else:
                mins, secs = divmod(res.remaining_seconds, 60)
                self.status_save_label.setText(f"Cooldown active: please wait {mins}m {secs:02d}s before logging again.")
                self._on_cooldown_tick(res.remaining_seconds)
            return res
        else:
            self.engine.on_user_drank_water(ml)
            self.status_save_label.setText(f"Logged +{ml} ml of water! Great job staying hydrated 💧")
            return None

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
        self.spin_daily_goal.setValue(s.daily_hydration_goal_ml)

        # Windows
        self.chk_startup.setChecked(s.launch_at_startup)
        self.chk_start_minimized.setChecked(s.start_minimized)
        self.chk_always_on_top.setChecked(s.always_on_top)

        # Reminders
        self.chk_reminders_enabled.setChecked(s.reminders_enabled)
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

        # Sync reservoir and telemetry
        self._on_stats_updated(s.today_reminders_completed, s.today_intake_ml)
        if hasattr(self, "streak_card"):
            self.streak_card.update_info(self.engine.get_streak_info())
        if hasattr(self, "_on_cooldown_tick"):
            rem = self.engine.streak_tracker.get_cooldown_remaining()
            self._on_cooldown_tick(rem)

    def save_and_apply(self):
        s = self.settings
        s.companion_name = self.edit_comp_name.text().strip() or "Spider-Man"
        s.user_name = self.edit_user_name.text().strip() or "Hero"
        s.daily_hydration_goal_ml = self.spin_daily_goal.value()

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
        # Refresh reservoir goal and streak card
        self._on_stats_updated(s.today_reminders_completed, s.today_intake_ml)
        if hasattr(self, "streak_card"):
            self.streak_card.update_info(self.engine.get_streak_info())

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
