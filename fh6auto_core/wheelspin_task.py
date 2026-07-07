import time

from .automation_context import ensure_automation_context


class WheelspinTask:
    def __init__(self, context, sleep_func=time.sleep):
        self.context = ensure_automation_context(context)
        self.sleep = sleep_func

    def run(self, target_count):
        bot = self.context
        bot.detail_state_confirmed = False
        if bot.cj_counter >= target_count:
            return True

        bot.update_running_ui("超级抽奖", bot.cj_counter, target_count)
        if not hasattr(bot, "memory_car_page"):
            bot.memory_car_page = 0
        bot.log("准备验证/进入菜单...")
        if not bot.enter_menu():
            return False

        bot.log("进入车辆与收藏...")
        bot.hw_press("pagedown", delay=0.15)
        self.sleep(1.0)

        pos_buycar = bot.wait_for_image(
            "BNandUC.png",
            region=bot.regions["左"],
            threshold=0.70,
            timeout=15,
            interval=0.3,
            fast_mode=True,
        )
        if not pos_buycar:
            bot.log("未识别到 购买新车与二手车")
            return False

        bot.game_click(pos_buycar)
        self.sleep(0.8)
        bot.hw_press("enter")
        self.sleep(5)

        pos_bs = bot.wait_for_any_image_gray(
            ["buyandsell-w.png", "buyandsell-b.png"],
            region=bot.regions["左"],
            threshold=0.75,
            timeout=60,
            interval=0.5,
            fast_mode=True,
        )
        if not pos_bs:
            bot.log("未找到购买与出售")
            return False

        bot.game_click(pos_bs)
        self.sleep(1.0)
        bot.hw_press("pagedown", delay=0.15)
        bot.log("进入车辆界面...")
        self.sleep(0.5)

        while bot.cj_counter < target_count:
            if not bot.is_running:
                return False
            cj_mode_str = _cj_mode_from_bot(bot)

            if "模式1" in cj_mode_str:
                bot.log("进入我的车辆.")
                bot.hw_press("enter")
                self.sleep(2.0)
            else:
                bot.log("进入设计与喷涂.")
                pos_dp = bot.wait_for_image_gray("DandP.png", region=bot.regions["全界面"], threshold=0.70, timeout=8, interval=0.3, fast_mode=True)
                if pos_dp:
                    bot.game_click(pos_dp)
                    self.sleep(1.5)
                else:
                    bot.log("未找到设计与喷涂(DandP.png)")
                    return False

                pos_choose = bot.wait_for_image_gray("choosecar.png", region=bot.regions["全界面"], threshold=0.70, timeout=8, interval=0.3, fast_mode=True)
                if pos_choose:
                    bot.game_click(pos_choose)
                    self.sleep(2.0)
                else:
                    bot.log("未找到选择车辆(choosecar.png)")
                    return False
            bot.hw_press("backspace")
            self.sleep(1.0)

            brand_pos = None
            for _ in range(30):
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
                bot.log("选品牌失败")
                return False

            bot.game_click(brand_pos)
            self.sleep(1.0)
            jump_pages = max(0, bot.memory_car_page - 1)

            if jump_pages > 0:
                bot.log(f"快速跳过前 {jump_pages} 页...")
                for _ in range(jump_pages):
                    if not bot.is_running:
                        return False
                    for _ in range(4):
                        bot.hw_press("right", delay=0.06)
                        self.sleep(0.1)
                    self.sleep(0.15)
            pos_target = None
            found_car = False
            current_page = jump_pages

            for _ in range(85 - jump_pages):
                if not bot.is_running:
                    return False
                pos_target = bot.wait_for_image_with_element_multi(
                    "newCC.png",
                    "newcartag.png",
                    region=bot.regions["全界面"],
                    main_threshold=0.70,
                    like_threshold=0.70,
                    final_threshold=0.70,
                    timeout=1.0,
                    interval=0.2,
                    fast_mode=True,
                )

                if pos_target:
                    bot.detail_state_confirmed = True

                if not pos_target and not bot.detail_state_confirmed:
                    bot.log("未找到目标车辆，尝试按 P 切换详情状态...")
                    bot.hw_press("p")
                    self.sleep(0.6)
                    pos_target = bot.wait_for_image_with_element_multi(
                        "newCC.png",
                        "newcartag.png",
                        region=bot.regions["全界面"],
                        main_threshold=0.70,
                        like_threshold=0.70,
                        final_threshold=0.70,
                        timeout=1.0,
                        interval=0.2,
                        fast_mode=True,
                    )
                    if pos_target:
                        bot.detail_state_confirmed = True

                if pos_target:
                    bot.game_click(pos_target)
                    found_car = True
                    bot.memory_car_page = current_page
                    bot.log(f"锁定目标车辆！已记录当前页码: {current_page}")
                    break

                for _ in range(4):
                    bot.hw_press("right", delay=0.06)
                    self.sleep(0.1)
                self.sleep(0.4)
                current_page += 1
            if not found_car:
                bot.log("列表中未找到目标车辆，重置记忆页码。")
                bot.memory_car_page = 0
                return False
            if "模式1" in cj_mode_str:
                self.sleep(0.5)
                bot.log("尝试寻找'上车'按钮...")
                pos_rc = bot.wait_for_image_gray("rc.png", region=bot.regions["全界面"], threshold=0.70, timeout=0.5, interval=0.1, fast_mode=True)
                if pos_rc:
                    bot.log("点击上车")
                    bot.game_click(pos_rc)
                    self.sleep(2.0)
                else:
                    bot.log("回车上车")
                    bot.hw_press("enter")
                    self.sleep(1.0)
                    bot.hw_press("enter")
                    self.sleep(1.0)
            else:
                self.sleep(0.5)
                bot.hw_press("enter")
                self.sleep(1.0)

            pos_sjy = None
            for _ in range(20):
                if not bot.is_running:
                    return False

                pos_sjy = bot.find_any_image_gray(["UandT-w.png", "UandT-b.png"], region=bot.regions["左下"], threshold=0.70)
                if pos_sjy:
                    break

                bot.hw_press("esc")
                self.sleep(0.5)

            if not pos_sjy:
                bot.log("找不到升级页面")
                return False

            bot.game_click(pos_sjy)
            self.sleep(0.5)

            pos_cls = bot.wait_for_any_image_gray(
                ["clsldcnw.png", "clsldcnb.png"],
                region=bot.regions["左下"],
                threshold=0.70,
                timeout=20,
            )
            if not pos_cls:
                bot.log("未找到车辆熟练度")
                return False
            bot.game_click(pos_cls)
            self.sleep(1.5)

            pos_exp = bot.wait_for_any_image(
                ["EXPwU.png"],
                region=bot.regions["左"],
                threshold=0.75,
                timeout=1.5,
                interval=0.3,
                fast_mode=True,
            )

            if pos_exp:
                bot.log("该车辆技能已点过，跳过计数")
            else:
                self.sleep(1.0)
                bot.hw_press("enter")
                self.sleep(1.5)

                for dk in bot.config["skill_dirs"]:
                    if not bot.is_running:
                        return False
                    bot.hw_press(dk)
                    self.sleep(0.2)
                    bot.hw_press("enter")
                    self.sleep(1.2)

                spne_found = bot.find_image_gray("SPNE.png", region=bot.regions["全界面"], threshold=0.70)

                if spne_found:
                    bot.log("已无技能点或技能已点完，提前结束抽奖！")
                    self.sleep(1.0)
                    bot.hw_press("enter")
                    self.sleep(0.8)
                    bot.hw_press("esc")
                    self.sleep(1.0)
                    bot.hw_press("esc")
                    self.sleep(1.0)
                    bot.hw_press("esc")
                    self.sleep(1.0)
                    return True
                bot.cj_counter += 1
                bot.update_running_ui("超级抽奖", bot.cj_counter, target_count)

            bot.hw_press("esc")
            self.sleep(1.2)
            bot.hw_press("esc")
            self.sleep(0.8)
            bot.hw_press("up", delay=0.15)
            self.sleep(0.8)
        bot.hw_press("esc")
        self.sleep(1.2)
        bot.hw_press("esc")
        self.sleep(1.2)
        return True


def _cj_mode_from_bot(bot):
    return "模式2" if str(bot.config.get("cj_mode", 1)) == "2" else "模式1"
