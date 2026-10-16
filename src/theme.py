"""
Design Tokens and Centralized QSS Theme Engine for Spider-Man Water Buddy.
Implements an authentic Spider-Man Crimson Red & Midnight Obsidian aesthetic.
No unwanted blue accents — vibrant scarlet, ruby, and charcoal styling throughout.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    # Background Colors (Deep Midnight Obsidian)
    BG_BASE: str = "#0c0a12"       # Deepest canvas
    BG_SURFACE: str = "#140f1e"    # Window & tab surface
    BG_CARD: str = "#1c152a"       # Raised card & container background
    BG_CARD_HOVER: str = "#261d38" # Hover state on cards
    BG_INPUT: str = "#181224"      # Inputs, text edits, dropdowns
    BG_OVERLAY: str = "rgba(18, 14, 26, 0.97)"  # Companion floating card

    # Authentic Spider-Man Crimson & Ruby Accents
    ACCENT_RED: str = "#e11d48"        # Spidey vibrant crimson red
    ACCENT_RED_HOVER: str = "#f43f5e"  # Glowing scarlet
    ACCENT_RED_ACTIVE: str = "#be123c" # Deep crimson
    ACCENT_RUBY: str = "#fb7185"       # Soft ruby highlight
    ACCENT_GOLD: str = "#f59e0b"       # Web gold for reminders & alerts

    # Status Colors
    STATUS_SUCCESS: str = "#10b981" # Fresh hydrated emerald
    STATUS_WARNING: str = "#f59e0b" # Snooze web gold
    STATUS_ERROR: str = "#ef4444"   # Missed / declined red
    STATUS_INFO: str = "#f43f5e"    # Info crimson

    # Text Colors
    TEXT_PRIMARY: str = "#f8fafc"   # Crisp white for headings
    TEXT_SECONDARY: str = "#e2e8f0" # High-contrast light gray for body
    TEXT_MUTED: str = "#a1a1aa"     # Neutral muted gray
    TEXT_SUBTLE: str = "#71717a"    # Disabled or placeholder text

    # Borders & Dividers
    BORDER_DEFAULT: str = "#2e2136" # Structural border
    BORDER_SUBTLE: str = "#24182b"  # Card dividers
    BORDER_FOCUS: str = "#f43f5e"   # Red focus halo (NO BLUE)
    BORDER_RED: str = "#e11d48"     # Accent highlight border

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
            color: {TOKENS.ACCENT_RED_HOVER};
            border-color: {TOKENS.ACCENT_RED_HOVER};
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
            background-color: {TOKENS.ACCENT_RED};
            border-color: {TOKENS.ACCENT_RED_HOVER};
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
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 {TOKENS.ACCENT_RED_ACTIVE}, stop: 1 {TOKENS.ACCENT_RED_HOVER});
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
            background: {TOKENS.ACCENT_RED_HOVER};
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
                stop: 0 rgba(22, 16, 30, 0.97),
                stop: 1 rgba(14, 10, 18, 0.99)
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
            border: 1px solid {TOKENS.ACCENT_RED};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 6px;
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QMenu::item {{
            padding: 6px 18px;
            border-radius: {TOKENS.RADIUS_SM};
        }}
        QMenu::item:selected {{
            background-color: {TOKENS.ACCENT_RED};
            color: #ffffff;
        }}
        QMenu::separator {{
            height: 1px;
            background: {TOKENS.BORDER_DEFAULT};
            margin: 4px 8px;
        }}
    """


def get_dialog_qss() -> str:
    """Returns general modal dialog styling for wizard and installers with pure Crimson Red theme."""
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
        QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
            background-color: {TOKENS.ACCENT_RED};
            border: 1.5px solid {TOKENS.ACCENT_RED_HOVER};
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
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 {TOKENS.ACCENT_RED_ACTIVE}, stop: 1 {TOKENS.ACCENT_RED_HOVER});
            border-radius: {TOKENS.RADIUS_SM};
        }}
    """
