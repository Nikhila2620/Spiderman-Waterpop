"""
Streak Card Component for Spider-Man Water Buddy.
Displays consecutive hydration streak, daily goal progress, completion status,
and celebration notifications in Aquatic Liquid Glass styling.
"""
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
    QGraphicsOpacityEffect,
)
from PySide6.QtGui import QFont, QColor

from src.theme import TOKENS
from src.components.glass_card import GlassCard
from src.streak_tracker import StreakInfo


class StreakCardWidget(GlassCard):
    """
    Aquatic Liquid Glass card displaying daily hydration progress,
    consecutive-day streaks with flame iconography, and goal celebration banner.
    """

    def __init__(self, parent=None):
        super().__init__(
            title="Daily Hydration Streak",
            subtitle="Consecutive Goal Tracking & Daily Habit",
            parent=parent,
        )
        self._init_card_content()

    def _init_card_content(self):
        # 1. Top Metrics Row: Streak Flame Badge (Left) & Completion Status (Right)
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # Left: Flame Streak Badge
        streak_box = QVBoxLayout()
        streak_box.setSpacing(2)

        self.lbl_streak_count = QLabel("🔥 0-Day Streak")
        self.lbl_streak_count.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 900;
            color: {TOKENS.ACCENT_GOLD};
            letter-spacing: 0.5px;
        """)
        streak_box.addWidget(self.lbl_streak_count)

        self.lbl_longest_streak = QLabel("Personal Best: 0 days")
        self.lbl_longest_streak.setStyleSheet(f"""
            font-size: 11.5px;
            font-weight: 600;
            color: {TOKENS.TEXT_MUTED};
        """)
        streak_box.addWidget(self.lbl_longest_streak)
        top_row.addLayout(streak_box)

        top_row.addStretch()

        # Right: Daily Status Pill
        self.lbl_status = QLabel("⏳ In Progress")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 700;
            color: {TOKENS.ACCENT_AQUA};
            background-color: rgba(0, 240, 255, 0.08);
            border: 1px solid rgba(0, 240, 255, 0.25);
            border-radius: {TOKENS.RADIUS_PILL};
            padding: 5px 12px;
        """)
        top_row.addWidget(self.lbl_status)

        self.content_layout.addLayout(top_row)

        # 2. Daily Goal Progress Section
        progress_info_row = QHBoxLayout()
        self.lbl_intake_numbers = QLabel("0 / 2,000 mL")
        self.lbl_intake_numbers.setStyleSheet(f"""
            font-size: 13.5px;
            font-weight: 700;
            color: {TOKENS.TEXT_PRIMARY};
        """)
        progress_info_row.addWidget(self.lbl_intake_numbers)

        progress_info_row.addStretch()

        self.lbl_pct = QLabel("0%")
        self.lbl_pct.setStyleSheet(f"""
            font-size: 13.5px;
            font-weight: 800;
            color: {TOKENS.ACCENT_AQUA};
        """)
        progress_info_row.addWidget(self.lbl_pct)
        self.content_layout.addLayout(progress_info_row)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        self._set_progress_style(is_completed=False)
        self.content_layout.addWidget(self.progress_bar)

        # Meta row: Total Goal Days & Web Shield Protection
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 4, 0, 0)
        self.lbl_total_goal_days = QLabel("Total Goals Met: 0 days")
        self.lbl_total_goal_days.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {TOKENS.TEXT_MUTED};")
        meta_row.addWidget(self.lbl_total_goal_days)

        meta_row.addStretch()

        self.lbl_shield_status = QLabel("🛡️ Web Shield: Ready")
        self.lbl_shield_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TOKENS.ACCENT_AQUA};")
        meta_row.addWidget(self.lbl_shield_status)
        self.content_layout.addLayout(meta_row)

        # 3. Celebration Banner (Subtle flame celebration)
        self.celebration_banner = QFrame()
        self.celebration_banner.setObjectName("celebrationBanner")
        self.celebration_banner.setStyleSheet(f"""
            QFrame#celebrationBanner {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(245, 158, 11, 0.18),
                    stop: 0.5 rgba(225, 29, 72, 0.18),
                    stop: 1 rgba(0, 230, 153, 0.18));
                border: 1px solid rgba(245, 158, 11, 0.45);
                border-radius: {TOKENS.RADIUS_MD};
                padding: 8px 12px;
            }}
        """)
        cb_layout = QHBoxLayout(self.celebration_banner)
        cb_layout.setContentsMargins(10, 8, 10, 8)
        cb_layout.setSpacing(10)

        self.lbl_celebration_icon = QLabel("🔥")
        self.lbl_celebration_icon.setStyleSheet("font-size: 20px;")
        cb_layout.addWidget(self.lbl_celebration_icon)

        self.lbl_celebration_text = QLabel("Goal Complete! 🔥 You're on a 1-Day Streak!")
        self.lbl_celebration_text.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: 0.3px;
        """)
        cb_layout.addWidget(self.lbl_celebration_text)
        cb_layout.addStretch()

        self.celebration_banner.setVisible(False)
        self.content_layout.addWidget(self.celebration_banner)

        # Animation effect for celebration banner
        self._opacity_effect = QGraphicsOpacityEffect(self.celebration_banner)
        self.celebration_banner.setGraphicsEffect(self._opacity_effect)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(600)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def _set_progress_style(self, is_completed: bool):
        if is_completed:
            chunk_gradient = f"qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 {TOKENS.ACCENT_MINT}, stop: 1 {TOKENS.ACCENT_AQUA})"
        else:
            chunk_gradient = f"qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 {TOKENS.ACCENT_AZURE}, stop: 1 {TOKENS.ACCENT_AQUA})"

        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {TOKENS.BG_INPUT};
                border: 1px solid {TOKENS.BORDER_DEFAULT};
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background: {chunk_gradient};
                border-radius: 4px;
            }}
        """)

    def update_info(self, info: StreakInfo):
        """Refreshes the streak card with the latest telemetry snapshot."""
        # 1. Update streak count and longest streak
        self.lbl_streak_count.setText(f"🔥 {info.current_streak}-Day Streak")
        self.lbl_longest_streak.setText(f"Personal Best: {info.longest_streak} days")

        # 2. Update intake and percentage
        intake_str = f"{info.today_intake_ml:,}"
        goal_str = f"{info.daily_goal_ml:,}"
        self.lbl_intake_numbers.setText(f"{intake_str} / {goal_str} mL")
        self.lbl_pct.setText(f"{info.progress_percentage}%")
        self.progress_bar.setValue(min(100, info.progress_percentage))
        self._set_progress_style(is_completed=info.is_completed_today)

        # Meta indicators
        total_days = getattr(info, "goal_days_total", 0)
        self.lbl_total_goal_days.setText(f"Total Goals Met: {total_days} days")
        shield_avail = getattr(info, "shield_available", True)
        shield_txt = "🛡️ Web Shield: Ready" if shield_avail else "🛡️ Web Shield: Used"
        shield_color = TOKENS.ACCENT_MINT if shield_avail else TOKENS.TEXT_MUTED
        self.lbl_shield_status.setText(shield_txt)
        self.lbl_shield_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {shield_color};")

        # 3. Update status badge and celebration banner
        if info.is_completed_today:
            self.lbl_status.setText("✨ Goal Completed!")
            self.lbl_status.setStyleSheet(f"""
                font-size: 12px;
                font-weight: 700;
                color: {TOKENS.STATUS_SUCCESS};
                background-color: rgba(0, 230, 153, 0.12);
                border: 1px solid rgba(0, 230, 153, 0.4);
                border-radius: {TOKENS.RADIUS_PILL};
                padding: 5px 12px;
            """)
            self.lbl_streak_count.setStyleSheet(f"""
                font-size: 22px;
                font-weight: 900;
                color: {TOKENS.ACCENT_MINT};
                letter-spacing: 0.5px;
            """)
            if info.celebrated_today and not self.is_celebration_active:
                msg = f"Goal Complete! 🔥 You're on a {info.current_streak}-Day Streak!"
                self.show_celebration_banner(msg, animate=False)
        else:
            self.lbl_status.setText("⏳ In Progress")
            self.lbl_status.setStyleSheet(f"""
                font-size: 12px;
                font-weight: 700;
                color: {TOKENS.ACCENT_AQUA};
                background-color: rgba(0, 240, 255, 0.08);
                border: 1px solid rgba(0, 240, 255, 0.25);
                border-radius: {TOKENS.RADIUS_PILL};
                padding: 5px 12px;
            """)
            self.lbl_streak_count.setStyleSheet(f"""
                font-size: 22px;
                font-weight: 900;
                color: {TOKENS.ACCENT_GOLD};
                letter-spacing: 0.5px;
            """)
            self.celebration_banner.setVisible(False)

    @property
    def is_celebration_active(self) -> bool:
        """Returns True if the celebration banner is active / visible."""
        return not self.celebration_banner.isHidden()

    def trigger_celebration(self, message: str):
        """Triggers celebratory fire animation and reveals celebration message."""
        self.show_celebration_banner(message, animate=True)

    def show_celebration_banner(self, message: str, animate: bool = True):
        self.lbl_celebration_text.setText(message)
        self.celebration_banner.setVisible(True)

        if animate:
            # Subtle smooth fade & pulse animation
            self._fade_anim.stop()
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.start()
        else:
            self._opacity_effect.setOpacity(1.0)

