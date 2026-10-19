"""
Windows Native Event Filter & Platform Integration for Spider-Man Water Buddy v2.0.
Implements:
1. True system-wide global hotkeys via RegisterHotKey (fixes MED-03/NEW-03)
2. Sleep / Hibernate / Resume detection via WM_POWERBROADCAST (fixes HIGH-01/Section 6 #2)
3. Named Mutex for race-free single-instance execution (fixes CRIT-05/NEW-06)
"""
import ctypes
from ctypes import wintypes
import logging
from typing import Optional, Callable

from PySide6.QtCore import QObject, QAbstractNativeEventFilter, Signal

logger = logging.getLogger("SpiderManWaterBuddy.WindowsNative")

# Windows API Constants
WM_HOTKEY = 0x0312
WM_POWERBROADCAST = 0x0218
PBT_APMRESUMEAUTOMATIC = 0x0012
PBT_APMRESUMESUSPEND = 0x0007

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

VK_W = 0x57
HOTKEY_ID_TOGGLE = 0x2099

ERROR_ALREADY_EXISTS = 183


class WindowsNativeEventFilter(QAbstractNativeEventFilter, QObject):
    """
    Catches system-wide Windows messages including global hotkeys and sleep/resume events.
    """

    hotkeyActivated = Signal(int)
    systemResumed = Signal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        QAbstractNativeEventFilter.__init__(self)
        self._user32 = ctypes.windll.user32
        self._registered_hotkeys = set()

    def register_global_hotkey(self, hotkey_id: int = HOTKEY_ID_TOGGLE, fs_modifiers: int = (MOD_CONTROL | MOD_ALT), vk: int = VK_W) -> bool:
        """Registers a system-wide hotkey that works across all applications."""
        try:
            # Try with MOD_NOREPEAT first, fallback if older Windows
            res = self._user32.RegisterHotKey(None, hotkey_id, fs_modifiers | MOD_NOREPEAT, vk)
            if not res:
                res = self._user32.RegisterHotKey(None, hotkey_id, fs_modifiers, vk)

            if res:
                self._registered_hotkeys.add(hotkey_id)
                logger.info(f"Global hotkey registered successfully (ID={hotkey_id}).")
                return True
            else:
                err = ctypes.GetLastError()
                logger.warning(f"Failed to register global hotkey (ID={hotkey_id}, win_err={err}).")
                return False
        except Exception as e:
            logger.error(f"Error registering global hotkey: {e}")
            return False

    def unregister_global_hotkey(self, hotkey_id: int = HOTKEY_ID_TOGGLE) -> None:
        """Unregisters the specified global hotkey."""
        try:
            if hotkey_id in self._registered_hotkeys:
                self._user32.UnregisterHotKey(None, hotkey_id)
                self._registered_hotkeys.discard(hotkey_id)
                logger.info(f"Unregistered global hotkey (ID={hotkey_id}).")
        except Exception as e:
            logger.warning(f"Error unregistering hotkey: {e}")

    def unregister_all(self) -> None:
        for hid in list(self._registered_hotkeys):
            self.unregister_global_hotkey(hid)

    def nativeEventFilter(self, eventType, message):
        """Processes Windows MSG structures."""
        if eventType == b"windows_generic_MSG" or eventType == "windows_generic_MSG":
            try:
                # MSG structure pointer
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == WM_HOTKEY:
                    hotkey_id = msg.wParam
                    logger.debug(f"WM_HOTKEY triggered: {hotkey_id}")
                    self.hotkeyActivated.emit(hotkey_id)
                    return True, 0
                elif msg.message == WM_POWERBROADCAST:
                    if msg.wParam in (PBT_APMRESUMEAUTOMATIC, PBT_APMRESUMESUSPEND):
                        logger.info("WM_POWERBROADCAST: System resumed from sleep/hibernate.")
                        self.systemResumed.emit()
            except Exception as e:
                logger.debug(f"Native event parse error: {e}")

        return False, 0


class NamedMutexGuard:
    """
    Enforces a strict Windows named mutex single-instance lock.
    """

    def __init__(self, mutex_name: str = "Local\\SpiderManWaterBuddy_SingleInstance_Mutex"):
        self.mutex_name = mutex_name
        self.handle = None
        self.already_running = False

    def acquire(self) -> bool:
        try:
            kernel32 = ctypes.windll.kernel32
            self.handle = kernel32.CreateMutexW(None, True, self.mutex_name)
            last_err = kernel32.GetLastError()
            if last_err == ERROR_ALREADY_EXISTS:
                self.already_running = True
                return False
            self.already_running = False
            return True
        except Exception as e:
            logger.error(f"Error creating named mutex {self.mutex_name}: {e}")
            return True

    def release(self):
        try:
            if self.handle:
                ctypes.windll.kernel32.ReleaseMutex(self.handle)
                ctypes.windll.kernel32.CloseHandle(self.handle)
                self.handle = None
        except Exception:
            pass
