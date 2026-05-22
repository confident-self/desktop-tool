import unittest

from PySide6.QtCore import QCoreApplication, QSettings

from app import config


class PreferenceSettingsTest(unittest.TestCase):
    def setUp(self):
        QCoreApplication.setOrganizationName("KeenPieTests")
        QCoreApplication.setApplicationName("StickyFocusPreferences")
        self._settings = QSettings("KeenPieTests", "StickyFocusPreferences")
        self._settings.clear()
        self._old_settings = config.SETTINGS
        config.SETTINGS = self._settings

    def tearDown(self):
        self._settings.clear()
        config.SETTINGS = self._old_settings

    def test_input_mode_defaults_and_rejects_unknown_values(self):
        self.assertEqual(config.get_input_time_mode(), "precise")

        config.set_input_time_mode("none")
        self.assertEqual(config.get_input_time_mode(), "none")

        config.SETTINGS.setValue("task/input_time_mode", "strange")
        self.assertEqual(config.get_input_time_mode(), "precise")

    def test_sticky_width_is_clamped(self):
        config.SETTINGS.setValue("sticky/width", 120)
        self.assertEqual(config.get_sticky_width(), config.STICKY_MIN_WIDTH)

        config.SETTINGS.setValue("sticky/width", 9999)
        self.assertEqual(config.get_sticky_width(), config.STICKY_MAX_WIDTH)

    def test_sticky_width_round_trips_after_resize_save(self):
        config.set_sticky_width(412)
        self.assertEqual(config.get_sticky_width(), 412)

    def test_sticky_readability_mode_defaults_round_trips_and_rejects_unknown_values(self):
        self.assertEqual(config.get_sticky_readability_mode(), "soft_panel")

        config.set_sticky_readability_mode("adaptive")
        self.assertEqual(config.get_sticky_readability_mode(), "adaptive")

        config.SETTINGS.setValue("sticky/readability_mode", "unknown")
        self.assertEqual(config.get_sticky_readability_mode(), "soft_panel")

    def test_active_task_context_round_trips(self):
        config.set_active_task(42, "2026-05-21T09:30:00")

        self.assertEqual(config.get_active_task_id(), 42)
        self.assertEqual(config.get_active_started_at(), "2026-05-21T09:30:00")

        config.clear_active_task()
        self.assertIsNone(config.get_active_task_id())
        self.assertIsNone(config.get_active_started_at())

    def test_home_page_mode_can_be_seeded_from_saved_preference(self):
        config.set_input_time_mode("none")
        self.assertEqual(config.get_input_time_mode(), "none")
