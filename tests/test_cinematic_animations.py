"""
Unit and integration tests for Spider-Man Water Buddy v2.0 Cinematic Animation System.
Verifies multi-property physics (swingAngle, swingX, swingY, bodyTilt, celebrationProgress),
4-phase YES sequence, 3-phase NO sequence, interruption safety, and exact resting recovery.
"""
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPixmap
import pytest

from src.character import SpideyWidget
from src.companion_window import CompanionWindow
from src.config import ConfigManager


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_spidey_properties(qapp):
    """Verifies that all Qt animation properties are properly exposed, typed, and reactive."""
    widget = SpideyWidget(width=260, height=325)

    widget.set_swing_angle(15.5)
    assert widget.get_swing_angle() == 15.5
    assert widget.swingAngle == 15.5

    widget.set_swing_x(-30.0)
    assert widget.get_swing_x() == -30.0
    assert widget.swingX == -30.0

    widget.set_swing_y(12.0)
    assert widget.get_swing_y() == 12.0
    assert widget.swingY == 12.0

    widget.set_body_tilt(-7.5)
    assert widget.get_body_tilt() == -7.5
    assert widget.bodyTilt == -7.5

    widget.set_celebration_progress(0.85)
    assert widget.get_celebration_progress() == 0.85
    assert widget.celebrationProgress == 0.85

    widget.set_disappointment_progress(0.70)
    assert widget.get_disappointment_progress() == 0.70
    assert widget.disappointmentProgress == 0.70

    widget.set_pull_offset(QPointF(10.0, 20.0))
    assert widget.get_pull_offset() == QPointF(10.0, 20.0)


def test_yes_sequence_execution_and_recovery(qapp):
    """Verifies that YES triggers the 4-phase sequence and safely recovers to exact (0, 0, 0) rest."""
    widget = SpideyWidget(width=260, height=325)
    widget.set_state(SpideyWidget.STATE_HAPPY)

    assert widget._state == SpideyWidget.STATE_HAPPY
    assert widget._active_sequence is not None
    assert widget._active_sequence.state() == widget._active_sequence.State.Running

    # Force reset to resting and confirm exact zero recovery
    widget.set_animation_enabled(False)
    widget.reset_to_idle()
    assert widget._state == SpideyWidget.STATE_IDLE
    assert widget.get_swing_angle() == 0.0
    assert widget.get_swing_x() == 0.0
    assert widget.get_swing_y() == 0.0
    assert widget.get_body_tilt() == 0.0
    assert widget.get_celebration_progress() == 0.0


def test_no_sequence_execution_and_recovery(qapp):
    """Verifies that NO triggers slump sag and recovers to exact (0, 0, 0) rest."""
    widget = SpideyWidget(width=260, height=325)
    widget.set_state(SpideyWidget.STATE_DISAPPOINTED)

    assert widget._state == SpideyWidget.STATE_DISAPPOINTED
    assert widget._active_sequence is not None
    assert widget._active_sequence.state() == widget._active_sequence.State.Running

    # Reset to resting and verify zero resting state
    widget.set_animation_enabled(False)
    widget.reset_to_idle()
    assert widget._state == SpideyWidget.STATE_IDLE
    assert widget.get_swing_angle() == 0.0
    assert widget.get_swing_x() == 0.0
    assert widget.get_swing_y() == 0.0
    assert widget.get_body_tilt() == 0.0
    assert widget.get_disappointment_progress() == 0.0


def test_rapid_clicks_interruption_safety(qapp):
    """Verifies that rapid state toggling does not raise exceptions, crash, or freeze animation."""
    widget = SpideyWidget(width=260, height=325)

    for _ in range(10):
        widget.set_state(SpideyWidget.STATE_HAPPY)
        widget.set_state(SpideyWidget.STATE_DISAPPOINTED)
        widget.set_state(SpideyWidget.STATE_IDLE)
        widget.set_state(SpideyWidget.STATE_HAPPY)

    assert widget._state == SpideyWidget.STATE_HAPPY
    widget.reset_to_idle()
    assert widget._state == SpideyWidget.STATE_IDLE


def test_paint_event_during_wide_swing_and_celebration(qapp):
    """Simulates rendering during extreme swing coordinates and celebration burst without error."""
    widget = SpideyWidget(width=260, height=325)
    widget.show()

    # Extreme swing coordinates
    widget.set_swing_angle(24.0)
    widget.set_swing_x(38.0)
    widget.set_swing_y(-8.0)
    widget.set_body_tilt(10.0)
    widget.set_celebration_progress(0.9)
    widget.repaint()

    # Extreme disappointment slump coordinates
    widget.set_celebration_progress(0.0)
    widget.set_swing_angle(-4.5)
    widget.set_swing_x(0.0)
    widget.set_swing_y(18.0)
    widget.set_body_tilt(-6.0)
    widget.set_disappointment_progress(1.0)
    widget.repaint()

    widget.hide()


def test_companion_yes_and_no_click_triggers(qapp):
    """Verifies that CompanionWindow YES and NO button clicks trigger the proper animation states."""
    companion = CompanionWindow(ConfigManager())
    companion.show()
    companion.reset_card_ui()

    # Click YES
    companion.btn_yes.click()
    assert companion.spidey._state == SpideyWidget.STATE_HAPPY
    assert companion._auto_close_timer.isActive()
    assert companion._auto_close_timer.interval() == 3200

    # Reset and click NO
    companion.reset_card_ui()
    assert companion.spidey._state == SpideyWidget.STATE_IDLE

    companion.btn_no.click()
    assert companion.spidey._state == SpideyWidget.STATE_DISAPPOINTED
    assert companion.snooze_widget.isVisible()
    assert not companion.action_widget.isVisible()
    companion.hide()
