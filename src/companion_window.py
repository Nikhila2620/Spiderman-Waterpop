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

        # 1. Spider-Man Hanging Character Widget
        spidey_box = QHBoxLayout()
        spidey_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spidey = SpideyWidget(parent=self, width=260, height=325)
        self.spidey.hoverEntered.connect(self._on_spidey_hover_enter)
        self.spidey.hoverLeft.connect(self._on_spidey_hover_leave)
        self.spidey.clicked.connect(self._on_spidey_clicked)
        spidey_box.addWidget(self.spidey)
        main_layout.addLayout(spidey_box)

        # 2. Cozy Speech & Action Card
        self.card = QFrame()
        self.card.setObjectName("spideyCard")
        self.card.setStyleSheet(get_companion_card_qss())

        # Drop shadow for soft depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 5)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 10, 14, 14)
        card_layout.setSpacing(8)

        # Header Bar
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        badge_text = f"E.D.I.T.H. // {self.settings.companion_name.upper()} PROTOCOL"
        self.badge = QLabel(badge_text)
        self.badge.setStyleSheet(f"color: #ffffff; font-size: 10px; font-weight: 800; letter-spacing: 1.5px; font-family: 'Cascadia Code', monospace;")
        header.addWidget(self.badge)
        header.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(20, 20)
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.setToolTip("Dismiss")
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TOKENS.TEXT_MUTED};
                border: none;
                font-size: 11px;
                padding: 0;
            }}
            QPushButton:hover {{
                color: #ffffff;
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 10px;
            }}
        """)
        self.btn_close.clicked.connect(self._on_dismiss_clicked)
        header.addWidget(self.btn_close)
        card_layout.addLayout(header)

        # Dialogue Bubble
        self.dialogue_label = QLabel(self._get_personalized_greeting())
        self.dialogue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dialogue_label.setWordWrap(True)
        self.dialogue_label.setStyleSheet(f"""
            color: #ffffff;
            font-size: 12px;
            font-weight: 600;
            padding: 8px 12px;
            background-color: #05070a;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.25);
        """)
        card_layout.addWidget(self.dialogue_label)

        # Action Buttons (YES / NO)
        self.action_widget = QWidget()
        action_layout = QHBoxLayout(self.action_widget)
        action_layout.setContentsMargins(0, 2, 0, 0)
        action_layout.setSpacing(8)

        self.btn_yes = QPushButton("YES, DRANK!")
        self.btn_yes.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_yes.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: #000000;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.5px;
                border: 1px solid #ffffff;
                border-radius: 6px;
                padding: 7px 12px;
            }}
            QPushButton:hover {{
                background-color: #e2e8f0;
            }}
            QPushButton:pressed {{ background-color: #cbd5e1; }}
        """)
        self.btn_yes.clicked.connect(self._on_yes_clicked)
        action_layout.addWidget(self.btn_yes)

        self.btn_no = QPushButton("NOT YET")
        self.btn_no.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_no.setStyleSheet(f"""
            QPushButton {{
                background-color: #05070a;
                color: {TOKENS.TEXT_SECONDARY};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.5px;
                border: 1px solid rgba(255, 255, 255, 0.35);
                border-radius: 6px;
                padding: 7px 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.10);
                color: #ffffff;
                border-color: #ffffff;
            }}
            QPushButton:pressed {{ background-color: #000000; }}
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
        snooze_label.setStyleSheet(f"color: {TOKENS.TEXT_SECONDARY}; font-size: 10.5px; font-weight: 600;")
        snooze_layout.addWidget(snooze_label)

        snooze_btn_layout = QHBoxLayout()
        snooze_btn_layout.setSpacing(6)

        self.snooze_buttons = []
        for minutes in (5, 10, 15):
            btn = QPushButton(f"{minutes} min")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(0, 240, 255, 0.10);
                    color: {TOKENS.ACCENT_AQUA};
                    font-size: 10.5px;
                    font-weight: 700;
                    border: 1px solid rgba(0, 240, 255, 0.35);
                    border-radius: 6px;
                    padding: 5px 8px;
                }}
                QPushButton:hover {{
                    background-color: rgba(0, 240, 255, 0.25);
                    color: #ffffff;
                    border-color: {TOKENS.ACCENT_AQUA};
                }}
            """)
            btn.clicked.connect(lambda chk=False, m=minutes: self._on_snooze_selected(m))
            snooze_btn_layout.addWidget(btn)
            self.snooze_buttons.append(btn)

        snooze_layout.addLayout(snooze_btn_layout)
        card_layout.addWidget(self.snooze_widget)

        main_layout.addWidget(self.card)
        self.setFixedWidth(270)

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
            if enable and not self._in_reminder_mode:
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
        if self.spidey._base_state == SpideyWidget.STATE_IDLE and self.action_widget.isVisible():
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
        self.apply_click_through(False)
        self.reset_card_ui()
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
            color: #f1f5f9;
            font-size: 12px;
            font-weight: 600;
            padding: 6px 8px;
            background-color: rgba(255, 255, 255, 0.07);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.06);
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
        self.dialogue_label.setStyleSheet(f"""
            color: {TOKENS.ACCENT_MINT};
            font-size: 12px;
            font-weight: 800;
            padding: 7px 10px;
            background-color: rgba(0, 230, 153, 0.16);
            border-radius: 8px;
            border: 1px solid {TOKENS.ACCENT_MINT};
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
            color: #f87171;
            font-size: 11.5px;
            font-weight: 600;
            padding: 6px 8px;
            background-color: rgba(244, 63, 94, 0.16);
            border-radius: 8px;
            border: 1px solid rgba(244, 63, 94, 0.3);
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
            color: #fbbf24;
            font-size: 11.5px;
            font-weight: 600;
            padding: 6px 8px;
            background-color: rgba(251, 191, 36, 0.16);
            border-radius: 8px;
            border: 1px solid rgba(251, 191, 36, 0.3);
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
        self.apply_click_through(self.settings.click_through_enabled)
        self.reset_card_ui()
        self.dismissed.emit()
        self.hide()

    def _on_auto_close(self):
        self._auto_close_timer.stop()
        self._in_reminder_mode = False
        self.apply_click_through(self.settings.click_through_enabled)
        self.reset_card_ui()
        self.hide()

    def _on_dismiss_clicked(self):
        self.dismiss()


# Backward compatibility alias
WaterBuddyPopup = CompanionWindow
SpideyWaterBuddyPopup = CompanionWindow
