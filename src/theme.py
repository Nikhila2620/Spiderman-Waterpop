"""
Design Tokens and Centralized QSS Theme Engine for Spider-Man Water Buddy.
Implements Tailwind-inspired design tokens adapted specifically for Qt/PySide6.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    # Background Colors
    BG_BASE: str = "#0b0914"       # Deepest midnight canvas
    BG_SURFACE: str = "#130f24"    # Primary window & tab surface
    BG_CARD: str = "#1c1633"       # Raised card & container background
    BG_CARD_HOVER: str = "#241d40" # Hover state on cards
    BG_INPUT: str = "#18132c"      # Inputs, text edits, dropdowns
    BG_OVERLAY: str = "rgba(18, 14, 34, 0.96)"  # Companion floating card

    # Brand & Accent Colors
    ACCENT_RED: str = "#e11d48"    # Spidey crimson red
    ACCENT_RED_HOVER: str = "#f43f5e"
    ACCENT_RED_ACTIVE: str = "#be123c"
    ACCENT_BLUE: str = "#0284c7"   # Web-slinger electric cyan/blue
    ACCENT_BLUE_HOVER: str = "#38bdf8"
    ACCENT_BLUE_ACTIVE: str = "#0369a1"

    # Status Colors
    STATUS_SUCCESS: str = "#34d399" # Hydrated green
    STATUS_WARNING: str = "#facc15" # Snooze amber
    STATUS_ERROR: str = "#f87171"   # Missed/Declined red
    STATUS_INFO: str = "#38bdf8"    # Info cyan

    # Text Colors
    TEXT_PRIMARY: str = "#f8fafc"   # High contrast header and primary text
    TEXT_SECONDARY: str = "#cbd5e1" # Body text
    TEXT_MUTED: str = "#94a3b8"     # Subtitles, captions, hints
    TEXT_SUBTLE: str = "#64748b"    # Disabled or placeholder text

    # Borders & Dividers
    BORDER_DEFAULT: str = "#2d2448" # Subtle structural border
    BORDER_SUBTLE: str = "#221b38"  # Card dividers
    BORDER_FOCUS: str = "#38bdf8"   # Input focus halo
    BORDER_RED: str = "#f43f5e"     # Accent highlight border

    # Radii
    RADIUS_SM: str = "6px"
    RADIUS_MD: str = "8px"
    RADIUS_LG: str = "12px"
    RADIUS_XL: str = "16px"

    # Typography
    FONT_FAMILY: str = "'Segoe UI', -apple-system, sans-serif"


# Global Tokens Instance
TOKENS = ThemeTokens()


def get_dashboard_qss() -> str:
    """Returns the master QSS stylesheet for the Dashboard and Settings window."""
    return f"""
        QWidget {{
            background-color: {TOKENS.BG_BASE};
            color: {TOKENS.TEXT_PRIMARY};
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QTabWidget::pane {{
            border: 1px solid {TOKENS.BORDER_DEFAULT};
            background-color: {TOKENS.BG_SURFACE};
            border-radius: {TOKENS.RADIUS_LG};
            top: -1px;
        }}
        QTabBar::tab {{
            background: {TOKENS.BG_BASE};
            color: {TOKENS.TEXT_MUTED};
            border: 1px solid {TOKENS.BORDER_DEFAULT};
            border-bottom: none;
            border-top-left-radius: {TOKENS.RADIUS_MD};
            border-top-right-radius: {TOKENS.RADIUS_MD};
            padding: 10px 18px;
            margin-right: 4px;
            font-weight: 700;
            font-size: 13px;
        }}
        QTabBar::tab:selected {{
            background: {TOKENS.BG_SURFACE};
            color: {TOKENS.ACCENT_BLUE_HOVER};
            border-color: {TOKENS.ACCENT_BLUE_HOVER};
        }}
        QTabBar::tab:hover {{
            color: {TOKENS.TEXT_PRIMARY};
            background: {TOKENS.BG_INPUT};
        }}
        QLineEdit, QSpinBox, QTimeEdit, QComboBox {{
            background-color: {TOKENS.BG_INPUT};
            color: {TOKENS.TEXT_PRIMARY};
            border: 1.5px solid {TOKENS.BORDER_DEFAULT};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 7px 11px;
            font-size: 13px;
        }}
        QLineEdit:focus, QSpinBox:focus, QTimeEdit:focus, QComboBox:focus {{
            border-color: {TOKENS.BORDER_FOCUS};
            background-color: {TOKENS.BG_CARD};
        }}
        QCheckBox {{
            color: {TOKENS.TEXT_SECONDARY};
            font-size: 13px;
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 17px;
            height: 17px;
            border: 1.5px solid {TOKENS.BORDER_DEFAULT};
            border-radius: 4px;
            background-color: {TOKENS.BG_INPUT};
        }}
        QCheckBox::indicator:checked {{
            background-color: {TOKENS.ACCENT_BLUE};
            border-color: {TOKENS.ACCENT_BLUE_HOVER};
        }}
        QPushButton {{
            font-weight: 700;
            border-radius: {TOKENS.RADIUS_MD};
            padding: 8px 16px;
            font-size: 12.5px;
        }}
        QProgressBar {{
            background-color: {TOKENS.BG_INPUT};
            border: 1px solid {TOKENS.BORDER_DEFAULT};
            border-radius: {TOKENS.RADIUS_MD};
            text-align: center;
            color: {TOKENS.TEXT_PRIMARY};
            font-weight: 700;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 {TOKENS.ACCENT_BLUE}, stop: 1 {TOKENS.ACCENT_BLUE_HOVER});
            border-radius: {TOKENS.RADIUS_SM};
        }}
        QScrollBar:vertical {{
            border: none;
            background: {TOKENS.BG_BASE};
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {TOKENS.BORDER_DEFAULT};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {TOKENS.ACCENT_BLUE_HOVER};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """


def get_companion_card_qss() -> str:
    """Returns the QSS stylesheet for the companion speech and action card."""
    return f"""
        #spideyCard {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(22, 17, 36, 0.96),
                stop: 1 rgba(13, 10, 22, 0.98)
            );
            border: 1.5px solid {TOKENS.ACCENT_RED};
            border-radius: {TOKENS.RADIUS_XL};
        }}
        QLabel {{
            color: {TOKENS.TEXT_PRIMARY};
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QPushButton {{
            font-family: {TOKENS.FONT_FAMILY};
            font-weight: 700;
            border-radius: {TOKENS.RADIUS_MD};
            padding: 7px 12px;
        }}
    """


def get_tray_menu_qss() -> str:
    """Returns the system tray context menu stylesheet."""
    return f"""
        QMenu {{
            background-color: {TOKENS.BG_CARD};
            color: {TOKENS.TEXT_PRIMARY};
            border: 1px solid {TOKENS.BORDER_FOCUS};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 6px;
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QMenu::item {{
            padding: 6px 18px;
            border-radius: {TOKENS.RADIUS_SM};
        }}
        QMenu::item:selected {{
            background-color: {TOKENS.ACCENT_BLUE};
            color: #ffffff;
        }}
        QMenu::separator {{
            height: 1px;
            background: {TOKENS.BORDER_DEFAULT};
            margin: 4px 8px;
        }}
    """


def get_dialog_qss() -> str:
    """Returns general modal dialog styling for wizard and installers."""
    return f"""
        QDialog {{
            background-color: {TOKENS.BG_BASE};
            color: {TOKENS.TEXT_PRIMARY};
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QLabel {{
            color: {TOKENS.TEXT_PRIMARY};
        }}
        QLineEdit, QSpinBox, QTimeEdit {{
            background-color: {TOKENS.BG_INPUT};
            color: {TOKENS.TEXT_PRIMARY};
            border: 1.5px solid {TOKENS.BORDER_DEFAULT};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 6px 10px;
            font-size: 13px;
        }}
        QLineEdit:focus, QSpinBox:focus, QTimeEdit:focus {{
            border-color: {TOKENS.BORDER_FOCUS};
        }}
        QRadioButton, QCheckBox {{
            color: {TOKENS.TEXT_SECONDARY};
            font-size: 13px;
            spacing: 8px;
        }}
        QPushButton {{
            font-weight: 700;
            border-radius: {TOKENS.RADIUS_MD};
            padding: 8px 16px;
            font-size: 13px;
        }}
        QProgressBar {{
            background-color: {TOKENS.BG_INPUT};
            border: 1px solid {TOKENS.BORDER_DEFAULT};
            border-radius: {TOKENS.RADIUS_MD};
            text-align: center;
            color: {TOKENS.TEXT_PRIMARY};
            font-weight: 700;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 {TOKENS.ACCENT_BLUE}, stop: 1 {TOKENS.ACCENT_BLUE_HOVER});
            border-radius: {TOKENS.RADIUS_SM};
        }}
    """
