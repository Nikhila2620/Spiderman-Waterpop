"""
Liquid Hydration Reservoir Widget for Spider-Man Water Buddy.
Implements custom QPainter-rendered fluid wave physics with translucent liquid glass aesthetic,
interactive percentage display, and lightweight timer-driven ripple animation.
"""
import math
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import (
    QPainter,
    QPainterPath,
    QColor,
    QLinearGradient,
    QPen,
    QFont,
)

from src.theme import TOKENS


class LiquidReservoirWidget(QWidget):
    """
    Aquatic Liquid Glass Hydration Reservoir.
    Renders realistic oscillating dual-layer fluid waves inside a frosted glass capsule.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 200)

        self._current_ml = 0
        self._goal_ml = 2000

        # Animation state
        self._phase = 0.0
        self._phase_speed = 0.07
        self._wave_amplitude = 6.0  # Wave peak height in px

        # Wave loop timer (30 FPS ~ 33ms)
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._update_wave)

        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

    @property
    def current_ml(self) -> int:
        return self._current_ml

    @property
    def goal_ml(self) -> int:
        return self._goal_ml

    @property
    def percentage(self) -> int:
        if self._goal_ml <= 0:
            return 0
        return int((self._current_ml / self._goal_ml) * 100)

    @property
    def clamped_percentage(self) -> int:
        return min(100, max(0, self.percentage))

    @property
    def is_animating(self) -> bool:
        return self._timer.isActive()

    def set_values(self, current_ml: int, goal_ml: int):
        """Updates current water level and daily goal."""
        self._current_ml = max(0, current_ml)
        self._goal_ml = max(1, goal_ml)
        self.update()

    def start_animation(self):
        if not self._timer.isActive():
            self._timer.start()

    def stop_animation(self):
        if self._timer.isActive():
            self._timer.stop()

    def showEvent(self, event):
        super().showEvent(event)
        self.start_animation()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_animation()

    def _update_wave(self):
        self._phase += self._phase_speed
        if self._phase > math.pi * 200:
            self._phase = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        width = self.width()
        height = self.height()
        rect = QRectF(6, 6, width - 12, height - 12)
        radius = 24.0

        # 1. Background Frosted Glass Capsule
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(clip_path)

        # Base Deep Abyss Background
        bg_grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
        bg_grad.setColorAt(0.0, QColor("#081424"))
        bg_grad.setColorAt(1.0, QColor("#040a12"))
        painter.fillPath(clip_path, bg_grad)

        # 2. Liquid Level Calculation
        fill_ratio = self.clamped_percentage / 100.0
        # Water surface Y coordinate
        water_y = rect.bottom() - (rect.height() * fill_ratio)

        # 3. Render Fluid Waves if fill_ratio > 0
        if fill_ratio > 0:
            # Back Wave (Electric Azure / Deeper Shade)
            back_wave = QPainterPath()
            back_wave.moveTo(rect.left(), rect.bottom())
            step_x = 4
            for x in range(int(rect.left()), int(rect.right()) + step_x, step_x):
                rel_x = x - rect.left()
                y = water_y + math.sin(rel_x * 0.04 + self._phase * 0.8) * (self._wave_amplitude * 0.75)
                back_wave.lineTo(x, y)
            back_wave.lineTo(rect.right(), rect.bottom())
            back_wave.closeSubpath()

            back_grad = QLinearGradient(0, water_y - 10, 0, rect.bottom())
            back_grad.setColorAt(0.0, QColor(10, 132, 255, 140))
            back_grad.setColorAt(1.0, QColor(4, 30, 60, 200))
            painter.fillPath(back_wave, back_grad)

            # Front Wave (Luminous Aqua / Vibrancy)
            front_wave = QPainterPath()
            front_wave.moveTo(rect.left(), rect.bottom())
            for x in range(int(rect.left()), int(rect.right()) + step_x, step_x):
                rel_x = x - rect.left()
                y = water_y + math.sin(rel_x * 0.05 - self._phase) * self._wave_amplitude
                front_wave.lineTo(x, y)
            front_wave.lineTo(rect.right(), rect.bottom())
            front_wave.closeSubpath()

            front_grad = QLinearGradient(0, water_y - 12, 0, rect.bottom())
            front_grad.setColorAt(0.0, QColor(0, 240, 255, 195))
            front_grad.setColorAt(0.4, QColor(10, 132, 255, 160))
            front_grad.setColorAt(1.0, QColor(6, 42, 85, 230))
            painter.fillPath(front_wave, front_grad)

            # Wave Crest Specular Foam Line
            crest_pen = QPen(QColor(255, 255, 255, 160), 1.5)
            painter.strokePath(front_wave, crest_pen)

        # 4. Subtle Ambient Rising Bubbles
        if fill_ratio > 0.15:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 50))
            b1_y = rect.bottom() - ((self._phase * 40) % (rect.height() * fill_ratio))
            b2_y = rect.bottom() - (((self._phase * 30) + 50) % (rect.height() * fill_ratio))
            painter.drawEllipse(QPointF(rect.left() + rect.width() * 0.3, b1_y), 3.5, 3.5)
            painter.drawEllipse(QPointF(rect.left() + rect.width() * 0.72, b2_y), 2.5, 2.5)

        # 5. Top Specular Glass Reflection Gloss
        gloss_path = QPainterPath()
        gloss_path.addRoundedRect(QRectF(rect.left() + 2, rect.top() + 2, rect.width() - 4, rect.height() * 0.38), radius - 2, radius - 2)
        gloss_grad = QLinearGradient(0, rect.top(), 0, rect.top() + rect.height() * 0.4)
        gloss_grad.setColorAt(0.0, QColor(255, 255, 255, 45))
        gloss_grad.setColorAt(0.8, QColor(255, 255, 255, 5))
        gloss_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.fillPath(gloss_path, gloss_grad)

        # 6. Glass Refraction Outer Border
        painter.setClipping(False)
        border_pen = QPen(QColor(0, 240, 255, 55), 1.5)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)

        # 7. Center Typography & Stats Overlay
        pct_text = f"{self.percentage}%"
        stat_text = f"{self._current_ml:,} / {self._goal_ml:,} ml"

        # Percentage Number
        painter.setPen(QColor("#ffffff"))
        pct_font = QFont("Segoe UI", 26, QFont.Weight.Bold)
        pct_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        painter.setFont(pct_font)
        painter.drawText(QRectF(rect.left(), rect.center().y() - 28, rect.width(), 36), Qt.AlignmentFlag.AlignCenter, pct_text)

        # Subtitle / Milliliters
        painter.setPen(QColor("#a8c4d8"))
        sub_font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        painter.setFont(sub_font)
        painter.drawText(QRectF(rect.left(), rect.center().y() + 10, rect.width(), 20), Qt.AlignmentFlag.AlignCenter, stat_text)

        # Status Pill Tag
        if self.percentage >= 100:
            status_text = "✨ GOAL REACHED"
            pill_color = QColor(0, 230, 153, 220)
        else:
            status_text = "💧 HYDRATING"
            pill_color = QColor(0, 240, 255, 180)

        painter.setPen(pill_color)
        status_font = QFont("Segoe UI", 9, QFont.Weight.ExtraBold)
        status_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        painter.setFont(status_font)
        painter.drawText(QRectF(rect.left(), rect.center().y() + 32, rect.width(), 18), Qt.AlignmentFlag.AlignCenter, status_text)
