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


def start_message(task: dict) -> str:
    return f"先把「{task['content']}」推进一点。"


def complete_message(content: str) -> str:
    return f"「{content}」已经推进完成。"
