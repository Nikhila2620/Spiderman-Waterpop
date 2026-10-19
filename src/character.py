import sys
import math
from pathlib import Path
from PySide6.QtCore import (
    Qt,
    QRectF,
    QPointF,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QParallelAnimationGroup,
    QEasingCurve,
    Property,
    Signal,
)
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import (
    QPainter,
    QColor,
    QFont,
    QPen,
    QPixmap,
    QCursor,
    QPainterPath,
    QRadialGradient,
)
from PySide6.QtSvg import QSvgRenderer


class SpideyWidget(QWidget):
    """
    Renders the photorealistic AAA 3D superhero character hanging upside down by a web.
    Features:
      - Photorealistic AAA 3D CGI character render with true RGBA alpha channel
      - Cinematic multi-phase motion design:
          * YES Sequence: Anticipation crouch -> Wide horizontal web swing -> Victory celebration -> Damped recovery
          * NO Sequence: Disappointment slump sag -> Defeated sigh sway -> Spring recovery
          * IDLE: Harmonic pendulum sway with organic breathing micro-bounce
      - Dynamic physics-based web strand connecting desktop ceiling anchor to hand grip
      - High-velocity comic action lines and particle celebration bursts
      - Interactive elastic web stretch with spring recoil physics
      - Interruption-safe animation engine preventing stuck states or visual jumps
    """

    STATE_IDLE = "idle"
    STATE_HOVER = "hover"
    STATE_HAPPY = "happy"
    STATE_DISAPPOINTED = "disappointed"

    clicked = Signal()
    hoverEntered = Signal()
    hoverLeft = Signal()
    animationFinished = Signal()

    def __init__(self, parent=None, width=260, height=325):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._state = self.STATE_IDLE
        self._base_state = self.STATE_IDLE

        # Transform physics properties
        self._swing_angle = 0.0
        self._swing_x = 0.0
        self._swing_y = 0.0
        self._body_tilt = 0.0
        self._celebration_progress = 0.0
        self._disappointment_progress = 0.0

        # Mouse interaction properties
        self._pull_offset = QPointF(0.0, 0.0)
        self._is_pulling = False
        self._drag_start = None

        # Assets
        self._pixmap_3d = None
        self._renderers = {}

        # Config flags
        self._animation_enabled = True
        self._performance_mode = False
        self._character_scale = 1.0

        # Animation controllers
        self._idle_group = None
        self._active_sequence = None

        self._init_assets()
        self._init_animations()

    # -------------------------------------------------------------------------
    # Properties for Qt Animation Engine
    # -------------------------------------------------------------------------

    def get_swing_angle(self) -> float:
        return self._swing_angle

    def set_swing_angle(self, val: float):
        self._swing_angle = float(val)
        self.update()

    swingAngle = Property(float, get_swing_angle, set_swing_angle)

    def get_swing_x(self) -> float:
        return self._swing_x

    def set_swing_x(self, val: float):
        self._swing_x = float(val)
        self.update()

    swingX = Property(float, get_swing_x, set_swing_x)

    def get_swing_y(self) -> float:
        return self._swing_y

    def set_swing_y(self, val: float):
        self._swing_y = float(val)
        self.update()

    swingY = Property(float, get_swing_y, set_swing_y)

    def get_body_tilt(self) -> float:
        return self._body_tilt

    def set_body_tilt(self, val: float):
        self._body_tilt = float(val)
        self.update()

    bodyTilt = Property(float, get_body_tilt, set_body_tilt)

    def get_celebration_progress(self) -> float:
        return self._celebration_progress

    def set_celebration_progress(self, val: float):
        self._celebration_progress = float(val)
        self.update()

    celebrationProgress = Property(float, get_celebration_progress, set_celebration_progress)

    def get_disappointment_progress(self) -> float:
        return self._disappointment_progress

    def set_disappointment_progress(self, val: float):
        self._disappointment_progress = float(val)
        self.update()

    disappointmentProgress = Property(float, get_disappointment_progress, set_disappointment_progress)

    def get_pull_offset(self) -> QPointF:
        return self._pull_offset

    def set_pull_offset(self, pt: QPointF):
        self._pull_offset = pt
        self.update()

    pullOffset = Property(QPointF, get_pull_offset, set_pull_offset)

    # -------------------------------------------------------------------------
    # Asset Loading
    # -------------------------------------------------------------------------

    def _init_assets(self):
        """Loads the AAA 3D photorealistic render and vector overlays."""
        base_dir = Path(__file__).resolve().parent.parent / "assets" / "images"
        png_path = base_dir / "spidey_3d_render.png"

        if png_path.exists():
            self._pixmap_3d = QPixmap(str(png_path))

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

    # -------------------------------------------------------------------------
    # Animation Setup & Lifecycles
    # -------------------------------------------------------------------------

    def _init_animations(self):
        """Initializes continuous idle pendulum sway and interactive recoil physics."""
        # Idle sway animation
        self._swing_anim = QPropertyAnimation(self, b"swingAngle")
        self._swing_anim.setDuration(2600)
        self._swing_anim.setStartValue(-4.0)
        self._swing_anim.setKeyValueAt(0.5, 4.0)
        self._swing_anim.setEndValue(-4.0)
        self._swing_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._swing_anim.setLoopCount(-1)

        # Breathing micro-bounce
        self._breathe_anim = QPropertyAnimation(self, b"swingY")
        self._breathe_anim.setDuration(2600)
        self._breathe_anim.setStartValue(0.0)
        self._breathe_anim.setKeyValueAt(0.5, 2.0)
        self._breathe_anim.setEndValue(0.0)
        self._breathe_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._breathe_anim.setLoopCount(-1)

        self._idle_group = QParallelAnimationGroup(self)
        self._idle_group.addAnimation(self._swing_anim)
        self._idle_group.addAnimation(self._breathe_anim)

        # Recoil animation for interactive web pull
        self._recoil_anim = QPropertyAnimation(self, b"pullOffset")
        self._recoil_anim.setDuration(700)
        self._recoil_anim.setEasingCurve(QEasingCurve.Type.OutElastic)

        if self._animation_enabled:
            self._idle_group.start()

    def set_character_scale(self, scale: float):
        """Sets character rendering scale (0.75x to 1.5x) with proportional container buffer."""
        self._character_scale = max(0.75, min(1.5, float(scale)))
        self.setFixedSize(int(260 * self._character_scale), int(325 * self._character_scale))
        self.update()

    def set_animation_enabled(self, enabled: bool):
        """Toggles animations on or off."""
        self._animation_enabled = enabled
        if not enabled:
            self._stop_active_sequence()
            if self._idle_group:
                self._idle_group.stop()
            self._reset_properties_to_resting()
        else:
            if self._state == self.STATE_IDLE and self._idle_group:
                if self._idle_group.state() != QParallelAnimationGroup.State.Running:
                    self._idle_group.start()

    def set_performance_mode(self, perf_mode: bool):
        """Reduces animation frequency and overhead for battery saving."""
        self._performance_mode = perf_mode
        duration = 4000 if perf_mode else 2600
        self._swing_anim.setDuration(duration)
        self._breathe_anim.setDuration(duration)
        self.update()

    def _stop_active_sequence(self):
        """Safely stops any active coordinated sequence."""
        if self._active_sequence:
            try:
                self._active_sequence.stop()
                self._active_sequence.deleteLater()
            except Exception:
                pass
            self._active_sequence = None

    def _reset_properties_to_resting(self):
        """Instantly resets physical transforms to absolute neutral rest (0, 0, 0 deg)."""
        self._swing_angle = 0.0
        self._swing_x = 0.0
        self._swing_y = 0.0
        self._body_tilt = 0.0
        self._celebration_progress = 0.0
        self._disappointment_progress = 0.0
        self.update()

    def set_state(self, state: str):
        """
        Public state transition API. Triggers coordinated cinematic sequences for
        STATE_HAPPY and STATE_DISAPPOINTED, or returns to resting STATE_IDLE.
        """
        if state not in (self.STATE_IDLE, self.STATE_HAPPY, self.STATE_DISAPPOINTED):
            return

        self._base_state = state
        self._state = state

        if not self._animation_enabled:
            self._reset_properties_to_resting()
            return

        if state == self.STATE_HAPPY:
            self.play_yes_sequence()
        elif state == self.STATE_DISAPPOINTED:
            self.play_no_sequence()
        else:
            self.reset_to_idle()

    # -------------------------------------------------------------------------
    # Cinematic YES Sequence: Anticipation -> Wide Swing -> Victory -> Recovery
    # -------------------------------------------------------------------------

    def play_yes_sequence(self):
        """
        Executes a 4-phase cinematic wide web swing and victory celebration sequence:
          Phase 1: Anticipation (web-pull crouch, body tilt, 240ms)
          Phase 2: High-Velocity Wide Swing (left swoop -> power right swoop -> reverse settle, 1360ms)
          Phase 3: Victory Pose & Sparkle Burst (triumphant vertical bounce, golden/ruby stars, 850ms)
          Phase 4: Damped Recovery (smooth return to exact resting origin, 350ms)
        """
        self._stop_active_sequence()
        if self._idle_group:
            self._idle_group.stop()

        self._state = self.STATE_HAPPY
        self._base_state = self.STATE_HAPPY

        seq = QSequentialAnimationGroup(self)

        # ---------------------------------------------------------------------
        # Phase 1: Anticipation (240ms)
        # Spider-Man prepares for movement with a subtle upward crouch and tilt
        # ---------------------------------------------------------------------
        p1 = QParallelAnimationGroup(seq)
        
        anim_y1 = QPropertyAnimation(self, b"swingY")
        anim_y1.setDuration(240)
        anim_y1.setStartValue(self._swing_y)
        anim_y1.setEndValue(-12.0)
        anim_y1.setEasingCurve(QEasingCurve.Type.InOutQuad)
        p1.addAnimation(anim_y1)

        anim_a1 = QPropertyAnimation(self, b"swingAngle")
        anim_a1.setDuration(240)
        anim_a1.setStartValue(self._swing_angle)
        anim_a1.setEndValue(-3.5)
        anim_a1.setEasingCurve(QEasingCurve.Type.InOutQuad)
        p1.addAnimation(anim_a1)

        anim_t1 = QPropertyAnimation(self, b"bodyTilt")
        anim_t1.setDuration(240)
        anim_t1.setStartValue(self._body_tilt)
        anim_t1.setEndValue(-5.0)
        anim_t1.setEasingCurve(QEasingCurve.Type.InOutQuad)
        p1.addAnimation(anim_t1)

        seq.addAnimation(p1)

        # ---------------------------------------------------------------------
        # Phase 2: Wide Horizontal Web Swing (1360ms total)
        # ---------------------------------------------------------------------
        # Subphase 2A: Power Swoop Left (400ms)
        p2a = QParallelAnimationGroup(seq)
        
        sx_2a = QPropertyAnimation(self, b"swingX")
        sx_2a.setDuration(400)
        sx_2a.setStartValue(0.0)
        sx_2a.setEndValue(-36.0)
        sx_2a.setEasingCurve(QEasingCurve.Type.InOutCubic)
        p2a.addAnimation(sx_2a)

        sa_2a = QPropertyAnimation(self, b"swingAngle")
        sa_2a.setDuration(400)
        sa_2a.setStartValue(-3.5)
        sa_2a.setEndValue(-22.0)
        sa_2a.setEasingCurve(QEasingCurve.Type.InOutCubic)
        p2a.addAnimation(sa_2a)

        sy_2a = QPropertyAnimation(self, b"swingY")
        sy_2a.setDuration(400)
        sy_2a.setStartValue(-12.0)
        sy_2a.setKeyValueAt(0.5, 4.0)
        sy_2a.setEndValue(-2.0)
        sy_2a.setEasingCurve(QEasingCurve.Type.InOutQuad)
        p2a.addAnimation(sy_2a)

        st_2a = QPropertyAnimation(self, b"bodyTilt")
        st_2a.setDuration(400)
        st_2a.setStartValue(-5.0)
        st_2a.setEndValue(-8.0)
        st_2a.setEasingCurve(QEasingCurve.Type.InOutQuad)
        p2a.addAnimation(st_2a)

        seq.addAnimation(p2a)

        # Subphase 2B: High-Velocity Power Swoop Across to Right (520ms)
        p2b = QParallelAnimationGroup(seq)
        
        sx_2b = QPropertyAnimation(self, b"swingX")
        sx_2b.setDuration(520)
        sx_2b.setStartValue(-36.0)
        sx_2b.setEndValue(38.0)
        sx_2b.setEasingCurve(QEasingCurve.Type.InOutCubic)
        p2b.addAnimation(sx_2b)

        sa_2b = QPropertyAnimation(self, b"swingAngle")
        sa_2b.setDuration(520)
        sa_2b.setStartValue(-22.0)
        sa_2b.setEndValue(24.0)
        sa_2b.setEasingCurve(QEasingCurve.Type.InOutCubic)
        p2b.addAnimation(sa_2b)

        sy_2b = QPropertyAnimation(self, b"swingY")
        sy_2b.setDuration(520)
        sy_2b.setStartValue(-2.0)
        sy_2b.setKeyValueAt(0.5, 8.0)
        sy_2b.setEndValue(-4.0)
        sy_2b.setEasingCurve(QEasingCurve.Type.InOutQuad)
        p2b.addAnimation(sy_2b)

        st_2b = QPropertyAnimation(self, b"bodyTilt")
        st_2b.setDuration(520)
        st_2b.setStartValue(-8.0)
        st_2b.setEndValue(10.0)
        st_2b.setEasingCurve(QEasingCurve.Type.InOutQuad)
        p2b.addAnimation(st_2b)

        seq.addAnimation(p2b)

        # Subphase 2C: Natural Reverse Arc to Center with Controlled Overshoot (440ms)
        p2c = QParallelAnimationGroup(seq)
        
        sx_2c = QPropertyAnimation(self, b"swingX")
        sx_2c.setDuration(440)
        sx_2c.setStartValue(38.0)
        sx_2c.setEndValue(0.0)
        sx_2c.setEasingCurve(QEasingCurve.Type.OutBack)
        p2c.addAnimation(sx_2c)

        sa_2c = QPropertyAnimation(self, b"swingAngle")
        sa_2c.setDuration(440)
        sa_2c.setStartValue(24.0)
        sa_2c.setEndValue(0.0)
        sa_2c.setEasingCurve(QEasingCurve.Type.OutBack)
        p2c.addAnimation(sa_2c)

        sy_2c = QPropertyAnimation(self, b"swingY")
        sy_2c.setDuration(440)
        sy_2c.setStartValue(-4.0)
        sy_2c.setEndValue(0.0)
        sy_2c.setEasingCurve(QEasingCurve.Type.OutQuad)
        p2c.addAnimation(sy_2c)

        st_2c = QPropertyAnimation(self, b"bodyTilt")
        st_2c.setDuration(440)
        st_2c.setStartValue(10.0)
        st_2c.setEndValue(0.0)
        st_2c.setEasingCurve(QEasingCurve.Type.OutQuad)
        p2c.addAnimation(st_2c)

        seq.addAnimation(p2c)

        # ---------------------------------------------------------------------
        # Phase 3: Victory Pose & Comic Celebration Sparkles (850ms)
        # Triumphant vertical bounce with radiating golden and ruby sparkles
        # ---------------------------------------------------------------------
        p3 = QParallelAnimationGroup(seq)
        
        sy_3 = QPropertyAnimation(self, b"swingY")
        sy_3.setDuration(850)
        sy_3.setStartValue(0.0)
        sy_3.setKeyValueAt(0.3, -15.0)
        sy_3.setKeyValueAt(0.7, 3.0)
        sy_3.setEndValue(0.0)
        sy_3.setEasingCurve(QEasingCurve.Type.OutBack)
        p3.addAnimation(sy_3)

        sc_3 = QPropertyAnimation(self, b"celebrationProgress")
        sc_3.setDuration(850)
        sc_3.setStartValue(0.0)
        sc_3.setKeyValueAt(0.5, 1.0)
        sc_3.setEndValue(1.0)
        sc_3.setEasingCurve(QEasingCurve.Type.OutCubic)
        p3.addAnimation(sc_3)

        seq.addAnimation(p3)

        # ---------------------------------------------------------------------
        # Phase 4: Smooth Recovery to Neutral Resting Position (350ms)
        # ---------------------------------------------------------------------
        p4 = QParallelAnimationGroup(seq)

        sx_4 = QPropertyAnimation(self, b"swingX")
        sx_4.setDuration(350)
        sx_4.setEndValue(0.0)
        sx_4.setEasingCurve(QEasingCurve.Type.InOutSine)
        p4.addAnimation(sx_4)

        sy_4 = QPropertyAnimation(self, b"swingY")
        sy_4.setDuration(350)
        sy_4.setEndValue(0.0)
        sy_4.setEasingCurve(QEasingCurve.Type.InOutSine)
        p4.addAnimation(sy_4)

        sa_4 = QPropertyAnimation(self, b"swingAngle")
        sa_4.setDuration(350)
        sa_4.setEndValue(0.0)
        sa_4.setEasingCurve(QEasingCurve.Type.InOutSine)
        p4.addAnimation(sa_4)

        st_4 = QPropertyAnimation(self, b"bodyTilt")
        st_4.setDuration(350)
        st_4.setEndValue(0.0)
        st_4.setEasingCurve(QEasingCurve.Type.InOutSine)
        p4.addAnimation(st_4)

        sc_4 = QPropertyAnimation(self, b"celebrationProgress")
        sc_4.setDuration(350)
        sc_4.setEndValue(0.0)
        sc_4.setEasingCurve(QEasingCurve.Type.InQuad)
        p4.addAnimation(sc_4)

        seq.addAnimation(p4)

        def on_yes_sequence_done():
            self._reset_properties_to_resting()
            self._state = self.STATE_IDLE
            self._base_state = self.STATE_IDLE
            self.animationFinished.emit()
            if self._animation_enabled and self._idle_group:
                self._idle_group.start()

        seq.finished.connect(on_yes_sequence_done)
        self._active_sequence = seq
        seq.start()

    # -------------------------------------------------------------------------
    # Cinematic NO Sequence: Slump Sag -> Sad Sway -> Spring Recovery
    # -------------------------------------------------------------------------

    def play_no_sequence(self):
        """
        Executes a 3-phase comedic disappointment sequence:
          Phase 1: Slump sag down under gravity, head slump, sweat drop (550ms)
          Phase 2: Sluggish sad sigh sway (1250ms)
          Phase 3: Smooth spring recovery back to neutral resting state (450ms)
        """
        self._stop_active_sequence()
        if self._idle_group:
            self._idle_group.stop()

        self._state = self.STATE_DISAPPOINTED
        self._base_state = self.STATE_DISAPPOINTED

        seq = QSequentialAnimationGroup(self)

        # Phase 1: Disappointment Sag
        p1 = QParallelAnimationGroup(seq)
        
        sy_1 = QPropertyAnimation(self, b"swingY")
        sy_1.setDuration(550)
        sy_1.setStartValue(self._swing_y)
        sy_1.setEndValue(18.0)
        sy_1.setEasingCurve(QEasingCurve.Type.OutQuad)
        p1.addAnimation(sy_1)

        st_1 = QPropertyAnimation(self, b"bodyTilt")
        st_1.setDuration(550)
        st_1.setStartValue(self._body_tilt)
        st_1.setEndValue(-6.0)
        st_1.setEasingCurve(QEasingCurve.Type.OutQuad)
        p1.addAnimation(st_1)

        sd_1 = QPropertyAnimation(self, b"disappointmentProgress")
        sd_1.setDuration(550)
        sd_1.setStartValue(0.0)
        sd_1.setEndValue(1.0)
        sd_1.setEasingCurve(QEasingCurve.Type.OutQuad)
        p1.addAnimation(sd_1)

        seq.addAnimation(p1)

        # Phase 2: Sad Heavy Sway
        p2 = QParallelAnimationGroup(seq)
        
        sa_2 = QPropertyAnimation(self, b"swingAngle")
        sa_2.setDuration(1250)
        sa_2.setStartValue(0.0)
        sa_2.setKeyValueAt(0.25, -4.5)
        sa_2.setKeyValueAt(0.75, 4.0)
        sa_2.setEndValue(0.0)
        sa_2.setEasingCurve(QEasingCurve.Type.InOutSine)
        p2.addAnimation(sa_2)

        seq.addAnimation(p2)

        # Phase 3: Smooth Spring Recovery
        p3 = QParallelAnimationGroup(seq)
        
        sy_3 = QPropertyAnimation(self, b"swingY")
        sy_3.setDuration(450)
        sy_3.setEndValue(0.0)
        sy_3.setEasingCurve(QEasingCurve.Type.OutBack)
        p3.addAnimation(sy_3)

        st_3 = QPropertyAnimation(self, b"bodyTilt")
        st_3.setDuration(450)
        st_3.setEndValue(0.0)
        st_3.setEasingCurve(QEasingCurve.Type.OutQuad)
        p3.addAnimation(st_3)

        sd_3 = QPropertyAnimation(self, b"disappointmentProgress")
        sd_3.setDuration(450)
        sd_3.setEndValue(0.0)
        sd_3.setEasingCurve(QEasingCurve.Type.InQuad)
        p3.addAnimation(sd_3)

        seq.addAnimation(p3)

        def on_no_sequence_done():
            self._reset_properties_to_resting()
            self._state = self.STATE_IDLE
            self._base_state = self.STATE_IDLE
            self.animationFinished.emit()
            if self._animation_enabled and self._idle_group:
                self._idle_group.start()

        seq.finished.connect(on_no_sequence_done)
        self._active_sequence = seq
        seq.start()

    def reset_to_idle(self):
        """Immediately and smoothly returns character to idle state."""
        self._stop_active_sequence()
        self._reset_properties_to_resting()
        self._state = self.STATE_IDLE
        self._base_state = self.STATE_IDLE
        if self._animation_enabled and self._idle_group:
            self._idle_group.start()

    # -------------------------------------------------------------------------
    # Mouse Interaction Handlers
    # -------------------------------------------------------------------------

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
            clamped_x = max(-25.0, min(25.0, delta.x() * 0.5))
            clamped_y = max(-5.0, min(55.0, delta.y() * 0.5))
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

    # -------------------------------------------------------------------------
    # Rendering & Visual Synthesis
    # -------------------------------------------------------------------------

    def _get_char_rect(self) -> QRectF:
        """Calculates base bounding box centered horizontally inside canvas."""
        char_w = 175.0 * self._character_scale
        char_h = 245.0 * self._character_scale
        char_x = (self.width() - char_w) / 2.0
        char_y = 0.0
        return QRectF(char_x, char_y, char_w, char_h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        anchor_x = self.width() / 2.0
        anchor_y = 0.0

        char_rect = self._get_char_rect()

        # Dynamic hand grip point where Spidey holds the web strand
        total_dx = self._swing_x + self._pull_offset.x()
        total_dy = self._swing_y + self._pull_offset.y()
        hand_x = anchor_x + total_dx
        hand_y = anchor_y + 45.0 + total_dy

        # 1. Draw Dynamic Silk Web Strand with Realistic Catenary Arc
        self._paint_web_strand(painter, anchor_x, anchor_y, hand_x, hand_y, total_dx)

        # 2. Draw Comic Speed Action Lines during high-velocity swing
        if abs(self._swing_angle) > 12.0 or abs(self._swing_x) > 16.0:
            self._paint_action_lines(painter, char_rect, anchor_x, total_dx, total_dy)

        # 3. Apply Multi-Axis Transformations around Hand Pivot
        painter.save()
        painter.translate(anchor_x + total_dx, anchor_y + total_dy)
        painter.rotate(self._swing_angle + self._body_tilt)
        painter.translate(-anchor_x, -anchor_y)

        # 4. Render Photorealistic AAA 3D Character
        if self._pixmap_3d and not self._pixmap_3d.isNull():
            painter.drawPixmap(char_rect.toRect(), self._pixmap_3d)
        else:
            renderer = self._renderers.get(self._state) or self._renderers.get(self.STATE_IDLE)
            if renderer and renderer.isValid():
                renderer.render(painter, char_rect)

        # 5. Overlays (Hover Spider-Sense)
        if self._state == self.STATE_HOVER:
            self._paint_hover_overlay(painter, char_rect)

        painter.restore()

        # 6. Global Canvas Overlays: Victory Celebration Bursts & Disappointment Sweat
        if self._celebration_progress > 0.01:
            self._paint_victory_bursts(painter, char_rect, hand_x, hand_y)
        elif self._disappointment_progress > 0.01:
            self._paint_disappointment_overlay(painter, char_rect, total_dx, total_dy)

    def _paint_web_strand(self, painter: QPainter, ax: float, ay: float, hx: float, hy: float, dx: float):
        """Renders silk web strand with glowing tension sheath and catenary curve."""
        path = QPainterPath()
        path.moveTo(ax, ay)
        # Physics curve: slight parabolic flex based on horizontal displacement
        ctrl_x = (ax + hx) / 2.0 - (dx * 0.12)
        ctrl_y = (ay + hy) / 2.0
        path.quadTo(ctrl_x, ctrl_y, hx, hy)

        # Outer soft silk glow
        glow_pen = QPen(QColor(0, 240, 255, 65), 3.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.strokePath(path, glow_pen)

        # High-contrast crisp white core
        core_pen = QPen(QColor(255, 255, 255, 240), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.strokePath(path, core_pen)

    def _paint_action_lines(self, painter: QPainter, char_rect: QRectF, anchor_x: float, dx: float, dy: float):
        """Draws dynamic comic speed streaks in the wake of a wide swing."""
        painter.save()
        alpha = int(min(180, abs(self._swing_angle) * 7.5))
        pen = QPen(QColor(0, 240, 255, alpha), 1.8, Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        direction = 1.0 if self._swing_x > 0 else -1.0
        base_y = char_rect.top() + char_rect.height() * 0.45 + dy
        arc_cx = anchor_x + dx - (direction * 35.0)

        # Upper and lower speed arcs
        painter.drawArc(int(arc_cx - 20), int(base_y - 25), 40, 50, int(-direction * 20 * 16), 80 * 16)
        painter.drawArc(int(arc_cx - 30), int(base_y + 15), 60, 45, int(-direction * 30 * 16), 70 * 16)
        painter.restore()

    def _paint_hover_overlay(self, painter: QPainter, char_rect: QRectF):
        """Crimson spider-sense tingling aura around mask."""
        pen = QPen(QColor("#f43f5e"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        head_cx = char_rect.center().x()
        head_cy = char_rect.top() + char_rect.height() * 0.85
        painter.drawArc(int(head_cx - 40), int(head_cy - 30), 80, 60, 30 * 16, 120 * 16)
        painter.drawArc(int(head_cx - 48), int(head_cy - 36), 96, 72, 40 * 16, 100 * 16)

    def _paint_victory_bursts(self, painter: QPainter, char_rect: QRectF, hand_x: float, hand_y: float):
        """
        Renders explosive comic book celebration particles:
        Expanding golden stars, ruby energy sparkles, and luminous hydration water beads.
        """
        p = self._celebration_progress
        alpha = int(255 * (1.0 - (p * 0.35)))
        cx = char_rect.center().x()
        cy = char_rect.top() + char_rect.height() * 0.65

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Golden Star Sparkles (Expanding outward)
        gold_color = QColor(251, 191, 36, alpha)
        painter.setBrush(gold_color)
        painter.setPen(Qt.PenStyle.NoPen)

        # Top-right golden star
        r1 = 6.0 + (p * 5.0)
        d1 = 25.0 + (p * 35.0)
        self._draw_star(painter, cx + d1, cy - (d1 * 0.6), r1, rotation=p * 90.0)

        # Bottom-left golden star
        r2 = 5.0 + (p * 4.0)
        d2 = 20.0 + (p * 30.0)
        self._draw_star(painter, cx - (d2 * 1.1), cy + (d2 * 0.5), r2, rotation=-p * 75.0)

        # 2. Ruby Comic Energy Bursts
        ruby_color = QColor(244, 63, 94, alpha)
        painter.setBrush(ruby_color)
        d3 = 30.0 + (p * 40.0)
        self._draw_star(painter, cx - (d3 * 0.9), cy - (d3 * 0.7), 5.5 + (p * 3.0), rotation=p * 45.0)

        # 3. Glowing Hydration Cyan Droplets
        cyan_pen = QPen(QColor(0, 240, 255, alpha), 1.6)
        painter.setPen(cyan_pen)
        painter.setBrush(QColor(0, 240, 255, int(alpha * 0.6)))
        
        # Droplet 1
        drop1_x = cx + (d1 * 0.75)
        drop1_y = cy + (d1 * 0.8)
        painter.drawEllipse(QPointF(drop1_x, drop1_y), 3.5, 3.5)

        # Droplet 2
        drop2_x = cx - (d2 * 0.6)
        drop2_y = cy - (d2 * 1.1)
        painter.drawEllipse(QPointF(drop2_x, drop2_y), 3.0, 3.0)

        painter.restore()

    def _paint_disappointment_overlay(self, painter: QPainter, char_rect: QRectF, dx: float, dy: float):
        """Comedic anime-style sweat drop dripping near Spidey's head during slump."""
        p = self._disappointment_progress
        alpha = int(240 * p)
        cx = char_rect.left() + (char_rect.width() * 0.68) + dx
        cy = char_rect.top() + (char_rect.height() * 0.72) + dy + (p * 12.0)

        painter.save()
        painter.setPen(QPen(QColor(100, 180, 255, alpha), 1.2))
        painter.setBrush(QColor(148, 163, 184, alpha))

        # Teardrop path
        drop_path = QPainterPath()
        drop_path.moveTo(cx, cy - 8.0)
        drop_path.cubicTo(cx + 6.0, cy - 2.0, cx + 5.0, cy + 6.0, cx, cy + 6.0)
        drop_path.cubicTo(cx - 5.0, cy + 6.0, cx - 6.0, cy - 2.0, cx, cy - 8.0)
        painter.drawPath(drop_path)
        painter.restore()

    def _draw_star(self, painter: QPainter, cx: float, cy: float, r: float, rotation: float = 0.0):
        """Draws a crisp 4-pointed or 8-pointed comic star polygon with optional rotation."""
        painter.save()
        painter.translate(cx, cy)
        if rotation != 0.0:
            painter.rotate(rotation)

        inner = r * 0.28
        points = [
            QPointF(0, -r),
            QPointF(inner, -inner),
            QPointF(r, 0),
            QPointF(inner, inner),
            QPointF(0, r),
            QPointF(-inner, inner),
            QPointF(-r, 0),
            QPointF(-inner, -inner),
        ]
        painter.drawPolygon(points)
        painter.restore()


# Compatibility alias
CharacterWidget = SpideyWidget
