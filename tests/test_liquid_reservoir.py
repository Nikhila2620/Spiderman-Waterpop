"""
Tests for LiquidReservoirWidget.
Verifies percentage calculation, wave animation phase, and timer lifecycle.
"""
from PySide6.QtWidgets import QApplication
import pytest

from src.components.liquid_reservoir import LiquidReservoirWidget


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_liquid_reservoir_values_and_percentage(qapp):
    reservoir = LiquidReservoirWidget()
    reservoir.set_values(current_ml=1000, goal_ml=2000)
    assert reservoir.current_ml == 1000
    assert reservoir.goal_ml == 2000
    assert reservoir.percentage == 50

    # Overfill caps at 100% or handles gracefully
    reservoir.set_values(current_ml=2500, goal_ml=2000)
    assert reservoir.percentage == 125
    assert reservoir.clamped_percentage == 100


def test_liquid_reservoir_animation_lifecycle(qapp):
    reservoir = LiquidReservoirWidget()
    reservoir.show()
    assert reservoir.is_animating is True

    # Wave phase advances
    phase1 = reservoir._phase
    reservoir._update_wave()
    phase2 = reservoir._phase
    assert phase2 > phase1

    reservoir.hide()
    assert reservoir.is_animating is False
