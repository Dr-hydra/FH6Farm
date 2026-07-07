import importlib
import sys
import tempfile
import unittest
from pathlib import Path

from fh6auto_core.headless_bot import HeadlessAutomationBot


class ImmediateThread:
    def __init__(self, target):
        self.target = target
        self.started = False

    def start(self):
        self.started = True
        self.target()


class FakeInput:
    def __init__(self):
        self.key_ups = []
        self.presses = []
        self.moves = []

    def key_down(self, key):
        return None

    def key_up(self, key):
        self.key_ups.append(key)

    def press(self, key, delay=0.08):
        self.presses.append((key, delay))

    def mouse_move(self, x, y):
        self.moves.append((x, y))


class FakeMouse:
    def __init__(self):
        self.mouse_up_count = 0

    def mouseDown(self):
        return None

    def mouseUp(self):
        self.mouse_up_count += 1


class FakeGameSession:
    def __init__(self):
        self.focus_calls = 0

    def check_and_focus_game(self):
        self.focus_calls += 1
        return True

    def set_english_input(self):
        return None


class FakeVision:
    template_cache = {}
    template_gray_cache = {}
    template_transparent_cache = {}
    scaled_template_cache = {}
    file_template_cache = {}
    last_positions = {}


class FakeRecovery:
    def attempt_recovery(self):
        return False


class FakeTaskObject:
    def __init__(self):
        self.calls = []

    def run(self, target_count):
        self.calls.append(("run", target_count))
        return True

    def run_recent(self, target_count):
        self.calls.append(("run_recent", target_count))
        return True

    def run_filtered(self, target_count):
        self.calls.append(("run_filtered", target_count))
        return True


class FakeRunner:
    def __init__(self, bot):
        self.bot = bot
        self.calls = []

    def run(self, start_step):
        self.calls.append(start_step)
        self.bot.stop_all()


def fake_pipeline_factory(bot):
    runner = FakeRunner(bot)
    task_objects = {
        "race": FakeTaskObject(),
        "buy": FakeTaskObject(),
        "cj": FakeTaskObject(),
        "sell": FakeTaskObject(),
    }
    return {}, runner, task_objects


class HeadlessBotTests(unittest.TestCase):
    def test_headless_module_does_not_import_legacy_main(self):
        original_main = sys.modules.pop("main", None)
        try:
            module = importlib.import_module("fh6auto_core.headless")
            importlib.reload(module)

            self.assertNotIn("main", sys.modules)
        finally:
            if original_main is not None:
                sys.modules["main"] = original_main

    def test_initializes_without_legacy_ui_or_config_shims(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            config_file.write_text('{"race_count": 5, "global_loops": 2}', encoding="utf-8")

            bot = HeadlessAutomationBot(
                config_file=str(config_file),
                input_controller=FakeInput(),
                game_session=FakeGameSession(),
                vision_service=FakeVision(),
                recovery_manager=FakeRecovery(),
                pipeline_factory=fake_pipeline_factory,
                screen_size_provider=lambda: (1280, 720),
                mouse_module=FakeMouse(),
                thread_factory=ImmediateThread,
                start_background_init=False,
                migrate_old_config=False,
            )

            self.assertTrue(bot.headless_mode)
            self.assertFalse(hasattr(bot, "setup_ui"))
            self.assertFalse(hasattr(bot, "entry_race"))
            self.assertEqual(5, bot.config["race_count"])
            self.assertEqual((0, 0, 1280, 720), bot.regions["全界面"])

    def test_start_pipeline_runs_and_stops_without_ctk_mainloop(self):
        fake_input = FakeInput()
        fake_mouse = FakeMouse()
        bot = HeadlessAutomationBot(
            input_controller=fake_input,
            game_session=FakeGameSession(),
            vision_service=FakeVision(),
            recovery_manager=FakeRecovery(),
            pipeline_factory=fake_pipeline_factory,
            screen_size_provider=lambda: (1280, 720),
            mouse_module=fake_mouse,
            thread_factory=ImmediateThread,
            start_background_init=False,
            migrate_old_config=False,
        )

        bot.start_pipeline("race")

        self.assertEqual(["race"], bot.pipeline_runner.calls)
        self.assertFalse(bot.is_running)
        self.assertTrue(bot._destroy_event.is_set())
        self.assertIn("w", fake_input.key_ups)
        self.assertGreaterEqual(fake_mouse.mouse_up_count, 1)


if __name__ == "__main__":
    unittest.main()
