import time

from .automation_context import ensure_automation_context


class SellCarTask:
    def __init__(self, context, sleep_func=time.sleep):
        self.context = ensure_automation_context(context)
        self.sleep = sleep_func

    def run_recent(self, target_count):
        bot = self.context
        if bot.sc_count >= target_count:
            return True

        bot.update_running_ui("移除车辆", bot.sc_count, target_count)

        bot.log("准备验证/进入菜单！！！使用前请人工核验到正常移除车辆再进行自动化移除处理")
        if not bot.enter_menu():
            return False

        bot.log("进入车辆与收藏！！！使用前请人工核验到正常移除车辆再进行自动化移除处理")
        bot.hw_press("pagedown", delay=0.15)
        self.sleep(1.0)

        pos_buycar = bot.wait_for_image("BNandUC.png", region=bot.regions["左"], threshold=0.70, timeout=12, interval=0.3, fast_mode=True)
        if not pos_buycar:
            bot.log("未识别到 购买新车与二手车")
            return False

        bot.game_click(pos_buycar)
        self.sleep(0.8)
        bot.hw_press("enter")
        self.sleep(5)

        pos_bs = bot.wait_for_any_image(["buyandsell-w.png", "buyandsell-b.png"], region=bot.regions["上"], threshold=0.75, timeout=40, interval=0.5, fast_mode=True)
        if not pos_bs:
            bot.log("未找到购买与出售")
            return False

        bot.game_click(pos_bs)
        self.sleep(1.0)

        bot.hw_press("pagedown", delay=0.15)
        self.sleep(1.0)

        bot.hw_press("enter")
        self.sleep(2.0)
        bot.hw_press("y")
        self.sleep(1.0)
        bot.hw_press("enter")
        self.sleep(0.8)
        bot.hw_press("esc")
        self.sleep(1.5)
        bot.hw_press("enter")
        self.sleep(0.8)
        bot.move_to_game_coord(5, 5)
        self.sleep(0.2)

        pos = bot.wait_for_image("rc.png", region=bot.regions["全界面"], threshold=0.65, timeout=5, interval=0.2, fast_mode=True)
        if pos:
            bot.log("找到上车，执行点击")
            bot.game_click(pos)
            self.sleep(2.0)
        else:
            bot.log("该车辆已经驾驶，或未找到图片，执行两次ESC")
            bot.hw_press("esc")
            self.sleep(1.5)
            bot.hw_press("esc")
        self.sleep(2.0)

        found = False
        for i in range(60):
            if not bot.is_running:
                return False

            pos = bot.wait_for_any_image(["buyandsell-b.png", "buyandsell-w.png"], region=bot.regions["上"], threshold=0.70, timeout=0.8, interval=0.2, fast_mode=True)
            if pos:
                bot.log(f"第 {i + 1} 次检测到购买与出售，进入车辆界面")
                bot.hw_press("enter")
                found = True
                break
            bot.log(f"第 {i + 1} 次未检测到购买与出售，等待后重试")
            self.sleep(1.0)
        if not found:
            bot.log("60次内未找到购买与出售")
            return False

        self.sleep(1.5)
        bot.hw_press("x")
        self.sleep(0.5)
        bot.move_to_game_coord(5, 5)
        bot.log("切换到 最近获得 的排序...")
        for _ in range(6):
            if not bot.is_running:
                return False
            bot.hw_press("down")
            self.sleep(0.25)
        self.sleep(0.2)
        bot.hw_press("enter")
        self.sleep(1.2)
        bot.log("回到最近获得的前面")
        bot.hw_press("backspace")
        self.sleep(0.8)
        bot.hw_press("enter")
        self.sleep(1.5)

        bot.log("开始删除最近获得的车辆！！！请人工确认是否移除")

        while bot.sc_count < target_count:
            bot.log(f"is_running = {bot.is_running}")
            if not bot.is_running:
                return False
            bot.hw_press("enter")
            self.sleep(1.2)
            for _ in range(6):
                if not bot.is_running:
                    return False
                bot.hw_press("down")
                self.sleep(0.2)
            bot.hw_press("enter")
            self.sleep(0.5)
            bot.hw_press("down")
            self.sleep(0.3)
            bot.hw_press("enter")
            self.sleep(0.8)
            bot.sc_count += 1
            bot.log(f"已尝试删除车辆 {bot.sc_count}/{target_count}")

        for _ in range(3):
            if not bot.is_running:
                return False
            bot.hw_press("esc")
            self.sleep(1.0)

        return True

    def run_filtered(self, target_count):
        bot = self.context
        bot.detail_state_confirmed = False
        if bot.sc_count >= target_count:
            return True

        bot.update_running_ui("移除车辆", bot.sc_count, target_count)

        bot.log("准备验证/进入菜单！！！使用前请人工核验到正常移除车辆再进行自动化移除处理")
        if not bot.enter_menu():
            return False

        bot.log("进入车辆与收藏！！！使用前请人工核验到正常移除车辆再进行自动化移除处理")
        bot.hw_press("pagedown", delay=0.15)
        self.sleep(1.0)

        pos_buycar = bot.wait_for_image("BNandUC.png", region=bot.regions["左"], threshold=0.70, timeout=12, interval=0.3, fast_mode=True)
        if not pos_buycar:
            bot.log("未识别到 购买新车与二手车")
            return False

        bot.game_click(pos_buycar)
        self.sleep(0.8)
        bot.hw_press("enter")
        self.sleep(5)

        pos_bs = bot.wait_for_any_image(["buyandsell-w.png", "buyandsell-b.png"], region=bot.regions["上"], threshold=0.75, timeout=40, interval=0.5, fast_mode=True)
        if not pos_bs:
            bot.log("未找到购买与出售")
            return False

        bot.game_click(pos_bs)
        self.sleep(1.0)

        bot.hw_press("pagedown", delay=0.15)
        self.sleep(1.0)

        bot.hw_press("enter")
        self.sleep(2.0)
        bot.hw_press("y")
        self.sleep(1.0)
        bot.hw_press("enter")
        self.sleep(0.8)
        bot.hw_press("esc")
        self.sleep(1.5)
        bot.hw_press("enter")
        self.sleep(0.8)
        bot.move_to_game_coord(5, 5)
        self.sleep(0.2)

        pos = bot.wait_for_image("rc.png", region=bot.regions["全界面"], threshold=0.65, timeout=2, interval=0.2, fast_mode=True)
        if pos:
            bot.log("找到上车，执行点击")
            bot.game_click(pos)
            self.sleep(2.0)
        else:
            bot.log("该车辆已经驾驶，或未找到图片，执行两次ESC")
            bot.hw_press("esc")
            self.sleep(1.5)
            bot.hw_press("esc")
        self.sleep(2.0)

        found = False
        for i in range(30):
            if not bot.is_running:
                return False

            pos = bot.wait_for_any_image(["buyandsell-b.png", "buyandsell-w.png"], region=bot.regions["上"], threshold=0.70, timeout=1.5, interval=0.2, fast_mode=True)
            if pos:
                bot.log(f"第 {i + 1} 次检测到购买与出售，进入车辆界面")
                bot.hw_press("enter")
                self.sleep(1.5)
                found = True
                break
            bot.log(f"第 {i + 1} 次未检测到购买与出售，等待后重试")
            self.sleep(1.0)
        if not found:
            bot.log("30次内未找到购买与出售")
            return False

        bot.hw_press("y")
        self.sleep(1.0)
        pos_repitem = bot.wait_for_image_gray("repitem.png", region=bot.regions["中间"], threshold=0.70, timeout=1, interval=0.3, fast_mode=True)
        if not pos_repitem:
            bot.log("未识别到 购买新车与二手车")
            return False

        bot.game_click(pos_repitem)
        self.sleep(0.8)

        bot.hw_press("esc")
        self.sleep(1.0)

        bot.log("切换到消耗品品牌...")
        bot.hw_press("backspace")
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

        bot.log("开始删除消耗品车辆！！！请人工确认是否移除")

        not_found_pages = 0
        while bot.sc_count < target_count:
            if not bot.is_running:
                return False
            bot.log(f"正在严格扫描当前页面... (连续未找到: {not_found_pages}/5)")

            pos_target = bot.wait_for_image_ultimate_safe(
                main_path="removecarobject.png",
                anti_path="newcartag.png",
                region=bot.regions["全界面"],
                main_threshold=0.77,
                anti_threshold=0.65,
                timeout=1.0,
                interval=0.2,
            )

            if pos_target:
                bot.detail_state_confirmed = True

            if not pos_target and not bot.detail_state_confirmed:
                bot.log("未找到目标车辆，尝试按 P 切换详情状态...")
                bot.hw_press("p")
                self.sleep(0.6)
                pos_target = bot.wait_for_image_ultimate_safe(
                    main_path="removecarobject.png",
                    anti_path="newcartag.png",
                    region=bot.regions["全界面"],
                    main_threshold=0.77,
                    anti_threshold=0.65,
                    timeout=1.0,
                    interval=0.2,
                )
                if pos_target:
                    bot.detail_state_confirmed = True

            if not pos_target:
                not_found_pages += 1
                if not_found_pages >= 5:
                    bot.log("=连续翻找 5 页仍未搜索到目标车辆！视为车辆已全部清理完毕。")
                    bot.log("主动结束清理任务，准备进入下一步骤...")
                    break

                bot.log(f"当前页面未找到，向右翻页寻找... (第 {not_found_pages} 次翻页)")
                for _ in range(4):
                    bot.hw_press("right", delay=0.06)
                    self.sleep(0.1)
                self.sleep(0.4)
                continue

            not_found_pages = 0

            bot.log("锁定目标车辆，执行点击...")
            bot.game_click(pos_target)
            self.sleep(0.8)

            bot.log("寻找 '从车库移除' 按钮...")
            pos_remove = bot.wait_for_image_gray("removecar.png", region=bot.regions["中间"], threshold=0.70, timeout=1.5, interval=0.3, fast_mode=True)

            if pos_remove:
                bot.log("直接找到移除按钮，点击...")
                bot.game_click(pos_remove)
            else:
                bot.log("未直接找到移除按钮，按下 Enter 呼出菜单...")
                bot.hw_press("enter")
                self.sleep(0.8)

                pos_remove = bot.wait_for_image_gray("removecar.png", region=bot.regions["中间"], threshold=0.75, timeout=1.5, interval=0.3, fast_mode=True)
                if pos_remove:
                    bot.log("呼出菜单后找到移除按钮，点击...")
                    bot.game_click(pos_remove)
                else:
                    bot.log("仍未找到移除按钮，可能点错了/该车无法移除，按 ESC 放弃该车...")
                    bot.hw_press("esc")
                    self.sleep(1.0)
                    bot.hw_press("right")
                    self.sleep(1.2)
                    continue

            self.sleep(0.8)

            bot.log("确认移除...")
            bot.hw_press("down")
            self.sleep(0.3)
            bot.hw_press("enter")
            self.sleep(1.2)

            bot.sc_count += 1
            bot.update_running_ui("移除车辆", bot.sc_count, target_count)
            bot.log(f"成功移除车辆！当前进度: {bot.sc_count}/{target_count}")

        for _ in range(3):
            if not bot.is_running:
                return False
            bot.hw_press("esc")
            self.sleep(1.0)

        return True
