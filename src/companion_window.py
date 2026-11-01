"""
Desktop Companion Overlay Window for Spider-Man Water Buddy.
Provides frameless transparency, desktop corner web-anchoring, mouse tracking,
hardware click-through toggling, and multi-monitor display compatibility.
"""
import sys
import ctypes
import logging
from typing import Optional

from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QApplication,
    QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QColor, QFont, QCursor, QGuiApplication, QScreen

from src.character import SpideyWidget
from src.config import ConfigManager, AppSettings
from src.theme import get_companion_card_qss, TOKENS

logger = logging.getLogger("SpiderManWaterBuddy.CompanionWindow")


class CompanionWindow(QWidget):
    """
    Transparent desktop companion overlay displaying Spider-Man hanging by a web.
    """

    waterDrank = Signal()
    snoozeRequested = Signal(int)
    declined = Signal()
    dismissed = Signal()
    openDashboardRequested = Signal()

    def __init__(self, config_manager: Optional[ConfigManager] = None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager or ConfigManager()
        self.settings = self.config_manager.settings

        # Window Flags: Frameless, Always on Top, Tool Window (does not steal focus or show in Alt-Tab)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)

        self._drag_start_pos: Optional[QPoint] = None
        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.setSingleShot(True)
        self._auto_close_timer.timeout.connect(self._on_auto_close)

        self._in_reminder_mode = False
        self._previous_click_through = False

        self._init_ui()
        self._setup_screen_monitoring()
        self.spidey.set_character_scale(self.settings.character_scale)
        self.spidey.set_animation_enabled(self.settings.animation_enabled)
        self.spidey.set_performance_mode(self.settings.performance_mode)
        self.reposition()
        self.apply_click_through(self.settings.click_through_enabled)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 0, 5, 10)
        main_layout.setSpacing(0)

        # 1. Spider-Man Hanging Character Widget (Generous width to prevent any clipping on wide drag/swing)
        spidey_box = QHBoxLayout()
        spidey_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spidey = SpideyWidget(parent=self, width=460, height=420)
        self.spidey.hoverEntered.connect(self._on_spidey_hover_enter)
        self.spidey.hoverLeft.connect(self._on_spidey_hover_leave)
        self.spidey.clicked.connect(self._on_spidey_clicked)
        spidey_box.addWidget(self.spidey)
        main_layout.addLayout(spidey_box)

        # 2. Speech & Action Card (Matching Pop-Art Spider-Man Comic theme)
        self.card = QFrame()
        self.card.setObjectName("spideyCard")
        self.card.setFixedWidth(320)
        self.card.setStyleSheet(get_companion_card_qss())

        # Drop shadow for clean comic pop
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(14)
        shadow.setColor(QColor(20, 26, 58, 140))
        shadow.setOffset(3, 4)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(16, 12, 16, 16)
        card_layout.setSpacing(10)

        # Header Bar (Customized Companion Name in Spider-Man Crimson)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        badge_text = f"🕷️ {self.settings.companion_name.upper()}"
        self.badge = QLabel(badge_text)
        self.badge.setStyleSheet("color: #d6483f; font-size: 12px; font-weight: 900; letter-spacing: 0.8px;")
        header.addWidget(self.badge)
        header.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(22, 22)
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.setToolTip("Dismiss")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #141a3a;
                border: 1.5px solid #141a3a;
                border-radius: 11px;
                font-size: 11px;
                font-weight: 800;
                padding: 0;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: #d6483f;
                border-color: #d6483f;
            }
        """)
        self.btn_close.clicked.connect(self._on_dismiss_clicked)
        header.addWidget(self.btn_close)
        card_layout.addLayout(header)

        # Dialogue Bubble (White well with crisp ink text, ample padding to prevent clipping)
        self.dialogue_label = QLabel(self._get_personalized_greeting())
        self.dialogue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dialogue_label.setWordWrap(True)
        self.dialogue_label.setStyleSheet("""
            color: #141a3a;
            font-size: 12.5px;
            font-weight: 700;
            line-height: 1.35;
            padding: 10px 14px;
            min-height: 44px;
            background-color: #f7f8ff;
            border-radius: 10px;
            border: 2px solid #141a3a;
        """)
        card_layout.addWidget(self.dialogue_label)

        # Action Buttons (Spider-Man Crimson & Blue styling with thick ink lines)
        self.action_widget = QWidget()
        action_layout = QHBoxLayout(self.action_widget)
        action_layout.setContentsMargins(0, 2, 0, 0)
        action_layout.setSpacing(10)

        self.btn_yes = QPushButton("YES, DRANK! 💧")
        self.btn_yes.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_yes.setStyleSheet("""
            QPushButton {
                background-color: #d6483f;
                color: #ffffff;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.5px;
                border: 2px solid #141a3a;
                border-radius: 10px;
                padding: 9px 14px;
            }
            QPushButton:hover {
                background-color: #b93931;
            }
            QPushButton:pressed {
                background-color: #9c2720;
            }
        """)
        self.btn_yes.clicked.connect(self._on_yes_clicked)
        action_layout.addWidget(self.btn_yes)

        self.btn_no = QPushButton("NOT YET")
        self.btn_no.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_no.setStyleSheet("""
            QPushButton {
                background-color: #2b3e8c;
                color: #ffffff;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.5px;
                border: 2px solid #141a3a;
                border-radius: 10px;
                padding: 9px 14px;
            }
            QPushButton:hover {
                background-color: #1e2e6d;
            }
            QPushButton:pressed {
                background-color: #162252;
            }
        """)
        self.btn_no.clicked.connect(self._on_no_clicked)
        action_layout.addWidget(self.btn_no)

        card_layout.addWidget(self.action_widget)

        # Snooze Container
        self.snooze_widget = QWidget()
        self.snooze_widget.setVisible(False)
        snooze_layout = QVBoxLayout(self.snooze_widget)
        snooze_layout.setContentsMargins(0, 0, 0, 0)
        snooze_layout.setSpacing(6)

        snooze_label = QLabel("Remind me in:")
        snooze_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        snooze_label.setStyleSheet("color: #141a3a; font-size: 11px; font-weight: 800;")
        snooze_layout.addWidget(snooze_label)

        snooze_btn_layout = QHBoxLayout()
        snooze_btn_layout.setSpacing(6)

        self.snooze_buttons = []
        for minutes in (5, 10, 15):
            btn = QPushButton(f"{minutes} min")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #141a3a;
                    font-size: 11px;
                    font-weight: 800;
                    border: 2px solid #141a3a;
                    border-radius: 8px;
                    padding: 6px 10px;
                }
                QPushButton:hover {
                    background-color: #2b3e8c;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda chk=False, m=minutes: self._on_snooze_selected(m))
            snooze_btn_layout.addWidget(btn)
            self.snooze_buttons.append(btn)

        snooze_layout.addLayout(snooze_btn_layout)
        card_layout.addWidget(self.snooze_widget)

        main_layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignCenter)
        scale = getattr(self.settings, "character_scale", 1.0)
        self.setFixedWidth(int(460 * scale))

    def _get_personalized_greeting(self) -> str:
        text = self.settings.custom_greeting or "Hey, [Name]! Your friendly neighbourhood Spider-Man says it's hydration time!"
        return text.replace("[Name]", self.settings.user_name)

    def _setup_screen_monitoring(self):
        """Monitors multi-display additions, removals, and resolution changes."""
        app = QGuiApplication.instance()
        if app:
            app.screenAdded.connect(self._on_display_changed)
            app.screenRemoved.connect(self._on_display_changed)
            app.primaryScreenChanged.connect(self._on_display_changed)

        screen = QGuiApplication.primaryScreen()
        if screen:
            screen.geometryChanged.connect(self._on_display_changed)

    def _on_display_changed(self, *args):
        logger.info("Display configuration changed. Recalculating placement...")
        self.reposition()

    def _get_base_corner_pos(self) -> tuple[int, int]:
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return 0, 0

        geom = screen.availableGeometry()
        pos = self.settings.corner_position

        w = self.width()
        h = self.sizeHint().height()

        if pos == "top-right":
            x = geom.right() - w - 24
            y = geom.top()
        elif pos == "top-left":
            x = geom.left() + 24
            y = geom.top()
        elif pos == "bottom-right":
            x = geom.right() - w - 24
            y = geom.bottom() - h - 16
        elif pos == "bottom-left":
            x = geom.left() + 24
            y = geom.bottom() - h - 16
        else:
            x = geom.right() - w - 24
            y = geom.top()

        return x, y

    def reposition(self):
        """Places the window at the configured desktop corner with DPI awareness and offset."""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return

        base_x, base_y = self._get_base_corner_pos()
        target_x = base_x + getattr(self.settings, "window_offset_x", 0)
        target_y = base_y + getattr(self.settings, "window_offset_y", 0)

        # Clamp within available screen geometry
        geom = screen.availableGeometry()
        target_x = max(geom.left(), min(geom.right() - self.width(), target_x))
        target_y = max(geom.top(), min(geom.bottom() - self.height(), target_y))

        self.move(target_x, target_y)

    # Windows Click-Through & Focus Management
    def apply_click_through(self, enable: bool):
        """Enables hardware click-through on Windows so clicks pass to background apps."""
        if sys.platform != "win32":
            return

        try:
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            WS_EX_NOACTIVATE = 0x08000000

            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= (WS_EX_LAYERED | WS_EX_NOACTIVATE)
            # Never enable click-through if card is visible, or in reminder mode
            if enable and not self._in_reminder_mode and not self.card.isVisible():
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT)
                logger.info("Click-through ENABLED")
            else:
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style & ~WS_EX_TRANSPARENT)
                logger.info("Click-through DISABLED (Interactive Mode)")
        except Exception as e:
            logger.error(f"Failed to set window click-through: {e}")

    # Mouse reaction handlers
    def _on_spidey_hover_enter(self):
        if self.spidey._base_state == SpideyWidget.STATE_IDLE and self.action_widget.isVisible():
            name = self.settings.user_name
            self.dialogue_label.setText(f"Spider-sense tingles: Hey {name}! Hydration check 🕸️")

    def _on_spidey_hover_leave(self):
        if self.spidey._base_state == SpideyWidget.STATE_IDLE and self.action_widget.isVisible():
            self.dialogue_label.setText(self._get_personalized_greeting())

    def _on_spidey_clicked(self):
        if not self._in_reminder_mode:
            self.card.setVisible(True)
            self.apply_click_through(False)
            self.adjustSize()
            self.openDashboardRequested.emit()
        elif self.spidey._base_state == SpideyWidget.STATE_IDLE and self.action_widget.isVisible():
            self.dialogue_label.setText("Thwip! Keep your hydration superpower active! 💧")

    # Mouse drag window repositioning
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_start_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_start_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._drag_start_pos is not None:
            self._drag_start_pos = None
            base_x, base_y = self._get_base_corner_pos()
            self.settings.window_offset_x = self.x() - base_x
            self.settings.window_offset_y = self.y() - base_y
            self.config_manager.save()
            logger.info(f"Persisted window offset: ({self.settings.window_offset_x}, {self.settings.window_offset_y})")

    # Reminder trigger mode
    def trigger_reminder_mode(self):
        """Enters active reminder interaction mode without stealing keyboard focus."""
        self._in_reminder_mode = True
        self.card.setVisible(True)
        self.apply_click_through(False)
        self.reset_card_ui()
        self.adjustSize()
        self.show()

        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                HWND_TOPMOST = -1
                SWP_NOSIZE = 0x0001
                SWP_NOMOVE = 0x0002
                SWP_NOACTIVATE = 0x0010
                SWP_SHOWWINDOW = 0x0040
                ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
                )
            except Exception as e:
                logger.warning(f"Failed to SetWindowPos without activate: {e}")
                self.raise_()
        else:
            self.raise_()

    @property
    def default_message(self) -> str:
        return self._get_personalized_greeting()

    def reset_popup(self):
        self.reset_card_ui()

    def reset_card_ui(self):
        self._auto_close_timer.stop()
        self.spidey.set_state(SpideyWidget.STATE_IDLE)
        self.dialogue_label.setText(self._get_personalized_greeting())
        self.dialogue_label.setStyleSheet("""
            color: #141a3a;
            font-size: 12.5px;
            font-weight: 700;
            line-height: 1.35;
            padding: 10px 14px;
            min-height: 44px;
            background-color: #f7f8ff;
            border-radius: 10px;
            border: 2px solid #141a3a;
        """)
        self.btn_yes.setEnabled(True)
        self.btn_no.setEnabled(True)
        self.action_widget.setVisible(True)
        self.snooze_widget.setVisible(False)
        for b in self.snooze_buttons:
            b.setEnabled(True)
        self.adjustSize()

    # User action events
    def _on_yes_clicked(self):
        self.spidey.set_state(SpideyWidget.STATE_HAPPY)
        yes_msg = self.settings.message_yes.replace("[Name]", self.settings.user_name)
        self.dialogue_label.setText(yes_msg)
        self.dialogue_label.setStyleSheet("""
            color: #0b6b38;
            font-size: 12.5px;
            font-weight: 800;
            line-height: 1.35;
            padding: 10px 14px;
            min-height: 44px;
            background-color: #eafaf1;
            border-radius: 10px;
            border: 2px solid #141a3a;
        """)
        self.btn_yes.setEnabled(False)
        self.btn_no.setEnabled(False)
        self.waterDrank.emit()
        self._auto_close_timer.start(3200)

    def _on_no_clicked(self):
        self.spidey.set_state(SpideyWidget.STATE_DISAPPOINTED)
        no_msg = self.settings.message_no.replace("[Name]", self.settings.user_name)
        self.dialogue_label.setText(no_msg)
        self.dialogue_label.setStyleSheet("""
            color: #a8201a;
            font-size: 12.5px;
            font-weight: 800;
            line-height: 1.35;
            padding: 10px 14px;
            min-height: 44px;
            background-color: #fdeeee;
            border-radius: 10px;
            border: 2px solid #141a3a;
        """)
        self.action_widget.setVisible(False)
        self.snooze_widget.setVisible(True)
        self.declined.emit()
        self.adjustSize()
        # Fallback: if user doesn't pick a snooze button, automatically auto-close after 15 seconds
        self._auto_close_timer.start(15000)

    def _on_snooze_selected(self, minutes: int):
        snooze_msg = self.settings.message_snooze.replace("{minutes}", str(minutes)).replace("[Name]", self.settings.user_name)
        self.dialogue_label.setText(snooze_msg)
        self.dialogue_label.setStyleSheet("""
            color: #1f3a7a;
            font-size: 12.5px;
            font-weight: 800;
            line-height: 1.35;
            padding: 10px 14px;
            min-height: 44px;
            background-color: #edf2ff;
            border-radius: 10px;
            border: 2px solid #141a3a;
        """)
        for b in self.snooze_buttons:
            b.setEnabled(False)
        self.snoozeRequested.emit(minutes)
        self._auto_close_timer.start(1500)

    def is_in_reminder_mode(self) -> bool:
        """Returns True if the companion is currently in an active reminder interaction."""
        return self._in_reminder_mode

    def dismiss(self):
        """Programmatically dismisses the companion window and cancels auto-close timer (MED-05)."""
        self._auto_close_timer.stop()
        self._in_reminder_mode = False
        self.card.setVisible(False)
        self.apply_click_through(self.settings.click_through_enabled)
        self.reset_card_ui()
        self.dismissed.emit()
        self.hide()

    def _on_auto_close(self):
        self._auto_close_timer.stop()
        self._in_reminder_mode = False
        self.apply_click_through(self.settings.click_through_enabled)
        self.reset_card_ui()
        self.dismissed.emit()
        self.hide()

    def _on_dismiss_clicked(self):
        self.dismiss()


# Backward compatibility alias
WaterBuddyPopup = CompanionWindow
SpideyWaterBuddyPopup = CompanionWindow
