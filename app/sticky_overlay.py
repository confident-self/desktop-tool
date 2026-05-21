from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QMouseEvent
from datetime import datetime
from app.db import get_pending_tasks, update_task_status
from app.config import (
    get_display_count,
    get_font_size,
    get_overdue_color,
    get_sticky_width,
    get_transparency,
    set_sticky_width,
)
from app.sticky_state import resize_width

TASK_TEXT = QColor("#f4f7fb")
META_TEXT = QColor("#aeb7c2")
PANEL_BORDER = QColor(255, 255, 255, 30)


def _is_overdue(task: dict) -> bool:
    label = task.get("time_label") or ""
    value = task.get("time_value") or ""
    now = datetime.now()
    if value:
        h, m = value.split(":")
        task_time = now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
        return now > task_time
    period_end = {
        "凌晨": (6, 0), "上午": (12, 0), "中午": (14, 0),
        "下午": (18, 0), "晚上": (23, 0), "夜晚": (23, 59),
    }
    for key, (eh, em) in period_end.items():
        if key in label:
            return now > now.replace(hour=eh, minute=em, second=0, microsecond=0)
    return False


def _ui_font(size: int, weight=QFont.Weight.Normal) -> QFont:
    font = QFont("Microsoft YaHei UI", size, weight)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    return font


class StickyOverlay(QWidget):
    done_toggled = Signal(int, str)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)

        self._tasks: list[dict] = []
        self._hovered = False
        self._drag_pos: QPoint | None = None
        self._resize_anchor: QPoint | None = None
        self._panel_width = get_sticky_width()
        self._resize_start_width = self._panel_width
        self._close_rect = QRect()
        self._resize_rect = QRect()
        self._title_rect = QRect()
        self._toggle_rects: list[QRect] = []

        self._overdue_color = get_overdue_color()
        self._font_size = get_font_size()

        self.setMinimumWidth(self._panel_width)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.left() + 20, geo.top() + 20)

    def load_tasks(self, target_date: str):
        limit = get_display_count()
        self._tasks = get_pending_tasks(target_date, limit)
        self._overdue_color = get_overdue_color()
        self._font_size = get_font_size()
        self._update_size()
        self.setWindowOpacity(1.0)
        if not self._tasks:
            self.hide()
        else:
            self.show()

    def _update_size(self):
        row_h = self._font_size + 20
        count = max(len(self._tasks), 1)
        title_h = 40
        h = title_h + count * row_h + 12
        self.setFixedSize(self._panel_width, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        row_h = self._font_size + 20
        title_h = 40
        w, h = self.width(), self.height()

        panel_alpha = 232 if self._hovered else max(
            132, int((100 - get_transparency()) / 100.0 * 110) + 132
        )
        painter.setBrush(QColor(18, 22, 28, panel_alpha))
        painter.setPen(QPen(PANEL_BORDER, 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)

        font = _ui_font(max(self._font_size - 2, 10), QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(META_TEXT)
        painter.drawText(16, 7, 110, title_h - 8, Qt.AlignmentFlag.AlignVCenter, "今日聚焦")

        # 关闭按钮
        close_x = w - 30
        close_y = 8
        self._close_rect = QRect(close_x, close_y, 20, 20)
        self._title_rect = QRect(0, 0, w, title_h)
        if self._hovered:
            painter.setPen(QColor("#9aa3ad"))
            painter.setFont(_ui_font(14, QFont.Weight.DemiBold))
            painter.drawText(self._close_rect, Qt.AlignmentFlag.AlignCenter, "×")
        self._resize_rect = QRect(w - 10, title_h, 10, h - title_h - 10)
        if self._hovered:
            painter.setPen(QPen(QColor("#6f7b88"), 1))
            painter.drawLine(w - 6, title_h + 10, w - 6, h - 18)

        self._toggle_rects = []
        # 事项行
        for i, task in enumerate(self._tasks):
            y = title_h + i * row_h
            toggle_rect = QRect(14, y + (row_h - 16) // 2, 16, 16)
            self._toggle_rects.append(toggle_rect)

            is_overdue = _is_overdue(task)

            painter.setPen(QPen(QColor("#cfd6df"), 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(toggle_rect)

            # 时间标签
            time_str = task.get("time_label") or ""
            category = task.get("category") or "生活"
            text_x = 40
            font = _ui_font(self._font_size, QFont.Weight.Medium)
            painter.setFont(font)
            if time_str:
                time_color = self._overdue_color if is_overdue else "#7a7a7a"
                painter.setPen(QColor(time_color))
                painter.drawText(text_x, y, 50, row_h, Qt.AlignmentFlag.AlignVCenter, time_str)
                text_x += 56

            pill_rect = QRect(text_x, y + (row_h - 20) // 2, 42, 20)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#173c31"))
            painter.drawRoundedRect(pill_rect, 8, 8)
            painter.setPen(QColor("#72e5ad"))
            painter.setFont(_ui_font(10, QFont.Weight.DemiBold))
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, category[:2])
            text_x += 48
            painter.setFont(font)

            # 内容文字
            if is_overdue:
                text_clr = QColor(self._overdue_color)
            else:
                text_clr = TASK_TEXT
            painter.setPen(text_clr)
            text_rect = QRect(text_x, y, w - text_x - 12, row_h)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextSingleLine, task["content"])

            # 分隔线
            if i < len(self._tasks) - 1:
                painter.setPen(QPen(QColor(255, 255, 255, 22), 0.5))
                painter.drawLine(text_x, y + row_h - 1, w - 12, y + row_h - 1)

        if not self._tasks:
            painter.setPen(QColor("#5a5a5a"))
            font = _ui_font(self._font_size, QFont.Weight.Medium)
            painter.setFont(font)
            painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, "所有事项已完成")

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._close_rect.contains(event.pos()):
                self.close_overlay()
                return
            if self._resize_rect.contains(event.pos()):
                self._resize_anchor = event.globalPosition().toPoint()
                self._resize_start_width = self._panel_width
                return
            if self._title_rect.contains(event.pos()):
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return
            for i, rect in enumerate(self._toggle_rects):
                if rect.contains(event.pos()) and i < len(self._tasks):
                    task = self._tasks[i]
                    update_task_status(task["id"], "done")
                    self.done_toggled.emit(task["id"], "done")
                    self._tasks.pop(i)
                    self._update_size()
                    self._refresh_colors()
                    if not self._tasks:
                        self.hide()
                        self._refresh_timer.stop()
                    return

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._resize_anchor is not None:
            delta_x = event.globalPosition().toPoint().x() - self._resize_anchor.x()
            self._panel_width = resize_width(self._resize_start_width, delta_x)
            self._update_size()
            self.update()
            return
        if self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._resize_anchor is not None:
            set_sticky_width(self._panel_width)
        self._resize_anchor = None
        self._drag_pos = None
        self.update()

    def close_overlay(self):
        self.hide()
        self.closed.emit()

    def closeEvent(self, event):
        super().closeEvent(event)
