"""
Automated unit verification for Spider-Man Water Buddy.
Runs in offscreen mode (QT_QPA_PLATFORM=offscreen).
"""
import os
import sys

# Ensure offscreen rendering for headless test execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPointF
from src.character import SpideyWidget
from src.popup import SpideyWaterBuddyPopup


def test_spidey_water_buddy():
    app = QApplication.instance() or QApplication(sys.argv)

    # 1. Test SpideyWidget initialization
    spidey = SpideyWidget()
    assert spidey._state == SpideyWidget.STATE_IDLE, "Default state should be IDLE"
    assert len(spidey._renderers) == 4, f"Expected 4 SVG renderers, got {len(spidey._renderers)}"

    # 2. Test SpideyWidget state transitions & animations
    spidey.set_state(SpideyWidget.STATE_HAPPY)
    assert spidey._state == SpideyWidget.STATE_HAPPY, "State should be HAPPY"

    spidey.set_state(SpideyWidget.STATE_DISAPPOINTED)
    assert spidey._state == SpideyWidget.STATE_DISAPPOINTED, "State should be DISAPPOINTED"

    # Test pendulum angle and elastic pull offset properties
    spidey.set_swing_angle(3.5)
    assert spidey.get_swing_angle() == 3.5, "Swing angle property should update"

    spidey.set_pull_offset(QPointF(10.0, 25.0))
    assert spidey.get_pull_offset() == QPointF(10.0, 25.0), "Pull offset should update"

    # 3. Test SpideyWaterBuddyPopup construction & properties
    popup = SpideyWaterBuddyPopup()
    popup.show()
    flags = popup.windowFlags()
    assert bool(flags & Qt.WindowType.FramelessWindowHint), "FramelessWindowHint must be set"
    assert bool(flags & Qt.WindowType.WindowStaysOnTopHint), "WindowStaysOnTopHint must be set"
    assert popup.testAttribute(Qt.WA_TranslucentBackground), "WA_TranslucentBackground must be True"

    # 4. Test Hover reaction
    popup._on_spidey_hover_enter()
    assert "Spider-sense says" in popup.dialogue_label.text(), "Hover should show spider-sense greeting"
    popup._on_spidey_hover_leave()
    assert popup.dialogue_label.text() == popup.default_message, "Leave should restore default message"

    # 5. Test YES interaction
    yes_called = []
    popup.waterDrank.connect(lambda: yes_called.append(True))
    popup.btn_yes.click()
    assert len(yes_called) == 1, "waterDrank signal should be emitted on YES click"
    assert popup.spidey._state == SpideyWidget.STATE_HAPPY, "Spidey must switch to HAPPY"
    assert "Super hydrated" in popup.dialogue_label.text(), "Dialogue should confirm hydration"
    assert not popup.btn_yes.isEnabled(), "YES button should be disabled after click"
    assert popup._auto_close_timer.isActive(), "Auto-close timer should be active"

    # Reset popup
    popup.reset_popup()
    assert popup.spidey._state == SpideyWidget.STATE_IDLE, "Spidey must be reset to IDLE"
    assert popup.action_widget.isVisible(), "Action buttons should be visible after reset"
    assert not popup.snooze_widget.isVisible(), "Snooze widget should be hidden after reset"

    # 6. Test NO interaction & Snooze buttons
    popup.btn_no.click()
    assert popup.spidey._state == SpideyWidget.STATE_DISAPPOINTED, "Spidey must switch to DISAPPOINTED"
    assert not popup.action_widget.isVisible(), "Action buttons should be hidden after NO click"
    assert popup.snooze_widget.isVisible(), "Snooze widget should be revealed"
    assert len(popup.snooze_buttons) == 3, "There should be 3 snooze buttons (5m, 10m, 15m)"

    snooze_values = []
    popup.snoozeRequested.connect(lambda m: snooze_values.append(m))
    popup.snooze_buttons[0].click()  # 5 min snooze
    assert snooze_values == [5], "Snooze 5 min button should emit 5"
    assert "Snoozed for 5 min" in popup.dialogue_label.text(), "Dialogue should confirm snooze"

    print("ALL SPIDER-MAN WATER BUDDY UNIT TESTS PASSED SUCCESSFULLY! [OK]")


if __name__ == "__main__":
    test_spidey_water_buddy()
