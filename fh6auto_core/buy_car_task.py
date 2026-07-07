import time

from .automation_context import ensure_automation_context


class BuyCarTask:
    def __init__(self, context, sleep_func=time.sleep):
        self.context = ensure_automation_context(context)
        self.sleep = sleep_func

    def run(self, target_count):
        bot = self.context
        if bot.car_counter >= target_count:
            return True

        bot.update_running_ui("批量买车", bot.car_counter, target_count)

        bot.log("准备验证/进入菜单...")
        if not bot.enter_menu():
            return False

        pos_collectionjournal = bot.wait_for_image_transparent(
            "collectionjournal.png",
            region=bot.regions["左"],
            threshold=0.7,
            timeout=30,
            interval=0.4,
            fast_mode=True,
        )
        if not pos_collectionjournal:
            bot.log("未找到收集簿")
            return False

        bot.game_click(pos_collectionjournal, double=True)
        self.sleep(1.0)

        pos_masterexplorer = bot.wait_for_image(
            "masterexplorer.png",
            region=bot.regions["全界面"],
            threshold=0.75,
            timeout=30,
            interval=0.4,
            fast_mode=True,
        )
        if not pos_masterexplorer:
            bot.log("未找到探索")
            return False

        bot.game_click(pos_masterexplorer, double=True)
        self.sleep(0.6)

        pos_carcollection = bot.wait_for_image_transparent(
            "carcollection.png",
            region=bot.regions["全界面"],
            threshold=0.75,
            timeout=30,
            interval=0.3,
            fast_mode=True,
        )
        if not pos_carcollection:
            bot.log("未找到车辆收集")
            return False

        bot.game_click(pos_carcollection, double=True)
        self.sleep(1.0)

        bot.hw_press("backspace")
        self.sleep(0.5)

        brand_pos = None
        for _ in range(5):
            if not bot.is_running:
                return False

            brand_pos = bot.wait_for_any_image_gray(
                ["CCbrand.png"],
                region=bot.regions["全界面"],
                threshold=0.75,
                timeout=0.8,
                interval=0.2,
                fast_mode=True,
            )
            if brand_pos:
                break

            bot.hw_press("up")
            self.sleep(0.25)

        if not brand_pos:
            bot.log("未找到品牌")
            return False

        bot.game_click(brand_pos)
        self.sleep(0.8)
        bot.hw_press("down")
        self.sleep(0.4)

        pos_22b = bot.wait_for_image(
            "consumablecar.png",
            region=bot.regions["全界面"],
            threshold=0.90,
            timeout=8,
            interval=0.3,
            fast_mode=False,
        )
        if not pos_22b:
            bot.log("未找到消耗品车辆")
            return False

        bot.game_click(pos_22b, double=True)
        self.sleep(1.0)

        while bot.car_counter < target_count:
            if not bot.is_running:
                return False

            bot.hw_press("space")
            self.sleep(0.6)
            bot.move_to_game_coord(5, 5)
            bot.hw_press("down")
            self.sleep(0.2)
            bot.move_to_game_coord(5, 5)
            bot.hw_press("enter")
            self.sleep(0.6)
            bot.move_to_game_coord(5, 5)
            bot.hw_press("enter")
            self.sleep(0.6)
            bot.move_to_game_coord(5, 5)
            bot.hw_press("enter")
            self.sleep(0.7)

            bot.car_counter += 1
            bot.update_running_ui("批量买车", bot.car_counter, target_count)

        for _ in range(5):
            if not bot.is_running:
                return False
            bot.hw_press("esc")
            self.sleep(0.8)

        return True
