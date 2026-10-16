"""
Glassmorphic Animated Toggle Switch for Spider-Man Water Buddy.
Implements modern pill toggle button with smooth position animation and aquatic glow.
"""
from PySide6.QtCore import Qt, Property, QPropertyAnimation, QEasingCurve, QRectF, QPointF
from PySide6.QtWidgets import QAbstractButton
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPen, QCursor

from src.theme import TOKENS


class GlassToggleSwitch(QAbstractButton):
    """
    Animated iOS / Fluent style glass toggle switch.
    """

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(46, 26)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Handle position: 0.0 (left/unchecked) to 1.0 (right/checked)
        self._position = 1.0 if checked else 0.0

        self._anim = QPropertyAnimation(self, b"position", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.toggled.connect(self._on_toggled)

    def get_position(self) -> float:
        return self._position

    def set_position(self, pos: float):
        self._position = pos
        self.update()

    position = Property(float, get_position, set_position)

    def _on_toggled(self, checked: bool):
        self._anim.stop()
        self._anim.setStartValue(self._position)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._position = 1.0 if checked else 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        width = self.width()
        height = self.height()
        radius = height / 2.0
        rect = QRectF(0, 0, width, height)

        # 1. Track Background
        if self._position > 0:
            track_grad = QLinearGradient(0, 0, width, 0)
            track_grad.setColorAt(0.0, QColor("#0a84ff"))
            track_grad.setColorAt(1.0, QColor("#00f0ff"))
            # Blend opacity based on position
            alpha = int(220 * self._position)
            track_color = QColor(10, 132, 255, alpha)
        else:
            track_color = QColor(8, 20, 36, 200)

        painter.setBrush(track_color)
        border_pen = QPen(QColor(0, 240, 255, int(60 + 120 * self._position)), 1.5)
        painter.setPen(border_pen)
        painter.drawRoundedRect(rect, radius, radius)

        # 2. Sliding White Glass Thumb
        thumb_margin = 3.0
        thumb_diameter = height - (thumb_margin * 2)
        x_min = thumb_margin
        x_max = width - thumb_margin - thumb_diameter
        current_x = x_min + (x_max - x_min) * self._position

        thumb_rect = QRectF(current_x, thumb_margin, thumb_diameter, thumb_diameter)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(thumb_rect)

        # Thumb Center Dot Indicator
        if self._position > 0.5:
            dot_color = QColor("#0a84ff")
            painter.setBrush(dot_color)
            painter.drawEllipse(thumb_rect.center(), 3.0, 3.0)
