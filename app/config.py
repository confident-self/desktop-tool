from PySide6.QtCore import QSettings

SETTINGS = QSettings("KeenPie", "KeenPie")


def get_display_count() -> int:
    return int(SETTINGS.value("display/count", 4))


def set_display_count(count: int):
    SETTINGS.setValue("display/count", count)


def get_overdue_color() -> str:
    return SETTINGS.value("display/overdue_color", "#FF4444")


def set_overdue_color(color: str):
    SETTINGS.setValue("display/overdue_color", color)


def get_font_size() -> int:
    return int(SETTINGS.value("display/font_size", 14))


def set_font_size(size: int):
    SETTINGS.setValue("display/font_size", size)


def get_autostart() -> bool:
    val = SETTINGS.value("system/autostart", False)
    if isinstance(val, str):
        return val.lower() == "true"
    return bool(val)


def set_autostart(enabled: bool):
    SETTINGS.setValue("system/autostart", enabled)


def get_transparency() -> int:
    return int(SETTINGS.value("display/transparency", 100))


def set_transparency(value: int):
    SETTINGS.setValue("display/transparency", value)
