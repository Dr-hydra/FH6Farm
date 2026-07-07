import unittest

from fh6auto_core.sell_car_task import SellCarTask


class FakeBot:
    def __init__(self):
        self.sc_count = 0
        self.is_running = True
        self.regions = {
            "全界面": (0, 0, 100, 100),
            "左": (0, 0, 50, 100),
            "上": (0, 0, 100, 50),
            "中间": (25, 25, 50, 50),
        }
        self.detail_state_confirmed = False
        self.logs = []
        self.presses = []
        self.clicks = []
        self.ui_updates = []
        self.moves = []
        self.enter_menu_result = True
        self.image_hits = {
            "BNandUC.png": (1, 1),
            "rc.png": (3, 3),
        }
        self.gray_hits = {
            "repitem.png": (4, 4),
            "removecar.png": (6, 6),
        }
        self.any_image_hits = {
            "buyandsell-w.png": (2, 2),
            "buyandsell-b.png": (2, 2),
        }
        self.any_gray_hits = {
            "CCbrand.png": (5, 5),
        }
        self.ultimate_hits = [(7, 7)]

    def update_running_ui(self, task_name, current_val=0, max_val=0):
        self.ui_updates.append((task_name, current_val, max_val))

    def log(self, message):
        self.logs.append(message)

    def enter_menu(self):
        return self.enter_menu_result

    def wait_for_image(self, template_path, **kwargs):
        return self.image_hits.get(template_path)

    def wait_for_any_image(self, image_list, **kwargs):
        for image in image_list:
            if image in self.any_image_hits:
                return self.any_image_hits[image]
        return None

    def wait_for_image_gray(self, template_path, **kwargs):
        return self.gray_hits.get(template_path)

    def wait_for_any_image_gray(self, image_list, **kwargs):
        for image in image_list:
            if image in self.any_gray_hits:
                return self.any_gray_hits[image]
        return None

    def wait_for_image_ultimate_safe(self, **kwargs):
        if self.ultimate_hits:
            return self.ultimate_hits.pop(0)
        return None

    def game_click(self, pos, double=False):
        self.clicks.append((pos, double))

    def hw_press(self, key, delay=None):
        self.presses.append(key)

    def move_to_game_coord(self, x, y):
        self.moves.append((x, y))


class SellCarTaskTests(unittest.TestCase):
    def test_returns_true_when_target_already_reached(self):
        bot = FakeBot()
        bot.sc_count = 2

        self.assertTrue(SellCarTask(bot, sleep_func=lambda seconds: None).run_recent(2))

        self.assertEqual([], bot.ui_updates)

    def test_stops_when_menu_entry_fails(self):
        bot = FakeBot()
        bot.enter_menu_result = False

        self.assertFalse(SellCarTask(bot, sleep_func=lambda seconds: None).run_recent(1))

        self.assertEqual([("移除车辆", 0, 1)], bot.ui_updates)
        self.assertIn("准备验证/进入菜单！！！使用前请人工核验到正常移除车辆再进行自动化移除处理", bot.logs)

    def test_stops_when_buy_and_used_car_entry_is_missing(self):
        bot = FakeBot()
        bot.image_hits["BNandUC.png"] = None

        self.assertFalse(SellCarTask(bot, sleep_func=lambda seconds: None).run_recent(1))

        self.assertIn("未识别到 购买新车与二手车", bot.logs)

    def test_successful_recent_flow_deletes_target_count_and_exits_menu(self):
        bot = FakeBot()

        self.assertTrue(SellCarTask(bot, sleep_func=lambda seconds: None).run_recent(2))

        self.assertEqual(2, bot.sc_count)
        self.assertIn("开始删除最近获得的车辆！！！请人工确认是否移除", bot.logs)
        self.assertEqual(3, bot.presses[-3:].count("esc"))
        self.assertIn(((3, 3), False), bot.clicks)
        self.assertGreaterEqual(len(bot.moves), 2)

    def test_successful_filtered_flow_removes_target_vehicle(self):
        bot = FakeBot()

        self.assertTrue(SellCarTask(bot, sleep_func=lambda seconds: None).run_filtered(1))

        self.assertEqual(1, bot.sc_count)
        self.assertIn("开始删除消耗品车辆！！！请人工确认是否移除", bot.logs)
        self.assertIn("成功移除车辆！当前进度: 1/1", bot.logs)
        self.assertIn(((7, 7), False), bot.clicks)
        self.assertIn(((6, 6), False), bot.clicks)

    def test_filtered_flow_finishes_when_target_vehicle_is_no_longer_found(self):
        bot = FakeBot()
        bot.ultimate_hits = []

        self.assertTrue(SellCarTask(bot, sleep_func=lambda seconds: None).run_filtered(1))

        self.assertEqual(0, bot.sc_count)
        self.assertIn("=连续翻找 5 页仍未搜索到目标车辆！视为车辆已全部清理完毕。", bot.logs)
        self.assertEqual(3, bot.presses[-3:].count("esc"))


if __name__ == "__main__":
    unittest.main()
