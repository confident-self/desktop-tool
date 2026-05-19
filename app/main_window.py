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
from app.config import get_theme
from app.icon_gen import home_icon, tasks_icon, settings_icon

DARK_STYLE = """
QMainWindow { background-color: #0a0a0a; }
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    color: #e0e0e0;
    background-color: #0a0a0a;
}
QAbstractScrollArea { background-color: #0a0a0a; }
QPushButton {
    border: 1px solid #2a2a2a; border-radius: 6px; padding: 7px 18px;
    background-color: #141414; color: #c0c0c0; font-size: 13px;
}
QPushButton:hover { background-color: #1c1c1c; border-color: #3a3a3a; color: #e8e8e8; }
QPushButton:pressed { background-color: #0e0e0e; border-color: #444; }
QPushButton:disabled { color: #4a4a4a; border-color: #1e1e1e; }
QLineEdit, QTextEdit, QPlainTextEdit {
    border: 1px solid #222; border-radius: 5px; padding: 7px 10px;
    background-color: #0c0c0c; color: #d8d8d8; font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus { border-color: #3e3e3e; background-color: #0f0f0f; }
QComboBox {
    border: 1px solid #222; border-radius: 5px; padding: 5px 8px;
    background-color: #0c0c0c; color: #c0c0c0; font-size: 12px;
}
QComboBox:hover { border-color: #3a3a3a; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #181818; border: 1px solid #2a2a2a; border-radius: 4px;
    color: #c0c0c0; selection-background-color: #242424; padding: 4px; outline: none;
}
QLabel { background-color: transparent; color: #c8c8c8; }
QSpinBox {
    border: 1px solid #222; border-radius: 5px; padding: 5px 8px;
    background-color: #0c0c0c; color: #d8d8d8; font-size: 13px;
}
QSpinBox:hover { border-color: #3a3a3a; }
QSpinBox:focus { border-color: #3e3e3e; background-color: #0f0f0f; }
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #1e1e1e; border: none; border-radius: 3px; width: 18px; margin: 2px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #333; }
QSpinBox::up-arrow {
    width: 0; height: 0; border-left: 4px solid transparent;
    border-right: 4px solid transparent; border-bottom: 5px solid #999; margin: 0 auto;
}
QSpinBox::down-arrow {
    width: 0; height: 0; border-left: 4px solid transparent;
    border-right: 4px solid transparent; border-top: 5px solid #999; margin: 0 auto;
}
QSlider::groove:horizontal { background: #1a1a1a; border-radius: 3px; height: 6px; }
QSlider::handle:horizontal {
    background: #3a3a3a; border-radius: 7px; width: 14px; height: 14px; margin: -4px 0;
}
QSlider::handle:horizontal:hover { background: #555; }
QSlider::sub-page:horizontal { background: #3a3a3a; border-radius: 3px; }
QScrollBar:vertical { background: transparent; width: 6px; border: none; margin: 0; }
QScrollBar::handle:vertical { background: #2a2a2a; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #444; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal { height: 0; }
QRadioButton { spacing: 6px; color: #909090; font-size: 12px; }
QRadioButton::indicator {
    width: 15px; height: 15px; border-radius: 8px;
    border: 1.5px solid #3a3a3a; background: transparent;
}
QRadioButton::indicator:checked {
    border-color: #707070;
    background: qradialgradient(cx:0.5 cy:0.5 radius:0.4, fx:0.5 fy:0.5, stop:0 #999, stop:1 transparent);
}
QRadioButton::indicator:hover { border-color: #555; }
QColorDialog { background-color: #181818; }
QToolTip { background-color: #222; color: #d0d0d0; border: 1px solid #333; border-radius: 4px; padding: 4px 8px; }
QFrame[HLine="true"] { color: #1e1e1e; }
"""

