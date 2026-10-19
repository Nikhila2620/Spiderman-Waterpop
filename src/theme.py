"""
Design Tokens and Centralized QSS Theme Engine for Spider-Man Water Buddy.
Implements a premium Aquatic Liquid Glass aesthetic inspired by liquidglassdesign.com.
Deep aquatic-indigo gradients (#07111E to #0C1A2E), translucent frosted glass surfaces,
subtle cyan refraction borders (rgba(0, 240, 255, 0.22)), and luminous Aqua & Mint accents.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    # Comic-Panel Night-City Palette
    BG_BASE: str = "#0b0e14"       # Obsidian Night
    BG_SURFACE: str = "#121824"    # Midnight Panel
    BG_CARD: str = "rgba(18, 24, 36, 0.88)"  # Translucent frosted midnight card
    BG_CARD_SOLID: str = "#121824" # Midnight Panel solid
    BG_CARD_HOVER: str = "rgba(25, 34, 52, 0.95)" # Hover midnight surface
    BG_INPUT: str = "rgba(11, 14, 20, 0.85)"       # Deep Obsidian input
    BG_OVERLAY: str = "rgba(11, 14, 20, 0.92)"     # Companion overlay frosted glass

    # Luminous Hero Accents
    ACCENT_AQUA: str = "#00d2ff"        # Web Fluid Blue
    ACCENT_AZURE: str = "#00a3ff"       # Deep electric blue
    ACCENT_MINT: str = "#00f5a0"        # Bio-Venom Cyan
    ACCENT_TEAL: str = "#00e0d0"        # Intermediate cyan gradient

    # Character Brand Accents (Crimson Spider Heritage)
    ACCENT_RED: str = "#ff3355"         # Crimson Spider
    ACCENT_RED_HOVER: str = "#ff5577"   # Glowing Crimson highlight
    ACCENT_RED_ACTIVE: str = "#e02040"  # Deep Crimson pressed
    ACCENT_RUBY: str = "#ff6b8b"        # Soft ruby highlight
    ACCENT_GOLD: str = "#ffb800"        # Silk Amber / Cooldown warning

    # Status Colors
    STATUS_SUCCESS: str = "#00f5a0"     # Bio-Venom Cyan
    STATUS_WARNING: str = "#ffb800"     # Silk Amber
    STATUS_ERROR: str = "#ff3355"       # Crimson Spider
    STATUS_INFO: str = "#00d2ff"        # Web Fluid Blue

    # Text Colors
    TEXT_PRIMARY: str = "#ffffff"       # Crisp white
    TEXT_SECONDARY: str = "#a8c4d8"     # Frosted slate
    TEXT_MUTED: str = "#6a8ca8"         # Subdued slate
    TEXT_SUBTLE: str = "#45627a"        # Disabled / placeholder

    # Web Mist Refraction Borders & Dividers
    BORDER_GLASS: str = "rgba(255, 255, 255, 0.08)"       # Web Mist stroke
    BORDER_GLASS_ACTIVE: str = "rgba(0, 210, 255, 0.40)" # Luminous Web Fluid Blue edge
    BORDER_DEFAULT: str = "rgba(255, 255, 255, 0.08)"     # Web Mist stroke
    BORDER_SUBTLE: str = "rgba(255, 255, 255, 0.04)"      # Card dividers
    BORDER_FOCUS: str = "#00d2ff"                         # Web Fluid Blue focus glow
    BORDER_RED: str = "#ff3355"                           # Crimson Spider accent border

    # Radii (Apple-style smooth curvature)
    RADIUS_SM: str = "6px"
    RADIUS_MD: str = "10px"
    RADIUS_LG: str = "14px"
    RADIUS_XL: str = "20px"
    RADIUS_PILL: str = "9999px"

    # Typography
    FONT_FAMILY: str = "'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"


# Global Tokens Instance
TOKENS = ThemeTokens()


def get_dashboard_qss() -> str:
    """Returns master QSS stylesheet for Dashboard and Settings window with Aquatic Liquid Glass styling."""
    return f"""
        QWidget#mainDashboard {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #07111e,
                stop: 0.5 #091729,
                stop: 1 #0c1a2e
            );
            color: {TOKENS.TEXT_PRIMARY};
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QWidget {{
            color: {TOKENS.TEXT_PRIMARY};
            font-family: {TOKENS.FONT_FAMILY};
        }}
        /* Tab Widget (Fallback & Standard Tabs) */
        QTabWidget::pane {{
            border: 1px solid {TOKENS.BORDER_GLASS};
            background-color: {TOKENS.BG_CARD};
            border-radius: {TOKENS.RADIUS_LG};
            top: -1px;
        }}
        QTabBar::tab {{
            background: transparent;
            color: {TOKENS.TEXT_MUTED};
            border: 1px solid transparent;
            border-bottom: none;
            border-top-left-radius: {TOKENS.RADIUS_MD};
            border-top-right-radius: {TOKENS.RADIUS_MD};
            padding: 8px 16px;
            margin-right: 4px;
            font-weight: 600;
        }}
        QTabBar::tab:selected {{
            background: rgba(0, 240, 255, 0.15);
            color: {TOKENS.ACCENT_AQUA};
            border: 1px solid {TOKENS.BORDER_GLASS_ACTIVE};
        }}
        /* Sidebar Navigation */
        QWidget#sidebarContainer {{
            background-color: rgba(7, 17, 30, 0.85);
            border-right: 1px solid {TOKENS.BORDER_GLASS};
        }}
        QPushButton.navBtn {{
            background-color: transparent;
            color: {TOKENS.TEXT_SECONDARY};
            border: 1px solid transparent;
            border-radius: {TOKENS.RADIUS_MD};
            padding: 10px 14px;
            font-size: 13px;
            font-weight: 600;
            text-align: left;
        }}
        QPushButton.navBtn:hover {{
            background-color: rgba(0, 240, 255, 0.08);
            color: {TOKENS.TEXT_PRIMARY};
            border-color: rgba(0, 240, 255, 0.15);
        }}
        QPushButton.navBtn[selected="true"] {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(0, 240, 255, 0.18),
                stop: 1 rgba(10, 132, 255, 0.12)
            );
            color: {TOKENS.ACCENT_AQUA};
            border: 1px solid {TOKENS.BORDER_GLASS_ACTIVE};
            font-weight: 700;
        }}
        /* Form Inputs */
        QLineEdit, QSpinBox, QTimeEdit, QComboBox {{
            background-color: {TOKENS.BG_INPUT};
            color: {TOKENS.TEXT_PRIMARY};
            border: 1.5px solid {TOKENS.BORDER_DEFAULT};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 7px 11px;
            font-size: 13px;
        }}
        QLineEdit:focus, QSpinBox:focus, QTimeEdit:focus, QComboBox:focus {{
            border: 1.5px solid {TOKENS.ACCENT_AQUA};
            background-color: rgba(12, 26, 46, 0.95);
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
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1.5px solid {TOKENS.BORDER_DEFAULT};
            border-radius: 5px;
            background-color: {TOKENS.BG_INPUT};
        }}
        QCheckBox::indicator:hover {{
            border-color: {TOKENS.ACCENT_AQUA};
        }}
        QCheckBox::indicator:checked {{
            background-color: {TOKENS.ACCENT_AZURE};
            border-color: {TOKENS.ACCENT_AQUA};
        }}
        /* Standard Action Buttons */
        QPushButton.primaryBtn {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {TOKENS.ACCENT_AZURE},
                stop: 1 {TOKENS.ACCENT_AQUA}
            );
            color: #051324;
            font-weight: 800;
            border: none;
            border-radius: {TOKENS.RADIUS_MD};
            padding: 9px 18px;
            font-size: 13px;
        }}
        QPushButton.primaryBtn:hover {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #3b9eff,
                stop: 1 #4df4ff
            );
        }}
        QPushButton.heroDrinkBtn {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {TOKENS.ACCENT_RED},
                stop: 1 {TOKENS.ACCENT_RED_HOVER}
            );
            color: #ffffff;
            font-size: 14.5px;
            font-weight: 900;
            letter-spacing: 0.5px;
            border: 1px solid rgba(255, 51, 85, 0.4);
            border-radius: {TOKENS.RADIUS_LG};
            padding: 12px 24px;
        }}
        QPushButton.heroDrinkBtn:hover {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {TOKENS.ACCENT_RED_HOVER},
                stop: 1 #ff7799
            );
            border-color: {TOKENS.ACCENT_AQUA};
        }}
        QPushButton.heroDrinkBtn:pressed {{
            background-color: {TOKENS.ACCENT_RED_ACTIVE};
        }}
        QPushButton.heroDrinkBtn:disabled {{
            background-color: rgba(25, 34, 52, 0.6);
            color: {TOKENS.TEXT_MUTED};
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        QPushButton.chipBtn {{
            background-color: rgba(18, 24, 36, 0.9);
            color: {TOKENS.TEXT_SECONDARY};
            font-size: 12px;
            font-weight: 700;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: {TOKENS.RADIUS_SM};
            padding: 6px 14px;
        }}
        QPushButton.chipBtn:hover {{
            background-color: rgba(25, 34, 52, 1.0);
            color: {TOKENS.ACCENT_AQUA};
            border-color: {TOKENS.BORDER_GLASS_ACTIVE};
        }}
        QPushButton.chipBtn[selected="true"] {{
            background-color: rgba(0, 210, 255, 0.15);
            color: {TOKENS.ACCENT_AQUA};
            border: 1.5px solid {TOKENS.ACCENT_AQUA};
            font-weight: 800;
        }}
        QPushButton.secondaryBtn {{
            background-color: rgba(18, 24, 36, 0.8);
            color: {TOKENS.TEXT_SECONDARY};
            font-weight: 600;
            border: 1px solid {TOKENS.BORDER_GLASS};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 8px 16px;
            font-size: 12.5px;
        }}
        QPushButton.secondaryBtn:hover {{
            background-color: rgba(25, 34, 52, 0.95);
            color: {TOKENS.TEXT_PRIMARY};
            border-color: {TOKENS.BORDER_GLASS_ACTIVE};
        }}
        /* Smooth Scrollbars */
        QScrollBar:vertical {{
            border: none;
            background: rgba(7, 17, 30, 0.5);
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {TOKENS.BORDER_DEFAULT};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {TOKENS.ACCENT_AQUA};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """


def get_companion_card_qss() -> str:
    """Returns the QSS stylesheet for the companion speech and action card with Aquatic Liquid Glass."""
    return f"""
        #spideyCard {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(10, 22, 40, 0.92),
                stop: 1 rgba(6, 14, 26, 0.96)
            );
            border: 1.5px solid {TOKENS.BORDER_GLASS_ACTIVE};
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
    """Returns the system tray context menu stylesheet with frosted glass aesthetic."""
    return f"""
        QMenu {{
            background-color: #0c1a2e;
            color: {TOKENS.TEXT_PRIMARY};
            border: 1px solid {TOKENS.BORDER_GLASS_ACTIVE};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 6px;
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QMenu::item {{
            padding: 7px 20px;
            border-radius: {TOKENS.RADIUS_SM};
        }}
        QMenu::item:selected {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {TOKENS.ACCENT_AZURE},
                stop: 1 {TOKENS.ACCENT_AQUA}
            );
            color: #051324;
            font-weight: 700;
        }}
        QMenu::separator {{
            height: 1px;
            background: {TOKENS.BORDER_DEFAULT};
            margin: 4px 8px;
        }}
    """


def get_dialog_qss() -> str:
    """Returns modal dialog styling for wizard and setup in Aquatic Liquid Glass style."""
    return f"""
        QDialog {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #07111e,
                stop: 1 #0c1a2e
            );
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
            border-color: {TOKENS.ACCENT_AQUA};
        }}
        QRadioButton, QCheckBox {{
            color: {TOKENS.TEXT_SECONDARY};
            font-size: 13px;
            spacing: 8px;
        }}
        QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
            background-color: {TOKENS.ACCENT_AZURE};
            border: 1.5px solid {TOKENS.ACCENT_AQUA};
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
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 {TOKENS.ACCENT_AZURE}, stop: 1 {TOKENS.ACCENT_AQUA});
            border-radius: {TOKENS.RADIUS_SM};
        }}
    """

