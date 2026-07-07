import unittest

from fh6auto_core.tasks import TaskSettings, task_settings_from_config, task_settings_from_values


class TaskSettingsTests(unittest.TestCase):
    def test_task_settings_from_config_accepts_wpf_config_shape(self):
        settings = task_settings_from_config(
            {
                "race_count": "7",
                "buy_count": "8",
                "cj_count": "9",
                "sc_count": "10",
                "sell_mode": 2,
                "cj_mode": 2,
            }
        )

        self.assertEqual(TaskSettings(7, 8, 9, 10, 2, 2), settings)

    def test_task_settings_from_values_falls_back_for_invalid_counts(self):
        settings = task_settings_from_values("bad", "", None, object(), "模式2：拍卖行卖车", "模式1")

        self.assertEqual(TaskSettings(99, 30, 30, 30, 2, 1), settings)


if __name__ == "__main__":
    unittest.main()
