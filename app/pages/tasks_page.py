from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from datetime import date

from app.db import (
    add_category,
    get_categories,
    get_distinct_dates,
    get_tasks_by_date,
    update_task_status,
    update_task_note,
)


class TaskItemWidget(QFrame):
    status_changed = Signal(int, str)
    note_changed = Signal(int, str)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self._task = task
        self.setProperty("card", True)
        self.setMinimumHeight(52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # 勾选圆圈
        self._check_btn = QPushButton("●" if task["status"] == "done" else "○")
        self._check_btn.setFixedSize(24, 24)
        is_done = task["status"] == "done"
        clr = "#8e9a93" if is_done else "#24c985"
        self._check_btn.setStyleSheet(f"QPushButton {{ border: none; color: {clr}; font-size: 16px; background: transparent; }}")
        self._check_btn.clicked.connect(self._toggle_status)
        layout.addWidget(self._check_btn)

        # 时间
        time_str = task.get("time_label") or ""
        time_lbl = QLabel(time_str)
        time_lbl.setFixedWidth(58)
        time_lbl.setProperty("muted", True)
        time_lbl.setStyleSheet("font-size: 12px;")
        layout.addWidget(time_lbl)

        category_lbl = QLabel(task.get("category") or "生活")
        category_lbl.setFixedWidth(54)
        category_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        category_lbl.setStyleSheet("""
            QLabel {
                background: #ddf8eb; color: #0e8c5d; border-radius: 8px;
                padding: 4px 6px; font-size: 12px; font-weight: bold;
            }
        """)
        layout.addWidget(category_lbl)

        # 内容
        content_lbl = QLabel(task["content"])
        content_lbl.setWordWrap(True)
        content_lbl.setMinimumHeight(24)
        content_lbl.setStyleSheet("font-size: 13px;")
        if is_done:
            content_lbl.setProperty("muted", True)
            content_lbl.setStyleSheet("font-size: 13px; text-decoration: line-through;")
        layout.addWidget(content_lbl, 1)

        # 备注图标 + 输入
        self._note_visible = False
        self._note_edit = QLineEdit(task.get("note", ""))
        self._note_edit.setPlaceholderText("备注...")
        self._note_edit.setFixedWidth(170)
        self._note_edit.setVisible(False)
        self._note_edit.textChanged.connect(self._on_note_changed)
        layout.addWidget(self._note_edit)

        note_btn = QPushButton("备注" if task.get("note") else "+")
        note_btn.setFixedSize(44, 28)
        note_btn.setToolTip("展开备注")
        note_btn.clicked.connect(self._toggle_note)
        layout.addWidget(note_btn)

    def _toggle_status(self):
        new_status = "pending" if self._task["status"] == "done" else "done"
        self._task["status"] = new_status
        update_task_status(self._task["id"], new_status)
        self.status_changed.emit(self._task["id"], new_status)
        is_done = new_status == "done"
        clr = "#8e9a93" if is_done else "#24c985"
        self._check_btn.setText("●" if is_done else "○")
        self._check_btn.setStyleSheet(f"QPushButton {{ border: none; color: {clr}; font-size: 16px; background: transparent; }}")

    def _toggle_note(self):
        self._note_visible = not self._note_visible
        self._note_edit.setVisible(self._note_visible)
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
        self.setProperty("card", True)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(6)

        # 日期头
        header = QPushButton(f"▼ {date_str}")
        header.setStyleSheet("""
            QPushButton { border: none; text-align: left; padding: 6px 8px;
                font-size: 12px; font-weight: bold; background: transparent; }
        """)
        header.clicked.connect(self._toggle)
        self._header = header
        self._layout.addWidget(header)

        # 事项容器
        self._task_container = QWidget()
        self._task_layout = QVBoxLayout(self._task_container)
        self._task_layout.setContentsMargins(0, 0, 0, 0)
        self._task_layout.setSpacing(6)
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
    categories_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0
        self._loading = False
        self._done = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 16)
        layout.setSpacing(12)

        title = QLabel("事项记录")
        title.setProperty("title", True)
        layout.addWidget(title)

        tip = QLabel("展开日期查看历史事项，完成状态和备注会即时保存")
        tip.setProperty("muted", True)
        tip.setWordWrap(True)
        layout.addWidget(tip)

        category_card = QFrame()
        category_card.setProperty("card", True)
        category_layout = QVBoxLayout(category_card)
        category_layout.setContentsMargins(12, 10, 12, 10)
        category_layout.setSpacing(8)

        category_header = QHBoxLayout()
        category_title = QLabel("事项分类")
        category_title.setStyleSheet("font-weight: bold;")
        self._category_input = QLineEdit()
        self._category_input.setPlaceholderText("添加分类，如 健身")
        self._category_input.setFixedWidth(180)
        self._category_input.returnPressed.connect(self._add_category)
        add_category_btn = QPushButton("添加")
        add_category_btn.clicked.connect(self._add_category)
        category_header.addWidget(category_title)
        category_header.addStretch()
        category_header.addWidget(self._category_input)
        category_header.addWidget(add_category_btn)
        category_layout.addLayout(category_header)

        self._category_chip_layout = QHBoxLayout()
        self._category_chip_layout.setSpacing(6)
        category_layout.addLayout(self._category_chip_layout)
        layout.addWidget(category_card)
        self._refresh_category_chips()

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
        self._group_layout.setContentsMargins(0, 4, 0, 0)
        self._group_layout.setSpacing(10)
        self._group_layout.addStretch()
        scroll.setWidget(self._container)

        # 监听滚动
        scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self._scroll = scroll

        layout.addWidget(scroll, 1)

    def _refresh_category_chips(self):
        while self._category_chip_layout.count():
            item = self._category_chip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for category in get_categories():
            chip = QLabel(category)
            chip.setStyleSheet("""
                QLabel {
                    background: #f1fcf7; color: #0e8c5d; border: 1px solid #cdeedc;
                    border-radius: 8px; padding: 5px 9px; font-size: 12px;
                }
            """)
            self._category_chip_layout.addWidget(chip)
        self._category_chip_layout.addStretch()

    def _add_category(self):
        name = self._category_input.text().strip()
        if add_category(name):
            self._category_input.clear()
            self._refresh_category_chips()
            self.categories_changed.emit()

    def refresh(self):
        self._refresh_category_chips()
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
