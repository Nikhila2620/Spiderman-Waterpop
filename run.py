"""
Spider-Man Water Buddy - Desktop App Launcher
"""
import sys
from PySide6.QtWidgets import QApplication
from src.popup import SpideyWaterBuddyPopup


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Spider-Man Water Buddy")

    # Instantiate the transparent Spider-Man popup hanging from desktop corner
    popup = SpideyWaterBuddyPopup()
    popup.show()

    # Log interaction events
    popup.waterDrank.connect(lambda: print("[EVENT] Hydration confirmed! (YES clicked)"))
    popup.snoozeRequested.connect(lambda m: print(f"[EVENT] Snooze requested for {m} minutes."))
    popup.dismissed.connect(lambda: print("[EVENT] Popup dismissed by user."))

    # Ensure UTF-8 console output on Windows if possible
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("==================================================")
    print(" 🕷️  SPIDER-MAN WATER BUDDY  🕸️")
    print(" Hanging in the top-right corner of your desktop!")
    print(" - Transparent background with glowing web strand.")
    print(" - Cozy pendulum swinging animation.")
    print(" - Mouse reactions: Hover to see Spidey perk up and wave,")
    print("   or click & pull him down to test elastic web recoil!")
    print(" - Click YES for web celebration, NO for snooze options.")
    print("==================================================")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
