import unittest

from fh6auto_core.buy_car_task import BuyCarTask


class FakeBot:
    def __init__(self):
        self.car_counter = 0
        self.is_running = True
        self.regions = {
            "全界面": (0, 0, 100, 100),
            "左": (0, 0, 50, 100),
        }
        self.logs = []
        self.presses = []
        self.clicks = []
        self.ui_updates = []
        self.moves = []
        self.enter_menu_result = True
        self.transparent_hits = {
            "collectionjournal.png": (1, 1),
            "carcollection.png": (3, 3),
        }
        self.image_hits = {
            "masterexplorer.png": (2, 2),
            "consumablecar.png": (5, 5),
        }
        self.any_gray_hits = {
            "CCbrand.png": (4, 4),
        }

    def update_running_ui(self, task_name, current_val=0, max_val=0):
        self.ui_updates.append((task_name, current_val, max_val))

    def log(self, message):
        self.logs.append(message)

    def enter_menu(self):
        return self.enter_menu_result

    def wait_for_image_transparent(self, template_path, **kwargs):
        return self.transparent_hits.get(template_path)

    def wait_for_image(self, template_path, **kwargs):
        return self.image_hits.get(template_path)

    def wait_for_any_image_gray(self, image_list, **kwargs):
        for image in image_list:
            if image in self.any_gray_hits:
                return self.any_gray_hits[image]
        return None

    def game_click(self, pos, double=False):
        self.clicks.append((pos, double))

    def hw_press(self, key, delay=None):
        self.presses.append(key)

    def move_to_game_coord(self, x, y):
        self.moves.append((x, y))


class BuyCarTaskTests(unittest.TestCase):
    def test_returns_true_when_target_already_reached(self):
        bot = FakeBot()
        bot.car_counter = 3

        self.assertTrue(BuyCarTask(bot, sleep_func=lambda seconds: None).run(3))

        self.assertEqual([], bot.ui_updates)

    def test_stops_when_menu_entry_fails(self):
        bot = FakeBot()
        bot.enter_menu_result = False

        self.assertFalse(BuyCarTask(bot, sleep_func=lambda seconds: None).run(1))

        self.assertIn("准备验证/进入菜单...", bot.logs)
        self.assertEqual([("批量买车", 0, 1)], bot.ui_updates)

    def test_stops_when_collection_journal_is_missing(self):
        bot = FakeBot()
        bot.transparent_hits["collectionjournal.png"] = None

        self.assertFalse(BuyCarTask(bot, sleep_func=lambda seconds: None).run(1))

        self.assertIn("未找到收集簿", bot.logs)

    def test_successful_flow_buys_target_count_and_exits_menu(self):
        bot = FakeBot()

        self.assertTrue(BuyCarTask(bot, sleep_func=lambda seconds: None).run(2))

        self.assertEqual(2, bot.car_counter)
        self.assertEqual(("批量买车", 2, 2), bot.ui_updates[-1])
        self.assertEqual(5, bot.presses[-5:].count("esc"))
        self.assertIn(((5, 5), True), bot.clicks)
        self.assertGreaterEqual(len(bot.moves), 6)


if __name__ == "__main__":
    unittest.main()
