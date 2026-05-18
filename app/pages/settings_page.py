from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QFrame, QFileDialog, QColorDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import os
import json

from app.config import (
    get_display_count, set_display_count,
    get_overdue_color, set_overdue_color,
    get_font_size, set_font_size,
    get_autostart, set_autostart,
)
from app.db import export_all_data, clear_all_data


class SettingsPage(QWidget):
    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(16)

        title = QLabel("设置")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #d4d4d4;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("QFrame { color: #2a2a2a; }")
        layout.addWidget(sep)

        # 显示条数
        layout.addLayout(self._setting_row(
            "显示条数上限",
            self._spin(get_display_count(), 1, 20, set_display_count)
        ))

        # 超时颜色
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("超时提醒颜色"))
        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(32, 32)
        self._color_btn.setStyleSheet(f"QPushButton {{ background: {get_overdue_color()}; border: 1px solid #3a3a3a; border-radius: 4px; }}")
        self._color_btn.clicked.connect(self._pick_color)
        color_layout.addWidget(self._color_btn)
        color_layout.addStretch()
        layout.addLayout(color_layout)

        # 字体大小
        layout.addLayout(self._setting_row(
            "便签字体大小",
            self._spin(get_font_size(), 10, 36, set_font_size)
        ))

        # 开机自启
        auto_layout = QHBoxLayout()
        auto_layout.addWidget(QLabel("开机自启"))
        self._auto_btn = QPushButton("开" if get_autostart() else "关")
        self._auto_btn.setFixedWidth(48)
        self._update_auto_style()
        self._auto_btn.clicked.connect(self._toggle_autostart)
        auto_layout.addWidget(self._auto_btn)
        auto_layout.addStretch()
        layout.addLayout(auto_layout)

        layout.addStretch()

        # 数据管理
        mgmt_label = QLabel("数据管理")
        mgmt_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #999; margin-top: 16px;")
        layout.addWidget(mgmt_label)

        data_layout = QHBoxLayout()
        export_btn = QPushButton("导出数据")
        export_btn.clicked.connect(self._export_data)
        data_layout.addWidget(export_btn)
        clear_btn = QPushButton("清空所有数据")
        clear_btn.setStyleSheet("QPushButton { border-color: #5a3a3a; color: #e08888; } QPushButton:hover { background: #3a2020; }")
        clear_btn.clicked.connect(self._clear_data)
        data_layout.addWidget(clear_btn)
        data_layout.addStretch()
        layout.addLayout(data_layout)

        # 版本
        version_lbl = QLabel("版本: 1.0.0")
        version_lbl.setStyleSheet("color: #555; font-size: 11px;")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_lbl)

    def refresh(self):
        self._color_btn.setStyleSheet(f"QPushButton {{ background: {get_overdue_color()}; border: 1px solid #3a3a3a; border-radius: 4px; }}")

    def _setting_row(self, label: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addWidget(widget)
        row.addStretch()
        return row

    def _spin(self, initial: int, min_v: int, max_v: int, setter) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(min_v, max_v)
        spin.setValue(initial)
        spin.setFixedWidth(72)
        spin.valueChanged.connect(lambda v: [setter(v), self.settings_changed.emit()])
        return spin

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(get_overdue_color()), self, "选择超时提醒颜色")
        if color.isValid():
            hex_color = color.name()
            set_overdue_color(hex_color)
            self._color_btn.setStyleSheet(f"QPushButton {{ background: {hex_color}; border: 1px solid #3a3a3a; border-radius: 4px; }}")
            self.settings_changed.emit()

    def _toggle_autostart(self):
        enabled = not get_autostart()
        set_autostart(enabled)
        self._auto_btn.setText("开" if enabled else "关")
        self._update_auto_style()
        self._apply_autostart(enabled)
        self.settings_changed.emit()

    def _update_auto_style(self):
        enabled = get_autostart()
        if enabled:
            self._auto_btn.setStyleSheet("QPushButton { background: #2a4a3a; color: #7ecf8a; border: 1px solid #3a5a3a; border-radius: 4px; }")
        else:
            self._auto_btn.setStyleSheet("QPushButton { background: #2a2a2a; color: #888; border: 1px solid #3a3a3a; border-radius: 4px; }")

    def _apply_autostart(self, enabled: bool):
        import sys
        startup_dir = os.path.join(os.getenv("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        shortcut_path = os.path.join(startup_dir, "KeenPie.lnk")
        if enabled:
            try:
                import pythoncom
                from win32com.client import Dispatch
                pythoncom.CoInitialize()
                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortcut(shortcut_path)
                shortcut.TargetPath = sys.executable
                shortcut.Arguments = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "main.py")
                shortcut.WorkingDirectory = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                shortcut.Save()
            except Exception:
                pass
        else:
            try:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
            except Exception:
                pass

    def _export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出数据", "keenpie_export.json", "JSON (*.json)")
        if path:
            data = export_all_data()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "导出成功", f"数据已导出到:\n{path}")

    def _clear_data(self):
        reply = QMessageBox.warning(
            self, "确认清空", "此操作将删除所有事项数据，不可恢复。确定继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            clear_all_data()
            self.settings_changed.emit()
