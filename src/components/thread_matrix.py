"""
Daily Thread Matrix (7-Day Log) Widget for Spider-Man Water Buddy v2.0.
Renders the 7 weekday nodes (M, T, W, T, F, S, S) connected by a spider web thread line,
marking days where hydration goals were reached.
"""
from datetime import date, timedelta
from typing import Dict, Any, Optional
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush

from src.theme import TOKENS


class ThreadMatrixWidget(QWidget):
    """
    Renders 7 weekday nodes connected by a delicate web thread.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(86)
        self.setMinimumWidth(320)
        self._history: Dict[str, Any] = {}
        self._today_intake: int = 0
        self._goal: int = 2000
        self._current_date: date = date.today()

    def update_matrix(
        self,
        history: Dict[str, Any],
        today_intake: int,
        daily_goal: int,
        current_date: Optional[date] = None,
    ):
        self._history = history or {}
        self._today_intake = max(0, today_intake)
        self._goal = max(1, daily_goal)
        self._current_date = current_date or date.today()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        w = self.width()
        h = self.height()

        # Compute Monday of the current week
        # Monday is weekday() == 0, Sunday is 6
        today = self._current_date
        monday = today - timedelta(days=today.weekday())

        # Build date -> entry map from list or dict
        hist_map = {}
        if isinstance(self._history, list):
            for entry in self._history:
                if isinstance(entry, dict) and "date" in entry:
                    hist_map[entry["date"]] = entry
        elif isinstance(self._history, dict):
            hist_map = self._history

        days_info = []
        day_letters = ["M", "T", "W", "T", "F", "S", "S"]

        for i in range(7):
            d = monday + timedelta(days=i)
            iso = d.isoformat()
            is_today = (d == today)
            is_past = (d < today)
            is_future = (d > today)

            # Check if completed
            if is_today:
                completed = self._today_intake >= self._goal
            else:
                entry = hist_map.get(iso, {})
                intake = entry.get("intake_ml", 0) if isinstance(entry, dict) else 0
                completed = intake >= self._goal or entry.get("goal_met", False)
                completed = intake >= self._goal

            days_info.append({
                "date": d,
                "letter": day_letters[i],
                "is_today": is_today,
                "is_past": is_past,
                "is_future": is_future,
                "completed": completed,
            })

        # Calculate node centers
        margin_x = 28.0
        avail_w = w - 2 * margin_x
        step_x = avail_w / 6.0 if avail_w > 0 else 40.0
        cy = 34.0
        r_node = 14.0

        centers = [QPointF(margin_x + i * step_x, cy) for i in range(7)]

        # 1. Draw web thread connecting all nodes
        pen_thread = QPen(QColor("#2c313a"), 2.0, Qt.PenStyle.SolidLine)
        painter.setPen(pen_thread)
        for i in range(6):
            painter.drawLine(centers[i], centers[i + 1])

        # Active glowing segments between completed nodes
        pen_glow = QPen(QColor(TOKENS.ACCENT_CRIMSON), 2.5, Qt.PenStyle.SolidLine)
        painter.setPen(pen_glow)
        for i in range(6):
            if days_info[i]["completed"] and days_info[i + 1]["completed"]:
                painter.drawLine(centers[i], centers[i + 1])

        # 2. Draw each node
        for i, pt in enumerate(centers):
            info = days_info[i]
            rect = QRectF(pt.x() - r_node, pt.y() - r_node, r_node * 2.0, r_node * 2.0)

            if info["completed"]:
                # Crimson completed badge with white checkmark
                painter.setPen(QPen(QColor("#ff2a40"), 1.5))
                painter.setBrush(QBrush(QColor(TOKENS.ACCENT_CRIMSON)))
                painter.drawEllipse(rect)

                # Draw checkmark
                painter.setPen(QPen(QColor("#ffffff"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p1 = QPointF(pt.x() - 4.5, pt.y() + 0.5)
                p2 = QPointF(pt.x() - 1.0, pt.y() + 4.0)
                p3 = QPointF(pt.x() + 5.0, pt.y() - 3.5)
                painter.drawLine(p1, p2)
                painter.drawLine(p2, p3)
            elif info["is_today"]:
                # Today active node - Amber / Cyan glowing reticle
                painter.setPen(QPen(QColor(TOKENS.ACCENT_GOLD), 2.0))
                painter.setBrush(QBrush(QColor("#1e2229")))
                painter.drawEllipse(rect)

                painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                painter.setPen(QColor(TOKENS.ACCENT_GOLD))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, info["letter"])
            else:
                # Normal or future node
                border_col = QColor("#333842") if not info["is_future"] else QColor("#22262d")
                bg_col = QColor("#14171c")
                text_col = QColor(TOKENS.TEXT_SECONDARY) if not info["is_future"] else QColor("#49505b")

                painter.setPen(QPen(border_col, 1.2))
                painter.setBrush(QBrush(bg_col))
                painter.drawEllipse(rect)

                painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
                painter.setPen(text_col)
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, info["letter"])

            # Day label below node
            label_rect = QRectF(pt.x() - 16.0, pt.y() + r_node + 4.0, 32.0, 16.0)
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))
            sub_col = QColor(TOKENS.ACCENT_GOLD) if info["is_today"] else QColor(TOKENS.TEXT_MUTED)
            painter.setPen(sub_col)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, info["letter"])
