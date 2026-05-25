import tempfile
import unittest
from pathlib import Path

from app import db


class CategoryDatabaseTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._old_db_path = db.DB_PATH
        db.DB_PATH = str(Path(self._tmpdir.name) / "test.db")
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self._old_db_path
        self._tmpdir.cleanup()

    def test_default_categories_are_created(self):
        self.assertEqual(db.get_categories(), ["学习", "工作", "娱乐", "生活"])

    def test_custom_category_can_be_added_once(self):
        self.assertTrue(db.add_category("健身"))
        self.assertFalse(db.add_category("健身"))
        self.assertEqual(db.get_categories(), ["学习", "工作", "娱乐", "生活", "健身"])

    def test_task_category_is_persisted(self):
        task_id = db.upsert_task({
            "date": "2026-05-21",
            "sort_order": 0,
            "content": "写周报",
            "category": "工作",
            "time_label": None,
            "time_value": None,
            "status": "pending",
        })

        task = db.get_tasks_by_date("2026-05-21")[0]

        self.assertEqual(task["id"], task_id)
        self.assertEqual(task["category"], "工作")


    def test_focus_sessions_are_summed_by_task_and_date(self):
        task_id = db.upsert_task({
            "date": "2026-05-25",
            "sort_order": 0,
            "content": "写周报",
            "category": "工作",
            "time_label": None,
            "time_value": None,
            "status": "pending",
        })

        db.add_focus_session(task_id, "2026-05-25", "2026-05-25T09:00:00", "2026-05-25T09:25:00", 1500)
        db.add_focus_session(task_id, "2026-05-25", "2026-05-25T10:00:00", "2026-05-25T10:05:00", 300)
        db.add_focus_session(task_id, "2026-05-24", "2026-05-24T10:00:00", "2026-05-24T10:05:00", 300)

        self.assertEqual(db.get_task_focus_seconds(task_id, "2026-05-25"), 1800)

    def test_focus_session_for_missing_task_is_ignored(self):
        db.add_focus_session(999, "2026-05-25", "2026-05-25T09:00:00", "2026-05-25T09:10:00", 600)
        self.assertEqual(db.get_task_focus_seconds(999, "2026-05-25"), 0)


if __name__ == "__main__":
    unittest.main()
