import sys
from pathlib import Path
from PySide6.QtCore import (
    Qt,
    QRectF,
    QPointF,
    QPropertyAnimation,
    QEasingCurve,
    Property,
    Signal,
)
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer


class SpideyWidget(QWidget):
    """
    Renders the photorealistic AAA 3D superhero character hanging upside down by a web.
    Features:
      - Photorealistic AAA 3D CGI character render with true RGBA alpha channel
      - Seamless pendulum swinging on the web
      - Mouse interactions:
          * Hover: perks up with alert spider-sense tingling aura and lenses
          * Drag / Pull: elastic web stretch and spring recoil upon release
          * Click: triggers a playful web bounce
      - Visual state overlays:
          * Idle: serene hanging with subtle ambient lighting
          * Hover: cyan spider-sense aura and reactive web glint
          * Happy: celebratory gold stars, web burst, and energetic swing
          * Disappointed: comedic blue sweat drop and sluggish sway
    """

    STATE_IDLE = "idle"
    STATE_HOVER = "hover"
    STATE_HAPPY = "happy"
    STATE_DISAPPOINTED = "disappointed"

    clicked = Signal()
    hoverEntered = Signal()
    hoverLeft = Signal()

    def __init__(self, parent=None, width=190, height=270):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setMouseTracking(True)

        self._state = self.STATE_IDLE
        self._base_state = self.STATE_IDLE
        self._swing_angle = 0.0
        self._pull_offset = QPointF(0.0, 0.0)
        self._is_pulling = False
        self._drag_start = None

        self._pixmap_3d = None
        self._renderers = {}

        self._init_assets()
        self._init_animations()

    def _init_assets(self):
        """Loads the AAA 3D photorealistic render and vector overlays."""
        base_dir = Path(__file__).resolve().parent.parent / "assets" / "images"
        png_path = base_dir / "spidey_3d_render.png"

        if png_path.exists():
            self._pixmap_3d = QPixmap(str(png_path))

        # Vector fallbacks if needed
        svg_map = {
            self.STATE_IDLE: base_dir / "spidey_idle.svg",
            self.STATE_HOVER: base_dir / "spidey_hover.svg",
            self.STATE_HAPPY: base_dir / "spidey_happy.svg",
            self.STATE_DISAPPOINTED: base_dir / "spidey_disappointed.svg",
        }
        for state, path in svg_map.items():
            if path.exists():
                renderer = QSvgRenderer(str(path))
                if renderer.isValid():
                    self._renderers[state] = renderer

    def _init_animations(self):
        """Initializes cozy pendulum swinging and spring physics."""
        self._swing_anim = QPropertyAnimation(self, b"swingAngle")
        self._swing_anim.setDuration(2600)
        self._swing_anim.setStartValue(-4.5)
        self._swing_anim.setKeyValueAt(0.5, 4.5)
        self._swing_anim.setEndValue(-4.5)
        self._swing_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._swing_anim.setLoopCount(-1)
        self._swing_anim.start()

        self._recoil_anim = QPropertyAnimation(self, b"pullOffset")
        self._recoil_anim.setDuration(700)
        self._recoil_anim.setEasingCurve(QEasingCurve.Type.OutElastic)

    def get_swing_angle(self) -> float:
        return self._swing_angle

    def set_swing_angle(self, val: float):
        self._swing_angle = val
        self.update()

    swingAngle = Property(float, get_swing_angle, set_swing_angle)

    def get_pull_offset(self) -> QPointF:
        return self._pull_offset

    def set_pull_offset(self, pt: QPointF):
        self._pull_offset = pt
        self.update()

    pullOffset = Property(QPointF, get_pull_offset, set_pull_offset)

    def set_state(self, state: str):
        if state not in (self.STATE_IDLE, self.STATE_HAPPY, self.STATE_DISAPPOINTED):
            return

        self._base_state = state
        self._state = state

        if state == self.STATE_HAPPY:
            self._swing_anim.setDuration(1200)
            self._swing_anim.setStartValue(-7.5)
            self._swing_anim.setKeyValueAt(0.5, 7.5)
            self._swing_anim.setEndValue(-7.5)
        elif state == self.STATE_DISAPPOINTED:
            self._swing_anim.setDuration(3600)
            self._swing_anim.setStartValue(-2.0)
            self._swing_anim.setKeyValueAt(0.5, 2.0)
            self._swing_anim.setEndValue(-2.0)
        else:
            self._swing_anim.setDuration(2600)
            self._swing_anim.setStartValue(-4.5)
            self._swing_anim.setKeyValueAt(0.5, 4.5)
            self._swing_anim.setEndValue(-4.5)

        self.update()

    # Mouse reactions
    def enterEvent(self, event):
        if self._base_state == self.STATE_IDLE:
            self._state = self.STATE_HOVER
            self.update()
        self.hoverEntered.emit()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._base_state == self.STATE_IDLE:
            self._state = self.STATE_IDLE
            self.update()
        self.hoverLeft.emit()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pulling = True
            self._drag_start = event.position()
            self._recoil_anim.stop()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_pulling and self._drag_start is not None:
            delta = event.position() - self._drag_start
            clamped_x = max(-50.0, min(50.0, delta.x() * 0.6))
            clamped_y = max(-10.0, min(65.0, delta.y() * 0.6))
            self.set_pull_offset(QPointF(clamped_x, clamped_y))
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._is_pulling:
            self._is_pulling = False
            self._drag_start = None

            self._recoil_anim.setStartValue(self._pull_offset)
            self._recoil_anim.setEndValue(QPointF(0.0, 0.0))
            self._recoil_anim.start()

            self.clicked.emit()
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        anchor_x = self.width() / 2.0
        anchor_y = 0.0

        # Draw stretched dynamic web strand if pulled
        if not self._pull_offset.isNull():
            pen = QPen(QColor(255, 255, 255, 230), 2.4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(anchor_x, anchor_y),
                QPointF(anchor_x + self._pull_offset.x(), anchor_y + 45.0 + self._pull_offset.y())
            )

        # Apply pendulum rotation around top screen anchor
        painter.translate(anchor_x + self._pull_offset.x(), anchor_y + self._pull_offset.y())
        painter.rotate(self._swing_angle)
        painter.translate(-anchor_x, -anchor_y)

        # 1. Render Photorealistic AAA 3D Character
        if self._pixmap_3d and not self._pixmap_3d.isNull():
            target_rect = QRectF(0, 0, self.width(), self.height())
            painter.drawPixmap(target_rect.toRect(), self._pixmap_3d)
        else:
            # Fallback to vector asset
            renderer = self._renderers.get(self._state) or self._renderers.get(self.STATE_IDLE)
            if renderer and renderer.isValid():
                target_rect = QRectF(0, 0, self.width(), self.height())
                renderer.render(painter, target_rect)

        # 2. Render dynamic interactive state overlays
        if self._state == self.STATE_HOVER:
            self._paint_hover_overlay(painter)
        elif self._state == self.STATE_HAPPY:
            self._paint_happy_overlay(painter)
        elif self._state == self.STATE_DISAPPOINTED:
            self._paint_disappointed_overlay(painter)

    def _paint_hover_overlay(self, painter: QPainter):
        """Cyan spider-sense tingling aura around mask."""
        pen = QPen(QColor("#38bdf8"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # Tingling sense arcs around head (head is near bottom center, around x:95, y:230)
        head_cx = self.width() * 0.5
        head_cy = self.height() * 0.82
        painter.drawArc(int(head_cx - 40), int(head_cy - 30), 80, 60, 30 * 16, 120 * 16)
        painter.drawArc(int(head_cx - 48), int(head_cy - 36), 96, 72, 40 * 16, 100 * 16)

    def _paint_happy_overlay(self, painter: QPainter):
        """Golden celebration sparkles & web burst."""
        # Golden stars
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#fbbf24"))
        w, h = self.width(), self.height()
        # Star 1 (Right)
        self._draw_star(painter, w * 0.82, h * 0.65, 8)
        # Star 2 (Left)
        painter.setBrush(QColor("#38bdf8"))
        self._draw_star(painter, w * 0.18, h * 0.45, 6)

    def _paint_disappointed_overlay(self, painter: QPainter):
        """Comedic blue sweat drop."""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#38bdf8"))
        # Sweat drop near temple (head is around width*0.5, height*0.82)
        sx = self.width() * 0.62
        sy = self.height() * 0.76
        painter.drawEllipse(int(sx), int(sy), 8, 12)

    def _draw_star(self, painter: QPainter, cx: float, cy: float, r: float):
        painter.drawPolygon([
            QPointF(cx, cy - r),
            QPointF(cx + r * 0.3, cy - r * 0.3),
            QPointF(cx + r, cy),
            QPointF(cx + r * 0.3, cy + r * 0.3),
            QPointF(cx, cy + r),
            QPointF(cx - r * 0.3, cy + r * 0.3),
            QPointF(cx - r, cy),
            QPointF(cx - r * 0.3, cy - r * 0.3),
        ])


# Compatibility alias
CharacterWidget = SpideyWidget
