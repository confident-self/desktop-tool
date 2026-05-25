from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, Signal, QRect, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QMouseEvent
from datetime import datetime
from app.db import add_focus_session, get_pending_tasks, get_task_focus_seconds, update_task_status
from app.color_adapt import sample_global_rect
from app.config import (
    clear_active_task,
    get_active_started_at,
    get_active_task_id,
    get_display_count,
    get_font_size,
    get_overdue_color,
    get_sticky_readability_mode,
    get_sticky_view_mode,
    get_sticky_width,
    get_transparency,
    set_active_task,
    set_sticky_view_mode,
    set_sticky_width,
)
from app.sticky_state import (
    complete_message,
    format_focus_seconds,
    get_active_task,
    get_next_task,
    normalize_view_mode,
    resize_width,
    start_message,
    sticky_palette,
)


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


def _palette_color(value) -> QColor:
    if isinstance(value, tuple):
        return QColor(*value)
    return QColor(value)


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
        self._start_rects: list[QRect] = []
        self._complete_rect = QRect()
        self._mode_rect = QRect()
        self._active_task = None
        self._next_task = None
        self._view_mode = get_sticky_view_mode()
        self._row_brightness: list[int] = []
        self._target_date = ""
        self._message = ""

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2000)
        self._refresh_timer.timeout.connect(self._refresh_colors)

        self._overdue_color = get_overdue_color()
        self._font_size = get_font_size()

        self.setMinimumWidth(self._panel_width)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.left() + 20, geo.top() + 20)

    def load_tasks(self, target_date: str):
        self._target_date = target_date
        limit = get_display_count()
        self._tasks = get_pending_tasks(target_date, limit)
        self._overdue_color = get_overdue_color()
        self._font_size = get_font_size()
        active_task_id = get_active_task_id()
        self._active_task = get_active_task(self._tasks, active_task_id)
        self._next_task = get_next_task(self._tasks, active_task_id)
        self._view_mode = normalize_view_mode(get_sticky_view_mode(), self._active_task)
        if active_task_id and not self._active_task:
            clear_active_task()
            set_sticky_view_mode("list")
        self._update_size()
        self._refresh_colors()
        self.setWindowOpacity(1.0)
        if not self._tasks:
            self._refresh_timer.stop()
            self.hide()
        else:
            self.show()
            if get_sticky_readability_mode() == "adaptive":
                self._refresh_timer.start()
            else:
                self._refresh_timer.stop()

    def _update_size(self):
        row_h = self._font_size + 20
        title_h = self._title_height()
        if self._view_mode == "active":
            h = title_h + (168 if self._hovered else 88)
        else:
            count = max(len(self._tasks), 1)
            h = title_h + count * row_h + 12
        self.setFixedSize(self._panel_width, h)

    def _title_height(self) -> int:
        return 40 if self._hovered else 12

    def _refresh_colors(self):
        if get_sticky_readability_mode() != "adaptive":
            self._row_brightness = []
            self.update()
            return
        geo = self.geometry()
        brightness_list = sample_global_rect(QRect(geo.left(), geo.top(), geo.width(), geo.height()))
        title_h = self._title_height()
        total_h = max(self.height(), 1)
        self._row_brightness = []
        for i, _ in enumerate(self._tasks):
            row_top = title_h + i * (total_h - title_h) // max(len(self._tasks), 1)
            seg_idx = min(row_top * 10 // total_h, 9)
            self._row_brightness.append(brightness_list[seg_idx])
        self.update()

    def _palette(self, brightness: int = 128) -> dict:
        return sticky_palette(
            get_sticky_readability_mode(),
            get_transparency(),
            self._hovered,
            brightness,
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        row_h = self._font_size + 20
        title_h = 40
        w, h = self.width(), self.height()

        palette = self._palette(self._row_brightness[0] if self._row_brightness else 128)
        panel_r, panel_g, panel_b, panel_alpha = palette["panel"]
        border_r, border_g, border_b, border_alpha = palette["panel_border"]
        painter.setBrush(QColor(panel_r, panel_g, panel_b, panel_alpha))
        painter.setPen(QPen(QColor(border_r, border_g, border_b, border_alpha), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)

        font = _ui_font(max(self._font_size - 2, 10), QFont.Weight.DemiBold)
        painter.setFont(font)
        self._mode_rect = QRect()
        if self._hovered:
            painter.setPen(QColor(palette["meta_text"]))
            painter.drawText(16, 7, 110, title_h - 8, Qt.AlignmentFlag.AlignVCenter, "今日聚焦")
            self._mode_rect = QRect(w - 112, 9, 72, 22)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#173c31"))
            painter.drawRoundedRect(self._mode_rect, 10, 10)
            painter.setPen(QColor("#72e5ad"))
            painter.setFont(_ui_font(10, QFont.Weight.DemiBold))
            label = "任务列表" if self._view_mode == "active" else "当前任务"
            painter.drawText(self._mode_rect, Qt.AlignmentFlag.AlignCenter, label)

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

        if self._view_mode == "active":
            self._paint_active_mode(painter, title_h, palette)
            return

        self._paint_list_mode(painter, title_h, row_h)

    def _paint_list_mode(self, painter: QPainter, title_h: int, row_h: int):
        w = self.width()
        self._toggle_rects = []
        self._start_rects = []
        self._complete_rect = QRect()
        # 事项行
        for i, task in enumerate(self._tasks):
            y = title_h + i * row_h
            brightness = self._row_brightness[i] if i < len(self._row_brightness) else 128
            palette = self._palette(brightness)
            toggle_rect = QRect(14, y + (row_h - 16) // 2, 16, 16)
            if self._hovered:
                self._toggle_rects.append(toggle_rect)

            is_overdue = _is_overdue(task)

            if self._hovered:
                painter.setPen(QPen(QColor(palette["meta_text"]), 1.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(toggle_rect)

            # 时间标签
            time_str = task.get("time_label") or ""
            category = task.get("category") or "生活"
            text_x = 40 if self._hovered else 18
            font = _ui_font(self._font_size, QFont.Weight.Medium)
            painter.setFont(font)
            if self._hovered and time_str:
                time_color = self._overdue_color if is_overdue else palette["muted_text"]
                painter.setPen(QColor(time_color))
                painter.drawText(text_x, y, 50, row_h, Qt.AlignmentFlag.AlignVCenter, time_str)
                text_x += 56

            if self._hovered:
                pill_rect = QRect(text_x, y + (row_h - 20) // 2, 42, 20)
                painter.setPen(QPen(QColor(palette["category_border"]), 1))
                painter.setBrush(_palette_color(palette["category_fill"]))
                painter.drawRoundedRect(pill_rect, 8, 8)
                painter.setPen(QColor(palette["category_text"]))
                painter.setFont(_ui_font(10, QFont.Weight.Bold))
                painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, category[:2])
                text_x += 48
                painter.setFont(font)

            # 内容文字
            if is_overdue:
                text_clr = QColor(self._overdue_color)
            else:
                text_clr = QColor(palette["task_text"])
            painter.setPen(text_clr)
            start_space = 54 if self._hovered else 0
            text_rect = QRect(text_x, y, w - text_x - 18 - start_space, row_h)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextSingleLine, task["content"])

            start_rect = QRect(w - 64, y + (row_h - 22) // 2, 42, 22)
            if self._hovered:
                self._start_rects.append(start_rect)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255, 20))
                painter.drawRoundedRect(start_rect, 8, 8)
                painter.setPen(QColor("#cfeedd"))
                painter.setFont(_ui_font(10, QFont.Weight.DemiBold))
                painter.drawText(start_rect, Qt.AlignmentFlag.AlignCenter, "开始")
                painter.setFont(font)

            # 分隔线
            if self._hovered and i < len(self._tasks) - 1:
                div_r, div_g, div_b, div_alpha = palette["divider"]
                painter.setPen(QPen(QColor(div_r, div_g, div_b, div_alpha), 0.5))
                painter.drawLine(text_x, y + row_h - 1, w - 12, y + row_h - 1)

        if not self._tasks:
            painter.setPen(QColor("#5a5a5a"))
            font = _ui_font(self._font_size, QFont.Weight.Medium)
            painter.setFont(font)
            painter.drawText(0, title_h, w, row_h, Qt.AlignmentFlag.AlignCenter, "所有事项已完成")

    def _paint_active_mode(self, painter: QPainter, title_h: int, palette: dict):
        w = self.width()
        task = self._active_task
        if self._hovered:
            painter.setPen(QColor("#72e5ad"))
            painter.setFont(_ui_font(11, QFont.Weight.DemiBold))
            painter.drawText(18, title_h + 8, w - 36, 18, Qt.AlignmentFlag.AlignVCenter, "现在做")
        painter.setPen(QColor(palette["task_text"]))
        painter.setFont(_ui_font(self._font_size + 3, QFont.Weight.Bold))
        content = task["content"] if task else "还没有开始的事项"
        content_y = title_h + (32 if self._hovered else 6)
        painter.drawText(
            18, content_y, w - 36, 34,
            Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextSingleLine,
            content
        )
        self._toggle_rects = []
        self._start_rects = []
        self._complete_rect = QRect()
        painter.setFont(_ui_font(11, QFont.Weight.Medium))
        painter.setPen(QColor(palette["meta_text"]))
        if not task:
            if self._hovered:
                painter.drawText(18, title_h + 72, w - 36, 18, Qt.AlignmentFlag.AlignVCenter, "回到列表选择一项开始。")
            return

        started_text = self._format_active_started_at()
        focus_text = format_focus_seconds(self._active_focus_seconds(task))
        if self._hovered:
            meta = f"{task.get('category') or '生活'} · 开始于 {started_text} · 今日累计 {focus_text}"
            painter.drawText(18, title_h + 72, w - 36, 18, Qt.AlignmentFlag.AlignVCenter, meta)
            next_text = f"下一项：{self._next_task['content']}" if self._next_task else "下一项：先把这一件收好。"
            painter.drawText(18, title_h + 94, w - 36, 18, Qt.AlignmentFlag.AlignVCenter, next_text)
        else:
            painter.drawText(18, title_h + 46, w - 36, 18, Qt.AlignmentFlag.AlignVCenter, f"开始 {started_text} · 今日累计 {focus_text}")
        if self._message:
            painter.setPen(QColor("#cfeedd"))
            painter.drawText(18, title_h + 116, w - 116, 18, Qt.AlignmentFlag.AlignVCenter, self._message)
        self._complete_rect = QRect(w - 94, title_h + 112, 74, 28)
        if self._hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#24c985"))
            painter.drawRoundedRect(self._complete_rect, 9, 9)
            painter.setPen(QColor("#062017"))
            painter.setFont(_ui_font(11, QFont.Weight.Bold))
            painter.drawText(self._complete_rect, Qt.AlignmentFlag.AlignCenter, "完成")
        else:
            self._complete_rect = QRect()

    def _format_active_started_at(self) -> str:
        value = get_active_started_at()
        if not value:
            return "刚刚"
        try:
            return datetime.fromisoformat(value).strftime("%H:%M")
        except ValueError:
            return value

    def _active_elapsed_seconds(self, task_id: int) -> int:
        if get_active_task_id() != task_id:
            return 0
        started_at = get_active_started_at()
        if not started_at:
            return 0
        try:
            started = datetime.fromisoformat(started_at)
        except ValueError:
            try:
                hour, minute = started_at.split(":")
                now = datetime.now()
                started = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            except (TypeError, ValueError):
                return 0
        return max(0, int((datetime.now() - started).total_seconds()))

    def _active_focus_seconds(self, task: dict) -> int:
        stored = get_task_focus_seconds(task["id"], self._target_date)
        return stored + self._active_elapsed_seconds(task["id"])

    def _finish_active_session(self):
        task_id = get_active_task_id()
        started_at = get_active_started_at()
        if not task_id or not started_at:
            return
        try:
            started = datetime.fromisoformat(started_at)
        except ValueError:
            try:
                hour, minute = started_at.split(":")
                now = datetime.now()
                started = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            except (TypeError, ValueError):
                return
        ended = datetime.now()
        duration = max(0, int((ended - started).total_seconds()))
        if duration <= 0:
            return
        task_date = self._target_date or ended.date().isoformat()
        add_focus_session(
            task_id,
            task_date,
            started_at,
            ended.isoformat(timespec="seconds"),
            duration,
        )

    def enterEvent(self, event):
        self._hovered = True
        self._update_size()
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self._update_size()
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._close_rect.contains(event.pos()):
                self.close_overlay()
                return
            if self._mode_rect.contains(event.pos()):
                self._view_mode = "list" if self._view_mode == "active" else "active"
                self._view_mode = normalize_view_mode(self._view_mode, self._active_task)
                set_sticky_view_mode(self._view_mode)
                self._update_size()
                self.update()
                return
            if self._resize_rect.contains(event.pos()):
                self._resize_anchor = event.globalPosition().toPoint()
                self._resize_start_width = self._panel_width
                return
            if self._title_rect.contains(event.pos()):
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return
            if self._complete_rect.contains(event.pos()) and self._active_task:
                task = self._active_task
                self._finish_active_session()
                update_task_status(task["id"], "done")
                clear_active_task()
                set_sticky_view_mode("list")
                self._message = complete_message(task["content"])
                self.done_toggled.emit(task["id"], "done")
                self.load_tasks(self._target_date)
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
                    return
            for i, rect in enumerate(self._start_rects):
                if rect.contains(event.pos()) and i < len(self._tasks):
                    task = self._tasks[i]
                    self._finish_active_session()
                    set_active_task(task["id"], datetime.now().isoformat(timespec="seconds"))
                    set_sticky_view_mode("active")
                    self._message = start_message(task)
                    self.load_tasks(self._target_date)
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
            self._refresh_colors()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._resize_anchor is not None:
            set_sticky_width(self._panel_width)
        self._resize_anchor = None
        self._drag_pos = None
        self.update()

    def close_overlay(self):
        self._refresh_timer.stop()
        self._finish_active_session()
        clear_active_task()
        self.hide()
        self.closed.emit()

    def closeEvent(self, event):
        self._refresh_timer.stop()
        self._finish_active_session()
        clear_active_task()
        super().closeEvent(event)
