"""
Performance and Resource Profiler for Spider-Man Water Buddy.
Measures real memory footprint (RSS/Working Set), Idle CPU, and Active Animation CPU.
"""
import os
import sys
import time
import psutil
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.app import SpiderManWaterBuddyApp


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def profile_application():
    process = psutil.Process(os.getpid())
    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    print("==================================================")
    print(" [PERFORMANCE & RESOURCE BENCHMARK SUITE]")
    print("==================================================")

    controller = SpiderManWaterBuddyApp(app)
    # Ensure first run completed for test
    controller.settings.first_run_completed = True
    controller.show_companion()

    mem_startup_mb = process.memory_info().rss / (1024 * 1024)
    print(f"[METRIC] Memory at startup: {mem_startup_mb:.2f} MB")

    measurements = {
        "idle_cpu": [],
        "active_cpu": [],
        "peak_mem_mb": mem_startup_mb,
    }

    # Step 1: Measure idle CPU for 3 seconds
    def measure_idle(seconds_left):
        if seconds_left > 0:
            cpu = process.cpu_percent(interval=0.5)
            measurements["idle_cpu"].append(cpu)
            mem = process.memory_info().rss / (1024 * 1024)
            measurements["peak_mem_mb"] = max(measurements["peak_mem_mb"], mem)
            QTimer.singleShot(100, lambda: measure_idle(seconds_left - 1))
        else:
            print("[INFO] Idle measurement finished. Starting active animation benchmark...")
            # Trigger active celebration animation & pendulum
            controller.companion.spidey.set_state("happy")
            measure_active(6)

    # Step 2: Measure active animation CPU for 3 seconds
    def measure_active(seconds_left):
        if seconds_left > 0:
            cpu = process.cpu_percent(interval=0.5)
            measurements["active_cpu"].append(cpu)
            mem = process.memory_info().rss / (1024 * 1024)
            measurements["peak_mem_mb"] = max(measurements["peak_mem_mb"], mem)
            QTimer.singleShot(100, lambda: measure_active(seconds_left - 1))
        else:
            finish_profiling()

    def finish_profiling():
        mem_final_mb = process.memory_info().rss / (1024 * 1024)
        avg_idle_cpu = sum(measurements["idle_cpu"]) / max(1, len(measurements["idle_cpu"]))
        avg_active_cpu = sum(measurements["active_cpu"]) / max(1, len(measurements["active_cpu"]))

        print("\n---------------- RESULTS ----------------")
        print(f"Startup Memory:       {mem_startup_mb:.2f} MB")
        print(f"Peak Working Set:     {measurements['peak_mem_mb']:.2f} MB")
        print(f"Final Memory:         {mem_final_mb:.2f} MB")
        print(f"Average Idle CPU:     {avg_idle_cpu:.2f}%")
        print(f"Active Animation CPU: {avg_active_cpu:.2f}%")
        print("-----------------------------------------")
        print("Performance profile complete. [OK]\n")

        controller.exit_app()

    # Start idle measurement after 1 second warm-up
    QTimer.singleShot(1000, lambda: measure_idle(6))
    app.exec()


if __name__ == "__main__":
    profile_application()
