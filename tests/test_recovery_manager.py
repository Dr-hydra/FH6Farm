import os
import tempfile
import unittest

from fh6auto_core.recovery_manager import RecoveryManager


class FakeVision:
    def __init__(self):
        self.menu_hits = []
        self.gray_calls = []
        self.any_gray_calls = []
        self.image_hits = {}

    def find_image_gray(self, path, region=None, threshold=0.75, fast_mode=True):
        self.gray_calls.append((path, region, threshold, fast_mode))
        if path == "collectionjournal.png":
            return self.menu_hits.pop(0) if self.menu_hits else None
        return None

    def find_any_image_gray(self, image_list, region=None, threshold=0.75, fast_mode=True):
        self.any_gray_calls.append((list(image_list), region, threshold, fast_mode))
        return None

    def find_image(self, path, region=None, threshold=0.75, fast_mode=True):
        return self.image_hits.get(path)

    def find_image_transparent(self, path, region=None, threshold=0.75, fast_mode=True):
        if path == "horizon6.png":
            return self.image_hits.get(path)
        return None


def make_manager(vision=None, **kwargs):
    options = {
        "vision": vision or FakeVision(),
        "logger": lambda message: None,
        "regions_provider": lambda: {"全界面": (0, 0, 100, 100), "左": (0, 0, 50, 100), "左下": (0, 50, 50, 50)},
        "running_checker": lambda: True,
        "pause_handler": lambda: None,
        "focus_game": lambda: True,
        "key_press": lambda key, delay=None: None,
        "click": lambda pos: None,
        "command_runner": lambda command: 0,
        "sleep_func": lambda seconds: None,
        "auto_restart_enabled": lambda: True,
        "restart_command_provider": lambda: "start test",
    }
    options.update(kwargs)
    return RecoveryManager(**options)


class RecoveryManagerTests(unittest.TestCase):
    def test_restart_game_respects_auto_restart_setting(self):
        commands = []
        manager = make_manager(
            auto_restart_enabled=lambda: False,
            command_runner=lambda command: commands.append(command),
        )

        self.assertFalse(manager.restart_game_and_boot())
        self.assertEqual([], commands)

    def test_force_restart_ignores_auto_restart_setting_and_focuses_game(self):
        commands = []
        focus_calls = []
        clock = [0.0]
        vision = FakeVision()
        vision.image_hits["horizon6.png"] = (1, 2)
        manager = make_manager(
            vision=vision,
            auto_restart_enabled=lambda: False,
            command_runner=lambda command: commands.append(command),
            focus_game=lambda: (focus_calls.append("focus") or True),
            sleep_func=lambda seconds: clock.__setitem__(0, clock[0] + seconds),
            time_func=lambda: clock[0],
        )
        manager.enter_menu = lambda: True

        self.assertTrue(manager.restart_game_and_boot(force_test=True))
        self.assertEqual(["start test"], commands)
        self.assertEqual(["focus"], focus_calls)

    def test_enter_menu_presses_escape_until_anchor_found(self):
        vision = FakeVision()
        vision.menu_hits = [None, (10, 20)]
        pressed = []
        manager = make_manager(vision=vision, key_press=lambda key, delay=None: pressed.append(key))

        self.assertTrue(manager.enter_menu())
        self.assertEqual(["esc"], pressed)

    def test_advanced_enter_menu_clicks_dynamic_obstacle(self):
        vision = FakeVision()
        clicked = []

        def find_any(image_list, region=None, threshold=0.75, fast_mode=True):
            vision.any_gray_calls.append((list(image_list), region, threshold, fast_mode))
            return (5, 6)

        vision.find_any_image_gray = find_any

        with tempfile.TemporaryDirectory() as tmp_dir:
            obstacle_dir = os.path.join(tmp_dir, "obstacles")
            os.makedirs(obstacle_dir)
            open(os.path.join(obstacle_dir, "dialog.png"), "wb").close()

            attempts = [False, True]
            manager = make_manager(
                vision=vision,
                obstacles_dir=obstacle_dir,
                click=lambda pos: clicked.append(pos),
            )
            manager.is_in_menu = lambda: attempts.pop(0)

            self.assertTrue(manager.advanced_enter_menu())

        self.assertEqual([(5, 6)], clicked)
        self.assertEqual([["obstacles/dialog.png"]], [call[0] for call in vision.any_gray_calls])

    def test_attempt_recovery_restarts_when_focus_fails(self):
        manager = make_manager(focus_game=lambda: False)
        restart_calls = []
        manager.restart_game_and_boot = lambda: (restart_calls.append("restart") or True)

        self.assertTrue(manager.attempt_recovery())
        self.assertEqual(["restart"], restart_calls)


if __name__ == "__main__":
    unittest.main()
