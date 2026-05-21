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


if __name__ == "__main__":
    unittest.main()
