from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QBrush, QPen, QMouseEvent
from datetime import datetime
from app.db import get_pending_tasks, update_task_status
from app.config import get_display_count, get_overdue_color, get_font_size
from app.color_adapt import sample_global_rect, brightness_to_text_color


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
        self._text_colors: list[str] = []
        self._hovered = False
        self._drag_pos: QPoint | None = None
        self._close_rect = QRect()
        self._title_rect = QRect()
        self._toggle_rects: list[QRect] = []

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_colors)
        self._refresh_timer.setInterval(2000)

        self._overdue_color = get_overdue_color()
        self._font_size = get_font_size()

        self.setMinimumWidth(200)

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
        self._refresh_colors()
        if not self._tasks:
            self.hide()
        else:
            self.show()
            self._refresh_timer.start()

    def _update_size(self):
        row_h = self._font_size + 14
        count = len(self._tasks)
        title_h = 28
        w = 280
        h = title_h + count * row_h + 8
        self.setFixedSize(w, h)

    def _refresh_colors(self):
        if self.isHidden():
            return
        geo = self.geometry()
        brightness_list = sample_global_rect(QRect(geo.left(), geo.top(), geo.width(), geo.height()))
        title_h = 28
        total_h = self.height()
        self._text_colors = []
        for i, _ in enumerate(self._tasks):
            row_top = title_h + i * (total_h - title_h) // max(len(self._tasks), 1)
            seg_idx = min(row_top * 10 // total_h, 9)
            b = brightness_list[seg_idx]
            self._text_colors.append(brightness_to_text_color(b))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        row_h = self._font_size + 14
        title_h = 28
        w, h = self.width(), self.height()

        # 背景
        if self._hovered:
            painter.setBrush(QColor(30, 30, 30, 180))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(0, 0, w, h, 8, 8)

        # 标题区（hover 可见）
        font = QFont("Microsoft YaHei", self._font_size - 2, QFont.Weight.Bold)
        painter.setFont(font)
        if self._hovered:
            painter.setPen(QColor("#999999"))
            painter.drawText(10, 4, 100, title_h - 4, Qt.AlignmentFlag.AlignVCenter, "今日事项")

        # 关闭按钮
        close_x = w - 24
        close_y = 4
        self._close_rect = QRect(close_x, close_y, 20, 20)
        self._title_rect = QRect(0, 0, w, title_h)
        if self._hovered:
            painter.setPen(QColor("#888888"))
            painter.setFont(QFont("Microsoft YaHei", 14))
            painter.drawText(self._close_rect, Qt.AlignmentFlag.AlignCenter, "×")

        self._toggle_rects = []
        # 事项行
        for i, task in enumerate(self._tasks):
            y = title_h + i * row_h
            row_rect = QRect(0, y, w, row_h)
            toggle_rect = QRect(8, y + (row_h - 16) // 2, 16, 16)
            self._toggle_rects.append(toggle_rect)

            is_overdue = _is_overdue(task)

            # 圆圈
            if self._hovered:
                painter.setPen(QPen(QColor("#666666"), 1.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(toggle_rect)

            # 时间标签
            time_str = task.get("time_label") or ""
            text_x = 32
            font = QFont("Microsoft YaHei", self._font_size)
            painter.setFont(font)
            if time_str:
                time_color = self._overdue_color if is_overdue else "#888888"
                if self._hovered:
                    painter.setPen(QColor(time_color))
                else:
                    base = self._text_colors[i] if i < len(self._text_colors) else "#e0e0e0"
                    painter.setPen(QColor(base))
                painter.drawText(text_x, y, 50, row_h, Qt.AlignmentFlag.AlignVCenter, time_str)
                text_x += 55

            # 内容文字
            if is_overdue:
                text_clr = QColor(self._overdue_color)
            elif self._hovered:
                text_clr = QColor("#e0e0e0")
            else:
                tc = self._text_colors[i] if i < len(self._text_colors) else "#e0e0e0"
                text_clr = QColor(tc)
            painter.setPen(text_clr)
            text_rect = QRect(text_x, y, w - text_x - 12, row_h)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextSingleLine, task["content"])

            # 分隔线
            if i < len(self._tasks) - 1 and self._hovered:
                painter.setPen(QPen(QColor(60, 60, 60), 0.5))
                painter.drawLine(text_x, y + row_h - 1, w - 12, y + row_h - 1)

        if not self._tasks:
            painter.setPen(QColor("#888888"))
            font = QFont("Microsoft YaHei", self._font_size)
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
        if self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            self._refresh_colors()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        self.update()

    def close_overlay(self):
        self._refresh_timer.stop()
        self.hide()
        self.closed.emit()

    def closeEvent(self, event):
        self._refresh_timer.stop()
        super().closeEvent(event)
