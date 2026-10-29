"""
Design Tokens and Centralized QSS Theme Engine for Spider-Man Water Buddy.
Implements the Spider-Man Stark Tech / E.D.I.T.H. Tactical HUD interface.
Features pure pitch-black backdrops (#000000), crisp high-contrast laser-cut white lines (#ffffff),
glowing silver/cyan telemetry accents, and modern, ultra-clean typography.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    # Solid Obsidian Dark Surfaces (Linear / Raycast Style - Zero Glassmorphism)
    BG_BASE: str = "#111317"        # Solid matte obsidian canvas
    BG_SURFACE: str = "#15181E"     # Top bar / header surface
    BG_CARD: str = "#181B22"        # Solid flat card surface
    BG_CARD_SOLID: str = "#181B22"  # Solid card surface
    BG_CARD_HOVER: str = "#212630"  # Card hover state
    BG_INPUT: str = "#13151A"       # Sunken solid input well
    BG_OVERLAY: str = "#181B22"     # Companion overlay card (solid opaque)

    # Calm Water Cyan Accents
    ACCENT_AQUA: str = "#6cb6c8"        # Calm bioluminescent water cyan
    ACCENT_AZURE: str = "#4f98ad"       # Deep water tone
    ACCENT_MINT: str = "#7fc8a0"        # Hydration complete / health mint
    ACCENT_TEAL: str = "#5aa5b5"        # Intermediate water tone

    # Spider-Man & Spider-Sense Brand Accents
    ACCENT_RED: str = "#d6483f"         # Muted brick crimson (Spider-Man emblem)
    ACCENT_CRIMSON: str = "#d6483f"     # Brick crimson alias
    ACCENT_RED_HOVER: str = "#e2584f"   # Glowing scarlet hover
    ACCENT_RED_ACTIVE: str = "#b33a33"  # Deep crimson pressed
    ACCENT_RUBY: str = "#e58a83"        # Soft ruby highlight
    ACCENT_GOLD: str = "#d9a548"        # Spider-Sense golden-amber tingle
    ACCENT_MAGENTA: str = "#ff1493"     # Spider-Verse neon magenta chromatic pulse

    # Status Colors
    STATUS_SUCCESS: str = "#7fc8a0"     # Green calibrated
    STATUS_WARNING: str = "#d9a548"     # Spider-Sense amber alert
    STATUS_ERROR: str = "#e2584f"       # Declined red
    STATUS_INFO: str = "#6cb6c8"        # Info cyan

    # Typography Colors (Warm paper white & legible muted graphite)
    TEXT_PRIMARY: str = "#ecebe6"       # Warm paper white
    TEXT_SECONDARY: str = "#c1c0ba"     # Calm secondary text
    TEXT_MUTED: str = "#8d9199"         # Muted slate labels
    TEXT_SUBTLE: str = "#5d6169"        # Inactive / placeholder

    # Crisp Precision Borders (Solid 1px Obsidian - No Glass Transparency)
    BORDER_GLASS: str = "#2D333D"       # Solid 1px container border
    BORDER_GLASS_ACTIVE: str = "#6cb6c8" # Solid active border
    BORDER_DEFAULT: str = "#2D333D"     # Clean 1px card border
    BORDER_SUBTLE: str = "#222730"      # Solid divider line
    BORDER_FOCUS: str = "#6cb6c8"       # Focus outline
    BORDER_RED: str = "#d6483f"         # Crimson accent border

    # Radii
    RADIUS_SM: str = "6px"
    RADIUS_MD: str = "10px"
    RADIUS_LG: str = "14px"
    RADIUS_XL: str = "18px"
    RADIUS_PILL: str = "9999px"

    # Typography
    FONT_FAMILY: str = "Segoe UI Variable, Segoe UI, -apple-system, sans-serif"
    FONT_MONO: str = "Cascadia Code, Consolas, monospace"


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
            background: #252B35;
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
            background-color: #212630;
            color: #ffffff;
            border-color: {TOKENS.BORDER_DEFAULT};
        }}
        QPushButton.navBtn[selected="true"] {{
            background-color: #252B35;
            color: #ffffff;
            border: 1px solid {TOKENS.ACCENT_AQUA};
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
            border: 1.5px solid {TOKENS.ACCENT_AQUA};
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
            background-color: {TOKENS.ACCENT_RED};
            color: #ffffff;
            font-weight: 700;
            border: 1px solid {TOKENS.ACCENT_RED_HOVER};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 9px 18px;
            font-size: 13px;
        }}
        QPushButton.primaryBtn:hover {{
            background-color: {TOKENS.ACCENT_RED_HOVER};
            border-color: #ffffff;
        }}
        QPushButton.primaryBtn:pressed {{
            background-color: {TOKENS.ACCENT_RED_ACTIVE};
        }}
        QPushButton.heroDrinkBtn {{
            background-color: {TOKENS.ACCENT_RED};
            color: #ffffff;
            font-size: 14px;
            font-weight: 800;
            border: 1px solid {TOKENS.ACCENT_RED_HOVER};
            border-radius: {TOKENS.RADIUS_PILL};
            padding: 12px 28px;
        }}
        QPushButton.heroDrinkBtn:hover {{
            background-color: {TOKENS.ACCENT_RED_HOVER};
            border-color: #ffffff;
        }}
        QPushButton.heroDrinkBtn:pressed {{
            background-color: {TOKENS.ACCENT_RED_ACTIVE};
        }}
        QPushButton.heroDrinkBtn:disabled {{
            background-color: #1E222A;
            color: {TOKENS.TEXT_MUTED};
            border: 1px solid {TOKENS.BORDER_DEFAULT};
        }}
        QPushButton.chipBtn {{
            background-color: {TOKENS.BG_CARD};
            color: {TOKENS.TEXT_PRIMARY};
            font-size: 12px;
            font-weight: 600;
            border: 1px solid {TOKENS.BORDER_DEFAULT};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 8px 14px;
        }}
        QPushButton.chipBtn:hover {{
            background-color: {TOKENS.BG_CARD_HOVER};
            border-color: {TOKENS.ACCENT_AQUA};
        }}
        QPushButton.chipBtn[selected="true"] {{
            background-color: #2D2224;
            color: #ffffff;
            border: 1px solid {TOKENS.ACCENT_RED};
            font-weight: 700;
        }}
        QPushButton.secondaryBtn {{
            background-color: {TOKENS.BG_CARD};
            color: {TOKENS.TEXT_PRIMARY};
            font-weight: 600;
            border: 1px solid {TOKENS.BORDER_DEFAULT};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 8px 16px;
            font-size: 12.5px;
        }}
        QPushButton.secondaryBtn:hover {{
            background-color: {TOKENS.BG_CARD_HOVER};
            border-color: {TOKENS.ACCENT_AQUA};
        }}
        /* Smooth Scrollbars */
        QScrollBar:vertical {{
            border: none;
            background: #111317;
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {TOKENS.BORDER_DEFAULT};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #3E4654;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """


