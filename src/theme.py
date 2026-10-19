"""
Design Tokens and Centralized QSS Theme Engine for Spider-Man Water Buddy.
Implements the Spider-Man Stark Tech / E.D.I.T.H. Tactical HUD interface.
Features pure pitch-black backdrops (#000000), crisp high-contrast laser-cut white lines (#ffffff),
glowing silver/cyan telemetry accents, and modern, ultra-clean typography.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    # Stark Tech / EDITH Pitch-Black & Tactical Obsidian Palette
    BG_BASE: str = "#000000"       # Pure Tactical Void Black
    BG_SURFACE: str = "#05070a"    # Deep Stark Obsidian Panel
    BG_CARD: str = "rgba(8, 12, 16, 0.95)"  # Crisp Stark Tactical Card
    BG_CARD_SOLID: str = "#080c10" # Solid Tactical Dark
    BG_CARD_HOVER: str = "rgba(16, 24, 34, 0.98)" # Hover HUD Surface
    BG_INPUT: str = "rgba(4, 6, 8, 0.95)"       # Deep Input Well
    BG_OVERLAY: str = "rgba(0, 0, 0, 0.95)"     # Companion overlay frosted glass

    # Stark HUD Laser Accents
    ACCENT_AQUA: str = "#ffffff"        # Stark Laser Crisp White
    ACCENT_AZURE: str = "#00f0ff"       # Holographic Cyan HUD Glow
    ACCENT_MINT: str = "#00f5a0"        # Target Lock Mint
    ACCENT_TEAL: str = "#5ce1e6"        # Telemetry Cyan

    # Character Brand Accents (Stark Armor Crimson & Gold)
    ACCENT_RED: str = "#ff2a4b"         # Stark Armor Crimson
    ACCENT_RED_HOVER: str = "#ff4d6a"   # Glowing Crimson Highlight
    ACCENT_RED_ACTIVE: str = "#d61b39"  # Deep Crimson Pressed
    ACCENT_RUBY: str = "#ff5577"        # Soft Ruby Highlight
    ACCENT_GOLD: str = "#ffb800"        # Stark Amber / Cooldown

    # Status Colors
    STATUS_SUCCESS: str = "#00f5a0"     # Calibrated Lock
    STATUS_WARNING: str = "#ffb800"     # Telemetry Warning
    STATUS_ERROR: str = "#ff2a4b"       # Stark Critical Alert
    STATUS_INFO: str = "#ffffff"        # System Info White

    # High-Contrast Modern Typography Colors
    TEXT_PRIMARY: str = "#ffffff"       # Crisp Stark White
    TEXT_SECONDARY: str = "#c2c8d0"     # Tactical Silver
    TEXT_MUTED: str = "#738090"         # Telemetry Muted Slate
    TEXT_SUBTLE: str = "#455060"        # Inactive / Placeholder

    # Laser-Cut HUD Borders & Dividers
    BORDER_GLASS: str = "rgba(255, 255, 255, 0.22)"       # Tactical HUD 1px Stroke
    BORDER_GLASS_ACTIVE: str = "rgba(255, 255, 255, 0.85)" # Active Laser-Cut Stroke
    BORDER_DEFAULT: str = "rgba(255, 255, 255, 0.22)"     # Default HUD Line
    BORDER_SUBTLE: str = "rgba(255, 255, 255, 0.10)"      # Subtle Division
    BORDER_FOCUS: str = "#ffffff"                         # Pure White Focus Ring
    BORDER_RED: str = "#ff2a4b"                           # Stark Red Alert Border

    # Radii (Sharp Tactical HUD Curves)
    RADIUS_SM: str = "4px"
    RADIUS_MD: str = "8px"
    RADIUS_LG: str = "12px"
    RADIUS_XL: str = "16px"
    RADIUS_PILL: str = "9999px"

    # Clean, Ultra-Modern High-Tech Typography (NO nested quotes for Qt parser)
    FONT_FAMILY: str = "Segoe UI, Arial, sans-serif"
    FONT_MONO: str = "Consolas, Segoe UI, monospace"


# Global Tokens Instance
TOKENS = ThemeTokens()


def get_dashboard_qss() -> str:
    """Returns master QSS stylesheet for Dashboard and Settings window with Stark Tech EDITH HUD styling."""
    return f"""
        QWidget#mainDashboard {{
            background-color: {TOKENS.BG_BASE};
            color: {TOKENS.TEXT_PRIMARY};
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QWidget {{
            color: {TOKENS.TEXT_PRIMARY};
            font-family: {TOKENS.FONT_FAMILY};
        }}
        /* Scroll Area Transparent Backgrounds */
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}
        /* Tab Widget (Fallback & Standard Tabs) */
        QTabWidget::pane {{
            border: 1px solid {TOKENS.BORDER_GLASS};
            background-color: {TOKENS.BG_CARD};
            border-radius: {TOKENS.RADIUS_MD};
            top: -1px;
        }}
        QTabBar::tab {{
            background: {TOKENS.BG_SURFACE};
            color: {TOKENS.TEXT_MUTED};
            border: 1px solid {TOKENS.BORDER_SUBTLE};
            border-bottom: none;
            border-top-left-radius: {TOKENS.RADIUS_SM};
            border-top-right-radius: {TOKENS.RADIUS_SM};
            padding: 8px 16px;
            margin-right: 4px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        QTabBar::tab:selected {{
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
            border: 1px solid {TOKENS.BORDER_GLASS_ACTIVE};
        }}
        /* Sidebar Navigation */
        QWidget#sidebarContainer {{
            background-color: {TOKENS.BG_SURFACE};
            border-right: 1px solid {TOKENS.BORDER_GLASS};
        }}
        QPushButton.navBtn {{
            background-color: transparent;
            color: {TOKENS.TEXT_SECONDARY};
            border: 1px solid transparent;
            border-radius: {TOKENS.RADIUS_SM};
            padding: 10px 14px;
            font-size: 12.5px;
            font-weight: 700;
            text-align: left;
            letter-spacing: 0.5px;
        }}
        QPushButton.navBtn:hover {{
            background-color: rgba(255, 255, 255, 0.08);
            color: #ffffff;
            border-color: rgba(255, 255, 255, 0.25);
        }}
        QPushButton.navBtn[selected="true"] {{
            background-color: rgba(255, 255, 255, 0.14);
            color: #ffffff;
            border: 1px solid #ffffff;
            font-weight: 800;
        }}
        /* Form Inputs */
        QLineEdit, QSpinBox, QTimeEdit, QComboBox {{
            background-color: {TOKENS.BG_INPUT};
            color: {TOKENS.TEXT_PRIMARY};
            border: 1.5px solid {TOKENS.BORDER_DEFAULT};
            border-radius: {TOKENS.RADIUS_SM};
            padding: 7px 11px;
            font-size: 13px;
            font-family: {TOKENS.FONT_MONO};
        }}
        QLineEdit:focus, QSpinBox:focus, QTimeEdit:focus, QComboBox:focus {{
            border: 1.5px solid #ffffff;
            background-color: #0c1219;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        /* Checkboxes */
        QCheckBox {{
            color: {TOKENS.TEXT_SECONDARY};
            font-size: 13px;
            spacing: 8px;
            font-weight: 600;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1.5px solid {TOKENS.BORDER_DEFAULT};
            border-radius: 4px;
            background-color: {TOKENS.BG_INPUT};
        }}
        QCheckBox::indicator:hover {{
            border-color: #ffffff;
        }}
        QCheckBox::indicator:checked {{
            background-color: #ffffff;
            border-color: #ffffff;
        }}
        /* Standard Action Buttons */
        QPushButton.primaryBtn {{
            background-color: #ffffff;
            color: #000000;
            font-weight: 800;
            border: 1px solid #ffffff;
            border-radius: {TOKENS.RADIUS_SM};
            padding: 9px 18px;
            font-size: 12.5px;
            letter-spacing: 0.5px;
        }}
        QPushButton.primaryBtn:hover {{
            background-color: #e2e8f0;
            border-color: #ffffff;
        }}
        QPushButton.primaryBtn:pressed {{
            background-color: #cbd5e1;
        }}
        QPushButton.heroDrinkBtn {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {TOKENS.ACCENT_RED},
                stop: 1 {TOKENS.ACCENT_RED_HOVER}
            );
            color: #ffffff;
            font-size: 14px;
            font-weight: 900;
            letter-spacing: 1px;
            border: 1.5px solid #ffffff;
            border-radius: {TOKENS.RADIUS_MD};
            padding: 12px 24px;
        }}
        QPushButton.heroDrinkBtn:hover {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {TOKENS.ACCENT_RED_HOVER},
                stop: 1 #ff6688
            );
            border-color: #00f0ff;
        }}
        QPushButton.heroDrinkBtn:pressed {{
            background-color: {TOKENS.ACCENT_RED_ACTIVE};
        }}
        QPushButton.heroDrinkBtn:disabled {{
            background-color: rgba(30, 36, 48, 0.7);
            color: {TOKENS.TEXT_MUTED};
            border: 1px solid rgba(255, 255, 255, 0.15);
        }}
        QPushButton.chipBtn {{
            background-color: #070a0e;
            color: {TOKENS.TEXT_SECONDARY};
            font-size: 12px;
            font-weight: 700;
            font-family: {TOKENS.FONT_MONO};
            border: 1px solid rgba(255, 255, 255, 0.20);
            border-radius: {TOKENS.RADIUS_SM};
            padding: 7px 14px;
        }}
        QPushButton.chipBtn:hover {{
            background-color: rgba(255, 255, 255, 0.10);
            color: #ffffff;
            border-color: #ffffff;
        }}
        QPushButton.chipBtn[selected="true"] {{
            background-color: rgba(255, 255, 255, 0.20);
            color: #ffffff;
            border: 1.5px solid #ffffff;
            font-weight: 800;
        }}
        QPushButton.secondaryBtn {{
            background-color: #070a0e;
            color: {TOKENS.TEXT_SECONDARY};
            font-weight: 700;
            border: 1px solid {TOKENS.BORDER_GLASS};
            border-radius: {TOKENS.RADIUS_SM};
            padding: 8px 16px;
            font-size: 12px;
        }}
        QPushButton.secondaryBtn:hover {{
            background-color: rgba(255, 255, 255, 0.08);
            color: #ffffff;
            border-color: #ffffff;
        }}
        /* Smooth Scrollbars */
        QScrollBar:vertical {{
            border: none;
            background: #000000;
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.25);
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #ffffff;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """


def get_companion_card_qss() -> str:
    """Returns the QSS stylesheet for the companion speech and action card with Stark Tech HUD aesthetic."""
    return f"""
        #spideyCard {{
            background-color: rgba(4, 6, 8, 0.96);
            border: 1.5px solid #ffffff;
            border-radius: {TOKENS.RADIUS_LG};
        }}
        QLabel {{
            color: {TOKENS.TEXT_PRIMARY};
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QPushButton {{
            font-family: {TOKENS.FONT_FAMILY};
            font-weight: 700;
            border-radius: {TOKENS.RADIUS_SM};
            padding: 7px 12px;
        }}
    """


def get_tray_menu_qss() -> str:
    """Returns the system tray context menu stylesheet with Stark Tech HUD aesthetic."""
    return f"""
        QMenu {{
            background-color: #05070a;
            color: {TOKENS.TEXT_PRIMARY};
            border: 1.5px solid #ffffff;
            border-radius: {TOKENS.RADIUS_SM};
            padding: 6px;
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QMenu::item {{
            padding: 7px 20px;
            border-radius: 4px;
            font-weight: 600;
        }}
        QMenu::item:selected {{
            background-color: #ffffff;
            color: #000000;
            font-weight: 800;
        }}
        QMenu::separator {{
            height: 1px;
            background: {TOKENS.BORDER_DEFAULT};
            margin: 4px 8px;
        }}
    """


def get_dialog_qss() -> str:
    """Returns modal dialog styling for wizard and setup in Stark Tech HUD style."""
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
            border-radius: {TOKENS.RADIUS_SM};
            padding: 6px 10px;
            font-size: 13px;
            font-family: {TOKENS.FONT_MONO};
        }}
        QLineEdit:focus, QSpinBox:focus, QTimeEdit:focus {{
            border-color: #ffffff;
        }}
        QRadioButton, QCheckBox {{
            color: {TOKENS.TEXT_SECONDARY};
            font-size: 13px;
            spacing: 8px;
            font-weight: 600;
        }}
        QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
            background-color: #ffffff;
            border: 1.5px solid #ffffff;
        }}
        QPushButton {{
            font-weight: 700;
            border-radius: {TOKENS.RADIUS_SM};
            padding: 8px 16px;
            font-size: 13px;
        }}
        QProgressBar {{
            background-color: {TOKENS.BG_INPUT};
            border: 1px solid {TOKENS.BORDER_DEFAULT};
            border-radius: {TOKENS.RADIUS_SM};
            text-align: center;
            color: {TOKENS.TEXT_PRIMARY};
            font-weight: 700;
            font-family: {TOKENS.FONT_MONO};
        }}
        QProgressBar::chunk {{
            background-color: #ffffff;
            border-radius: 2px;
        }}
    """
