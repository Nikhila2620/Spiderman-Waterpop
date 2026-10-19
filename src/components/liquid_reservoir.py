"""
Spider-Man Stark Tech / E.D.I.T.H. Tactical HUD Reticle Widget.
Renders the high-tech tactical circular HUD interface with compass degree markings,
Spider-Man eye-lenses targeting crosshairs, segmented web-fluid charge meters,
and real-time hydration telemetry with modern, ultra-clean typography.
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
    Spider-Man Stark Tech / E.D.I.T.H. Tactical HUD Reticle.
    Renders high-precision targeting rings, degree dials, Spider-Man eye-lens crosshairs,
    and live hydration progress telemetry.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(270, 260)

        self._current_ml = 0
        self._goal_ml = 2000

        # Animation state for telemetry pulse & rotating orbital ticks
        self._phase = 0.0
        self._phase_speed = 0.04

        # Wave / pulse loop timer (30 FPS ~ 33ms)
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._update_hud_tick)

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

    def _update_hud_tick(self):
        self._phase += self._phase_speed
        if self._phase > math.pi * 200:
            self._phase = 0.0
        self.update()

    _update_wave = _update_hud_tick

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # Radius for circular HUD
        r_outer = min(cx, cy) - 14.0
        r_degrees = r_outer - 12.0
        r_main = r_degrees - 14.0
        r_dotted = r_main - 18.0
        r_inner = r_dotted - 20.0

        # 1. Pitch-Black Background Frame
        painter.fillRect(0, 0, w, h, QColor("#000000"))

        # 2. Outer Calibration Compass Arc Rings
        pen_white_faint = QPen(QColor(255, 255, 255, 60), 1.0)
        painter.setPen(pen_white_faint)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), r_outer, r_outer)

        # Draw compass degree tick marks & labels (10, 20, 30, 40, 50...)
        degree_font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        painter.setFont(degree_font)
        painter.setPen(QColor(255, 255, 255, 180))

        degree_values = [10, 20, 30, 40, 50, 40, 30, 20, 10]
        step_angle = 18.0  # degrees
        start_angle_top = -80.0
        for i, val in enumerate(degree_values):
            ang = math.radians(start_angle_top + (i * step_angle))
            tx = cx + r_degrees * math.sin(ang)
            ty = cy - r_degrees * math.cos(ang)
            painter.drawText(QRectF(tx - 12, ty - 8, 24, 16), Qt.AlignmentFlag.AlignCenter, str(val))

        # Bottom degree mirror
        for i, val in enumerate(degree_values):
            ang = math.radians(start_angle_top + (i * step_angle))
            tx = cx + r_degrees * math.sin(ang)
            ty = cy + r_degrees * math.cos(ang)
            painter.drawText(QRectF(tx - 12, ty - 8, 24, 16), Qt.AlignmentFlag.AlignCenter, str(val))

        # 3. Main Concentric Tracking Circles
        pen_white_med = QPen(QColor(255, 255, 255, 140), 1.5)
        painter.setPen(pen_white_med)
        painter.drawEllipse(QPointF(cx, cy), r_main, r_main)

        # Concentric dotted radar circle
        pen_dotted = QPen(QColor(255, 255, 255, 90), 1.2, Qt.PenStyle.DotLine)
        painter.setPen(pen_dotted)
        painter.drawEllipse(QPointF(cx, cy), r_dotted, r_dotted)

        # Inner fine targeting circle
        pen_inner = QPen(QColor(255, 255, 255, 110), 1.0)
        painter.setPen(pen_inner)
        painter.drawEllipse(QPointF(cx, cy), r_inner, r_inner)

        # 4. Left and Right Segmented Power / Web-Fluid Charge Flanks
        self._paint_flank_cells(painter, cx, cy, r_main + 5.0, is_left=True)
        self._paint_flank_cells(painter, cx, cy, r_main + 5.0, is_left=False)

        # 5. Dynamic Hydration Progress Arc (0% to 100%+)
        pct = self.clamped_percentage
        if pct > 0:
            span_angle = int((pct / 100.0) * 360 * 16)
            arc_rect = QRectF(cx - r_main, cy - r_main, r_main * 2, r_main * 2)

            # Outer subtle glow
            pen_glow = QPen(QColor(0, 240, 255, 100), 5.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_glow)
            painter.drawArc(arc_rect, 90 * 16, -span_angle)

            # Core high-contrast crisp white laser arc
            pen_arc = QPen(QColor(255, 255, 255, 255), 2.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_arc)
            painter.drawArc(arc_rect, 90 * 16, -span_angle)

        # 6. Center Crosshairs with Gaps for Eyes
        pen_cross = QPen(QColor(255, 255, 255, 160), 1.2)
        painter.setPen(pen_cross)
        # Vertical crosshair (Top & Bottom)
        painter.drawLine(QPointF(cx, cy - r_main), QPointF(cx, cy - 26))
        painter.drawLine(QPointF(cx, cy + 26), QPointF(cx, cy + r_main))
        # Horizontal crosshair (Left & Right)
        painter.drawLine(QPointF(cx - r_main, cy), QPointF(cx - 52.0, cy))
        painter.drawLine(QPointF(cx + 52.0, cy), QPointF(cx + r_main, cy))

        # 7. Flanking Chevrons / Arrow Targeting Brackets (<<< and >>>)
        self._paint_chevrons(painter, cx - 42, cy, is_left=True)
        self._paint_chevrons(painter, cx + 42, cy, is_left=False)

        # 8. Center Spider-Man Eye Lenses Reticle
        self._paint_spidey_eye_reticle(painter, cx, cy)

        # 9. Modern High-Tech HUD Telemetry Readouts (Clean Segoe UI / Cascadia Code)
        # Top Box: [ WEB-FLUID: XX% ]
        box_w = 96.0
        box_h = 20.0
        box_x = cx - 48.0
        box_y = cy - r_inner + 8.0

        painter.setPen(QPen(QColor(255, 255, 255, 220), 1.2))
        painter.setBrush(QColor(0, 0, 0, 220))
        painter.drawRect(QRectF(box_x, box_y, box_w, box_h))

        painter.setPen(QColor("#ffffff"))
        lbl_font = QFont("Cascadia Code", 8, QFont.Weight.Bold)
        lbl_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        painter.setFont(lbl_font)
        painter.drawText(QRectF(box_x, box_y, box_w, box_h), Qt.AlignmentFlag.AlignCenter, f"WEB: {self.percentage}%")

        # Bottom Telemetry: INTAKE & TARGET
        bot_box_w = 170.0
        bot_box_h = 24.0
        bot_box_x = cx - 85.0
        bot_box_y = cy + r_inner - 32.0

        painter.setPen(QPen(QColor(255, 255, 255, 140), 1.0))
        painter.setBrush(QColor(0, 0, 0, 220))
        painter.drawRect(QRectF(bot_box_x, bot_box_y, bot_box_w, bot_box_h))

        status_str = f"TARGETING: {self._current_ml:,} / {self._goal_ml:,} ML"
        painter.setPen(QColor(255, 255, 255, 240))
        bot_font = QFont("Cascadia Code", 7, QFont.Weight.Bold)
        bot_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
        painter.setFont(bot_font)
        painter.drawText(QRectF(bot_box_x, bot_box_y, bot_box_w, bot_box_h), Qt.AlignmentFlag.AlignCenter, status_str)

    def _paint_flank_cells(self, painter: QPainter, cx: float, cy: float, r: float, is_left: bool):
        """Draws the vertical curved segmented charge bars on the flanks like in the reference image."""
        num_cells = 4
        cell_span = 7.0
        gap = 2.5
        base_angle = 180.0 if is_left else 0.0

        painter.save()
        painter.setBrush(QColor(255, 255, 255, 210))
        painter.setPen(Qt.PenStyle.NoPen)

        rect = QRectF(cx - r, cy - r, r * 2, r * 2)

        for i in range(num_cells):
            start = (base_angle - 15.0) + (i * (cell_span + gap))
            pen = QPen(QColor(255, 255, 255, 200), 3.5)
            painter.setPen(pen)
            painter.drawArc(rect, int(start * 16), int(cell_span * 16))

        painter.restore()

    def _paint_chevrons(self, painter: QPainter, x: float, y: float, is_left: bool):
        """Draws the tactical chevron brackets flanking the eye lenses."""
        painter.save()
        pen = QPen(QColor(255, 255, 255, 220), 1.4)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        d = -1.0 if is_left else 1.0
        for i in range(3):
            ox = x + (i * 5.0 * d)
            p1 = QPointF(ox, y - 8.0)
            p2 = QPointF(ox + (4.0 * d), y)
            p3 = QPointF(ox, y + 8.0)
            painter.drawPolyline([p1, p2, p3])

        painter.restore()

    def _paint_spidey_eye_reticle(self, painter: QPainter, cx: float, cy: float):
        """
        Renders the iconic stylized Spider-Man angular eye lenses in laser-cut white
        with precision polygonal lines.
        """
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Left Eye Polygon
        # Angular convex eye polygon with sharp outer flare
        left_eye = [
            QPointF(cx - 24, cy - 11),  # Top outer corner
            QPointF(cx - 7, cy - 14),   # Top inner corner
            QPointF(cx - 5, cy + 8),    # Bottom inner corner
            QPointF(cx - 20, cy + 12),  # Bottom outer corner
            QPointF(cx - 26, cy + 1),   # Lateral outer flare point
        ]

        # Right Eye Polygon (symmetric mirror)
        right_eye = [
            QPointF(cx + 24, cy - 11),
            QPointF(cx + 7, cy - 14),
            QPointF(cx + 5, cy + 8),
            QPointF(cx + 20, cy + 12),
            QPointF(cx + 26, cy + 1),
        ]

        # Fill with subtle holographic glow
        pulse_alpha = int(180 + (math.sin(self._phase * 2.0) * 45))
        painter.setBrush(QColor(255, 255, 255, 220))
        painter.setPen(QPen(QColor(255, 255, 255, 255), 2.0))

        painter.drawPolygon(left_eye)
        painter.drawPolygon(right_eye)

        # Crisp inner lens pupil line
        painter.setPen(QPen(QColor(0, 0, 0, 240), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(left_eye)
        painter.drawPolygon(right_eye)

        painter.setPen(QPen(QColor(255, 255, 255, pulse_alpha), 1.5))
        painter.drawPolygon(left_eye)
        painter.drawPolygon(right_eye)

        painter.restore()
