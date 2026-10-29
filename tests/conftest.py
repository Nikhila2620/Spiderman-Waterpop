"""Global test configuration and fixtures for PySide6."""
import os

# Ensure headless execution in CI / automated test environments
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
