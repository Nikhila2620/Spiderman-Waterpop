"""
Settings & Hydration Dashboard Window for Spider-Man Water Buddy.
Implements a premium Aquatic Liquid Glass user interface with custom left navigation sidebar,
animated liquid reservoir widget, translucent glass cards, and real-time hydration telemetry.
"""
from datetime import datetime, timedelta
from pathlib import Path
import os
import json
from PySide6.QtCore import Qt, QTime, Signal, QTimer, QObject, Slot, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
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
from PySide6.QtGui import QFont, QCursor, QColor, QPixmap, QIcon

from src.config import ConfigManager, AppSettings
from src.startup_manager import StartupManager
from src.reminder_engine import ReminderEngine, ReminderState
from src.theme import get_dashboard_qss, TOKENS
from src.version import VERSION, FULL_NAME
from src.components.glass_card import GlassCard
from src.components.liquid_reservoir import LiquidReservoirWidget
from src.components.streak_card import StreakCardWidget
from src.components.thread_matrix import ThreadMatrixWidget
from src.components.cinematic_splash import CinematicSplashOverlay
from src.streak_tracker import StreakInfo


class WebBridge(QObject):
    """Bridge for bidirectional communication between Qt Python and QWebEngine JavaScript."""
    actionDispatched = Signal(str, str)

    @Slot(str, str)
    def dispatch(self, action: str, payload_json: str):
        self.actionDispatched.emit(action, payload_json)


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
        self.setWindowTitle("Spider-Man Waterpop v2.0 — Lab Logbook")
        self.setMinimumSize(920, 700)
        self.resize(1020, 760)

        self._init_ui()
        self._connect_engine_signals()
        self.load_values_from_settings()

    def _init_ui(self):
        self.setStyleSheet(get_dashboard_qss())

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Primary Neo-Brutalist Pop-Art Graphic Dashboard (QWebEngineView)
        self.web_view = QWebEngineView(self)
        self.web_channel = QWebChannel(self)
        self.web_bridge = WebBridge(self)
        self.web_bridge.actionDispatched.connect(self._handle_web_action)
        self.web_channel.registerObject("pybridge", self.web_bridge)
        self.web_view.page().setWebChannel(self.web_channel)

        html_path = Path(__file__).resolve().parent / "web" / "dashboard.html"
        if html_path.exists():
            self.web_view.setUrl(QUrl.fromLocalFile(str(html_path)))
            self.web_view.loadFinished.connect(lambda ok: self._push_full_state_to_web())

        root_layout.addWidget(self.web_view)

        # 2. Native Subsystem Container (Retained for test compliance and instant fallback)
        self._native_container = QWidget(self)
        self._native_container.setVisible(False)
        native_layout = QVBoxLayout(self._native_container)
        native_layout.setContentsMargins(0, 0, 0, 0)
        native_layout.setSpacing(0)

        # 1. Peter Parker Lab Logbook Top Header Bar
        top_bar = QFrame()
        top_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {TOKENS.BG_BASE};
                border-bottom: 1px solid {TOKENS.BORDER_DEFAULT};
                padding: 10px 20px;
            }}
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 12, 20, 12)
        top_layout.setSpacing(14)

        # PP / App Icon Avatar Badge (Official Logo)
        lbl_pp = QLabel()
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "images" / "app_icon.png"
        if icon_path.exists():
            lbl_pp.setPixmap(QPixmap(str(icon_path)).scaled(34, 34, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl_pp.setText("PP")
            lbl_pp.setStyleSheet(f"""
                background-color: {TOKENS.ACCENT_RED};
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
                border-radius: 16px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
                qproperty-alignment: AlignCenter;
            """)
        top_layout.addWidget(lbl_pp)

        # Title & Subtitle Stack
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        
        t_row = QHBoxLayout()
        t_row.setSpacing(8)
        logo_title = QLabel("LAB LOGBOOK")
        logo_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 800;
            color: {TOKENS.TEXT_PRIMARY};
            letter-spacing: 0.5px;
        """)
        t_row.addWidget(logo_title)

        subtitle_badge = QLabel("v2.0")
        subtitle_badge.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 700;
            color: {TOKENS.TEXT_MUTED};
            background-color: {TOKENS.BORDER_DEFAULT};
            border-radius: 4px;
            padding: 2px 6px;
        """)
        t_row.addWidget(subtitle_badge)
        t_row.addStretch()
        title_box.addLayout(t_row)

        sub_desc = QLabel("Daily Osmosis & Hydration Metric")
        sub_desc.setStyleSheet(f"font-size: 11px; color: {TOKENS.TEXT_MUTED};")
        title_box.addWidget(sub_desc)

        top_layout.addLayout(title_box)
        top_layout.addStretch()

        # Center Spider-Sense Status Pill
        self.sense_pill = QLabel("●  SPIDER-SENSE: ACTIVE")
        self.sense_pill.setStyleSheet(f"""
            background-color: #242018;
            color: {TOKENS.ACCENT_GOLD};
            border: 1px solid #59421A;
            border-radius: 13px;
            padding: 5px 14px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
        """)
        top_layout.addWidget(self.sense_pill)
        top_layout.addStretch()

        # Right Controls: Cinematic Shoot / Spidey Perch / Settings / Remind Now
        self.btn_replay_intro = QPushButton("⚡ Intro")
        self.btn_replay_intro.setProperty("class", "secondaryBtn")
        self.btn_replay_intro.setToolTip("Play cinematic superhero intro sequence")
        self.btn_replay_intro.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_replay_intro.clicked.connect(self._play_cinematic_intro)
        top_layout.addWidget(self.btn_replay_intro)

        self.btn_spidey_perch = QPushButton("🕷️ Spidey Perch")
        self.btn_spidey_perch.setProperty("class", "secondaryBtn")
        self.btn_spidey_perch.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_spidey_perch.clicked.connect(self._on_toggle_visibility_clicked)
        top_layout.addWidget(self.btn_spidey_perch)

        self.btn_settings_tab = QPushButton("⚙️ Settings")
        self.btn_settings_tab.setProperty("class", "secondaryBtn")
        self.btn_settings_tab.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_settings_tab.clicked.connect(self._toggle_settings_sidebar)
        top_layout.addWidget(self.btn_settings_tab)

        self.btn_remind_now_top = QPushButton("💧 Remind Now")
        self.btn_remind_now_top.setProperty("class", "primaryBtn")
        self.btn_remind_now_top.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_remind_now_top.clicked.connect(self._on_remind_now_clicked)
        top_layout.addWidget(self.btn_remind_now_top)

        native_layout.addWidget(top_bar)

        # 2. Main Body Split: Left Sidebar + Right Stacked Content
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left Sidebar (Hidden by default for pure Image 2 replica, toggled by ⚙️ Settings)
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebarContainer")
        self.sidebar.setFixedWidth(170)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 16, 10, 16)
        sidebar_layout.setSpacing(4)

        self.nav_buttons = []
        nav_items = [
            ("Dashboard", 0),
            ("General", 1),
            ("Reminders", 2),
            ("Appearance", 3),
            ("Advanced", 4),
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
        self.sidebar.setVisible(False)
        body_layout.addWidget(self.sidebar)

        # Right Stacked Content Pages
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_dashboard_tab())
        self.stack.addWidget(self._build_general_tab())
        self.stack.addWidget(self._build_reminders_tab())
        self.stack.addWidget(self._build_appearance_tab())
        self.stack.addWidget(self._build_advanced_tab())
        body_layout.addWidget(self.stack)

        native_layout.addLayout(body_layout)

        # 3. Bottom Save & Status Bar (Visible on Settings pages)
        self.bottom_bar = QFrame()
        self.bottom_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {TOKENS.BG_SURFACE};
                border-top: 1px solid {TOKENS.BORDER_DEFAULT};
                padding: 10px 20px;
            }}
        """)
        bottom_layout = QHBoxLayout(self.bottom_bar)
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

        self.bottom_bar.setVisible(False)
        native_layout.addWidget(self.bottom_bar)

        root_layout.addWidget(self._native_container)

        # 4. Cinematic Splash Opening Animation Overlay
        self.splash_overlay = CinematicSplashOverlay(self)

    def _switch_nav(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            is_active = (i == index)
            btn.setProperty("selected", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        if index == 0:
            if hasattr(self, "bottom_bar"):
                self.bottom_bar.setVisible(False)
            if hasattr(self, "sidebar"):
                self.sidebar.setVisible(False)
        else:
            if hasattr(self, "bottom_bar"):
                self.bottom_bar.setVisible(True)
            if hasattr(self, "sidebar"):
                self.sidebar.setVisible(True)

        if hasattr(self, "web_view") and self.web_view.page():
            view_id = "today" if index == 0 else "settings"
            self.web_view.page().runJavaScript(f"if(typeof view==='function') view('{view_id}');")

    def _toggle_settings_sidebar(self):
        new_vis = not self.sidebar.isVisible()
        self.sidebar.setVisible(new_vis)
        self.bottom_bar.setVisible(new_vis)
        if new_vis and self.stack.currentIndex() == 0:
            self._switch_nav(1)
        elif not new_vis and self.stack.currentIndex() != 0:
            self._switch_nav(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "splash_overlay"):
            self.splash_overlay.setGeometry(self.rect())

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "splash_overlay") and not getattr(self, "_has_played_intro", False):
            self._has_played_intro = True
            QTimer.singleShot(80, self.splash_overlay.start_intro)
        QTimer.singleShot(250, self._push_full_state_to_web)

    def _play_cinematic_intro(self):
        if hasattr(self, "splash_overlay"):
            self.splash_overlay.start_intro()

    # PAGE 1: Aquatic Dashboard & Liquid Reservoir
    def _build_dashboard_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # 2-Column Split Layout
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(16)

        # -------------------------------------------------------------
        # LEFT COLUMN (Hero Fluid Reservoir & Manual Hydration Logging)
        # -------------------------------------------------------------
        left_col = QVBoxLayout()
        left_col.setSpacing(14)

        core_card = GlassCard("● CORE FLUID LEVEL", "Active desktop HUD presence & daily volume")
        res_layout = QVBoxLayout()
        res_layout.setSpacing(12)

        # Animated Liquid Reservoir Widget
        self.reservoir_widget = LiquidReservoirWidget()
        res_layout.addWidget(self.reservoir_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # Hero Water Intake Controls & Amount Chips
        hero_log_box = QVBoxLayout()
        hero_log_box.setSpacing(10)

        # Chips row
        chip_box = QHBoxLayout()
        chip_box.setSpacing(8)

        lbl_chip_prompt = QLabel("TARGET DOSE:")
        lbl_chip_prompt.setStyleSheet(f"color: {TOKENS.TEXT_SECONDARY}; font-weight: 800; font-size: 11px; font-family: 'Cascadia Code', monospace;")
        chip_box.addWidget(lbl_chip_prompt)

        self._chip_buttons = []
        amounts = [(150, "[ 150 ml ]"), (250, "[ 250 ml ]"), (350, "[ 350 ml ]"), (500, "[ 500 ml ]")]
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
        self.btn_hero_drink = QPushButton(f"💧 [ +{self._selected_amount} ml ] YES, I DRANK")
        self.btn_hero_drink.setProperty("class", "heroDrinkBtn")
        self.btn_hero_drink.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_hero_drink.clicked.connect(self._on_hero_drink_clicked)
        hero_log_box.addWidget(self.btn_hero_drink)

        # Cooldown & Status Label
        self.lbl_cooldown_status = QLabel("Ready to log hydration")
        self.lbl_cooldown_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cooldown_status.setStyleSheet(f"font-size: 11.5px; font-weight: 600; color: {TOKENS.ACCENT_MINT};")
        hero_log_box.addWidget(self.lbl_cooldown_status)

        # Quick Log Dose Buttons (Glass, Flask, Canteen)
        quick_btns_box = QHBoxLayout()
        quick_btns_box.setSpacing(8)

        self.btn_quick_250 = QPushButton("+250ml Glass")
        self.btn_quick_250.setProperty("class", "secondaryBtn")
        self.btn_quick_250.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_quick_250.clicked.connect(lambda: self._on_quick_dose_clicked(250))
        quick_btns_box.addWidget(self.btn_quick_250)

        self.btn_quick_350 = QPushButton("+350ml Flask")
        self.btn_quick_350.setProperty("class", "secondaryBtn")
        self.btn_quick_350.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_quick_350.clicked.connect(lambda: self._on_quick_dose_clicked(350))
        quick_btns_box.addWidget(self.btn_quick_350)

        self.btn_quick_500 = QPushButton("+500ml Canteen")
        self.btn_quick_500.setProperty("class", "secondaryBtn")
        self.btn_quick_500.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_quick_500.clicked.connect(lambda: self._on_quick_dose_clicked(500))
        quick_btns_box.addWidget(self.btn_quick_500)

        hero_log_box.addLayout(quick_btns_box)

        # Custom Intake Spinbox + Reset Day row
        adjust_row = QHBoxLayout()
        adjust_row.setSpacing(8)

        lbl_custom = QLabel("Custom:")
        lbl_custom.setStyleSheet(f"color: {TOKENS.TEXT_SECONDARY}; font-size: 11px;")
        adjust_row.addWidget(lbl_custom)

        self.spin_custom_amount = QSpinBox()
        self.spin_custom_amount.setRange(50, 1500)
        self.spin_custom_amount.setSingleStep(50)
        self.spin_custom_amount.setValue(200)
        self.spin_custom_amount.setSuffix(" ml")
        adjust_row.addWidget(self.spin_custom_amount)

        self.btn_log_custom = QPushButton("+ Log")
        self.btn_log_custom.setProperty("class", "secondaryBtn")
        self.btn_log_custom.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_log_custom.clicked.connect(lambda: self._on_quick_dose_clicked(self.spin_custom_amount.value()))
        adjust_row.addWidget(self.btn_log_custom)

        adjust_row.addStretch()

        self.btn_reset_day = QPushButton("↺ Reset Today")
        self.btn_reset_day.setProperty("class", "secondaryBtn")
        self.btn_reset_day.setToolTip("Reset today's logged hydration counter to 0")
        self.btn_reset_day.clicked.connect(self._on_reset_today_clicked)
        adjust_row.addWidget(self.btn_reset_day)

        hero_log_box.addLayout(adjust_row)
        res_layout.addLayout(hero_log_box)

        # Legacy Quick Log Buttons & Labels (Kept for compatibility with test suites & quick shortcuts)
        self.btn_log_250 = QPushButton("💧 +250 ml")
        self.btn_log_250.setVisible(False)
        self.btn_log_250.clicked.connect(lambda: self._quick_log_water(250))
        self.btn_log_500 = QPushButton("🌊 +500 ml")
        self.btn_log_500.setVisible(False)
        self.btn_log_500.clicked.connect(lambda: self._quick_log_water(500))
        res_layout.addWidget(self.btn_log_250)
        res_layout.addWidget(self.btn_log_500)

        self.lbl_hydro_stats = QLabel("0 / 2000 ml (0%)")
        self.lbl_hydro_stats.setVisible(False)
        self.progress_hydro = QProgressBar()
        self.progress_hydro.setVisible(False)
        self.lbl_reminders_completed = QLabel("Completed Reminders Today: 0")
        self.lbl_reminders_completed.setStyleSheet(f"color: {TOKENS.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        res_layout.addWidget(self.lbl_reminders_completed)

        core_card.content_layout.addLayout(res_layout)
        left_col.addWidget(core_card)
        left_col.addStretch()
        cols_layout.addLayout(left_col, stretch=1)

        # -------------------------------------------------------------
        # RIGHT COLUMN: HERO REMINDER PROTOCOL & LAB LOGBOOK CARDS
        # -------------------------------------------------------------
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        # Card 1: HERO REMINDER PROTOCOL & NEXT PROMPT (v1.0.0 Restored & Enhanced)
        self.card_timer = GlassCard("REMINDER PROTOCOL & NEXT PROMPT", "Countdown to hydration prompt")
        timer_box = QVBoxLayout()
        timer_box.setSpacing(10)

        # Status & Scheduled Trigger Time Row
        sched_header_row = QHBoxLayout()
        sched_header_row.setSpacing(8)

        self.lbl_companion_status = QLabel("🟢 ACTIVE MONITORING")
        self.lbl_companion_status.setStyleSheet(f"""
            background-color: #121E17;
            color: {TOKENS.STATUS_SUCCESS};
            border: 1px solid #1E3D2B;
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 800;
            font-family: 'Cascadia Code', monospace;
        """)
        sched_header_row.addWidget(self.lbl_companion_status)

        self.lbl_next_time = QLabel("Scheduled Trigger: --:--")
        self.lbl_next_time.setStyleSheet(f"""
            color: {TOKENS.TEXT_SECONDARY};
            font-size: 11.5px;
            font-weight: 600;
            font-family: 'Cascadia Code', monospace;
        """)
        sched_header_row.addWidget(self.lbl_next_time)
        sched_header_row.addStretch()

        timer_box.addLayout(sched_header_row)

        # Huge Central Monospace Countdown
        countdown_container = QFrame()
        countdown_container.setStyleSheet(f"""
            background-color: {TOKENS.BG_INPUT};
            border: 1px solid {TOKENS.BORDER_DEFAULT};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 12px 16px;
        """)
        cd_vbox = QVBoxLayout(countdown_container)
        cd_vbox.setContentsMargins(0, 0, 0, 0)
        cd_vbox.setSpacing(2)

        self.lbl_countdown = QLabel("--:--")
        self.lbl_countdown.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_countdown.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 900;
            color: {TOKENS.ACCENT_AQUA};
            font-family: 'Cascadia Code', monospace;
            letter-spacing: 1px;
        """)
        cd_vbox.addWidget(self.lbl_countdown)

        lbl_cd_sub = QLabel("NEXT HYDRATION DISPATCH")
        lbl_cd_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_cd_sub.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 700;
            color: {TOKENS.TEXT_MUTED};
            letter-spacing: 0.8px;
            font-family: 'Cascadia Code', monospace;
        """)
        cd_vbox.addWidget(lbl_cd_sub)

        timer_box.addWidget(countdown_container)

        # Quick Interval Selector & Pause Toggle
        protocol_ctrl_row = QHBoxLayout()
        protocol_ctrl_row.setSpacing(10)

        lbl_cadence = QLabel("Cadence:")
        lbl_cadence.setStyleSheet(f"color: {TOKENS.TEXT_SECONDARY}; font-size: 11.5px; font-weight: 700;")
        protocol_ctrl_row.addWidget(lbl_cadence)

        self.quick_combo_interval = QComboBox()
        self.quick_combo_interval.addItems(["15 Mins", "30 Mins", "45 Mins", "60 Mins"])
        self.quick_combo_interval.setCurrentText("30 Mins")
        self.quick_combo_interval.currentTextChanged.connect(self._on_quick_interval_changed)
        protocol_ctrl_row.addWidget(self.quick_combo_interval)

        self.btn_pause_toggle = QPushButton("⏸️ Pause Reminders")
        self.btn_pause_toggle.setProperty("class", "secondaryBtn")
        self.btn_pause_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pause_toggle.clicked.connect(self._on_toggle_pause_clicked)
        protocol_ctrl_row.addWidget(self.btn_pause_toggle)

        protocol_ctrl_row.addStretch()
        timer_box.addLayout(protocol_ctrl_row)

        self.card_timer.content_layout.addLayout(timer_box)
        right_col.addWidget(self.card_timer)

        # Card 2: DAILY THREAD MATRIX & OSMOSIS METRICS (7-Day Log)
        card_matrix = GlassCard("DAILY THREAD MATRIX", "7-Day continuous hydration thread network")
        self.thread_matrix = ThreadMatrixWidget()
        card_matrix.content_layout.addWidget(self.thread_matrix)

        # Analytics row: Weekly Average & Peak Intake
        osmo_row2 = QHBoxLayout()
        osmo_row2.setSpacing(10)

        tile_avg = QFrame()
        tile_avg.setStyleSheet(f"background-color: {TOKENS.BG_INPUT}; border: 1px solid {TOKENS.BORDER_DEFAULT}; border-radius: {TOKENS.RADIUS_MD}; padding: 8px 12px;")
        avg_vbox = QVBoxLayout(tile_avg)
        avg_vbox.setSpacing(2)
        lbl_avg_t = QLabel("WEEKLY AVG")
        lbl_avg_t.setStyleSheet(f"color: {TOKENS.TEXT_MUTED}; font-size: 10px; font-weight: 700; font-family: 'Cascadia Code', monospace;")
        self.lbl_metric_avg = QLabel("1.8 L")
        self.lbl_metric_avg.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 800; font-family: 'Cascadia Code', monospace;")
        avg_vbox.addWidget(lbl_avg_t)
        avg_vbox.addWidget(self.lbl_metric_avg)
        osmo_row2.addWidget(tile_avg)

        tile_peak = QFrame()
        tile_peak.setStyleSheet(f"background-color: {TOKENS.BG_INPUT}; border: 1px solid {TOKENS.BORDER_DEFAULT}; border-radius: {TOKENS.RADIUS_MD}; padding: 8px 12px;")
        peak_vbox = QVBoxLayout(tile_peak)
        peak_vbox.setSpacing(2)
        lbl_peak_t = QLabel("PEAK INTAKE")
        lbl_peak_t.setStyleSheet(f"color: {TOKENS.TEXT_MUTED}; font-size: 10px; font-weight: 700; font-family: 'Cascadia Code', monospace;")
        self.lbl_metric_peak = QLabel("2:15 PM")
        self.lbl_metric_peak.setStyleSheet(f"color: {TOKENS.ACCENT_GOLD}; font-size: 16px; font-weight: 800; font-family: 'Cascadia Code', monospace;")
        peak_vbox.addWidget(lbl_peak_t)
        peak_vbox.addWidget(self.lbl_metric_peak)
        osmo_row2.addWidget(tile_peak)

        card_matrix.content_layout.addLayout(osmo_row2)
        right_col.addWidget(card_matrix)

        # Card 3: LAB PARAMETERS & COMPANION CONTROLS
        card_params = GlassCard("LAB PARAMETERS & QUICK CONTROLS", "Fast protocol calibration & companion state")
        params_layout = QVBoxLayout()
        params_layout.setSpacing(10)

        # 1. Parameter rows
        row_goal = QHBoxLayout()
        lbl_g = QLabel("Daily Target (ml):")
        lbl_g.setStyleSheet(f"color: {TOKENS.TEXT_SECONDARY}; font-size: 11.5px; font-weight: 600;")
        self.quick_spin_goal = QSpinBox()
        self.quick_spin_goal.setRange(500, 5000)
        self.quick_spin_goal.setSingleStep(250)
        self.quick_spin_goal.setValue(2000)
        self.quick_spin_goal.setSuffix(" ml")
        self.quick_spin_goal.valueChanged.connect(self._on_quick_goal_changed)
        row_goal.addWidget(lbl_g)
        row_goal.addStretch()
        row_goal.addWidget(self.quick_spin_goal)
        params_layout.addLayout(row_goal)

        row_fx = QHBoxLayout()
        self.quick_chk_sound = QCheckBox("Acoustic Audio FX")
        self.quick_chk_sound.setChecked(True)
        self.quick_chk_sound.toggled.connect(self._on_quick_sound_changed)
        row_fx.addWidget(self.quick_chk_sound)
        row_fx.addStretch()

        self.btn_visibility_toggle = QPushButton("👁️ Hide Companion")
        self.btn_visibility_toggle.setProperty("class", "secondaryBtn")
        self.btn_visibility_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_visibility_toggle.clicked.connect(self._on_toggle_visibility_clicked)
        row_fx.addWidget(self.btn_visibility_toggle)
        params_layout.addLayout(row_fx)

        card_params.content_layout.addLayout(params_layout)
        right_col.addWidget(card_params)

        right_col.addStretch()
        cols_layout.addLayout(right_col, stretch=1)

        layout.addLayout(cols_layout)

        # Bottom Full-Width Streak Tracker Card (Maintains full test compatibility & flame celebration)
        self.streak_card = StreakCardWidget()
        layout.addWidget(self.streak_card)

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
            ("Version:", f"{VERSION} (Spider-Sense Edition)"),
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

    def _on_quick_goal_changed(self, val: int):
        self.settings.daily_hydration_goal_ml = val
        if hasattr(self, "spin_daily_goal"):
            self.spin_daily_goal.setValue(val)
        self.config_manager.save()
        self.reservoir_widget.set_values(self.settings.today_intake_ml, val)
        if hasattr(self, "thread_matrix"):
            self.thread_matrix.update_matrix(self.settings.daily_history, self.settings.today_intake_ml, val)
        self.settingsChanged.emit()

    def _on_quick_interval_changed(self, text: str):
        try:
            mins = int(text.split()[0])
            self.settings.reminder_interval_minutes = mins
            self.config_manager.save()
            self.engine.reset_schedule()
            self.settingsChanged.emit()
        except Exception:
            pass

    def _on_quick_sound_changed(self, enabled: bool):
        self.settings.sound_effects_enabled = enabled
        if hasattr(self, "chk_sound"):
            self.chk_sound.setChecked(enabled)
        self.config_manager.save()
        self.settingsChanged.emit()

    def _on_cooldown_tick(self, rem_secs: int):
        if not hasattr(self, "btn_hero_drink"):
            return
        cooldown_active = (rem_secs > 0)
        cooldown_text = ""
        if rem_secs > 0:
            mins, secs = divmod(rem_secs, 60)
            cooldown_text = f"⏳ Next log in {mins:02d}:{secs:02d}"
            self.btn_hero_drink.setEnabled(False)
            self.btn_hero_drink.setText(cooldown_text)
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

        self._send_js_state({
            "cooldown_active": cooldown_active,
            "cooldown_text": cooldown_text
        })

    def _on_streak_updated(self, info: StreakInfo):
        if hasattr(self, "streak_card"):
            self.streak_card.update_info(info)
        if hasattr(self, "thread_matrix"):
            self.thread_matrix.update_matrix(
                self.settings.daily_history,
                info.today_intake_ml,
                info.daily_goal_ml
            )
        self._push_full_state_to_web()

    def _on_goal_celebrated(self, msg: str):
        if hasattr(self, "streak_card"):
            self.streak_card.trigger_celebration(msg)
        self._send_js_state({"note_message": msg})

    def _on_quick_dose_clicked(self, ml: int):
        self._select_amount(ml)
        self._quick_log_water(ml, is_manual=True)

    def _on_reset_today_clicked(self):
        reply = QMessageBox.question(
            self,
            "Reset Today's Intake?",
            "Are you sure you want to reset today's logged water to 0 ml?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.today_intake_ml = 0
            self.config_manager.save()
            info = self.engine.get_streak_info()
            if hasattr(self, "streak_card"):
                self.streak_card.update_info(info)
            if hasattr(self, "thread_matrix"):
                self.thread_matrix.update_matrix(
                    self.settings.daily_history, 0, self.settings.daily_hydration_goal_ml
                )
            self.reservoir_widget.set_values(0, self.settings.daily_hydration_goal_ml)
            self.status_save_label.setText("Today's intake was reset to 0 ml.")

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
            if hasattr(self, "lbl_next_time"):
                self.lbl_next_time.setText(f"Resumes at: {formatted_end}")
            self.lbl_countdown.setToolTip(
                f"Quiet Hours are active ({self.settings.quiet_hours_start} to {self.settings.quiet_hours_end}).\n"
                f"Hydration reminders will automatically resume at {formatted_end} (in {hrs}h {mins:02d}m {secs:02d}s)."
            )
            self._send_js_state({"next_time": self.lbl_countdown.text()})
            return

        if hasattr(self, "card_timer"):
            self.card_timer.lbl_subtitle.setText("Countdown to hydration prompt")

        if seconds < 0 or self.settings.reminders_paused or not self.settings.reminders_enabled:
            self.lbl_countdown.setText("Paused")
            self.lbl_countdown.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {TOKENS.STATUS_WARNING};")
            self.lbl_countdown.setToolTip("Reminders are currently paused.")
            if hasattr(self, "lbl_next_time"):
                self.lbl_next_time.setText("Protocol status: PAUSED")
        elif seconds == 0:
            self.lbl_countdown.setText("DUE NOW!")
            self.lbl_countdown.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {TOKENS.ACCENT_MINT};")
            self.lbl_countdown.setToolTip("Hydration reminder is due right now!")
            if hasattr(self, "lbl_next_time"):
                self.lbl_next_time.setText("Prompt triggering now!")
        else:
            hrs, rem = divmod(seconds, 3600)
            mins, secs = divmod(rem, 60)
            if hrs > 0:
                self.lbl_countdown.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")
            else:
                self.lbl_countdown.setText(f"{mins:02d}:{secs:02d}")
            self.lbl_countdown.setStyleSheet(f"font-size: 28px; font-weight: 900; color: {TOKENS.ACCENT_AQUA};")
            self.lbl_countdown.setToolTip(
                f"Next reminder in {hrs}h {mins}m {secs}s" if hrs > 0 else f"Next reminder in {mins}m {secs}s"
            )
            if hasattr(self, "lbl_next_time"):
                target_dt = datetime.now() + timedelta(seconds=seconds)
                time_str = target_dt.strftime("%I:%M %p").lstrip("0")
                self.lbl_next_time.setText(f"Scheduled Trigger: {time_str}")
        self._send_js_state({"next_time": self.lbl_countdown.text()})

    def _on_state_changed(self, state: ReminderState):
        if state == ReminderState.PAUSED:
            self.lbl_companion_status.setText("⏸️ PAUSED")
            self.lbl_companion_status.setStyleSheet(f"""
                background-color: #242018;
                color: {TOKENS.STATUS_WARNING};
                border: 1px solid #59421A;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 800;
                font-family: 'Cascadia Code', monospace;
            """)
            self.btn_pause_toggle.setText("▶️ Resume Reminders")
            if hasattr(self, "lbl_next_time"):
                self.lbl_next_time.setText("Protocol status: PAUSED")
        elif state == ReminderState.QUIET_HOURS:
            self.lbl_companion_status.setText("🌙 QUIET HOURS")
            self.lbl_companion_status.setStyleSheet(f"""
                background-color: #1A1D24;
                color: {TOKENS.TEXT_MUTED};
                border: 1px solid {TOKENS.BORDER_DEFAULT};
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 800;
                font-family: 'Cascadia Code', monospace;
            """)
            rem_secs = self.engine.get_seconds_remaining()
            if rem_secs > 0:
                self._on_timer_tick(rem_secs)
        elif state == ReminderState.WAITING_FOR_RESPONSE:
            self.lbl_companion_status.setText("💧 PROMPT ACTIVE")
            self.lbl_companion_status.setStyleSheet(f"""
                background-color: #112028;
                color: {TOKENS.ACCENT_AQUA};
                border: 1px solid #1E3D48;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 800;
                font-family: 'Cascadia Code', monospace;
            """)
        else:
            self.lbl_companion_status.setText("🟢 ACTIVE MONITORING")
            self.lbl_companion_status.setStyleSheet(f"""
                background-color: #121E17;
                color: {TOKENS.STATUS_SUCCESS};
                border: 1px solid #1E3D2B;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 800;
                font-family: 'Cascadia Code', monospace;
            """)
            self.btn_pause_toggle.setText("⏸️ Pause Reminders")
            if hasattr(self, "card_timer"):
                self.card_timer.lbl_subtitle.setText("Countdown to hydration prompt")
        self._push_full_state_to_web()

    def _on_stats_updated(self, count: int, ml: int):
        self.lbl_reminders_completed.setText(f"Completed Reminders Today: {count}")
        goal = self.settings.daily_hydration_goal_ml
        pct = min(100, int((ml / goal) * 100)) if goal > 0 else 0
        self.lbl_hydro_stats.setText(f"{ml} / {goal} ml ({pct}%)")
        self.progress_hydro.setValue(pct)
        # Update animated fluid reservoir
        self.reservoir_widget.set_values(ml, goal)
        if hasattr(self, "thread_matrix"):
            self.thread_matrix.update_matrix(
                self.settings.daily_history,
                ml,
                goal
            )
        self._push_full_state_to_web()

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
        if hasattr(self, "quick_spin_goal"):
            self.quick_spin_goal.blockSignals(True)
            self.quick_spin_goal.setValue(s.daily_hydration_goal_ml)
            self.quick_spin_goal.blockSignals(False)
        if hasattr(self, "quick_combo_interval"):
            self.quick_combo_interval.blockSignals(True)
            self.quick_combo_interval.setCurrentText(f"{s.reminder_interval_minutes} Mins")
            self.quick_combo_interval.blockSignals(False)
        if hasattr(self, "quick_chk_sound"):
            self.quick_chk_sound.blockSignals(True)
            self.quick_chk_sound.setChecked(s.sound_effects_enabled)
            self.quick_chk_sound.blockSignals(False)

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

    def _send_js_state(self, payload: dict):
        if hasattr(self, "web_view") and self.web_view.page():
            js = f"if(window.updateState) {{ window.updateState({json.dumps(payload)}); }}"
            self.web_view.page().runJavaScript(js)

    def _push_full_state_to_web(self):
        if not hasattr(self, "web_view"):
            return
        total = self.settings.today_intake_ml
        goal = self.settings.daily_hydration_goal_ml
        rem = self.settings.today_reminders_completed

        week = [0.0] * 7
        today = datetime.now()
        today_weekday = today.weekday()
        if goal > 0:
            week[today_weekday] = min(1.0, round(total / goal, 2))

        history_map = {item.get("date"): item for item in self.settings.daily_history}
        for i in range(7):
            d = today - timedelta(days=(today_weekday - i))
            d_str = d.strftime("%Y-%m-%d")
            if d_str in history_map:
                h_goal = history_map[d_str].get("goal_ml", goal) or goal
                h_intake = history_map[d_str].get("intake_ml", 0)
                week[i] = min(1.0, round(h_intake / h_goal, 2)) if h_goal > 0 else 0.0

        entries = []
        if total > 0:
            entries.append({"t": "Today", "ml": total})

        cooldown_rem = self.engine.streak_tracker.get_cooldown_remaining()
        cooldown_active = (cooldown_rem > 0)
        cooldown_text = ""
        if cooldown_active:
            m, s = divmod(cooldown_rem, 60)
            cooldown_text = f"⏳ Next log in {m:02d}:{s:02d}"

        status_text = f"Logged {total} / {goal} ml today"
        sys_state = "Active" if not self.settings.reminders_paused and self.engine.state != ReminderState.QUIET_HOURS else ("Sleeping" if self.engine.state == ReminderState.QUIET_HOURS else "Paused")

        settings_payload = {
            "companion_name": self.settings.companion_name,
            "user_name": self.settings.user_name,
            "daily_goal": self.settings.daily_hydration_goal_ml,
            "launch_at_startup": self.settings.launch_at_startup,
            "start_minimized": self.settings.start_minimized,
            "always_on_top": self.settings.always_on_top,
            "interval_mins": self.settings.reminder_interval_minutes,
            "quiet_hours_enabled": self.settings.quiet_hours_enabled,
            "quiet_hours_start": self.settings.quiet_hours_start,
            "quiet_hours_end": self.settings.quiet_hours_end,
            "sound_effects_enabled": self.settings.sound_effects_enabled,
            "corner_position": self.settings.corner_position,
            "click_through_enabled": self.settings.click_through_enabled,
            "animation_enabled": self.settings.animation_enabled,
            "performance_mode": self.settings.performance_mode,
        }

        weekly_avg = f"{total} ml"
        if self.settings.daily_history:
            total_hist = sum(h.get("intake_ml", 0) for h in self.settings.daily_history) + total
            count_days = len(self.settings.daily_history) + 1
            weekly_avg = f"{int(total_hist / count_days)} ml"

        peak_intake = f"{max(total, max([h.get('intake_ml', 0) for h in self.settings.daily_history] or [0]))} ml"

        payload = {
            "goal": goal,
            "total": total,
            "reminders_today": rem,
            "week": week,
            "entries": entries,
            "status_text": status_text,
            "sys_state": sys_state,
            "cooldown_active": cooldown_active,
            "cooldown_text": cooldown_text,
            "spider_sense_active": not self.settings.reminders_paused,
            "weekly_avg": weekly_avg,
            "peak_intake": peak_intake,
            "settings": settings_payload
        }
        if hasattr(self, "lbl_countdown"):
            payload["next_time"] = self.lbl_countdown.text()
        self._send_js_state(payload)

    def _handle_web_action(self, action: str, payload_json: str):
        try:
            data = json.loads(payload_json) if payload_json else {}
        except Exception:
            data = {}

        if action == "web_ready":
            self._push_full_state_to_web()
        elif action == "log_water":
            amount = int(data.get("amount", self._selected_amount))
            self._select_amount(amount)
            self._quick_log_water(amount, is_manual=True)
            self._push_full_state_to_web()
        elif action == "reset_today":
            self._on_reset_today_clicked()
            self._push_full_state_to_web()
        elif action == "toggle_spider_sense":
            self._on_toggle_pause_clicked()
            self._push_full_state_to_web()
        elif action == "trigger_reminder_now":
            self._on_remind_now_clicked()
        elif action == "save_settings":
            self._save_settings_from_web(data)
        elif action == "reset_defaults":
            self._reset_defaults()
            self._push_full_state_to_web()
        elif action == "restore_backup":
            self._restore_backup()
            self._push_full_state_to_web()
        elif action == "test_animation":
            anim_type = data if isinstance(data, str) else data.get("type", "happy")
            self.testAnimationRequested.emit(anim_type)

    def _save_settings_from_web(self, data: dict):
        if "companion_name" in data and hasattr(self, "edit_comp_name"):
            self.edit_comp_name.setText(str(data["companion_name"]))
        if "user_name" in data and hasattr(self, "edit_user_name"):
            self.edit_user_name.setText(str(data["user_name"]))
        if "daily_goal" in data and hasattr(self, "spin_daily_goal"):
            self.spin_daily_goal.setValue(int(data["daily_goal"]))
        if "launch_at_startup" in data and hasattr(self, "chk_startup"):
            self.chk_startup.setChecked(bool(data["launch_at_startup"]))
        if "start_minimized" in data and hasattr(self, "chk_start_minimized"):
            self.chk_start_minimized.setChecked(bool(data["start_minimized"]))
        if "always_on_top" in data and hasattr(self, "chk_always_on_top"):
            self.chk_always_on_top.setChecked(bool(data["always_on_top"]))
        if "interval_mins" in data and hasattr(self, "combo_interval"):
            int_val = int(data["interval_mins"])
            idx = self.combo_interval.findText(f"{int_val} min")
            if idx >= 0:
                self.combo_interval.setCurrentIndex(idx)
            else:
                self.combo_interval.setCurrentText("Custom")
                if hasattr(self, "spin_interval_custom"):
                    self.spin_interval_custom.setValue(int_val)
        if "quiet_hours_enabled" in data and hasattr(self, "chk_quiet"):
            self.chk_quiet.setChecked(bool(data["quiet_hours_enabled"]))
        if "quiet_hours_start" in data and hasattr(self, "time_q_start"):
            self.time_q_start.setTime(QTime.fromString(str(data["quiet_hours_start"]), "HH:mm"))
        if "quiet_hours_end" in data and hasattr(self, "time_q_end"):
            self.time_q_end.setTime(QTime.fromString(str(data["quiet_hours_end"]), "HH:mm"))
        if "sound_effects_enabled" in data and hasattr(self, "chk_sound"):
            self.chk_sound.setChecked(bool(data["sound_effects_enabled"]))
        if "corner_position" in data and hasattr(self, "combo_corner"):
            self.combo_corner.setCurrentText(str(data["corner_position"]))
        if "click_through_enabled" in data and hasattr(self, "chk_click_through"):
            self.chk_click_through.setChecked(bool(data["click_through_enabled"]))
        if "animation_enabled" in data and hasattr(self, "chk_animation"):
            self.chk_animation.setChecked(bool(data["animation_enabled"]))
        if "performance_mode" in data and hasattr(self, "chk_perf_mode"):
            self.chk_perf_mode.setChecked(bool(data["performance_mode"]))

        self.save_and_apply()

    def toggle_view_mode(self):
        """Toggle between Neo-Brutalist Pop-Art Graphic View and Native Aquatic View."""
        if hasattr(self, "web_view") and hasattr(self, "_native_container"):
            is_web = self.web_view.isVisible()
            self.web_view.setVisible(not is_web)
            self._native_container.setVisible(is_web)
