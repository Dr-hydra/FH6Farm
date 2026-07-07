import unittest

from fh6auto_core.wheelspin_task import WheelspinTask


class FakeBot:
    def __init__(self, config_cj_mode=1):
        self.cj_counter = 0
        self.is_running = True
        self.detail_state_confirmed = False
        self.config = {"skill_dirs": ["right", "up"], "cj_mode": config_cj_mode}
        self.regions = {
            "全界面": (0, 0, 100, 100),
            "左": (0, 0, 50, 100),
            "左下": (0, 50, 50, 50),
        }
        self.logs = []
        self.presses = []
        self.clicks = []
        self.ui_updates = []
        self.enter_menu_result = True
        self.image_hits = {"BNandUC.png": (1, 1)}
        self.gray_hits = {"rc.png": (5, 5)}
        self.any_gray_hits = {
            "buyandsell-w.png": (2, 2),
            "CCbrand.png": (3, 3),
            "clsldcnw.png": (7, 7),
        }
        self.find_any_gray_hits = {
            "UandT-w.png": (6, 6),
        }
        self.any_image_hits = {}
        self.image_with_element_hit = (4, 4)
        self.spne_hit = None

    def update_running_ui(self, task_name, current_val=0, max_val=0):
        self.ui_updates.append((task_name, current_val, max_val))

    def log(self, message):
        self.logs.append(message)

    def enter_menu(self):
        return self.enter_menu_result

    def wait_for_image(self, template_path, **kwargs):
        return self.image_hits.get(template_path)

    def wait_for_image_gray(self, template_path, **kwargs):
        return self.gray_hits.get(template_path)

    def wait_for_any_image_gray(self, image_list, **kwargs):
        for image in image_list:
            if image in self.any_gray_hits:
                return self.any_gray_hits[image]
        return None

    def wait_for_any_image(self, image_list, **kwargs):
        for image in image_list:
            if image in self.any_image_hits:
                return self.any_image_hits[image]
        return None

    def find_any_image_gray(self, image_list, **kwargs):
        for image in image_list:
            if image in self.find_any_gray_hits:
                return self.find_any_gray_hits[image]
        return None

    def find_image_gray(self, template_path, **kwargs):
        if template_path == "SPNE.png":
            return self.spne_hit
        return self.gray_hits.get(template_path)

    def wait_for_image_with_element_multi(self, *args, **kwargs):
        return self.image_with_element_hit

    def game_click(self, pos, double=False):
        self.clicks.append((pos, double))

    def hw_press(self, key, delay=None):
        self.presses.append(key)


class WheelspinTaskTests(unittest.TestCase):
    def test_returns_true_when_target_already_reached(self):
        bot = FakeBot()
        bot.cj_counter = 2

        self.assertTrue(WheelspinTask(bot, sleep_func=lambda seconds: None).run(2))

        self.assertEqual([], bot.ui_updates)

    def test_stops_when_menu_entry_fails(self):
        bot = FakeBot()
        bot.enter_menu_result = False

        self.assertFalse(WheelspinTask(bot, sleep_func=lambda seconds: None).run(1))

        self.assertEqual([("超级抽奖", 0, 1)], bot.ui_updates)
        self.assertIn("准备验证/进入菜单...", bot.logs)

    def test_mode_two_stops_when_design_and_paint_is_missing(self):
        bot = FakeBot(config_cj_mode=2)

        self.assertFalse(WheelspinTask(bot, sleep_func=lambda seconds: None).run(1))

        self.assertIn("未找到设计与喷涂(DandP.png)", bot.logs)

    def test_mode_two_comes_from_config(self):
        bot = FakeBot(config_cj_mode=2)

        self.assertFalse(WheelspinTask(bot, sleep_func=lambda seconds: None).run(1))

        self.assertIn("未找到设计与喷涂(DandP.png)", bot.logs)

    def test_successful_mode_one_flow_applies_skill_path_and_counts_car(self):
        bot = FakeBot()

        self.assertTrue(WheelspinTask(bot, sleep_func=lambda seconds: None).run(1))

        self.assertEqual(1, bot.cj_counter)
        self.assertEqual(("超级抽奖", 1, 1), bot.ui_updates[-1])
        self.assertIn("right", bot.presses)
        self.assertIn("up", bot.presses)
        self.assertIn(((4, 4), False), bot.clicks)
        self.assertEqual(0, bot.memory_car_page)


if __name__ == "__main__":
    unittest.main()
