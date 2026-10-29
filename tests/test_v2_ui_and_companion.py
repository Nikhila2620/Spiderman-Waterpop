import tempfile
from pathlib import Path
from datetime import date
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
import pytest

from src.config import ConfigManager
from src.reminder_engine import ReminderEngine
from src.dashboard_window import DashboardWindow
from src.companion_window import CompanionWindow
from src.character import SpideyWidget


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_companion_scale_and_offset_persistence(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.character_scale = 1.2
        cm.settings.corner_position = "top-right"
        cm.save()

        companion = CompanionWindow(cm)
        assert companion.spidey._character_scale == 1.2

        # Check drag release persists offset
        base_x, base_y = companion._get_base_corner_pos()
        companion.move(base_x - 50, base_y + 30)
        
        # Simulate drag release
        companion._drag_start_pos = QPoint(10, 10)
        class DummyEvent:
            pass
        companion.mouseReleaseEvent(DummyEvent())

        assert cm.settings.window_offset_x == -50
        assert cm.settings.window_offset_y == 30

        # Create another instance and verify offset was respected on reposition
        companion2 = CompanionWindow(cm)
        assert companion2.x() == base_x - 50
        assert companion2.y() == base_y + 30


def test_companion_clean_dismiss(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        companion = CompanionWindow(cm)

        companion.trigger_reminder_mode()
        assert companion.is_in_reminder_mode() is True

        dismissed_calls = []
        companion.dismissed.connect(lambda: dismissed_calls.append(True))
        companion.dismiss()

        assert companion.is_in_reminder_mode() is False
        assert len(dismissed_calls) == 1
        assert not companion._auto_close_timer.isActive()


def test_dashboard_hero_drink_and_chips(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.today_intake_ml = 0
        cm.settings.daily_hydration_goal_ml = 2000
        cm.settings.last_tracking_date = date.today().isoformat()
        cm.save()

        engine = ReminderEngine(cm)
        dash = DashboardWindow(cm, engine)

        assert dash.btn_hero_drink.isEnabled()
        assert "250 ml" in dash.btn_hero_drink.text()

        # Select 500 ml chip
        dash._select_amount(500)
        assert dash._selected_amount == 500
        assert "500 ml" in dash.btn_hero_drink.text()

        # Click hero drink button
        dash.btn_hero_drink.click()

        # Check intake updated
        assert cm.settings.today_intake_ml == 500
        assert dash.reservoir_widget.current_ml == 500

        # Cooldown should now be active
        assert not dash.btn_hero_drink.isEnabled()
        assert "Next log in" in dash.btn_hero_drink.text()
        assert "Cooldown active" in dash.lbl_cooldown_status.text()


def test_cinematic_splash_and_logo_overlay(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        engine = ReminderEngine(cm)
        dash = DashboardWindow(cm, engine)

        assert hasattr(dash, "splash_overlay")
        assert dash.splash_overlay is not None

        # Trigger cinematic intro animation
        dash._play_cinematic_intro()
        assert not dash.splash_overlay.isHidden()
        assert dash.splash_overlay.get_anim_progress() >= 0.0

        # Advance / finish splash
        dash.splash_overlay.set_anim_progress(1.0)
        dash.splash_overlay._on_animation_finished()
        assert dash.splash_overlay.isHidden()


def test_spidey_wide_unclipped_canvas_and_tilt(qapp):
    """Verifies that Spidey has a wide 460px unconstrained canvas preventing edge clipping."""
    spidey = SpideyWidget(width=460, height=420)
    assert spidey.width() >= 460
    assert spidey.height() >= 420

    # Test extreme left drag: clamped_x = -75.0, pull_angle & tilt
    class DummyPos:
        def __init__(self, x, y):
            self._x = x
            self._y = y
        def x(self): return self._x
        def y(self): return self._y
        def __sub__(self, other):
            return DummyPos(self._x - other._x, self._y - other._y)

    class DummyMoveEvent:
        def position(self): return DummyPos(10, 80)
        def accept(self): pass

    spidey._is_pulling = True
    spidey._drag_start = DummyPos(150, 0)
    spidey.mouseMoveEvent(DummyMoveEvent())

    assert spidey._pull_offset.x() == -75.0
    # Center anchor is 230px, char_w is 175px (half width = 87.5px)
    # Even with left offset -75px and tilt, Spidey's body is well within [0, 460]
    char_rect = spidey._get_char_rect()
    assert char_rect.left() == (460 - 175.0) / 2.0  # 142.5px base margin


def test_dashboard_reminder_protocol_hero_card(qapp):
    """Verifies the restored v1.0.0 Reminder Protocol Hero card with scheduled trigger time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        cm = ConfigManager(custom_path=config_path)
        cm.settings.reminder_interval_minutes = 30
        cm.save()

        engine = ReminderEngine(cm)
        dash = DashboardWindow(cm, engine)

        assert hasattr(dash, "lbl_next_time")
        assert hasattr(dash, "lbl_companion_status")
        assert hasattr(dash, "quick_combo_interval")

        # Simulate timer tick at 1200 seconds (20 mins remaining)
        dash._on_timer_tick(1200)
        assert "20:00" in dash.lbl_countdown.text()
        assert "Scheduled Trigger:" in dash.lbl_next_time.text()
        assert "ACTIVE" in dash.lbl_companion_status.text()


def test_solid_obsidian_theme_zero_glassmorphism():
    """Verifies all theme tokens are opaque solid hex colors with no translucent glassmorphism."""
    from src.theme import TOKENS, get_companion_card_qss, get_dashboard_qss

    assert TOKENS.BG_BASE == "#111317"
    assert TOKENS.BG_CARD == "#181B22"
    assert TOKENS.BORDER_DEFAULT == "#2D333D"
    assert "rgba" not in TOKENS.BG_BASE
    assert "rgba" not in TOKENS.BG_CARD
    assert "rgba" not in TOKENS.BORDER_DEFAULT

    comp_qss = get_companion_card_qss()
    assert "rgba" not in comp_qss
    assert "#fffef6" in comp_qss
