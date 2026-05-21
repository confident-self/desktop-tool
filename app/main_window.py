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
QMainWindow { background-color: #101114; }
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    color: #e7e8ea;
    background-color: #101114;
}
QAbstractScrollArea { background-color: #101114; }
QPushButton {
    border: 1px solid #2b2f36; border-radius: 8px; padding: 8px 14px;
    background-color: #181b20; color: #d6d9df; font-size: 13px;
}
QPushButton:hover { background-color: #20242b; border-color: #36c58a; color: #ffffff; }
QPushButton:pressed { background-color: #15181d; border-color: #24a876; }
QPushButton:disabled { color: #5c616b; border-color: #22262c; }
QPushButton[accent="true"] {
    border: none; background-color: #23c483; color: #062017; font-weight: 700;
}
QPushButton[accent="true"]:hover { background-color: #35d593; color: #051b13; }
QPushButton[danger="true"] { color: #ff8a8a; border-color: #493137; background-color: #1d1518; }
QPushButton[danger="true"]:hover { background-color: #2a181d; border-color: #da5b68; }
QLineEdit, QTextEdit, QPlainTextEdit {
    border: 1px solid #2b2f36; border-radius: 8px; padding: 8px 10px;
    background-color: #15181d; color: #eef0f2; font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus { border-color: #23c483; background-color: #171d20; }
QComboBox {
    border: 1px solid #2b2f36; border-radius: 8px; padding: 7px 8px;
    background-color: #15181d; color: #d6d9df; font-size: 12px;
}
QComboBox:hover { border-color: #23c483; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #181b20; border: 1px solid #2b2f36; border-radius: 6px;
    color: #d6d9df; selection-background-color: #173c31; padding: 4px; outline: none;
}
QLabel { background-color: transparent; color: #d6d9df; }
QLabel[muted="true"] { color: #8b929d; }
QLabel[title="true"] { color: #f2f4f7; font-size: 18px; font-weight: 800; }
QFrame[card="true"] {
    background-color: #15181d; border: 1px solid #242932; border-radius: 10px;
}
QSpinBox {
    border: 1px solid #2b2f36; border-radius: 8px; padding: 7px 8px;
    background-color: #15181d; color: #eef0f2; font-size: 13px;
}
QSpinBox:hover { border-color: #23c483; }
QSpinBox:focus { border-color: #23c483; background-color: #171d20; }
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
QSlider::groove:horizontal { background: #252a32; border-radius: 3px; height: 6px; }
QSlider::handle:horizontal {
    background: #23c483; border-radius: 7px; width: 14px; height: 14px; margin: -4px 0;
}
QSlider::handle:horizontal:hover { background: #35d593; }
QSlider::sub-page:horizontal { background: #23c483; border-radius: 3px; }
QScrollBar:vertical { background: transparent; width: 6px; border: none; margin: 0; }
QScrollBar::handle:vertical { background: #2a2a2a; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #444; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal { height: 0; }
QRadioButton { spacing: 6px; color: #aeb4bd; font-size: 12px; }
QRadioButton::indicator {
    width: 15px; height: 15px; border-radius: 8px;
    border: 1.5px solid #3b424c; background: transparent;
}
QRadioButton::indicator:checked {
    border-color: #23c483;
    background: qradialgradient(cx:0.5 cy:0.5 radius:0.4, fx:0.5 fy:0.5, stop:0 #23c483, stop:1 transparent);
}
QRadioButton::indicator:hover { border-color: #23c483; }
QColorDialog { background-color: #181818; }
QToolTip { background-color: #20242b; color: #eef0f2; border: 1px solid #303641; border-radius: 4px; padding: 4px 8px; }
QFrame[HLine="true"] { color: #252a32; }
"""

LIGHT_STYLE = """
QMainWindow { background-color: #f5f7fb; }
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    color: #162018;
    background-color: #f5f7fb;
}
QAbstractScrollArea { background-color: #f5f7fb; }
QPushButton {
    border: 1px solid #dfe5eb; border-radius: 8px; padding: 8px 14px;
    background-color: #ffffff; color: #1d2a22; font-size: 13px;
}
QPushButton:hover { background-color: #f1fcf7; border-color: #26bd7b; color: #0f8f5d; }
QPushButton:pressed { background-color: #ddf7eb; border-color: #10905e; }
QPushButton:disabled { color: #b9c0c8; border-color: #edf0f3; }
QPushButton[accent="true"] {
    border: none; background-color: #24c985; color: #052016; font-weight: 700;
}
QPushButton[accent="true"]:hover { background-color: #31d892; color: #041a11; }
QPushButton[danger="true"] { color: #c94e5a; border-color: #f0d0d4; background-color: #fff8f8; }
QPushButton[danger="true"]:hover { background-color: #fff0f1; border-color: #dc7a84; }
QLineEdit, QTextEdit, QPlainTextEdit {
    border: 1px solid #dfe5eb; border-radius: 8px; padding: 8px 10px;
    background-color: #ffffff; color: #162018; font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus { border-color: #24c985; background-color: #fbfffd; }
QComboBox {
    border: 1px solid #dfe5eb; border-radius: 8px; padding: 7px 8px;
    background-color: #ffffff; color: #27342c; font-size: 12px;
}
QComboBox:hover { border-color: #24c985; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #fff; border: 1px solid #dfe5eb; border-radius: 6px;
    color: #27342c; selection-background-color: #dcf8eb; padding: 4px; outline: none;
}
QLabel { background-color: transparent; color: #27342c; }
QLabel[muted="true"] { color: #718071; }
QLabel[title="true"] { color: #162018; font-size: 18px; font-weight: 800; }
QFrame[card="true"] {
    background-color: #ffffff; border: 1px solid #e3e9ef; border-radius: 10px;
}
QSpinBox {
    border: 1px solid #dfe5eb; border-radius: 8px; padding: 7px 8px;
    background-color: #ffffff; color: #162018; font-size: 13px;
}
QSpinBox:hover { border-color: #24c985; }
QSpinBox:focus { border-color: #24c985; background-color: #fbfffd; }
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
    background: #24c985; border-radius: 7px; width: 14px; height: 14px; margin: -4px 0;
}
QSlider::handle:horizontal:hover { background: #16aa6f; }
QSlider::sub-page:horizontal { background: #24c985; border-radius: 3px; }
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
    border-color: #24c985;
    background: qradialgradient(cx:0.5 cy:0.5 radius:0.4, fx:0.5 fy:0.5, stop:0 #24c985, stop:1 transparent);
}
QRadioButton::indicator:hover { border-color: #24c985; }
QColorDialog { background-color: #fff; }
QToolTip { background-color: #fff; color: #333; border: 1px solid #d4d4d8; border-radius: 4px; padding: 4px 8px; }
QFrame[HLine="true"] { color: #e0e0e0; }
"""

DARK_NAV = """
QPushButton {
    border: none; border-radius: 10px; padding: 10px 8px;
    text-align: center; color: #8b929d; font-size: 11px; margin: 2px 0;
    background: transparent;
}
QPushButton:hover { background-color: #1a1e24; color: #d5d9df; }
QPushButton:checked { background-color: #173c31; color: #62e3a7; font-weight: bold; }
"""

LIGHT_NAV = """
QPushButton {
    border: none; border-radius: 10px; padding: 10px 8px;
    text-align: center; color: #6e7b75; font-size: 11px; margin: 2px 0;
    background: transparent;
}
QPushButton:hover { background-color: #eff5f1; color: #129864; }
QPushButton:checked { background-color: #ddf8eb; color: #0e8c5d; font-weight: bold; }
"""


def _icon_size() -> int:
    return 20


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._current_theme = get_theme()
        self.setWindowTitle("KeenPie")
        self.setMinimumSize(760, 500)
        self.resize(960, 640)
        self._apply_stylesheet()

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 左侧导航栏
        self._nav = QFrame()
        self._nav.setFixedWidth(84)
        self._nav_layout = QVBoxLayout(self._nav)
        self._nav_layout.setContentsMargins(10, 18, 10, 18)
        self._nav_layout.setSpacing(6)

        brand = QLabel("KP")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setFixedSize(40, 40)
        brand.setStyleSheet("""
            QLabel {
                border-radius: 12px; background-color: #24c985; color: #052016;
                font-size: 15px; font-weight: 900;
            }
        """)
        self._nav_layout.addWidget(brand, 0, Qt.AlignmentFlag.AlignHCenter)
        self._nav_layout.addSpacing(12)

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
        self.tasks_page.categories_changed.connect(self.home_page.refresh_categories)

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
            nav_bg = "#0d0f13" if theme == "dark" else "#eef3f1"
            nav_border = "#20242b" if theme == "dark" else "#dbe5df"
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
            self.home_page.refresh_categories()
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
