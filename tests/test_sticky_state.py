import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from app.sticky_overlay import StickyOverlay
from app.sticky_state import (
    complete_message,
    get_active_task,
    get_next_task,
    non_hover_panel_alpha,
    normalize_view_mode,
    resize_width,
    sticky_palette,
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

    def test_non_hover_panel_alpha_tracks_transparency_setting(self):
        self.assertEqual(non_hover_panel_alpha(100), 0)
        self.assertEqual(non_hover_panel_alpha(50), 110)
        self.assertEqual(non_hover_panel_alpha(0), 220)

    def test_soft_panel_palette_keeps_a_visible_backing_panel(self):
        palette = sticky_palette("soft_panel", 100, hovered=False, brightness=230)
        slightly_denser = sticky_palette("soft_panel", 90, hovered=False, brightness=230)
        denser = sticky_palette("soft_panel", 50, hovered=False, brightness=230)

        self.assertGreater(palette["panel"][3], 0)
        self.assertGreater(slightly_denser["panel"][3], palette["panel"][3])
        self.assertGreater(denser["panel"][3], palette["panel"][3])
        self.assertEqual(palette["task_text"], "#f4f7fb")
        self.assertNotEqual(palette["category_fill"], "#173c31")

    def test_adaptive_palette_switches_text_for_light_and_dark_backgrounds(self):
        light = sticky_palette("adaptive", 100, hovered=False, brightness=220)
        dark = sticky_palette("adaptive", 100, hovered=False, brightness=35)

        self.assertEqual(light["task_text"], "#1a1a1a")
        self.assertEqual(dark["task_text"], "#e0e0e0")
        self.assertNotEqual(light["category_text"], dark["category_text"])
        self.assertLess(light["category_fill"][3], 255)
        self.assertLess(dark["category_fill"][3], 255)

    def test_loading_tasks_requests_overlay_repaint(self):
        app = QApplication.instance() or QApplication([])
        overlay = StickyOverlay()
        task = {
            "id": 1,
            "content": "写周报",
            "category": "工作",
            "time_label": None,
            "time_value": None,
            "status": "pending",
        }
        with patch("app.sticky_overlay.get_pending_tasks", return_value=[task]):
            with patch.object(overlay, "update") as update:
                overlay.load_tasks("2026-05-22")
        update.assert_called_once()
        overlay.close()
        app.processEvents()

    def test_adaptive_overlay_refreshes_sampled_row_brightness_when_tasks_load(self):
        app = QApplication.instance() or QApplication([])
        overlay = StickyOverlay()
        task = {
            "id": 1,
            "content": "写周报",
            "category": "工作",
            "time_label": None,
            "time_value": None,
            "status": "pending",
        }
        with patch("app.sticky_overlay.get_sticky_readability_mode", return_value="adaptive"):
            with patch("app.sticky_overlay.get_pending_tasks", return_value=[task]):
                with patch("app.sticky_overlay.sample_global_rect", return_value=[220] * 10) as sample:
                    overlay.load_tasks("2026-05-22")
        sample.assert_called_once()
        self.assertEqual(overlay._row_brightness, [220])
        overlay.close()
        app.processEvents()
