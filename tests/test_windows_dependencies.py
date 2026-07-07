import types
import unittest
from unittest.mock import Mock, patch

from fh6auto_core import windows_dependencies


class WindowsDependencyTests(unittest.TestCase):
    def test_skips_checks_on_non_windows(self):
        with patch.object(windows_dependencies.sys, "platform", "linux"):
            self.assertEqual([], windows_dependencies.check_windows_dependencies())

    def test_returns_missing_dlls_and_warns_on_windows(self):
        message_box = Mock()
        fake_windll = types.SimpleNamespace(
            user32=types.SimpleNamespace(MessageBoxW=message_box)
        )

        with patch.object(windows_dependencies.sys, "platform", "win32"):
            with patch.object(windows_dependencies.ctypes, "WinDLL", side_effect=OSError):
                with patch.object(windows_dependencies.ctypes, "windll", fake_windll):
                    missing = windows_dependencies.check_windows_dependencies()

        self.assertEqual(
            ["vcruntime140.dll", "msvcp140.dll", "vcruntime140_1.dll"],
            missing,
        )
        message_box.assert_called_once()


if __name__ == "__main__":
    unittest.main()
