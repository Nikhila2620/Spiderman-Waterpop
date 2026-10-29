"""Global test configuration and fixtures for PySide6."""
import os

# Ensure headless execution in CI / automated test environments
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Disable Chromium sandbox and GPU acceleration to prevent crashes in CI, Docker, or root environments
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--no-sandbox --disable-gpu --disable-software-rasterizer --disable-dev-shm-usage",
)
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
