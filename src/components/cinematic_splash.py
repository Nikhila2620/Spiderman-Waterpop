from src.utils import resource_path
"""
Cinematic Opening Shoot & Splash Animation Overlay for Spider-Man Water Buddy v2.0.
Executes a high-impact superhero movie title pop sequence:
  Phase 1: Center logo spring pop with radiating web rings.
  Phase 2: App Name 'SPIDER-MAN WATER BUDDY' comic pulse with scarlet neon glow.
  Phase 3: Spider-Sense chromatic energy flash and smooth dissolve into Lab Logbook dashboard.
"""
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, Signal, QRectF
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect, QFrame, QHBoxLayout
from PySide6.QtGui import QPainter, QColor, QPixmap, QFont, QPen, QRadialGradient

from src.theme import TOKENS


class CinematicSplashOverlay(QWidget):
    """
    Cinematic App Intro Animation Overlay that plays on launch or on replay.
    """
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._progress = 0.0
        self._logo_scale = 0.3
        self._opacity = 1.0

        # Load Logo Pixmap
        icon_path = resource_path("assets/images/app_icon.png")
        self._logo_pixmap = QPixmap(str(icon_path)) if icon_path.exists() else QPixmap()

        self._anim = QPropertyAnimation(self, b"animProgress")
        self._anim.setDuration(1500)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim.finished.connect(self._on_animation_finished)

    def get_anim_progress(self) -> float:
        return self._progress

    def set_anim_progress(self, val: float):
        self._progress = float(val)
        # Phase 1: 0.0 to 0.4 -> Logo scale pops from 0.3 to 1.05 then settles to 1.0
        if self._progress < 0.4:
            p = self._progress / 0.4
            self._logo_scale = 0.3 + 0.75 * math_ease_out_back(p)
            self._opacity = 1.0
        # Phase 2: 0.4 to 0.75 -> Title holds, energy squiggles pulse
        elif self._progress < 0.75:
            self._logo_scale = 1.0
            self._opacity = 1.0
        # Phase 3: 0.75 to 1.0 -> Dissolve out
        else:
            p = (self._progress - 0.75) / 0.25
            self._logo_scale = 1.0 + p * 0.08
            self._opacity = max(0.0, 1.0 - p)
        self.update()

    animProgress = Property(float, get_anim_progress, set_anim_progress)

    def start_intro(self):
        self.show()
        self.raise_()
        self._anim.stop()
        self._progress = 0.0
        self._logo_scale = 0.3
        self._opacity = 1.0
        self._anim.start()

    def mousePressEvent(self, event):
        # Click to skip immediately
        self._anim.stop()
        self._on_animation_finished()

    def _on_animation_finished(self):
        self.hide()
        self.finished.emit()

    def paintEvent(self, event):
        if self._opacity <= 0.0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0 - 20.0

        # Background Noir Dim with Opacity Fade
        painter.setOpacity(self._opacity)
        painter.fillRect(0, 0, w, h, QColor(14, 16, 20, 252))

        # 1. Radiating Cinematic Spider-Web Telemetry Rings
        pen_ring = QPen(QColor(214, 72, 63, int(45 * self._opacity)), 1.5, Qt.PenStyle.SolidLine)
        painter.setPen(pen_ring)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for r_step in (80, 150, 230, 320, 420):
            r = r_step * (0.8 + self._progress * 0.3)
            painter.drawEllipse(QRectF(cx - r, cy - r, r * 2.0, r * 2.0))

        # Spider-Sense energy flash cross-hairs
        if 0.3 < self._progress < 0.8:
            sweep = (self._progress - 0.3) / 0.5
            pen_sweep = QPen(QColor(0, 240, 255, int(120 * (1.0 - abs(sweep - 0.5) * 2))), 2.0)
            painter.setPen(pen_sweep)
            painter.drawLine(cx - 260, cy, cx + 260, cy)
            painter.drawLine(cx, cy - 200, cx, cy + 200)

        # 2. Centered Logo Pop
        logo_base_size = 110.0
        draw_size = logo_base_size * self._logo_scale
        if not self._logo_pixmap.isNull():
            target_rect = QRectF(cx - draw_size / 2.0, cy - draw_size / 2.0 - 45.0, draw_size, draw_size)
            painter.drawPixmap(target_rect.toRect(), self._logo_pixmap)

        # 3. Main Title Pop: "SPIDER-MAN WATER BUDDY"
        title_alpha = int(255 * min(1.0, max(0.0, (self._progress - 0.15) / 0.25)) * self._opacity)
        if title_alpha > 0:
            painter.setOpacity(title_alpha / 255.0)

            # Glow shadow
            painter.setFont(QFont("Segoe UI", 22, QFont.Weight.Black))
            painter.setPen(QColor(214, 72, 63, 140))
            painter.drawText(QRectF(0, cy + 32.0, w, 40.0), Qt.AlignmentFlag.AlignCenter, "SPIDER-MAN WATER BUDDY")

            # Core Crisp Paper White
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QRectF(0, cy + 30.0, w, 40.0), Qt.AlignmentFlag.AlignCenter, "SPIDER-MAN WATER BUDDY")

            # 4. Subtitle: "LAB LOGBOOK v2.0"
            sub_alpha = int(220 * min(1.0, max(0.0, (self._progress - 0.35) / 0.25)) * self._opacity)
            painter.setOpacity(sub_alpha / 255.0)
            painter.setFont(QFont("Cascadia Code", 11, QFont.Weight.Bold))
            painter.setPen(QColor(TOKENS.ACCENT_GOLD))
            painter.drawText(QRectF(0, cy + 72.0, w, 24.0), Qt.AlignmentFlag.AlignCenter, "⚡ LAB LOGBOOK v2.0 // OSMOSIS METRICS ONLINE")

            # Instruction pill
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
            painter.setPen(QColor(TOKENS.TEXT_MUTED))
            painter.drawText(QRectF(0, cy + 104.0, w, 20.0), Qt.AlignmentFlag.AlignCenter, "Click anywhere to continue")


def math_ease_out_back(x: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * ((x - 1.0) ** 3) + c1 * ((x - 1.0) ** 2)
