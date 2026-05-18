from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QRadioButton, QButtonGroup, QComboBox, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from datetime import date, timedelta

from app.db import get_tasks_by_date, upsert_task, delete_task, reorder_tasks

PERIOD_OPTIONS = ["上午", "中午", "下午", "晚上", "凌晨"]
HOURS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]


class TaskRow(QFrame):
    changed = Signal()
    deleted = Signal(object)

    def __init__(self, task: dict, time_mode: str, parent=None):
        super().__init__(parent)
        self._task = task
        self._time_mode = time_mode
        self.setFixedHeight(44)
        self.setStyleSheet("TaskRow { background: transparent; border: none; }")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # 时间列
        self.time_combo = QComboBox()
        self.time_combo.setFixedWidth(72)
        self.time_combo.addItem("")
        for h in range(24):
            for m in (0, 30):
                self.time_combo.addItem(f"{h:02d}:{m:02d}")
        self.time_period = QComboBox()
        self.time_period.setFixedWidth(72)
        self.time_period.addItem("")
        self.time_period.addItems(PERIOD_OPTIONS)

        self._update_time_widget()
        self.time_combo.currentTextChanged.connect(self._on_changed)
        self.time_period.currentTextChanged.connect(self._on_changed)

        # 内容
        self.content_edit = QLineEdit(task.get("content", ""))
        self.content_edit.setPlaceholderText("输入事项...")
        self.content_edit.textChanged.connect(self._on_changed)
        self.content_edit.setStyleSheet("QLineEdit { border: 1px solid #2a2a2a; background: #121212; }")

        # 删除
        del_btn = QPushButton("×")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("QPushButton { border: none; color: #555; font-size: 16px; } QPushButton:hover { color: #e04040; }")
        del_btn.clicked.connect(lambda: self.deleted.emit(self))

        layout.addWidget(self.time_combo)
        layout.addWidget(self.time_period)
        layout.addWidget(self.content_edit)
        layout.addWidget(del_btn)

    def _update_time_widget(self):
        self.time_combo.setVisible(self._time_mode == "precise")
        self.time_period.setVisible(self._time_mode == "period")

    def set_time_mode(self, mode: str):
        self._time_mode = mode
        self._update_time_widget()

    def _on_changed(self):
        self._task["content"] = self.content_edit.text()
        if self._time_mode == "precise":
            self._task["time_label"] = self.time_combo.currentText() or None
            self._task["time_value"] = self.time_combo.currentText() or None
        elif self._time_mode == "period":
            self._task["time_label"] = self.time_period.currentText() or None
            self._task["time_value"] = None
        else:
            self._task["time_label"] = None
            self._task["time_value"] = None
        self.changed.emit()

    def get_task(self) -> dict:
        return self._task

    def set_task(self, task: dict):
        self._task = task
        self.content_edit.blockSignals(True)
        self.content_edit.setText(task.get("content", ""))
        self.content_edit.blockSignals(False)
        self.time_combo.blockSignals(True)
        self.time_combo.setCurrentText(task.get("time_value") or "")
        self.time_combo.blockSignals(False)
        self.time_period.blockSignals(True)
        self.time_period.setCurrentText(task.get("time_label") or "")
        self.time_period.blockSignals(False)


