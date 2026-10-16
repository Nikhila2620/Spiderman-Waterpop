"""
Tests for reusable glass components: GlassCard and GlassToggleSwitch.
"""
from PySide6.QtWidgets import QApplication
import pytest

from src.components.glass_card import GlassCard
from src.components.toggle_switch import GlassToggleSwitch


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_glass_card_creation(qapp):
    card = GlassCard(title="Hydration Settings", subtitle="Configure water reminders")
    assert card.title == "Hydration Settings"
    assert card.subtitle == "Configure water reminders"
    assert card.content_layout is not None


def test_glass_toggle_switch(qapp):
    switch = GlassToggleSwitch(checked=False)
    assert switch.isChecked() is False

    signals = []
    switch.toggled.connect(lambda val: signals.append(val))

    switch.setChecked(True)
    assert switch.isChecked() is True
    assert len(signals) == 1
    assert signals[0] is True
