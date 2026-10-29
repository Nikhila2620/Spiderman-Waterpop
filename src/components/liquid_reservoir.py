"""
Core Fluid Level & Spider-Sense Hydration Chamber Widget for Spider-Man Water Buddy v2.0.
Synthesizes calm bioluminescent water fluid dynamics with comic Spider-Sense electric squiggles
and clean, legible telemetry (warm paper white and graphite).
"""
import math
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal, Property
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath

from src.theme import TOKENS


class LiquidReservoirWidget(QWidget):
    """
    Minimal Core Fluid Level Chamber with Spider-Sense electric arcs and fluid telemetry.
    """
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)

        self._current_ml = 0
        self._goal_ml = 2000
        self._fill_level = 0.0

        # Animation phase for subtle liquid and Spider-Sense shimmer
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 FPS
        self._timer.timeout.connect(self._update_hud_tick)
        self._timer.start()

    # Qt Property for fill level
    def get_fill_level(self) -> float:
        return self._fill_level

    def set_fill_level(self, val: float):
        self._fill_level = max(0.0, min(1.0, val))
        self.update()

    fill_level = Property(float, get_fill_level, set_fill_level)

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

    def _update_hud_tick(self):
        self._phase += 0.04
        if self._phase > math.pi * 200:
            self._phase = 0.0
        self.update()

    _update_wave = _update_hud_tick

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        r_main = min(cx, cy) - 26.0

        # 1. Base Track Groove (Smooth dark graphite ring)
        pen_track = QPen(QColor("#24282f"), 14.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_track)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        arc_rect = QRectF(cx - r_main, cy - r_main, r_main * 2.0, r_main * 2.0)
        painter.drawArc(arc_rect, 0, 360 * 16)

        # 2. Outer Subtle Spider-Sense Electric Squiggles at the Crown
        self._paint_chamber_squiggles(painter, cx, cy, r_main)

        # 3. Dynamic Bioluminescent Water Fluid Arc (Calm Cyan #6cb6c8)
        pct = self.clamped_percentage
        if pct > 0:
            span_angle = int((pct / 100.0) * 360 * 16)

            # Soft ambient water glow
            glow_pen = QPen(QColor(108, 182, 200, 70), 20.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(glow_pen)
            painter.drawArc(arc_rect, 90 * 16, -span_angle)

            # Core fluid arc
            arc_pen = QPen(QColor("#6cb6c8"), 14.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(arc_pen)
            painter.drawArc(arc_rect, 90 * 16, -span_angle)

            # Tiny water drop bead at leading edge
            lead_rad = math.radians(90.0 - ((pct / 100.0) * 360.0))
            drop_x = cx + r_main * math.cos(lead_rad)
            drop_y = cy - r_main * math.sin(lead_rad)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#ffffff"))
            painter.drawEllipse(QPointF(drop_x, drop_y), 4.0, 4.0)

        # 4. Center Typography (From user's Lab Logbook)
        # Percentage numeral (e.g. "60%")
        painter.setPen(QColor(TOKENS.TEXT_PRIMARY))
        pct_font = QFont("Segoe UI Variable", 34, QFont.Weight.Bold)
        pct_font.setStyleHint(QFont.StyleHint.SansSerif)
        painter.setFont(pct_font)
        painter.drawText(QRectF(cx - 80, cy - 42, 160, 44), Qt.AlignmentFlag.AlignCenter, f"{self.percentage}%")

        # Telemetry: current / goal (e.g. "1,500 / 2,500 ml")
        painter.setPen(QColor(TOKENS.TEXT_SECONDARY))
        stat_font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        painter.setFont(stat_font)
        stat_text = f"{self._current_ml:,} / {self._goal_ml:,} ml"
        painter.drawText(QRectF(cx - 100, cy + 4, 200, 22), Qt.AlignmentFlag.AlignCenter, stat_text)

        # Hint: "Tap dose or custom to log"
        painter.setPen(QColor(TOKENS.TEXT_MUTED))
        hint_font = QFont("Segoe UI", 9, QFont.Weight.Normal)
        painter.setFont(hint_font)
        painter.drawText(QRectF(cx - 100, cy + 28, 200, 18), Qt.AlignmentFlag.AlignCenter, "Tap dose or custom to log")

    def _paint_chamber_squiggles(self, painter: QPainter, cx: float, cy: float, r_main: float):
        """Paints Spider-Verse electric squiggle arcs radiating at the crown."""
        painter.save()
        # Squiggle rays radiating outward above the chamber
        squiggles_deg = [130.0, 105.0, 75.0, 50.0]
        pulse = math.sin(self._phase * 2.0) * 2.0

        for i, deg in enumerate(squiggles_deg):
            rad = math.radians(deg)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)
            perp_x = -sin_a
            perp_y = cos_a

            r0 = r_main + 12.0
            r_len = 18.0 + pulse + (i % 2) * 4.0
            kink = 4.0 if i % 2 == 0 else -4.0

            p0 = QPointF(cx + cos_a * r0, cy - sin_a * r0)
            p1 = QPointF(cx + cos_a * (r0 + r_len * 0.4) + perp_x * kink,
                         cy - sin_a * (r0 + r_len * 0.4) + perp_y * kink)
            p2 = QPointF(cx + cos_a * (r0 + r_len * 0.7) - perp_x * (kink * 0.8),
                         cy - sin_a * (r0 + r_len * 0.7) - perp_y * (kink * 0.8))
            p3 = QPointF(cx + cos_a * (r0 + r_len), cy - sin_a * (r0 + r_len))

            path = QPainterPath()
            path.moveTo(p0)
            path.cubicTo(p1, p2, p3)

            # Cyan chromatic shift underlay
            painter.setPen(QPen(QColor(0, 240, 255, 120), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawPath(path)

            # Neon gold / magenta electric squiggle
            color_sense = QColor("#ff1493") if i % 2 == 1 else QColor("#d9a548")
            painter.setPen(QPen(color_sense, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawPath(path)

        painter.restore()
