import sys
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
from PySide6.QtGui import QColor, QFont, QCursor, QGuiApplication

from src.character import SpideyWidget
from src.theme import TOKENS


class SpideyWaterBuddyPopup(QWidget):
    """
    Transparent, cozy desktop popup featuring Spider-Man hanging from the top screen corner by a web.
    Features:
      - Transparent window with web anchored to desktop corner
      - Frameless & always-on-top
      - Spider-Man responds to mouse hover and elastic drag
      - Cozy speech card with YES / NO buttons and 5/10/15m snooze
    """

    waterDrank = Signal()
    snoozeRequested = Signal(int)
    dismissed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._drag_start_pos = None
        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.setSingleShot(True)
        self._auto_close_timer.timeout.connect(self.close)

        self._init_ui()
        self._position_at_desktop_corner()

    def _init_ui(self):
        """Builds the cozy Spidey hanging popup."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 10, 10)
        main_layout.setSpacing(0)

        # 1. Spider-Man hanging widget (Anchors directly to the top of the window)
        spidey_box = QHBoxLayout()
        spidey_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spidey = SpideyWidget(width=180, height=240)
        # Connect mouse reactions to dialogue updates
        self.spidey.hoverEntered.connect(self._on_spidey_hover_enter)
        self.spidey.hoverLeft.connect(self._on_spidey_hover_leave)
        self.spidey.clicked.connect(self._on_spidey_clicked)
        spidey_box.addWidget(self.spidey)
        main_layout.addLayout(spidey_box)

        # 2. Cozy Speech & Action Card (Hangs right below Spidey)
        self.card = QFrame()
        self.card.setObjectName("spideyCard")
        self.card.setStyleSheet("""
            #spideyCard {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(26, 20, 36, 0.94),
                    stop: 1 rgba(15, 12, 24, 0.96)
                );
                border: 1.5px solid #f43f5e;
                border-radius: 18px;
            }
            QLabel {
                color: #f8fafc;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QPushButton {
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-weight: 700;
                border-radius: 10px;
                padding: 8px 12px;
            }
        """)

        # Soft drop shadow for cozy depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 6)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(16, 12, 16, 16)
        card_layout.setSpacing(10)

        # Header Bar: Spider-Man badge and Close button
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        badge = QLabel("🕸️ SPIDER-MAN WATER BUDDY")
        badge.setStyleSheet(f"color: {TOKENS.ACCENT_RED_HOVER}; font-size: 10.5px; font-weight: 800; letter-spacing: 1px;")
        header.addWidget(badge)
        header.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(22, 22)
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.setToolTip("Dismiss")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: none;
                font-size: 12px;
                padding: 0;
            }
            QPushButton:hover {
                color: #f43f5e;
                background-color: rgba(244, 63, 94, 0.2);
                border-radius: 11px;
            }
        """)
        self.btn_close.clicked.connect(self._on_dismiss)
        header.addWidget(self.btn_close)
        card_layout.addLayout(header)

        # Dialogue Bubble
        self.default_message = "Hey web-slinger! Take a cozy sip of water ☕💧"
        self.dialogue_label = QLabel(self.default_message)
        self.dialogue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dialogue_label.setWordWrap(True)
        self.dialogue_label.setStyleSheet("""
            color: #f1f5f9;
            font-size: 12.5px;
            font-weight: 600;
            padding: 8px 10px;
            background-color: rgba(255, 255, 255, 0.07);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        """)
        card_layout.addWidget(self.dialogue_label)

        # Primary Action Buttons (YES / NO)
        self.action_widget = QWidget()
        action_layout = QHBoxLayout(self.action_widget)
        action_layout.setContentsMargins(0, 2, 0, 0)
        action_layout.setSpacing(10)

        self.btn_yes = QPushButton("💧 YES, DRANK!")
        self.btn_yes.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_yes.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #059669, stop: 1 #047857
                );
                color: #ffffff;
                font-size: 11.5px;
                border: 1px solid #10b981;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #10b981, stop: 1 #059669
                );
                border-color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #064e3b;
            }
        """)
        self.btn_yes.clicked.connect(self._on_yes_clicked)
        action_layout.addWidget(self.btn_yes)

        self.btn_no = QPushButton("⏳ NOT YET")
        self.btn_no.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_no.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #33202e, stop: 1 #241421
                );
                color: #fca5a5;
                font-size: 11.5px;
                border: 1px solid #e11d48;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #e11d48, stop: 1 #9f1239
                );
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #881337;
            }
        """)
        self.btn_no.clicked.connect(self._on_no_clicked)
        action_layout.addWidget(self.btn_no)

        card_layout.addWidget(self.action_widget)

        # Snooze Choice Container (Revealed on NO)
        self.snooze_widget = QWidget()
        self.snooze_widget.setVisible(False)
        snooze_layout = QVBoxLayout(self.snooze_widget)
        snooze_layout.setContentsMargins(0, 0, 0, 0)
        snooze_layout.setSpacing(6)

        snooze_label = QLabel("Remind me in:")
        snooze_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        snooze_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        snooze_layout.addWidget(snooze_label)

        snooze_btn_layout = QHBoxLayout()
        snooze_btn_layout.setSpacing(8)

        self.snooze_buttons = []
        for minutes in (5, 10, 15):
            btn = QPushButton(f"{minutes} min")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(225, 29, 72, 0.12);
                    color: #fb7185;
                    font-size: 11px;
                    border: 1px solid rgba(244, 63, 94, 0.35);
                    padding: 6px 8px;
                }
                QPushButton:hover {
                    background-color: #e11d48;
                    color: #ffffff;
                    border-color: #f43f5e;
                }
                QPushButton:pressed {
                    background-color: #be123c;
                }
            """)
            btn.clicked.connect(lambda chk=False, m=minutes: self._on_snooze_selected(m))
            snooze_btn_layout.addWidget(btn)
            self.snooze_buttons.append(btn)

        snooze_layout.addLayout(snooze_btn_layout)
        card_layout.addWidget(self.snooze_widget)

        main_layout.addWidget(self.card)
        self.setFixedWidth(270)

    def _position_at_desktop_corner(self):
        """Positions Spider-Man hanging directly from the top-right desktop corner."""
        screen = QGuiApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            # Flush with top (y=0) so the web emerges from monitor frame
            x = geom.right() - self.width() - 36
            y = geom.top()
            self.move(x, y)

    # Mouse reaction callbacks from SpideyWidget
    def _on_spidey_hover_enter(self):
        if self.spidey._base_state == SpideyWidget.STATE_IDLE and self.action_widget.isVisible():
            self.dialogue_label.setText("Spider-sense says: Hey there! Ready to drink? 🕸️")

    def _on_spidey_hover_leave(self):
        if self.spidey._base_state == SpideyWidget.STATE_IDLE and self.action_widget.isVisible():
            self.dialogue_label.setText(self.default_message)

    def _on_spidey_clicked(self):
        if self.spidey._base_state == SpideyWidget.STATE_IDLE and self.action_widget.isVisible():
            self.dialogue_label.setText("Thwip! Don't forget your water, hero! 💧")

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
        self._drag_start_pos = None

    # Interaction responses
    def _on_yes_clicked(self):
        """User drank water: Spidey shoots web celebration and gives thumbs up!"""
        self.spidey.set_state(SpideyWidget.STATE_HAPPY)
        self.dialogue_label.setText("Thwip! Super hydrated! Spider-sense at 100%! 🌟")
        self.dialogue_label.setStyleSheet("""
            color: #34d399;
            font-size: 12.5px;
            font-weight: 700;
            padding: 8px 10px;
            background-color: rgba(16, 185, 129, 0.18);
            border-radius: 10px;
            border: 1px solid #10b981;
        """)

        self.btn_yes.setEnabled(False)
        self.btn_no.setEnabled(False)
        self.waterDrank.emit()

        # Auto-dismiss celebration after 2 seconds
        self._auto_close_timer.start(2000)

    def _on_no_clicked(self):
        """User declined: Spidey slumps with dehydration sweat and offers snooze."""
        self.spidey.set_state(SpideyWidget.STATE_DISAPPOINTED)
        self.dialogue_label.setText("Even superheroes need H2O... Snooze for a bit? 🕷️")
        self.dialogue_label.setStyleSheet("""
            color: #f87171;
            font-size: 12px;
            font-weight: 600;
            padding: 8px 10px;
            background-color: rgba(244, 63, 94, 0.16);
            border-radius: 10px;
            border: 1px solid rgba(244, 63, 94, 0.3);
        """)

        self.action_widget.setVisible(False)
        self.snooze_widget.setVisible(True)
        self.adjustSize()

    def _on_snooze_selected(self, minutes: int):
        """User selected a snooze interval."""
        self.dialogue_label.setText(f"Snoozed for {minutes} min! Web-slinging back soon. ⏱️")
        self.dialogue_label.setStyleSheet("""
            color: #fbbf24;
            font-size: 12px;
            font-weight: 600;
            padding: 8px 10px;
            background-color: rgba(251, 191, 36, 0.16);
            border-radius: 10px;
            border: 1px solid rgba(251, 191, 36, 0.3);
        """)
        for btn in self.snooze_buttons:
            btn.setEnabled(False)

        self.snoozeRequested.emit(minutes)
        self._auto_close_timer.start(1400)

    def _on_dismiss(self):
        self.dismissed.emit()
        self.close()

    def reset_popup(self):
        """Resets popup for reuse."""
        self._auto_close_timer.stop()
        self.spidey.set_state(SpideyWidget.STATE_IDLE)
        self.dialogue_label.setText(self.default_message)
        self.dialogue_label.setStyleSheet("""
            color: #f1f5f9;
            font-size: 12.5px;
            font-weight: 600;
            padding: 8px 10px;
            background-color: rgba(255, 255, 255, 0.07);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        """)
        self.btn_yes.setEnabled(True)
        self.btn_no.setEnabled(True)
        self.action_widget.setVisible(True)
        self.snooze_widget.setVisible(False)
        for btn in self.snooze_buttons:
            btn.setEnabled(True)
        self.adjustSize()


# Backward compatibility alias
WaterBuddyPopup = SpideyWaterBuddyPopup
