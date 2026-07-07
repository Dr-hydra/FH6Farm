import json
import tempfile
import unittest
from pathlib import Path

from fh6auto_core.config import DEFAULT_CONFIG, ensure_config_file, load_config


class ConfigFileTests(unittest.TestCase):
    def test_ensure_does_not_rewrite_existing_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            original = '{"race_count": 777, "custom_key": "keep-me"}\n'
            path.write_text(original, encoding="utf-8")

            config = ensure_config_file(path)

            self.assertEqual(777, config["race_count"])
            self.assertEqual("keep-me", config["custom_key"])
            self.assertEqual(original, path.read_text(encoding="utf-8"))

    def test_invalid_config_is_not_replaced_with_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            original = '{"race_count": 777'
            path.write_text(original, encoding="utf-8")

            with self.assertRaises(json.JSONDecodeError):
                ensure_config_file(path)

            self.assertEqual(original, path.read_text(encoding="utf-8"))

    def test_utf8_bom_config_is_supported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            path.write_text('{"race_count": 777}', encoding="utf-8-sig")

            config = load_config(path)

            self.assertEqual(777, config["race_count"])

    def test_missing_config_uses_shared_wpf_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"

            config = load_config(path)

            self.assertEqual(DEFAULT_CONFIG["next_3"], config["next_3"])
            self.assertEqual(4, config["next_3"])
            self.assertEqual("race", config["hotkey_start_task"])


if __name__ == "__main__":
    unittest.main()
