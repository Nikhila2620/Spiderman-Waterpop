"""
Reusable Frosted Glass Card Component for Spider-Man Water Buddy.
Implements translucent aquatic glassmorphic card containers with subtle cyan borders and top gloss highlights.
"""
from PySide6.QtCore import Qt, QRectF
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPen

from src.theme import TOKENS


class GlassCard(QFrame):
    """
    Frosted Glass Card Container with top gloss highlight and subtle cyan edge glow.
    """

    def __init__(self, title: str = "", subtitle: str = "", parent=None):
        super().__init__(parent)
        self._title_text = title
        self._subtitle_text = subtitle

        self.setObjectName("glassCard")
        self.setStyleSheet(f"""
            QFrame#glassCard {{
                background-color: {TOKENS.BG_CARD};
                border: 1px solid {TOKENS.BORDER_GLASS};
                border-radius: {TOKENS.RADIUS_LG};
            }}
        """)

        # Main Layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(18, 16, 18, 18)
        self._main_layout.setSpacing(12)

        # Header Section
        if title or subtitle:
            self._header_layout = QVBoxLayout()
            self._header_layout.setSpacing(2)

            if title:
                self.lbl_title = QLabel(title)
                self.lbl_title.setStyleSheet(f"""
                    font-size: 14.5px;
                    font-weight: 800;
                    color: {TOKENS.TEXT_PRIMARY};
                    letter-spacing: 0.3px;
                """)
                self._header_layout.addWidget(self.lbl_title)

            if subtitle:
                self.lbl_subtitle = QLabel(subtitle)
                self.lbl_subtitle.setStyleSheet(f"""
                    font-size: 12px;
                    font-weight: 500;
                    color: {TOKENS.TEXT_SECONDARY};
                """)
                self._header_layout.addWidget(self.lbl_subtitle)

            self._main_layout.addLayout(self._header_layout)

        # Internal Content Container
        self._content_widget = QWidget()
        self.content_layout = QVBoxLayout(self._content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)
        self._main_layout.addWidget(self._content_widget)

    @property
    def title(self) -> str:
        return self._title_text

    @property
    def subtitle(self) -> str:
        return self._subtitle_text
