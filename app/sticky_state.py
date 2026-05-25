from app.config import STICKY_MAX_WIDTH, STICKY_MIN_WIDTH


def get_active_task(tasks: list[dict], active_task_id: int | None) -> dict | None:
    for task in tasks:
        if task.get("id") == active_task_id and task.get("status") == "pending":
            return task
    return None


def get_next_task(tasks: list[dict], active_task_id: int | None) -> dict | None:
    for task in tasks:
        if task.get("status") == "pending" and task.get("id") != active_task_id:
            return task
    return None


def normalize_view_mode(view_mode: str, active_task: dict | None) -> str:
    if view_mode == "active" and active_task:
        return "active"
    return "list"


def resize_width(width: int, delta_x: int) -> int:
    return max(STICKY_MIN_WIDTH, min(STICKY_MAX_WIDTH, width + delta_x))


def non_hover_panel_alpha(transparency: int) -> int:
    value = max(0, min(100, int(transparency)))
    return round((100 - value) / 100 * 220)


def sticky_palette(mode: str, transparency: int, hovered: bool, brightness: int = 128) -> dict:
    if hovered or mode == "soft_panel":
        alpha_range = round(non_hover_panel_alpha(transparency) * 148 / 220)
        panel_alpha = 232 if hovered else 72 + alpha_range
        return {
            "panel": (18, 22, 28, panel_alpha),
            "panel_border": (255, 255, 255, 30),
            "task_text": "#f4f7fb",
            "meta_text": "#aeb7c2",
            "muted_text": "#8e99a6",
            "category_fill": (38, 48, 59, 190),
            "category_text": "#dbe6f2",
            "category_border": "#536171",
            "divider": (255, 255, 255, 22),
        }

    panel_alpha = non_hover_panel_alpha(transparency)
    if brightness > 150:
        return {
            "panel": (18, 22, 28, panel_alpha),
            "panel_border": (25, 32, 39, 50),
            "task_text": "#1a1a1a",
            "meta_text": "#3f4650",
            "muted_text": "#4d5661",
            "category_fill": (217, 223, 230, 168),
            "category_text": "#1a1f26",
            "category_border": "#aab6c5",
            "divider": (22, 30, 38, 35),
        }

    if brightness > 90:
        return {
            "panel": (18, 22, 28, panel_alpha),
            "panel_border": (255, 255, 255, 24),
            "task_text": "#333333",
            "meta_text": "#4d5661",
            "muted_text": "#59636f",
            "category_fill": (197, 206, 217, 168),
            "category_text": "#20262e",
            "category_border": "#8d9bab",
            "divider": (30, 39, 49, 32),
        }

    return {
        "panel": (18, 22, 28, panel_alpha),
        "panel_border": (255, 255, 255, 30),
        "task_text": "#e0e0e0",
        "meta_text": "#b9c3cf",
        "muted_text": "#a8b3bf",
        "category_fill": (42, 52, 64, 182),
        "category_text": "#eef4fb",
        "category_border": "#738295",
        "divider": (255, 255, 255, 22),
    }


def format_focus_seconds(seconds: int) -> str:
    total_minutes = max(0, int(seconds)) // 60
    hours, minutes = divmod(total_minutes, 60)
    if hours and minutes:
        return f"{hours}小时{minutes}分钟"
    if hours:
        return f"{hours}小时"
    return f"{minutes}分钟"


def start_message(task: dict) -> str:
    return f"先把「{task['content']}」推进一点。"


def complete_message(content: str) -> str:
    return f"「{content}」已经推进完成。"
