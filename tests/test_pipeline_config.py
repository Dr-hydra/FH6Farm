import unittest

from fh6auto_core.pipeline_config import (
    parse_next_index,
    parse_total_loops,
    pipeline_settings_from_config,
    pipeline_settings_from_values,
)


class PipelineConfigTests(unittest.TestCase):
    def test_parse_total_loops_uses_integer_value(self):
        self.assertEqual(7, parse_total_loops("7", fallback=10))

    def test_parse_total_loops_falls_back_when_invalid(self):
        self.assertEqual(10, parse_total_loops("bad", fallback=10))

    def test_parse_next_index_returns_none_when_current_step_disabled(self):
        self.assertIsNone(parse_next_index(False, "2", 0))

    def test_parse_next_index_converts_one_based_ui_value_to_zero_based_index(self):
        self.assertEqual(2, parse_next_index(True, "3", 0))

    def test_parse_next_index_clamps_to_legacy_four_step_range(self):
        self.assertEqual(0, parse_next_index(True, "-9", 0))
        self.assertEqual(3, parse_next_index(True, "99", 0))

    def test_parse_next_index_uses_legacy_default_when_invalid(self):
        self.assertEqual(2, parse_next_index(True, "bad", 1))

    def test_pipeline_settings_from_values_snapshots_loop_and_step_rules(self):
        settings = pipeline_settings_from_values(
            total_loops="6",
            enabled_values=(True, "false", True, True),
            next_values=("2", "bad", "99", "1"),
        )

        self.assertEqual(6, settings.total_loops)
        self.assertEqual(1, settings.get_next_index(0))
        self.assertIsNone(settings.get_next_index(1))
        self.assertEqual(3, settings.get_next_index(2))
        self.assertEqual(0, settings.get_next_index(3))

    def test_pipeline_settings_from_config_accepts_wpf_config_shape(self):
        settings = pipeline_settings_from_config(
            {
                "global_loops": 3,
                "chk_1": True,
                "chk_2": False,
                "chk_3": True,
                "chk_4": True,
                "next_1": 2,
                "next_2": 3,
                "next_3": 4,
                "next_4": 1,
            }
        )

        self.assertEqual(3, settings.total_loops)
        self.assertEqual(1, settings.get_next_index(0))
        self.assertIsNone(settings.get_next_index(1))
        self.assertEqual(3, settings.get_next_index(2))


if __name__ == "__main__":
    unittest.main()
