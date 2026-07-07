import unittest

from fh6auto_core.game_session import GameSession


class GameSessionTests(unittest.TestCase):
    def test_snap_overlay_places_overlay_on_monitor_right_edge(self):
        calls = []
        session = GameSession(
            is_running=lambda: True,
            set_overlay_geometry=lambda *args: calls.append(args),
        )

        session._snap_overlay(100, 50, 1920, 1080)

        self.assertEqual(calls, [(1232, 70, 768, 162)])

    def test_snap_overlay_respects_minimum_size(self):
        calls = []
        session = GameSession(
            is_running=lambda: True,
            set_overlay_geometry=lambda *args: calls.append(args),
        )

        session._snap_overlay(0, 0, 1280, 720)

        self.assertEqual(calls, [(610, 20, 650, 150)])

    def test_snap_overlay_skips_when_not_running(self):
        calls = []
        session = GameSession(
            is_running=lambda: False,
            set_overlay_geometry=lambda *args: calls.append(args),
        )

        session._snap_overlay(0, 0, 1920, 1080)

        self.assertEqual([], calls)

    def test_snap_overlay_uses_ui_scheduler_when_available(self):
        calls = []
        scheduled = []
        session = GameSession(
            ui_call=lambda func: scheduled.append(func),
            is_running=lambda: True,
            set_overlay_geometry=lambda *args: calls.append(args),
        )

        session._snap_overlay(0, 0, 1920, 1080)

        self.assertEqual([], calls)
        self.assertEqual(1, len(scheduled))
        scheduled[0]()
        self.assertEqual([(1132, 20, 768, 162)], calls)


if __name__ == "__main__":
    unittest.main()