def get_companion_card_qss() -> str:
    """Returns the QSS stylesheet for the companion speech and action card matching the Spider-Man comic pop-art theme."""
    return """
        #spideyCard {
            background-color: #fffef6;
            border: 2.5px solid #141a3a;
            border-radius: 18px;
        }
        QLabel {
            color: #141a3a;
            font-family: 'Instrument Sans', 'Segoe UI', system-ui, sans-serif;
        }
        QPushButton {
            font-family: 'Instrument Sans', 'Segoe UI', system-ui, sans-serif;
            font-weight: 700;
        }
    """


def get_tray_menu_qss() -> str:
    """Returns the system tray context menu stylesheet with Lab Logbook aesthetic."""
    return f"""
        QMenu {{
            background-color: {TOKENS.BG_CARD};
            color: {TOKENS.TEXT_PRIMARY};
            border: 1px solid {TOKENS.BORDER_DEFAULT};
            border-radius: {TOKENS.RADIUS_MD};
            padding: 6px;
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QMenu::item {{
            padding: 7px 20px;
            border-radius: 6px;
            font-weight: 600;
        }}
        QMenu::item:selected {{
            background-color: {TOKENS.ACCENT_RED};
            color: #ffffff;
            font-weight: 700;
        }}
        QMenu::separator {{
            height: 1px;
            background: {TOKENS.BORDER_SUBTLE};
            margin: 4px 8px;
        }}
    """


def get_dialog_qss() -> str:
    """Returns modal dialog styling for wizard and setup in Deep Black & Polished Gold aesthetic."""
    return f"""
        QDialog {{
            background-color: #0b0c10;
            color: #f5f6f9;
            font-family: {TOKENS.FONT_FAMILY};
        }}
        QLabel {{
            color: #f5f6f9;
        }}
        QLineEdit, QSpinBox, QTimeEdit, QComboBox {{
            background-color: #12141a;
            color: #f5f6f9;
            border: 1.5px solid #3d341a;
            border-radius: {TOKENS.RADIUS_SM};
            padding: 6px 10px;
            font-size: 13px;
            font-family: {TOKENS.FONT_MONO};
        }}
        QLineEdit:focus, QSpinBox:focus, QTimeEdit:focus, QComboBox:focus {{
            border-color: #d4af37;
            background-color: #161922;
        }}
        QRadioButton, QCheckBox {{
            color: #c5bfab;
            font-size: 13px;
            spacing: 8px;
            font-weight: 600;
        }}
        QRadioButton::indicator, QCheckBox::indicator {{
            width: 17px;
            height: 17px;
            border: 1.5px solid #4a3e1b;
            border-radius: 4px;
            background-color: #12141a;
        }}
        QRadioButton::indicator:hover, QCheckBox::indicator:hover {{
            border-color: #d4af37;
        }}
        QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
            background-color: #d4af37;
            border: 1.5px solid #f5d77f;
        }}
        QPushButton {{
            font-weight: 700;
            border-radius: {TOKENS.RADIUS_SM};
            padding: 8px 16px;
            font-size: 13px;
            background-color: #181b24;
            color: #dcd8cc;
            border: 1px solid #4a3e1b;
        }}
        QPushButton:hover {{
            background-color: #222633;
            border-color: #d4af37;
            color: #ffffff;
        }}
        QProgressBar {{
            background-color: #12141a;
            border: 1px solid #3d341a;
            border-radius: {TOKENS.RADIUS_SM};
            text-align: center;
            color: #f5f6f9;
            font-weight: 700;
            font-family: {TOKENS.FONT_MONO};
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #d4af37, stop: 1 #f5d77f);
            border-radius: 2px;
        }}
    """
