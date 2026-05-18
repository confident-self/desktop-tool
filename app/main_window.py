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
QMainWindow {
    background-color: #0d0d0d;
}
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    color: #d4d4d4;
    background-color: #0d0d0d;
}
QAbstractScrollArea {
    background-color: #0d0d0d;
}
QPushButton {
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 8px 16px;
    background-color: #1e1e1e;
    color: #d4d4d4;
}
QPushButton:hover {
    background-color: #2a2a2a;
    border-color: #555555;
}
QPushButton:pressed {
    background-color: #151515;
}
QPushButton:disabled {
    color: #555555;
    border-color: #2a2a2a;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 6px 10px;
    background-color: #121212;
    color: #d4d4d4;
    selection-background-color: #264f78;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #555555;
}
QComboBox {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #121212;
    color: #d4d4d4;
}
QComboBox:hover {
    border-color: #555555;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
    color: #d4d4d4;
    selection-background-color: #2a2a2a;
}
QLabel {
    background-color: transparent;
    color: #d4d4d4;
}
QSpinBox {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #121212;
    color: #d4d4d4;
}
QSpinBox:hover {
    border-color: #555555;
}
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #1e1e1e;
    border: none;
    width: 16px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #2a2a2a;
}
QScrollBar:vertical {
    background: #0d0d0d;
    width: 8px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #3a3a3a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #555555;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
}
QRadioButton {
    spacing: 4px;
    color: #999999;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid #555555;
    background: transparent;
}
QRadioButton::indicator:checked {
    border-color: #888888;
    background: #888888;
}
QColorDialog {
    background-color: #1e1e1e;
}
"""

NAV_STYLE = """
QPushButton {
    border: none;
    border-radius: 6px;
    padding: 10px 8px;
    text-align: left;
    color: #888888;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #1a1a1a;
    color: #cccccc;
}
QPushButton:checked {
    background-color: #1e1e1e;
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
        nav.setStyleSheet("QFrame { background-color: #0b0b0b; border-right: 1px solid #1e1e1e; }")
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(6, 12, 6, 12)
        nav_layout.setSpacing(4)

        self.nav_home = QPushButton("● 主页")
        self.nav_tasks = QPushButton("□ 事项")
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
        self.settings_page.settings_changed.connect(self._on_settings_changed)

    def _switch_page(self, index: int):
        for i, btn in enumerate([self.nav_home, self.nav_tasks, self.nav_settings]):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)
        if index == 1:
            self.tasks_page.refresh()
        if index == 2:
            self.settings_page.refresh()

    def _start_sticky(self, target_date: str):
        self.sticky.load_tasks(target_date)

    def _stop_sticky(self):
        self.sticky.close_overlay()

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
