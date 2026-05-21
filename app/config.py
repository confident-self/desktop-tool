from PySide6.QtCore import QSettings

SETTINGS = QSettings("KeenPie", "KeenPie")
INPUT_TIME_MODES = {"none", "period", "precise"}
STICKY_VIEW_MODES = {"list", "active"}
STICKY_MIN_WIDTH = 280
STICKY_DEFAULT_WIDTH = 360
STICKY_MAX_WIDTH = 680


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


def get_theme() -> str:
    return SETTINGS.value("display/theme", "light")


def set_theme(theme: str):
    SETTINGS.setValue("display/theme", theme)


def get_input_time_mode() -> str:
    mode = SETTINGS.value("task/input_time_mode", "precise")
    return mode if mode in INPUT_TIME_MODES else "precise"


def set_input_time_mode(mode: str):
    if mode in INPUT_TIME_MODES:
        SETTINGS.setValue("task/input_time_mode", mode)


def _clamp_sticky_width(width: int) -> int:
    return max(STICKY_MIN_WIDTH, min(STICKY_MAX_WIDTH, width))


def get_sticky_width() -> int:
    return _clamp_sticky_width(int(SETTINGS.value("sticky/width", STICKY_DEFAULT_WIDTH)))


def set_sticky_width(width: int):
    SETTINGS.setValue("sticky/width", _clamp_sticky_width(int(width)))


def get_sticky_view_mode() -> str:
    mode = SETTINGS.value("sticky/view_mode", "list")
    return mode if mode in STICKY_VIEW_MODES else "list"


def set_sticky_view_mode(mode: str):
    if mode in STICKY_VIEW_MODES:
        SETTINGS.setValue("sticky/view_mode", mode)


def get_active_task_id() -> int | None:
    value = SETTINGS.value("sticky/active_task_id")
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_active_started_at() -> str | None:
    value = SETTINGS.value("sticky/active_started_at")
    return str(value) if value else None


def set_active_task(task_id: int, started_at: str):
    SETTINGS.setValue("sticky/active_task_id", int(task_id))
    SETTINGS.setValue("sticky/active_started_at", started_at)


def clear_active_task():
    SETTINGS.remove("sticky/active_task_id")
    SETTINGS.remove("sticky/active_started_at")