LIGHT_STYLE = """
QMainWindow { background-color: #f2f3f5; }
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    color: #1a1a1a;
    background-color: #f2f3f5;
}
QAbstractScrollArea { background-color: #f2f3f5; }
QPushButton {
    border: 1px solid #d4d4d8; border-radius: 6px; padding: 7px 18px;
    background-color: #ffffff; color: #333333; font-size: 13px;
}
QPushButton:hover { background-color: #f0f4ff; border-color: #2563eb; color: #2563eb; }
QPushButton:pressed { background-color: #e0e7ff; border-color: #1d4ed8; }
QPushButton:disabled { color: #bbb; border-color: #eee; }
QLineEdit, QTextEdit, QPlainTextEdit {
    border: 1px solid #d4d4d8; border-radius: 5px; padding: 7px 10px;
    background-color: #ffffff; color: #1a1a1a; font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus { border-color: #2563eb; background-color: #fafbff; }
QComboBox {
    border: 1px solid #d4d4d8; border-radius: 5px; padding: 5px 8px;
    background-color: #ffffff; color: #333; font-size: 12px;
}
QComboBox:hover { border-color: #2563eb; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #fff; border: 1px solid #d4d4d8; border-radius: 4px;
    color: #333; selection-background-color: #e0e7ff; padding: 4px; outline: none;
}
QLabel { background-color: transparent; color: #333; }
QSpinBox {
    border: 1px solid #d4d4d8; border-radius: 5px; padding: 5px 8px;
    background-color: #ffffff; color: #1a1a1a; font-size: 13px;
}
QSpinBox:hover { border-color: #2563eb; }
QSpinBox:focus { border-color: #2563eb; background-color: #fafbff; }
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #e8e8e8; border: none; border-radius: 3px; width: 18px; margin: 2px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #d4d4d8; }
QSpinBox::up-arrow {
    width: 0; height: 0; border-left: 4px solid transparent;
    border-right: 4px solid transparent; border-bottom: 5px solid #555; margin: 0 auto;
}
QSpinBox::down-arrow {
    width: 0; height: 0; border-left: 4px solid transparent;
    border-right: 4px solid transparent; border-top: 5px solid #555; margin: 0 auto;
}
QSlider::groove:horizontal { background: #e0e0e0; border-radius: 3px; height: 6px; }
QSlider::handle:horizontal {
    background: #2563eb; border-radius: 7px; width: 14px; height: 14px; margin: -4px 0;
}
QSlider::handle:horizontal:hover { background: #1d4ed8; }
QSlider::sub-page:horizontal { background: #2563eb; border-radius: 3px; }
QScrollBar:vertical { background: transparent; width: 6px; border: none; margin: 0; }
QScrollBar::handle:vertical { background: #ccc; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #aaa; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal { height: 0; }
QRadioButton { spacing: 6px; color: #555; font-size: 12px; }
QRadioButton::indicator {
    width: 15px; height: 15px; border-radius: 8px;
    border: 1.5px solid #bbb; background: transparent;
}
QRadioButton::indicator:checked {
    border-color: #2563eb;
    background: qradialgradient(cx:0.5 cy:0.5 radius:0.4, fx:0.5 fy:0.5, stop:0 #2563eb, stop:1 transparent);
}
QRadioButton::indicator:hover { border-color: #2563eb; }
QColorDialog { background-color: #fff; }
QToolTip { background-color: #fff; color: #333; border: 1px solid #d4d4d8; border-radius: 4px; padding: 4px 8px; }
QFrame[HLine="true"] { color: #e0e0e0; }
"""

DARK_NAV = """
QPushButton {
    border: none; border-radius: 8px; padding: 12px 8px;
    text-align: center; color: #6a6a6a; font-size: 11px;
    margin: 1px 0;
}
QPushButton:hover { background-color: #141414; color: #b0b0b0; }
QPushButton:checked { background-color: #1a1a1a; color: #e0e0e0; font-weight: bold; }
"""

LIGHT_NAV = """
QPushButton {
    border: none; border-radius: 8px; padding: 12px 8px;
    text-align: center; color: #999; font-size: 11px;
    margin: 1px 0;
}
QPushButton:hover { background-color: #e8ecf4; color: #2563eb; }
QPushButton:checked { background-color: #dce4f8; color: #2563eb; font-weight: bold; }
"""


def _icon_size() -> int:
    return 20


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._current_theme = get_theme()
        self.setWindowTitle("KeenPie")
        self.setMinimumSize(900, 600)
        self.resize(1400, 900)
        self._apply_stylesheet()

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 左侧导航栏
        self._nav = QFrame()
        self._nav.setFixedWidth(74)
        self._nav_layout = QVBoxLayout(self._nav)
        self._nav_layout.setContentsMargins(8, 16, 8, 16)
        self._nav_layout.setSpacing(6)

        isize = _icon_size()
        self.nav_home = self._make_nav_btn("主页", home_icon(isize))
        self.nav_tasks = self._make_nav_btn("事项", tasks_icon(isize))
        self.nav_settings = self._make_nav_btn("设置", settings_icon(isize))
        self.nav_home.setChecked(True)
        self._nav_layout.addStretch()

        # 页面
        self.stack = QStackedWidget()
        self.home_page = HomePage()
        self.tasks_page = TasksPage()
        self.settings_page = SettingsPage()
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.tasks_page)
        self.stack.addWidget(self.settings_page)

        root_layout.addWidget(self._nav)
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
        self.settings_page.theme_changed.connect(self._on_theme_changed)

    def _make_nav_btn(self, text: str, pixmap) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setIcon(QIcon(pixmap))
        btn.setIconSize(QSize(_icon_size(), _icon_size()))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(text)
        btn.setStyleSheet(self._nav_style())
        self._nav_layout.addWidget(btn)
        return btn

    def _apply_stylesheet(self):
        theme = self._current_theme
        self.setStyleSheet(DARK_STYLE if theme == "dark" else LIGHT_STYLE)
        self._apply_title_bar(theme == "dark")
        # 更新导航栏
        if hasattr(self, '_nav_layout'):
            for i in range(self._nav_layout.count()):
                w = self._nav_layout.itemAt(i).widget()
                if isinstance(w, QPushButton):
                    w.setStyleSheet(self._nav_style())
            nav_bg = "#080808" if theme == "dark" else "#e4e6eb"
            nav_border = "#181818" if theme == "dark" else "#d4d4d8"
            self._nav.setStyleSheet(
                f"QFrame {{ background-color: {nav_bg}; border-right: 1px solid {nav_border}; }}"
            )

    def _nav_style(self) -> str:
        return DARK_NAV if self._current_theme == "dark" else LIGHT_NAV

    def _apply_title_bar(self, dark: bool):
        import ctypes
        try:
            hwnd = int(self.winId())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(1 if dark else 0)),
                ctypes.sizeof(ctypes.c_int(2))
            )
        except Exception:
            pass

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

    def _on_theme_changed(self, theme: str):
        self._current_theme = theme
        self._apply_stylesheet()
