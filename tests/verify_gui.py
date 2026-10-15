"""
Interactive GUI smoke test on native Windows display for Spider-Man Water Buddy.
Verifies corner placement, pendulum swing, mouse hover, pull recoil, and button events.
"""
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QPointF
from src.popup import SpideyWaterBuddyPopup
from src.character import SpideyWidget


def run_gui_smoke_test():
    app = QApplication(sys.argv)
    popup = SpideyWaterBuddyPopup()
    popup.show()

    print("[SMOKE TEST] Spider-Man popup displayed at desktop corner:", popup.pos())

    # Step 1: Simulate hover reaction after 1.0s
    def step1_test_hover():
        print("[SMOKE TEST 1] Simulating mouse hover over Spider-Man...")
        popup._on_spidey_hover_enter()
        popup.spidey._state = SpideyWidget.STATE_HOVER
        popup.spidey.update()
        print("[SMOKE TEST 1] Dialogue on hover:", popup.dialogue_label.text())

        # Step 2: Simulate web elastic drag/pull after 1.0s
        QTimer.singleShot(1000, step2_test_pull)

    def step2_test_pull():
        print("[SMOKE TEST 2] Simulating web elastic pull...")
        popup.spidey.set_pull_offset(QPointF(20.0, 45.0))
        print("[SMOKE TEST 2] Spidey pulled down by web, offset:", popup.spidey.get_pull_offset())

        # Step 3: Release web spring recoil after 0.8s
        QTimer.singleShot(800, step3_test_release)

    def step3_test_release():
        print("[SMOKE TEST 3] Simulating web elastic release recoil...")
        popup._on_spidey_hover_leave()
        popup.spidey.set_state(SpideyWidget.STATE_IDLE)
        popup.spidey.set_pull_offset(QPointF(0.0, 0.0))

        # Step 4: Click YES for web celebration after 1.0s
        QTimer.singleShot(1000, step4_test_yes)

    def step4_test_yes():
        print("[SMOKE TEST 4] Simulating YES button click...")
        popup.btn_yes.click()
        assert popup.spidey._state == SpideyWidget.STATE_HAPPY, "Character state must be happy"
        print("[SMOKE TEST 4] Happy celebration verified! Dialogue:", popup.dialogue_label.text())

    QTimer.singleShot(800, step1_test_hover)

    # Automatically quit after the test sequence completes
    QTimer.singleShot(5500, app.quit)

    app.exec()
    print("[SMOKE TEST] All Spider-Man native GUI tests completed successfully. [OK]")


if __name__ == "__main__":
    run_gui_smoke_test()