class HomePage(QWidget):
    start_requested = Signal(str)
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_date = str(date.today())
        self._time_mode = "precise"
        self._task_rows: list[TaskRow] = []
        self._running = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        # 日期导航
        date_layout = QHBoxLayout()
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedWidth(36)
        self._prev_btn.setStyleSheet("QPushButton { border: none; color: #888; } QPushButton:hover { color: #ccc; }")
        self._prev_btn.clicked.connect(self._prev_day)

        self._date_label = QLabel(self._selected_date)
        self._date_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #d4d4d4;")
        self._date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedWidth(36)
        self._next_btn.setStyleSheet("QPushButton { border: none; color: #888; } QPushButton:hover { color: #ccc; }")
        self._next_btn.clicked.connect(self._next_day)

        self._today_btn = QPushButton("今天")
        self._today_btn.setFixedWidth(56)
        self._today_btn.setStyleSheet("QPushButton { border: none; color: #888; } QPushButton:hover { color: #ccc; }")
        self._today_btn.clicked.connect(self._go_today)

        date_layout.addStretch()
        date_layout.addWidget(self._prev_btn)
        date_layout.addWidget(self._date_label)
        date_layout.addWidget(self._next_btn)
        date_layout.addWidget(self._today_btn)
        date_layout.addStretch()
        layout.addLayout(date_layout)

        # 时间模式
        mode_layout = QHBoxLayout()
        mode_layout.addStretch()
        self._mode_group = QButtonGroup(self)
        modes = [("无时间", "none"), ("时段", "period"), ("精确", "precise")]
        for label, val in modes:
            rb = QRadioButton(label)
            rb.setProperty("mode", val)
            self._mode_group.addButton(rb)
            mode_layout.addWidget(rb)
            if val == self._time_mode:
                rb.setChecked(True)
        self._mode_group.buttonClicked.connect(self._on_mode_changed)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("QFrame { color: #2a2a2a; }")
        layout.addWidget(sep)

        # 事项列表
        self._task_layout = QVBoxLayout()
        self._task_layout.setSpacing(2)
        task_container = QWidget()
        task_container.setLayout(self._task_layout)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(task_container)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._scroll, 1)

        # 添加 + 开始
        action_layout = QHBoxLayout()
        add_btn = QPushButton("＋ 添加")
        add_btn.clicked.connect(self._add_task)
        action_layout.addWidget(add_btn)
        action_layout.addStretch()
        self._start_btn = QPushButton("▶ 开始")
        self._start_btn.setStyleSheet("""
            QPushButton { border: none; background: #2a4a3a; color: #7ecf8a; font-weight: bold; padding: 10px 28px; }
            QPushButton:hover { background: #345a4a; }
        """)
        self._start_btn.clicked.connect(self._toggle_start)
        action_layout.addWidget(self._start_btn)
        layout.addLayout(action_layout)

        self.refresh_tasks()

    def refresh_tasks(self):
        tasks = get_tasks_by_date(self._selected_date)
        for row in self._task_rows:
            row.setParent(None)
        self._task_rows.clear()
        # 清除旧 layout
        while self._task_layout.count():
            item = self._task_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for task in tasks:
            row = TaskRow(task, self._time_mode)
            row.changed.connect(lambda r=row: self._save_row(r))
            row.deleted.connect(self._delete_row)
            self._task_layout.addWidget(row)
            self._task_rows.append(row)
        if not tasks:
            self._task_layout.addStretch()

    def _save_row(self, row: TaskRow):
        task = row.get_task()
        if not task.get("id") and not task.get("content"):
            return
        task["sort_order"] = self._task_rows.index(row)
        task["date"] = self._selected_date
        new_id = upsert_task(task)
        task["id"] = new_id

    def _add_task(self):
        task = {"date": self._selected_date, "sort_order": len(self._task_rows), "content": "", "time_label": None, "time_value": None, "status": "pending"}
        row = TaskRow(task, self._time_mode)
        row.changed.connect(lambda r=row: self._save_row(r))
        row.deleted.connect(self._delete_row)
        self._task_layout.addWidget(row)
        self._task_rows.append(row)
        row.content_edit.setFocus()

    def _delete_row(self, row: TaskRow):
        task = row.get_task()
        if task.get("id"):
            delete_task(task["id"])
        self._task_rows.remove(row)
        row.setParent(None)
        row.deleteLater()
        for i, r in enumerate(self._task_rows):
            r.get_task()["sort_order"] = i
        task_ids = [r.get_task().get("id") for r in self._task_rows if r.get_task().get("id")]
        if task_ids:
            reorder_tasks(self._selected_date, task_ids)

    def _on_mode_changed(self, btn):
        self._time_mode = btn.property("mode")
        for row in self._task_rows:
            row.set_time_mode(self._time_mode)
            row._on_changed()

    def _prev_day(self):
        d = date.fromisoformat(self._selected_date) - timedelta(days=1)
        self._selected_date = str(d)
        self._date_label.setText(self._selected_date)
        self.refresh_tasks()

    def _next_day(self):
        d = date.fromisoformat(self._selected_date) + timedelta(days=1)
        if d > date.today():
            return
        self._selected_date = str(d)
        self._date_label.setText(self._selected_date)
        self.refresh_tasks()

    def _go_today(self):
        self._selected_date = str(date.today())
        self._date_label.setText(self._selected_date)
        self.refresh_tasks()

    def _toggle_start(self):
        if self._running:
            self.stop_requested.emit()
            self.set_start_button_state(False)
        else:
            self.start_requested.emit(self._selected_date)
            self.set_start_button_state(True)

    def set_start_button_state(self, running: bool):
        self._running = running
        if running:
            self._start_btn.setText("■ 暂停")
            self._start_btn.setStyleSheet("""
                QPushButton { border: none; background: #4a2a2a; color: #e08888; font-weight: bold; padding: 10px 28px; }
                QPushButton:hover { background: #5a3a3a; }
            """)
        else:
            self._start_btn.setText("▶ 开始")
            self._start_btn.setStyleSheet("""
                QPushButton { border: none; background: #2a4a3a; color: #7ecf8a; font-weight: bold; padding: 10px 28px; }
                QPushButton:hover { background: #345a4a; }
            """)
