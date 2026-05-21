from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QRadioButton, QButtonGroup, QComboBox, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from datetime import date, timedelta

from app.db import get_categories, get_tasks_by_date, upsert_task, delete_task, reorder_tasks

PERIOD_OPTIONS = ["上午", "中午", "下午", "晚上", "凌晨"]
HOURS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]


class TaskRow(QFrame):
    changed = Signal()
    deleted = Signal(object)

    def __init__(self, task: dict, time_mode: str, categories: list[str], parent=None):
        super().__init__(parent)
        self._task = task
        self._time_mode = time_mode
        self._categories = categories
        self.setMinimumHeight(52)
        self.setProperty("card", True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 10, 8)
        layout.setSpacing(10)

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

        # 分类
        self.category_combo = QComboBox()
        self.category_combo.setFixedWidth(78)
        self.category_combo.addItems(categories)
        self.category_combo.currentTextChanged.connect(self._on_changed)

        # 内容
        self.content_edit = QLineEdit(task.get("content", ""))
        self.content_edit.setPlaceholderText("输入事项...")
        self.content_edit.textChanged.connect(self._on_changed)
        self.content_edit.setMinimumHeight(34)

        # 删除
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setProperty("danger", True)
        del_btn.setToolTip("删除事项")
        del_btn.clicked.connect(lambda: self.deleted.emit(self))

        layout.addWidget(self.time_combo)
        layout.addWidget(self.time_period)
        layout.addWidget(self.category_combo)
        layout.addWidget(self.content_edit)
        layout.addWidget(del_btn)
        self.set_task(task)

    def _update_time_widget(self):
        self.time_combo.setVisible(self._time_mode == "precise")
        self.time_period.setVisible(self._time_mode == "period")

    def set_time_mode(self, mode: str):
        self._time_mode = mode
        self._update_time_widget()

    def _on_changed(self):
        self._task["content"] = self.content_edit.text()
        self._task["category"] = self.category_combo.currentText() or "生活"
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
        self.category_combo.blockSignals(True)
        category = task.get("category") or "生活"
        if category not in self._categories:
            self.category_combo.addItem(category)
            self._categories.append(category)
        self.category_combo.setCurrentText(category)
        self.category_combo.blockSignals(False)


