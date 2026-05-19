from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont

from app.pages.home_page import HomePage
from app.pages.tasks_page import TasksPage
from app.pages.settings_page import SettingsPage
from app.sticky_overlay import StickyOverlay


STYLE = """
/* ===== 全局 ===== */
QMainWindow {
    background-color: #0a0a0a;
}
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    color: #e0e0e0;
    background-color: #0a0a0a;
}
QAbstractScrollArea {
    background-color: #0a0a0a;
}

/* ===== 按钮 ===== */
QPushButton {
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 7px 18px;
    background-color: #141414;
    color: #c0c0c0;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #1c1c1c;
    border-color: #3a3a3a;
    color: #e8e8e8;
}
QPushButton:pressed {
    background-color: #0e0e0e;
    border-color: #444444;
}
QPushButton:disabled {
    color: #4a4a4a;
    border-color: #1e1e1e;
}

/* ===== 输入框 ===== */
QLineEdit, QTextEdit, QPlainTextEdit {
    border: 1px solid #222222;
    border-radius: 5px;
    padding: 7px 10px;
    background-color: #0c0c0c;
    color: #d8d8d8;
    selection-background-color: #1a3a5c;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #3e3e3e;
    background-color: #0f0f0f;
}

/* ===== 下拉框 ===== */
QComboBox {
    border: 1px solid #222222;
    border-radius: 5px;
    padding: 5px 8px;
    background-color: #0c0c0c;
    color: #c0c0c0;
    font-size: 12px;
}
QComboBox:hover {
    border-color: #3a3a3a;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox QAbstractItemView {
    background-color: #181818;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    color: #c0c0c0;
    selection-background-color: #242424;
    padding: 4px;
    outline: none;
}

/* ===== 标签 ===== */
QLabel {
    background-color: transparent;
    color: #c8c8c8;
}

/* ===== 数字输入 ===== */
QSpinBox {
    border: 1px solid #222222;
    border-radius: 5px;
    padding: 5px 8px;
    background-color: #0c0c0c;
    color: #d8d8d8;
    font-size: 13px;
}
QSpinBox:hover {
    border-color: #3a3a3a;
}
QSpinBox:focus {
    border-color: #3e3e3e;
    background-color: #0f0f0f;
}
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #1e1e1e;
    border: none;
    border-radius: 3px;
    width: 18px;
    margin: 2px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #333333;
}
QSpinBox::up-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #999999;
    margin: 0 auto;
}
QSpinBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #999999;
    margin: 0 auto;
}

/* ===== 滑条 ===== */
QSlider::groove:horizontal {
    background: #1a1a1a;
    border-radius: 3px;
    height: 6px;
}
QSlider::handle:horizontal {
    background: #3a3a3a;
    border-radius: 7px;
    width: 14px;
    height: 14px;
    margin: -4px 0;
}
QSlider::handle:horizontal:hover {
    background: #555555;
}
QSlider::sub-page:horizontal {
    background: #3a3a3a;
    border-radius: 3px;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2a2a2a;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #444444;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    border: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    height: 0;
}

/* ===== 单选框 ===== */
QRadioButton {
    spacing: 6px;
    color: #909090;
    font-size: 12px;
}
QRadioButton::indicator {
    width: 15px;
    height: 15px;
    border-radius: 8px;
    border: 1.5px solid #3a3a3a;
    background: transparent;
}
QRadioButton::indicator:checked {
    border-color: #707070;
    background: qradialgradient(cx:0.5 cy:0.5 radius:0.4, fx:0.5 fy:0.5, stop:0 #999999, stop:1 transparent);
}
QRadioButton::indicator:hover {
    border-color: #555555;
}

/* ===== 颜色对话框 ===== */
QColorDialog {
    background-color: #181818;
}

/* ===== 提示框 ===== */
QToolTip {
    background-color: #222222;
    color: #d0d0d0;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 4px 8px;
}

/* ===== 分割线 ===== */
QFrame[HLine="true"] {
    color: #1e1e1e;
}
"""

NAV_STYLE = """
QPushButton {
    border: none;
    border-radius: 8px;
    padding: 10px 10px;
    text-align: left;
    color: #6a6a6a;
    font-size: 12px;
    margin: 1px 0;
}
QPushButton:hover {
    background-color: #141414;
    color: #b0b0b0;
}
QPushButton:checked {
    background-color: #1a1a1a;
    color: #e0e0e0;
    font-weight: bold;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KeenPie")
        self.setMinimumSize(620, 480)
        self.resize(680, 560)
        self.setStyleSheet(STYLE)
        self._apply_dark_title_bar()

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 左侧导航栏
        nav = QFrame()
        nav.setFixedWidth(80)
        nav.setStyleSheet("QFrame { background-color: #080808; border-right: 1px solid #181818; }")
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(6, 12, 6, 12)
        nav_layout.setSpacing(4)

        self.nav_home = QPushButton("⌂ 主页")
        self.nav_tasks = QPushButton("☰ 事项")
        self.nav_settings = QPushButton("⚙ 设置")
        for btn in [self.nav_home, self.nav_tasks, self.nav_settings]:
            btn.setCheckable(True)
            btn.setStyleSheet(NAV_STYLE)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            nav_layout.addWidget(btn)
        self.nav_home.setChecked(True)
        nav_layout.addStretch()

        # 页面
        self.stack = QStackedWidget()

        self.home_page = HomePage()
        self.tasks_page = TasksPage()
        self.settings_page = SettingsPage()

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.tasks_page)
        self.stack.addWidget(self.settings_page)

        root_layout.addWidget(nav)
        root_layout.addWidget(self.stack)

        # 置顶便签
        self.sticky = StickyOverlay()
        self.sticky.done_toggled.connect(self._on_sticky_done)
        self.sticky.closed.connect(self._on_sticky_closed)

        # 信号
        self.nav_home.clicked.connect(lambda: self._switch_page(0))
        self.nav_tasks.clicked.connect(lambda: self._switch_page(1))
        self.nav_settings.clicked.connect(lambda: self._switch_page(2))
        self.home_page.start_requested.connect(self._start_sticky)
        self.home_page.stop_requested.connect(self._stop_sticky)
        self.home_page.tasks_changed.connect(self._on_tasks_changed)
        self.settings_page.settings_changed.connect(self._on_settings_changed)

    def _switch_page(self, index: int):
        for i, btn in enumerate([self.nav_home, self.nav_tasks, self.nav_settings]):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.home_page.refresh_tasks()
        if index == 1:
            self.tasks_page.refresh()
        if index == 2:
            self.settings_page.refresh()

    def _start_sticky(self, target_date: str):
        self.sticky.load_tasks(target_date)

    def _stop_sticky(self):
        self.sticky.close_overlay()

    def _on_tasks_changed(self, target_date: str):
        if self.sticky.isVisible():
            self.sticky.load_tasks(target_date)

    def _on_sticky_done(self, task_id: int, status: str):
        self.home_page.refresh_tasks()
        self.tasks_page.refresh()

    def _on_sticky_closed(self):
        self.home_page.set_start_button_state(False)

    def _on_settings_changed(self):
        if self.sticky.isVisible():
            send = self.home_page._selected_date or self.home_page._date_label.text()
        else:
            send = self.home_page._date_label.text()
        self.sticky.load_tasks(send)

    def _apply_dark_title_bar(self):
        import ctypes
        try:
            hwnd = int(self.winId())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int(2))
            )
        except Exception:
            pass
