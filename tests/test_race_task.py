import unittest

from fh6auto_core.race_task import RaceTask


class IncrementingClock:
    def __init__(self):
        self.value = 0

    def __call__(self):
        self.value += 1
        return self.value


class FakeBot:
    def __init__(self):
        self.race_counter = 0
        self.is_running = True
        self.is_paused = False
        self.detail_state_confirmed = False
        self.config = {"share_code": "A12B"}
        self.regions = {
            "全界面": (0, 0, 100, 100),
            "中间": (25, 25, 50, 50),
            "下": (0, 50, 100, 50),
            "左下": (0, 50, 50, 50),
        }
        self.logs = []
        self.presses = []
        self.key_downs = []
        self.key_ups = []
        self.clicks = []
        self.ui_updates = []
        self.enter_menu_result = True
        self.gray_hits = {
            "eventlab.png": (1, 1),
            "playenent.png": (2, 2),
            "VEI.png": (3, 3),
            "restart.png": (5, 5),
        }
        self.any_gray_hits = {
            "start.png": (4, 4),
        }
        self.target_hit = (6, 6)

    def update_running_ui(self, task_name, current_val=0, max_val=0):
        self.ui_updates.append((task_name, current_val, max_val))

    def log(self, message):
        self.logs.append(message)

    def enter_menu(self):
        return self.enter_menu_result

    def hw_press(self, key, delay=None):
        self.presses.append(key)

    def hw_key_down(self, key):
        self.key_downs.append(key)

    def hw_key_up(self, key):
        self.key_ups.append(key)

    def game_click(self, pos, double=False):
        self.clicks.append((pos, double))

    def wait_for_image_gray(self, template_path, **kwargs):
        return self.gray_hits.get(template_path)

    def find_image_gray(self, template_path, **kwargs):
        return self.gray_hits.get(template_path)

    def wait_for_any_image_gray(self, image_list, **kwargs):
        for image in image_list:
            if image in self.any_gray_hits:
                return self.any_gray_hits[image]
        return None

    def find_any_image_gray(self, image_list, **kwargs):
        return None

    def wait_for_image_with_element_multi(self, *args, **kwargs):
        return self.target_hit

    def check_vramne_during_race(self):
        return None

    def check_pause(self):
        return None


class RaceTaskTests(unittest.TestCase):
    def test_returns_true_when_target_already_reached(self):
        bot = FakeBot()
        bot.race_counter = 2

        self.assertTrue(RaceTask(bot, sleep_func=lambda seconds: None).run(2))

        self.assertEqual([], bot.ui_updates)

    def test_stops_when_menu_entry_fails(self):
        bot = FakeBot()
        bot.enter_menu_result = False

        self.assertFalse(RaceTask(bot, sleep_func=lambda seconds: None).run(1))

        self.assertEqual([("循环跑图", 0, 1)], bot.ui_updates)
        self.assertIn("准备验证/进入菜单...", bot.logs)

    def test_stops_when_eventlab_is_missing(self):
        bot = FakeBot()
        bot.gray_hits["eventlab.png"] = None

        self.assertFalse(RaceTask(bot, sleep_func=lambda seconds: None).run(1))

        self.assertIn("未找到 eventlab", bot.logs)

    def test_successful_flow_runs_one_race_and_releases_driving_keys(self):
        bot = FakeBot()

        self.assertTrue(RaceTask(bot, sleep_func=lambda seconds: None, time_func=IncrementingClock()).run(1))

        self.assertEqual(1, bot.race_counter)
        self.assertEqual(("循环跑图", 1, 1), bot.ui_updates[-1])
        self.assertIn("1", bot.presses)
        self.assertIn("2", bot.presses)
        self.assertEqual(["w", "up"], bot.key_downs)
        self.assertEqual(["w", "up"], bot.key_ups)
        self.assertIn(((6, 6), False), bot.clicks)

    def test_uses_config_share_code(self):
        bot = FakeBot()
        bot.config = {"share_code": "C34D"}

        self.assertTrue(RaceTask(bot, sleep_func=lambda seconds: None, time_func=IncrementingClock()).run(1))

        self.assertIn("3", bot.presses)
        self.assertIn("4", bot.presses)


if __name__ == "__main__":
    unittest.main()