class HomePage(QWidget):
    start_requested = Signal(str)
    stop_requested = Signal()
    tasks_changed = Signal(str)  # 事项变更时发出，携带当前日期

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_date = str(date.today())
        self._time_mode = "precise"
        self._categories = get_categories()
        self._task_rows: list[TaskRow] = []
        self._running = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 16)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_text = QVBoxLayout()
        title = QLabel("今日便签")
        title.setProperty("title", True)
        subtitle = QLabel("把今天要盯住的事放在这里，开始后会生成置顶便签")
        subtitle.setProperty("muted", True)
        subtitle.setWordWrap(True)
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header_layout.addLayout(header_text, 1)
        layout.addLayout(header_layout)

        # 日期导航
        date_layout = QHBoxLayout()
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedWidth(36)
        self._prev_btn.clicked.connect(self._prev_day)

        self._date_label = QLabel(self._selected_date)
        self._date_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self._date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedWidth(36)
        self._next_btn.clicked.connect(self._next_day)

        self._today_btn = QPushButton("今天")
        self._today_btn.setFixedWidth(56)
        self._today_btn.clicked.connect(self._go_today)

        date_layout.addStretch()
        date_layout.addWidget(self._prev_btn)
        date_layout.addWidget(self._date_label)
        date_layout.addWidget(self._next_btn)
        date_layout.addWidget(self._today_btn)
        date_layout.addStretch()
        layout.addLayout(date_layout)

        summary_card = QFrame()
        summary_card.setProperty("card", True)
        summary_layout = QHBoxLayout(summary_card)
        summary_layout.setContentsMargins(14, 10, 14, 10)
        summary_layout.setSpacing(12)
        self._summary_total = QLabel("总计 0")
        self._summary_pending = QLabel("待办 0")
        self._summary_done = QLabel("完成 0")
        for label in (self._summary_total, self._summary_pending, self._summary_done):
            label.setProperty("muted", True)
            summary_layout.addWidget(label)
        summary_layout.addStretch()
        layout.addWidget(summary_card)

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
        sep.setProperty("HLine", True)
        layout.addWidget(sep)

        # 事项列表
        self._task_layout = QVBoxLayout()
        self._task_layout.setSpacing(2)
        task_container = QWidget()
        task_container.setLayout(self._task_layout)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(task_container)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollArea > QWidget > QWidget { background: transparent; }")
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._scroll, 1)

        self._empty_label = QLabel("还没有事项，点“添加”写下第一件。")
        self._empty_label.setProperty("muted", True)
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setWordWrap(True)

        # 添加 + 开始
        action_layout = QHBoxLayout()
        add_btn = QPushButton("＋ 添加")
        add_btn.clicked.connect(self._add_task)
        action_layout.addWidget(add_btn)
        action_layout.addStretch()
        self._start_btn = QPushButton("▶ 开始")
        self._start_btn.setProperty("accent", True)
        self._start_btn.setMinimumWidth(108)
        self._start_btn.clicked.connect(self._toggle_start)
        action_layout.addWidget(self._start_btn)
        layout.addLayout(action_layout)

        self.refresh_tasks()

    def refresh_tasks(self):
        self._categories = get_categories()
        all_tasks = get_tasks_by_date(self._selected_date)
        tasks = [t for t in all_tasks if t["status"] == "pending"]
        for row in self._task_rows:
            row.setParent(None)
        self._task_rows.clear()
        # 清除旧 layout
        while self._task_layout.count():
            item = self._task_layout.takeAt(0)
            if item.widget() is self._empty_label:
                self._empty_label.setParent(None)
            elif item.widget():
                item.widget().deleteLater()
        for task in tasks:
            row = TaskRow(task, self._time_mode, self._categories.copy())
            row.changed.connect(lambda r=row: self._save_row(r))
            row.deleted.connect(self._delete_row)
            self._task_layout.addWidget(row)
            self._task_rows.append(row)
        if not tasks:
            self._task_layout.addWidget(self._empty_label)
        self._task_layout.addStretch()
        done_count = len([t for t in all_tasks if t["status"] == "done"])
        self._summary_total.setText(f"总计 {len(all_tasks)}")
        self._summary_pending.setText(f"待办 {len(tasks)}")
        self._summary_done.setText(f"完成 {done_count}")

    def _save_row(self, row: TaskRow):
        task = row.get_task()
        if not task.get("id") and not task.get("content"):
            return
        task["sort_order"] = self._task_rows.index(row)
        task["date"] = self._selected_date
        new_id = upsert_task(task)
        task["id"] = new_id
        self.tasks_changed.emit(self._selected_date)

    def _add_task(self):
        for i in range(self._task_layout.count() - 1, -1, -1):
            item = self._task_layout.itemAt(i)
            widget = item.widget()
            if widget is self._empty_label:
                self._task_layout.takeAt(i)
                self._empty_label.setParent(None)
            elif widget is None:
                self._task_layout.takeAt(i)
        task = {"date": self._selected_date, "sort_order": len(self._task_rows), "content": "", "category": "生活", "time_label": None, "time_value": None, "status": "pending"}
        row = TaskRow(task, self._time_mode, self._categories.copy())
        row.changed.connect(lambda r=row: self._save_row(r))
        row.deleted.connect(self._delete_row)
        self._task_layout.addWidget(row)
        self._task_rows.append(row)
        self._task_layout.addStretch()
        row.content_edit.setFocus()

    def refresh_categories(self):
        self._categories = get_categories()
        for row in self._task_rows:
            current = row.category_combo.currentText()
            row.category_combo.blockSignals(True)
            row.category_combo.clear()
            row.category_combo.addItems(self._categories)
            row.category_combo.setCurrentText(current if current in self._categories else "生活")
            row.category_combo.blockSignals(False)

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
        self.tasks_changed.emit(self._selected_date)

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
            self._start_btn.setProperty("accent", False)
            self._start_btn.setProperty("danger", True)
        else:
            self._start_btn.setText("▶ 开始")
            self._start_btn.setProperty("danger", False)
            self._start_btn.setProperty("accent", True)
        self._start_btn.style().unpolish(self._start_btn)
        self._start_btn.style().polish(self._start_btn)
