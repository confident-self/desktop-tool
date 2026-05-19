from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from datetime import date

from app.db import get_distinct_dates, get_tasks_by_date, update_task_status, update_task_note


class TaskItemWidget(QFrame):
    status_changed = Signal(int, str)
    note_changed = Signal(int, str)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self._task = task
        self.setStyleSheet("TaskItemWidget { background: transparent; border: none; }")
        self.setFixedHeight(38)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)

        # 勾选圆圈
        self._check_btn = QPushButton("●" if task["status"] == "done" else "○")
        self._check_btn.setFixedSize(24, 24)
        is_done = task["status"] == "done"
        clr = "#555" if is_done else "#888"
        self._check_btn.setStyleSheet(f"QPushButton {{ border: none; color: {clr}; font-size: 16px; }} QPushButton:hover {{ color: #b0b0b0; }}")
        self._check_btn.clicked.connect(self._toggle_status)
        layout.addWidget(self._check_btn)

        # 时间
        time_str = task.get("time_label") or ""
        time_lbl = QLabel(time_str)
        time_lbl.setFixedWidth(52)
        time_lbl.setStyleSheet("color: #5a5a5a; font-size: 12px;")
        layout.addWidget(time_lbl)

        # 内容
        content_lbl = QLabel(task["content"])
        content_lbl.setStyleSheet("color: #c8c8c8; font-size: 13px;")
        if is_done:
            content_lbl.setStyleSheet("color: #4a4a4a; font-size: 13px; text-decoration: line-through;")
        layout.addWidget(content_lbl, 1)

        # 备注图标 + 输入
        self._note_visible = False
        self._note_edit = QLineEdit(task.get("note", ""))
        self._note_edit.setPlaceholderText("备注...")
        self._note_edit.setMaximumWidth(0)
        self._note_edit.setStyleSheet("QLineEdit { border: 1px solid #1e1e1e; background: #0e0e0e; border-radius: 3px; }")
        self._note_edit.textChanged.connect(self._on_note_changed)
        layout.addWidget(self._note_edit)

        note_btn = QPushButton("📝" if task.get("note") else "💬")
        note_btn.setFixedSize(28, 28)
        note_btn.setStyleSheet("QPushButton { border: none; color: #4a4a4a; font-size: 12px; } QPushButton:hover { color: #b0b0b0; }")
        note_btn.clicked.connect(self._toggle_note)
        layout.addWidget(note_btn)

    def _toggle_status(self):
        new_status = "pending" if self._task["status"] == "done" else "done"
        self._task["status"] = new_status
        update_task_status(self._task["id"], new_status)
        self.status_changed.emit(self._task["id"], new_status)
        is_done = new_status == "done"
        clr = "#555" if is_done else "#888"
        self._check_btn.setText("●" if is_done else "○")
        self._check_btn.setStyleSheet(f"QPushButton {{ border: none; color: {clr}; font-size: 16px; }} QPushButton:hover {{ color: #b0b0b0; }}")

    def _toggle_note(self):
        self._note_visible = not self._note_visible
        self._note_edit.setMaximumWidth(160 if self._note_visible else 0)
        if self._note_visible:
            self._note_edit.setFocus()

    def _on_note_changed(self, text: str):
        if self._task.get("id"):
            update_task_note(self._task["id"], text)
        self._task["note"] = text
        self.note_changed.emit(self._task["id"], text)


class DateGroup(QFrame):
    def __init__(self, date_str: str, tasks: list[dict], parent=None):
        super().__init__(parent)
        self._date_str = date_str
        self._tasks = tasks
        self._expanded = (date_str == str(date.today()))

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # 日期头
        header = QPushButton(f"▼ {date_str}")
        header.setStyleSheet("""
            QPushButton { border: none; border-bottom: 1px solid #1a1a1a; text-align: left; padding: 8px 16px;
                color: #7a7a7a; font-size: 12px; font-weight: bold; background: transparent; }
            QPushButton:hover { color: #b0b0b0; background: #111111; }
        """)
        header.clicked.connect(self._toggle)
        self._header = header
        self._layout.addWidget(header)

        # 事项容器
        self._task_container = QWidget()
        self._task_layout = QVBoxLayout(self._task_container)
        self._task_layout.setContentsMargins(0, 0, 0, 0)
        self._task_layout.setSpacing(1)
        for t in tasks:
            item = TaskItemWidget(t)
            self._task_layout.addWidget(item)
        self._layout.addWidget(self._task_container)
        self._task_container.setVisible(self._expanded)

    def _toggle(self):
        self._expanded = not self._expanded
        self._task_container.setVisible(self._expanded)
        self._header.setText(f"{'▼' if self._expanded else '▶'} {self._date_str}")


class TasksPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0
        self._loading = False
        self._done = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(0)

        title = QLabel("事项记录")
        title.setStyleSheet("font-size: 15px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setProperty("HLine", True)
        layout.addWidget(sep)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollArea > QWidget > QWidget { background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._group_layout = QVBoxLayout(self._container)
        self._group_layout.setContentsMargins(0, 8, 0, 0)
        self._group_layout.setSpacing(0)
        self._group_layout.addStretch()
        scroll.setWidget(self._container)

        # 监听滚动
        scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self._scroll = scroll

        layout.addWidget(scroll, 1)

    def refresh(self):
        # 清空
        while self._group_layout.count():
            item = self._group_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._offset = 0
        self._done = False
        self._load_dates()

    def _load_dates(self):
        if self._done or self._loading:
            return
        self._loading = True
        dates = get_distinct_dates(limit=7, before_date=self._offset_date())
        if len(dates) < 7:
            self._done = True
        for d in dates:
            tasks = get_tasks_by_date(d)
            group = DateGroup(d, tasks)
            # 移除 stretch 再添加
            if self._group_layout.count():
                stretch_item = self._group_layout.takeAt(self._group_layout.count() - 1)
                if stretch_item.widget():
                    stretch_item.widget().deleteLater()
            self._group_layout.addWidget(group)
            self._group_layout.addStretch()
        self._offset += len(dates)
        self._loading = False

    def _offset_date(self) -> str | None:
        if self._offset == 0:
            return None
        # 从最后一个 group 获取日期
        for i in range(self._group_layout.count() - 1, -1, -1):
            item = self._group_layout.itemAt(i)
            if isinstance(item.widget(), DateGroup):
                return item.widget()._date_str
        return None

    def _on_scroll(self, value: int):
        bar = self._scroll.verticalScrollBar()
        if bar.maximum() - value < 40:
            self._load_dates()
