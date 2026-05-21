import unittest

from app.sticky_state import (
    complete_message,
    get_active_task,
    get_next_task,
    normalize_view_mode,
    resize_width,
)


TASKS = [
    {"id": 1, "content": "写周报", "status": "pending"},
    {"id": 2, "content": "听英语", "status": "pending"},
    {"id": 3, "content": "已完成", "status": "done"},
]


class StickyStateTest(unittest.TestCase):
    def test_active_task_is_found_only_when_pending(self):
        self.assertEqual(get_active_task(TASKS, 2)["content"], "听英语")
        self.assertIsNone(get_active_task(TASKS, 3))
        self.assertIsNone(get_active_task(TASKS, 99))

    def test_next_task_skips_the_active_task(self):
        self.assertEqual(get_next_task(TASKS, 1)["id"], 2)
        self.assertEqual(get_next_task(TASKS, None)["id"], 1)

    def test_view_mode_falls_back_to_list_without_active_task(self):
        self.assertEqual(normalize_view_mode("active", None), "list")
        self.assertEqual(normalize_view_mode("active", TASKS[0]), "active")
        self.assertEqual(normalize_view_mode("unknown", TASKS[0]), "list")

    def test_resize_width_clamps_bounds(self):
        self.assertEqual(resize_width(360, 40), 400)
        self.assertEqual(resize_width(280, -50), 280)
        self.assertEqual(resize_width(680, 50), 680)

    def test_completion_message_is_encouraging(self):
        self.assertIn("推进", complete_message("写周报"))

    def test_missing_active_task_returns_list_mode(self):
        missing = get_active_task(TASKS, 77)
        self.assertIsNone(missing)
        self.assertEqual(normalize_view_mode("active", missing), "list")
