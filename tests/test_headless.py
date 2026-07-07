import importlib
import sys
import unittest

from fh6auto_core.headless import run_headless


class FakeBot:
    instances = []

    def __init__(self):
        self.calls = []
        FakeBot.instances.append(self)

    def after(self, delay_ms, callback):
        self.calls.append(("after", delay_ms))
        callback()

    def start_pipeline(self, start_step):
        self.calls.append(("start_pipeline", start_step))

    def mainloop(self):
        self.calls.append(("mainloop",))


class HeadlessEntrypointTests(unittest.TestCase):
    def test_import_headless_does_not_import_default_bot_or_legacy_main(self):
        original_main = sys.modules.pop("main", None)
        original_bot = sys.modules.pop("fh6auto_core.headless_bot", None)
        try:
            module = importlib.import_module("fh6auto_core.headless")
            importlib.reload(module)

            self.assertNotIn("main", sys.modules)
            self.assertNotIn("fh6auto_core.headless_bot", sys.modules)
        finally:
            if original_main is not None:
                sys.modules["main"] = original_main
            if original_bot is not None:
                sys.modules["fh6auto_core.headless_bot"] = original_bot

    def test_run_headless_starts_requested_step_without_legacy_constructor_args(self):
        FakeBot.instances = []

        run_headless(bot_cls=FakeBot, start_step="buy")

        self.assertEqual(
            [("after", 800), ("start_pipeline", "buy"), ("mainloop",)],
            FakeBot.instances[0].calls,
        )


if __name__ == "__main__":
    unittest.main()
