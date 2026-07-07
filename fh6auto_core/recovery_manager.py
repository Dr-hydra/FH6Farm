import os
import time

import cv2


class RecoveryManager:
    """Owns menu recovery, VRAM handling, and game restart bootstrapping."""

    def __init__(
        self,
        vision,
        logger=None,
        regions_provider=None,
        running_checker=None,
        pause_handler=None,
        focus_game=None,
        key_press=None,
        click=None,
        command_runner=None,
        sleep_func=None,
        time_func=None,
        auto_restart_enabled=None,
        restart_command_provider=None,
        process_name="forzahorizon6.exe",
        obstacles_dir=None,
    ):
        self.vision = vision
        self.logger = logger or (lambda message: None)
        self.regions_provider = regions_provider or (lambda: {})
        self.running_checker = running_checker or (lambda: True)
        self.pause_handler = pause_handler or (lambda: None)
        self.focus_game = focus_game or (lambda: False)
        self.key_press = key_press or (lambda key, delay=None: None)
        self.click = click or (lambda pos: None)
        self.command_runner = command_runner or os.system
        self.sleep = sleep_func or time.sleep
        self.time = time_func or time.time
        self.auto_restart_enabled = auto_restart_enabled or (lambda: False)
        self.restart_command_provider = restart_command_provider or (lambda: "start steam://run/2483190")
        self.process_name = process_name
        self.obstacles_dir = obstacles_dir or os.path.join("images", "obstacles")

    def log(self, message):
        self.logger(message)

    def is_running(self):
        return self.running_checker()

    @property
    def regions(self):
        return self.regions_provider() or {}

    def restart_game_and_boot(self, force_test=False):
        if not force_test and not self.auto_restart_enabled():
            self.log("未开启自动重启，任务结束。")
            return False

        self.log("触发启动机制！正在拉起游戏...")
        try:
            self.command_runner(self.restart_command_provider())
        except Exception as e:
            self.log(f"执行启动命令失败: {e}")
            return False

        self.log("等待游戏进程出现 (最多60秒)...")
        process_found = False
        for _ in range(120):
            self.pause_handler()
            if not self.is_running():
                return False
            if self.focus_game():
                process_found = True
                break
            self.sleep(1)

        if not process_found:
            self.log("未检测到游戏进程，启动失败。")
            return False

        self.log("游戏进程已启动，进入动态识别阶段 (限制5分钟)...")
        start_time = self.time()
        passed_screen_1 = False
        last_continue_time = 0

        while self.is_running() and self.time() - start_time < 300:
            self.pause_handler()
            full_region = self.regions.get("全界面")

            if not passed_screen_1:
                pos_h6 = self.vision.find_image_transparent("horizon6.png", region=full_region, threshold=0.60, fast_mode=False)

                if not pos_h6:
                    pos_h6 = self._find_horizon_by_edge(full_region)

                if pos_h6:
                    self.log("✅ 成功识别到 画面1 (horizon6.png)，按下【回车键】...")
                    self.sleep(1)
                    for _ in range(2):
                        self.key_press("enter")
                        self.sleep(1)
                    passed_screen_1 = True
                    last_continue_time = self.time()
                    self.log("已确认画面1，强制等待 10 秒等待画面2加载...")
                    self.sleep(10)
                    continue

                self.log("未找到画面1。正在使用全比例深度扫描...")

            if passed_screen_1:
                pos_continue = self.vision.find_any_image_gray(["continue-b.png", "continue-w.png"], threshold=0.75)
                if pos_continue:
                    self.log("识别到 画面2 (继续按钮)，进行点击...")
                    self.click(pos_continue)
                    last_continue_time = self.time()
                    self.sleep(3.0)
                    continue

                if self.time() - last_continue_time >= 30.0:
                    self.log("✅ 已经连续 30 秒未再发现继续按钮，判定为漫游载入完毕！开始尝试进入菜单...")
                    if self.enter_menu():
                        self.log("🎉 验证成功：已成功进入游戏主菜单！启动流程完美结束。")
                        return True
                    self.log("普通进入菜单失败(可能还在黑屏或有新弹窗)，重置 30秒倒计时，继续观察...")
                    last_continue_time = self.time()

            self.sleep(1.0)

        self.log("自动启动超时(5分钟)，放弃抢救。")
        return False

    def _find_horizon_by_edge(self, full_region):
        try:
            screen_bgr = self.vision.capture_region(full_region)
            template_bgr, _ = self.vision.load_template("horizon6.png")
            if template_bgr is None:
                return None

            screen_edge = self.vision.to_edge_image(screen_bgr)
            template_edge = self.vision.to_edge_image(template_bgr)

            for scale in self.vision.get_scales_to_try(fast_mode=False):
                scaled = template_edge if scale == 1.0 else cv2.resize(template_edge, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                h, w = scaled.shape[:2]
                if h > screen_edge.shape[0] or w > screen_edge.shape[1] or h < 5 or w < 5:
                    continue

                result = cv2.matchTemplate(screen_edge, scaled, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                if max_val >= 0.40:
                    self.log(f"[轮廓黑科技] 无视背景命中！得分: {max_val:.2f} 缩放: {scale:.2f}")
                    offset_x = full_region[0] if full_region else 0
                    offset_y = full_region[1] if full_region else 0
                    return (max_loc[0] + w // 2 + offset_x, max_loc[1] + h // 2 + offset_y)
        except Exception:
            return None

        return None

    def handle_vramne_restart(self):
        self.log("!!! 检测到 VRAMNE.png，2秒后强杀游戏，等待10分钟再重启...")
        self.sleep(2.0)

        if not self.is_running():
            return False

        if not self.kill_game():
            return False

        self.log("开始等待 10 分钟释放显存...")
        for _ in range(600):
            self.pause_handler()
            if not self.is_running():
                return False
            self.sleep(1)

        self.log("10分钟等待结束，准备自动重启游戏...")
        return self.restart_game_and_boot()

    def check_vramne_during_race(self):
        try:
            pos_vram = self.vision.find_image_gray(
                "VRAMNE.png",
                region=self.regions.get("全界面"),
                threshold=0.70,
                fast_mode=True,
            )
            if pos_vram:
                return self.handle_vramne_restart()
            return None
        except Exception as e:
            self.log(f"检测到显存不足: {e}")
            return None

    def attempt_recovery(self):
        self.log("任务执行异常中断，准备执行断点恢复流程...")
        if not self.focus_game():
            if not self.restart_game_and_boot():
                return False
        else:
            if not self.advanced_enter_menu():
                self.log("高级动态退回失败(可能游戏卡死或致命报错)，准备强杀进程并重启...")
                try:
                    self.command_runner(f"taskkill /F /IM {self.process_name} /T")
                    self.sleep(4)
                except Exception:
                    pass

                if not self.restart_game_and_boot():
                    return False
        self.log("环境重置成功！即将从中断处继续剩余任务。")
        return True

    def wait_for_freeroam(self):
        self.log("验证漫游状态...")
        for i in range(100):
            if not self.is_running():
                return False

            if self.vision.find_image("anna.png", region=self.regions.get("左下"), threshold=0.5):
                self.log("验证成功：已确认处于游戏漫游界面。")
                return True

            self.log(f"重试返回漫游界面({i + 1}/100)")
            self.key_press("esc")

            for _ in range(20):
                if not self.is_running():
                    return False
                self.sleep(0.1)

        self.log("多次尝试验证漫游界面失败，尝试进入菜单。")
        return True

    def recover_to_menu(self):
        self.log("开始尝试退回主菜单...")
        return self.enter_menu()

    def is_in_menu(self):
        return self.vision.find_image_gray(
            "collectionjournal.png",
            region=self.regions.get("左"),
            threshold=0.70,
            fast_mode=True,
        )

    def enter_menu(self):
        self.log("正在尝试进入主菜单...")
        for i in range(60):
            if not self.is_running():
                return False

            if self.is_in_menu():
                self.log(f"成功定位到菜单锚点！({i + 1}/60)")
                self.sleep(0.5)
                return True

            self.log(f"未在主菜单... ({i + 1}/60)")
            self.key_press("esc")
            self.sleep(1.0)

        self.log("60 次尝试均未进入菜单，请检查游戏状态。")
        return False

    def advanced_enter_menu(self):
        self.log("正在使用【高级恢复模式】尝试退回主菜单...")
        dynamic_obstacles = self._load_dynamic_obstacles()

        if not dynamic_obstacles:
            self.log("提示：images/obstacles/ 文件夹为空或不存在，将只使用 ESC 退回。")

        for i in range(80):
            self.pause_handler()
            if not self.is_running():
                return False

            if self.is_in_menu():
                self.log(f"成功定位到菜单锚点！(尝试次数: {i + 1})")
                self.sleep(0.5)
                return True

            if self.vision.find_image_gray("VRAMNE.png", region=self.regions.get("全界面"), threshold=0.75, fast_mode=True):
                self.log("!!! 严重警告: 检测到显存不足 (VRAMNE.png) 报错！")
                self.log("2秒后强杀游戏，随后冷却 10 分钟...")
                self.sleep(2.0)
                if not self.kill_game():
                    return False

                for _ in range(600):
                    self.pause_handler()
                    if not self.is_running():
                        return False
                    self.sleep(1)
                self.log("10 分钟冷却完毕，交给外层执行重启流程。")
                return False

            pos_obs = self.vision.find_any_image_gray(dynamic_obstacles, region=self.regions.get("全界面"), threshold=0.75, fast_mode=True)
            if pos_obs:
                self.log(f"退回途中检测到已知图片/弹窗，点击推进... ({i + 1}/80)")
                self.click(pos_obs)
                self.sleep(1.5)
                continue

            self.log(f"未在主菜单且无已知特定图片，按下 ESC... ({i + 1}/80)")
            self.key_press("esc")
            self.sleep(1.2)

        self.log("80 次动态尝试均未进入菜单，高级退回失败。")
        return False

    def _load_dynamic_obstacles(self):
        dynamic_obstacles = []
        if os.path.exists(self.obstacles_dir):
            for file in os.listdir(self.obstacles_dir):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    dynamic_obstacles.append(f"obstacles/{file}")
        return dynamic_obstacles

    def kill_game(self):
        try:
            self.command_runner(f"taskkill /F /IM {self.process_name} /T")
            self.log(f"已强杀 {self.process_name}")
            return True
        except Exception as e:
            self.log(f"强杀游戏失败: {e}")
            return False
