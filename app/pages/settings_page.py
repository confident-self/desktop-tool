from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QSlider, QFrame, QFileDialog, QColorDialog, QMessageBox, QScrollArea,
    QComboBox
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
    get_transparency, set_transparency,
    get_theme, set_theme,
    get_sticky_readability_mode, set_sticky_readability_mode,
)
from app.db import export_all_data, clear_all_data


class SettingsPage(QWidget):
    settings_changed = Signal()
    theme_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(22, 18, 22, 16)
        root_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollArea > QWidget > QWidget { background: transparent; }")
        root_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("设置")
        title.setProperty("title", True)
        layout.addWidget(title)

        tip = QLabel("控制置顶便签展示、启动行为和数据维护")
        tip.setProperty("muted", True)
        tip.setWordWrap(True)
        layout.addWidget(tip)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setProperty("HLine", True)
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

        # 主题切换
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("界面主题"))
        self._theme_dark = QPushButton("深色")
        self._theme_light = QPushButton("浅色")
        self._theme_dark.setFixedWidth(56)
        self._theme_light.setFixedWidth(56)
        self._theme_dark.setCheckable(True)
        self._theme_light.setCheckable(True)
        current = get_theme()
        self._theme_dark.setChecked(current == "dark")
        self._theme_light.setChecked(current == "light")
        self._theme_dark.clicked.connect(lambda: self._on_theme_switch("dark"))
        self._theme_light.clicked.connect(lambda: self._on_theme_switch("light"))
        theme_layout.addWidget(self._theme_dark)
        theme_layout.addWidget(self._theme_light)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        # 非悬浮便签透明度
        transp_layout = QHBoxLayout()
        transp_layout.addWidget(QLabel("非悬浮透明度"))
        self._transp_slider = QSlider(Qt.Orientation.Horizontal)
        self._transp_slider.setRange(0, 100)
        self._transp_slider.setValue(get_transparency())
        self._transp_slider.setFixedWidth(180)
        self._transp_slider.valueChanged.connect(self._on_transparency_changed)
        self._transp_label = QLabel(f"{get_transparency()}%")
        self._transp_label.setFixedWidth(40)
        self._transp_label.setStyleSheet("")
        transp_layout.addWidget(self._transp_slider)
        transp_layout.addWidget(self._transp_label)
        transp_layout.addStretch()
        layout.addLayout(transp_layout)

        readability_layout = QHBoxLayout()
        readability_layout.addWidget(QLabel("便签可读性模式"))
        self._readability_combo = QComboBox()
        self._readability_combo.addItem("柔和底板", "soft_panel")
        self._readability_combo.addItem("智能适配", "adaptive")
        self._readability_combo.setCurrentIndex(self._readability_index())
        self._readability_combo.currentIndexChanged.connect(self._on_readability_mode_changed)
        readability_layout.addWidget(self._readability_combo)
        readability_layout.addStretch()
        layout.addLayout(readability_layout)

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
        mgmt_label.setStyleSheet("font-size: 13px; font-weight: bold; margin-top: 12px;")
        layout.addWidget(mgmt_label)

        data_layout = QHBoxLayout()
        export_btn = QPushButton("导出数据")
        export_btn.clicked.connect(self._export_data)
        data_layout.addWidget(export_btn)
        clear_btn = QPushButton("清空所有数据")
        clear_btn.setProperty("danger", True)
        clear_btn.clicked.connect(self._clear_data)
        data_layout.addWidget(clear_btn)
        data_layout.addStretch()
        layout.addLayout(data_layout)

        # 版本
        version_lbl = QLabel("版本: 1.0.0")
        version_lbl.setProperty("muted", True)
        version_lbl.setStyleSheet("font-size: 11px;")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_lbl)

    def refresh(self):
        self._color_btn.setStyleSheet(f"QPushButton {{ background: {get_overdue_color()}; border: 1px solid #3a3a3a; border-radius: 4px; }}")
        self._transp_slider.blockSignals(True)
        self._transp_slider.setValue(get_transparency())
        self._transp_slider.blockSignals(False)
        self._transp_label.setText(f"{get_transparency()}%")
        self._readability_combo.blockSignals(True)
        self._readability_combo.setCurrentIndex(self._readability_index())
        self._readability_combo.blockSignals(False)

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

    def _on_theme_switch(self, theme: str):
        set_theme(theme)
        self._theme_dark.setChecked(theme == "dark")
        self._theme_light.setChecked(theme == "light")
        self.theme_changed.emit(theme)

    def _on_transparency_changed(self, value: int):
        set_transparency(value)
        self._transp_label.setText(f"{value}%")
        self.settings_changed.emit()

    def _readability_index(self) -> int:
        return max(0, self._readability_combo.findData(get_sticky_readability_mode()))

    def _on_readability_mode_changed(self, index: int):
        set_sticky_readability_mode(self._readability_combo.itemData(index))
        self.settings_changed.emit()

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
        self._auto_btn.setProperty("accent", enabled)
        self._auto_btn.style().unpolish(self._auto_btn)
        self._auto_btn.style().polish(self._auto_btn)

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
