import time

from .automation_context import ensure_automation_context
from .input_controller import DIK_CODES


class RaceTask:
    def __init__(self, context, sleep_func=time.sleep, time_func=time.time):
        self.context = ensure_automation_context(context)
        self.sleep = sleep_func
        self.time = time_func

    def run(self, target_count):
        bot = self.context
        bot.detail_state_confirmed = False
        if bot.race_counter >= target_count:
            return True

        bot.update_running_ui("循环跑图", bot.race_counter, target_count)

        bot.log("准备验证/进入菜单...")
        if not bot.enter_menu():
            return False

        bot.log("切换到创意中心...")
        for _ in range(4):
            bot.hw_press("pagedown", delay=0.15)
            self.sleep(0.3)

        self.sleep(0.8)

        pos_el = bot.wait_for_image_gray(
            "eventlab.png",
            region=bot.regions["全界面"],
            threshold=0.7,
            timeout=5,
            interval=0.25,
            fast_mode=True,
        )

        if not pos_el:
            bot.log("未找到 eventlab")
            return False

        bot.game_click(pos_el)
        self.sleep(1.2)

        pos_yg = bot.wait_for_image_gray(
            "playenent.png",
            region=bot.regions["中间"],
            threshold=0.75,
            timeout=40,
            interval=0.3,
            fast_mode=True,
        )
        if not pos_yg:
            bot.log("未找到游玩赛事")
            return False

        bot.game_click(pos_yg)
        self.sleep(1.5)

        bot.hw_press("backspace")
        self.sleep(0.8)
        bot.hw_press("up")
        self.sleep(0.4)
        bot.hw_press("enter")
        self.sleep(0.8)

        code_text = _share_code_from_bot(bot)
        for char in code_text:
            if not bot.is_running:
                return False
            if char in DIK_CODES:
                bot.hw_press(char, delay=0.05)
                self.sleep(0.05)

        self.sleep(0.4)
        bot.hw_press("enter")
        self.sleep(0.8)
        bot.hw_press("down")
        self.sleep(0.3)
        bot.hw_press("enter")
        self.sleep(1.5)

        pos_ck = bot.wait_for_image_gray(
            "VEI.png",
            region=bot.regions["下"],
            threshold=0.75,
            timeout=20,
            interval=1.0,
            fast_mode=True,
        )
        if not pos_ck:
            bot.log("链接超时")
            return False

        bot.hw_press("enter")
        self.sleep(2.0)
        bot.hw_press("enter")
        self.sleep(2.0)

        pos_target = bot.wait_for_image_with_element_multi(
            "skillcar.png",
            "liketag.png",
            region=bot.regions["全界面"],
            fast_mode=True,
            main_threshold=0.70,
            like_threshold=0.7,
            final_threshold=0.7,
            timeout=1.2,
            interval=0.2,
            ignore_top_text=True,
        )
        if pos_target:
            bot.detail_state_confirmed = True

        if not pos_target and not bot.detail_state_confirmed:
            bot.log("当前页面未找到车辆，尝试按 P 切换详情状态...")
            bot.hw_press("p")
            self.sleep(0.6)
            pos_target = bot.wait_for_image_with_element_multi(
                "skillcar.png",
                "liketag.png",
                region=bot.regions["全界面"],
                fast_mode=True,
                main_threshold=0.70,
                like_threshold=0.7,
                final_threshold=0.7,
                timeout=1.2,
                interval=0.2,
                ignore_top_text=True,
            )
            if pos_target:
                bot.detail_state_confirmed = True

        if not pos_target:
            bot.log("未找到带收藏的目标车辆，重新选品牌...")
            bot.hw_press("backspace")
            self.sleep(1.2)

            found_brand = False
            for _ in range(5):
                if not bot.is_running:
                    return False

                pos_brand = bot.wait_for_image_gray("skillcarbrand.png", region=bot.regions["全界面"], threshold=0.8, timeout=1.2, interval=0.2, fast_mode=True)
                if pos_brand:
                    bot.game_click(pos_brand)
                    self.sleep(1.2)
                    found_brand = True
                    break

                bot.hw_press("up")
                self.sleep(0.4)

            if not found_brand:
                bot.log("5次尝试未找到刷图车辆品牌。")
                return False

            for _ in range(20):
                if not bot.is_running:
                    return False

                pos_target = bot.wait_for_image_with_element_multi(
                    "skillcar.png",
                    "liketag.png",
                    region=bot.regions["全界面"],
                    main_threshold=0.75,
                    like_threshold=0.7,
                    final_threshold=0.7,
                    timeout=1.2,
                    interval=0.2,
                    fast_mode=True,
                    ignore_top_text=True,
                )
                if pos_target:
                    bot.detail_state_confirmed = True
                    break

                if not bot.detail_state_confirmed:
                    bot.log("当前页面未找到车辆，尝试按 P 切换详情状态...")
                    bot.hw_press("p")
                    self.sleep(0.6)
                    pos_target = bot.wait_for_image_with_element_multi(
                        "skillcar.png",
                        "liketag.png",
                        region=bot.regions["全界面"],
                        main_threshold=0.75,
                        like_threshold=0.7,
                        final_threshold=0.7,
                        timeout=1.2,
                        interval=0.2,
                        fast_mode=True,
                        ignore_top_text=True,
                    )
                    if pos_target:
                        bot.detail_state_confirmed = True
                        break

                for _ in range(4):
                    bot.hw_press("right", delay=0.08)
                    self.sleep(0.08)
                self.sleep(0.4)

        if not pos_target:
            bot.log("翻页未能找到带有收藏的刷图车辆！")
            return False

        bot.game_click(pos_target)
        self.sleep(0.5)
        bot.hw_press("enter")
        self.sleep(4.0)

        bot.log("前置完成，开始循环跑图！")

        while bot.race_counter < target_count:
            if not bot.is_running:
                return False

            bot.log(f"跑图 {bot.race_counter + 1}/{target_count}: 找赛事起点...")

            pos = None
            for _ in range(120):
                if not bot.is_running:
                    return False

                pos = bot.wait_for_any_image_gray(
                    ["start.png", "startw.png"],
                    region=bot.regions["左下"],
                    threshold=0.75,
                    timeout=0.7,
                    interval=0.2,
                    fast_mode=True,
                )
                if pos:
                    break

                bot.hw_press("down")
                self.sleep(0.25)

            if not pos:
                bot.log("找不到赛事起点，退出跑图。")
                return False

            bot.game_click(pos)
            self.sleep(4.0)
            bot.hw_key_down("w")
            bot.hw_key_down("up")

            race_start_time = self.time()
            last_like_chk = self.time()
            last_chk = 0
            finished = False
            timeout_triggered = False

            driving_keys_held = True

            while bot.is_running:
                if bot.is_paused:
                    if driving_keys_held:
                        bot.hw_key_up("w")
                        bot.hw_key_up("up")
                        driving_keys_held = False
                    bot.check_pause()
                    if bot.is_running:
                        bot.hw_key_down("w")
                        bot.hw_key_down("up")
                        driving_keys_held = True

                    race_start_time = self.time()
                    last_like_chk = self.time()
                    last_chk = self.time()
                    continue

                now = self.time()

                if now - race_start_time > 120.0:
                    bot.log("跑图超时(已超过120秒)！触发强制重开赛事逻辑...")
                    timeout_triggered = True
                    break

                if now - last_like_chk >= 3.0:
                    vram_result = bot.check_vramne_during_race()
                    if vram_result is True:
                        bot.log("VRAM恢复完成，结束当前跑图流程，交给外层重新恢复。")
                        return False
                    elif vram_result is False:
                        bot.log("VRAM恢复失败。")
                        return False
                    pos_like = bot.find_any_image_gray(
                        ["likeauthor.png", "dislikeauthor.png"],
                        region=bot.regions["中间"],
                        threshold=0.70,
                    )
                    if pos_like:
                        bot.log("识别到点赞作界面，执行回车确认！")
                        bot.hw_press("enter")
                    last_like_chk = now

                if now - last_chk >= 1.0:
                    found_restart = bot.find_image_gray("restart.png", region=bot.regions["下"], threshold=0.75, fast_mode=True)
                    if found_restart:
                        finished = True
                        break
                    last_chk = now

                self.sleep(0.3)

            bot.hw_key_up("w")
            bot.hw_key_up("up")

            if not bot.is_running:
                return False

            if timeout_triggered:
                self.sleep(0.5)
                bot.hw_press("esc")
                self.sleep(1.5)

                pos_restarta = bot.wait_for_image_gray("restarta.png", region=bot.regions["全界面"], threshold=0.70, timeout=4.0, interval=0.3, fast_mode=True)
                if pos_restarta:
                    bot.log("找到 restarta.png，点击重开赛事...")
                    bot.game_click(pos_restarta)
                    self.sleep(1.0)
                    bot.hw_press("enter")
                    self.sleep(4.0)
                else:
                    bot.log("未找到 restarta.png，尝试直接继续...")

                continue

            if not finished:
                return False

            if bot.race_counter == target_count - 1:
                bot.hw_press("enter")
                self.sleep(2.0)
            else:
                bot.hw_press("x")
                self.sleep(0.8)
                bot.hw_press("enter")
                self.sleep(2.0)

            bot.race_counter += 1
            bot.update_running_ui("循环跑图", bot.race_counter, target_count)

        return True


def _share_code_from_bot(bot):
    return "".join(c for c in str(bot.config.get("share_code", "")) if c.isdigit())
