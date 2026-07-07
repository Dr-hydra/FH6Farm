import unittest

from fh6auto_core.config_runtime import ConfigPipelineRuntime
from fh6auto_core.headless_pipeline import create_headless_pipeline
from fh6auto_core.pipeline_runner import PipelineRunner


class FakeBot:
    def __init__(self):
        self.config = {
            "race_count": 7,
            "buy_count": 8,
            "cj_count": 9,
            "sc_count": 10,
            "sell_mode": 2,
            "cj_mode": 1,
        }


class FakeTask:
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


class HeadlessPipelineTests(unittest.TestCase):
    def test_uses_config_runtime_and_config_task_settings(self):
        bot = FakeBot()

        tasks, runner, task_objects = create_headless_pipeline(bot)
        race = FakeTask()
        sell = FakeTask()
        task_objects["race"] = race
        task_objects["sell"] = sell

        self.assertIsInstance(runner, PipelineRunner)
        self.assertIsInstance(runner.runtime, ConfigPipelineRuntime)
        self.assertTrue(tasks["race"].run())
        self.assertTrue(tasks["sell"].run())

        self.assertEqual([("run", 7)], race.calls)
        self.assertEqual([("run_recent", 10)], sell.calls)


if __name__ == "__main__":
    unittest.main()
