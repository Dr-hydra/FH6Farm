import unittest

from fh6auto_core.config_runtime import ConfigPipelineRuntime


class FakeBot:
    def __init__(self):
        self.config = {
            "global_loops": 3,
            "chk_1": True,
            "chk_2": False,
            "chk_3": True,
            "chk_4": True,
            "next_1": 2,
            "next_2": 3,
            "next_3": 4,
            "next_4": 1,
            "auto_close_game": False,
            "auto_shutdown": False,
        }
        self.is_running = True
        self.global_loop_current = 0
        self.race_counter = 3
        self.car_counter = 4
        self.cj_counter = 5
        self.sc_count = 6
        self.logs = []
        self.stopped = False

    def check_and_focus_game(self):
        return True

    def stop_all(self):
        self.stopped = True

    def log(self, message):
        self.logs.append(message)

    def attempt_recovery(self):
        return False


class ConfigPipelineRuntimeTests(unittest.TestCase):
    def test_reads_loop_and_next_step_rules_from_config(self):
        bot = FakeBot()
        runtime = ConfigPipelineRuntime(bot)

        self.assertEqual(3, runtime.get_total_loops())
        self.assertEqual(1, runtime.get_next_index(0))
        self.assertIsNone(runtime.get_next_index(1))
        self.assertEqual(3, runtime.get_next_index(2))

    def test_updates_loop_status_and_resets_counters(self):
        bot = FakeBot()
        runtime = ConfigPipelineRuntime(bot)

        runtime.set_current_loop(2, 3)
        runtime.reset_task_counters()

        self.assertEqual((2, 3), bot.last_loop_status)
        self.assertEqual((0, 0, 0, 0), (bot.race_counter, bot.car_counter, bot.cj_counter, bot.sc_count))


if __name__ == "__main__":
    unittest.main()
