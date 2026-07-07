import threading
import time

import pyautogui
import pydirectinput

from .config import DEFAULT_CONFIG, load_config as load_core_config, save_config as save_core_config
from .game_session import GameSession
from .headless_pipeline import create_headless_pipeline
from .input_controller import DIK_CODES, InputController
from .recovery_manager import RecoveryManager
from .regions import build_screen_regions
from .runtime_paths import (
    APP_DIR,
    CACHE_DIR,
    CURRENT_VERSION,
    INTERNAL_DIR,
    TEMPLATE_CACHE_FILE,
    TEMPLATE_META_FILE,
    USER_CONFIG_FILE,
    auto_extract_configs,
    auto_extract_images,
)
from .vision_service import VisionService


class HeadlessAutomationBot:
    """Non-CTk automation core used by WPF and the headless CLI."""

    def __init__(
        self,
        *,
        config_file=USER_CONFIG_FILE,
        app_dir=APP_DIR,
        internal_dir=INTERNAL_DIR,
        cache_dir=CACHE_DIR,
        template_cache_file=TEMPLATE_CACHE_FILE,
        template_meta_file=TEMPLATE_META_FILE,
        current_version=CURRENT_VERSION,
        input_controller=None,
        game_session=None,
        vision_service=None,
        recovery_manager=None,
        pipeline_factory=create_headless_pipeline,
        screen_size_provider=None,
        mouse_module=pydirectinput,
        thread_factory=None,
        start_background_init=True,
        migrate_old_config=True,
    ):
        self.headless_mode = True
        self.config_file = config_file
        self.app_dir = app_dir
        self.internal_dir = internal_dir
        self.cache_dir = cache_dir
        self.template_cache_file = template_cache_file
        self.template_meta_file = template_meta_file
        self.current_version = current_version
        self.mouse = mouse_module
        self.thread_factory = thread_factory or (lambda target: threading.Thread(target=target, daemon=True))
        self._destroy_event = threading.Event()

        self.is_running = False
        self.current_thread = None
        self.is_paused = False
        self.race_counter = 0
        self.car_counter = 0
        self.cj_counter = 0
        self.sc_count = 0
        self.global_loop_current = 0
        self.detail_state_confirmed = False
        self.support_win = None
        self.overlay_geometry = None
        self.last_task_status = ("", 0, 0)

        self.input = input_controller or InputController(
            pause_checker=self.check_pause,
            running_checker=lambda: self.is_running,
        )

        self.game_session = game_session or GameSession(
            logger=self.log,
            update_regions=self.update_regions_by_window,
            ui_call=self.ui_call,
            is_running=lambda: self.is_running,
            set_overlay_geometry=self._set_overlay_geometry,
        )

        self.vision = vision_service or VisionService(
            app_dir=app_dir,
            internal_dir=internal_dir,
            cache_dir=cache_dir,
            template_cache_file=template_cache_file,
            template_meta_file=template_meta_file,
            current_version=current_version,
            logger=self.log,
            regions_provider=lambda: self.regions,
            running_checker=lambda: self.is_running,
            paused_checker=lambda: self.is_paused,
            pause_handler=self.check_pause,
        )
        self._bind_vision_caches()

        self.recovery = recovery_manager or RecoveryManager(
            vision=self.vision,
            logger=self.log,
            regions_provider=lambda: self.regions,
            running_checker=lambda: self.is_running,
            pause_handler=self.check_pause,
            focus_game=self.check_and_focus_game,
            key_press=self.hw_press,
            click=self.game_click,
            auto_restart_enabled=self._is_auto_restart_enabled,
            restart_command_provider=self._get_restart_command,
        )

        self.init_regions(screen_size_provider or pyautogui.size)

        if migrate_old_config and config_file == USER_CONFIG_FILE:
            auto_extract_configs()
        self.load_config()

        self.pipeline_tasks, self.pipeline_runner, automation_tasks = pipeline_factory(self)
        self.race_task = automation_tasks["race"]
        self.buy_car_task = automation_tasks["buy"]
        self.wheelspin_task = automation_tasks["cj"]
        self.sell_car_task = automation_tasks["sell"]

        if start_background_init:
            self._start_background_init()

        self.log("Headless core initialized. WPF is the active UI surface.")

    def _bind_vision_caches(self):
        self.template_cache = getattr(self.vision, "template_cache", {})
        self.template_gray_cache = getattr(self.vision, "template_gray_cache", {})
        self.template_transparent_cache = getattr(self.vision, "template_transparent_cache", {})
        self.scaled_template_cache = getattr(self.vision, "scaled_template_cache", {})
        self.file_template_cache = getattr(self.vision, "file_template_cache", {})
        self.last_positions = getattr(self.vision, "last_positions", {})

    def _start_background_init(self):
        def background_init():
            auto_extract_images()
            self.vision.prepare_template_cache()
            self.file_template_cache = getattr(self.vision, "file_template_cache", {})

        threading.Thread(target=background_init, daemon=True).start()

    def _set_overlay_geometry(self, x, y, width, height):
        self.overlay_geometry = (x, y, width, height)

    def ui_call(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return None

    def after(self, delay_ms, callback):
        if delay_ms <= 0:
            callback()
            return None
        timer = threading.Timer(delay_ms / 1000.0, callback)
        timer.daemon = True
        timer.start()
        return timer

    def mainloop(self):
        self._destroy_event.wait()

    def destroy(self):
        self._destroy_event.set()

    def init_regions(self, screen_size_provider=pyautogui.size):
        width, height = screen_size_provider()
        self.update_regions_by_window(0, 0, width, height)

    def update_regions_by_window(self, x, y, width, height):
        self.regions = build_screen_regions(x, y, width, height)

    def load_config(self):
        self.config = dict(DEFAULT_CONFIG)
        try:
            self.config = load_core_config(self.config_file)
        except Exception as e:
            self.log(f"用户 config.json 读取失败，已保留原文件：{e}")

    def save_config(self):
        try:
            self.config = save_core_config(self.config, self.config_file)
        except Exception as e:
            self.log(f"保存配置失败: {e}")

    def log(self, message):
        current_time = time.strftime("%H:%M:%S")
        try:
            print(f"[{current_time}] {message}", flush=True)
        except Exception:
            pass

    def update_timer(self):
        if not self.is_running:
            return
        self.elapsed_seconds = int(time.time() - self.start_time)

    def update_running_ui(self, task_name="", current_val=0, max_val=0):
        self.last_task_status = (task_name, current_val, max_val)
        if task_name and hasattr(self, "lbl_mini_task"):
            self.ui_call(self.lbl_mini_task.configure, text=f"当前任务: {task_name}")
        if max_val > 0 and hasattr(self, "lbl_mini_prog"):
            self.ui_call(self.lbl_mini_prog.configure, text=f"执行进度: {current_val} / {max_val}")

    def hw_key_down(self, key):
        self.input.key_down(key)

    def hw_key_up(self, key):
        self.input.key_up(key)

    def hw_press(self, key, delay=0.08):
        self.input.press(key, delay=delay)

    def hw_mouse_move(self, x, y):
        self.input.mouse_move(x, y)

    def game_click(self, pos, double=False):
        self.check_pause()
        if not self.is_running or not pos:
            return

        x, y = int(pos[0]), int(pos[1])
        self.hw_mouse_move(x, y)
        time.sleep(0.2)
        for _ in range(2 if double else 1):
            self.mouse.mouseDown()
            time.sleep(0.1)
            self.mouse.mouseUp()
            time.sleep(0.1)
        time.sleep(0.1)

        try:
            gx, gy, _gw, _gh = self.regions["全界面"]
            self.hw_mouse_move(gx + 5, gy + 5)
        except Exception:
            self.hw_mouse_move(5, 5)
        time.sleep(0.2)

    def move_to_game_coord(self, x, y):
        try:
            gx, gy, _gw, _gh = self.regions["全界面"]
            self.hw_mouse_move(gx + x, gy + y)
        except Exception:
            self.hw_mouse_move(x, y)

    def start_pipeline(self, start_step):
        if self.is_running:
            return

        self.is_running = True
        self._reset_pipeline_run_state()

        def runner():
            self.pipeline_runner.run(start_step)

        self.current_thread = self.thread_factory(runner)
        self.current_thread.start()

    def _reset_pipeline_run_state(self):
        self.start_time = time.time()
        self.update_timer()
        self.update_running_ui("初始化中...")
        self.race_counter = 0
        self.car_counter = 0
        self.cj_counter = 0
        self.sc_count = 0
        self.global_loop_current = 0

    def stop_all(self):
        if not self.is_running:
            self.destroy()
            return

        self.is_running = False
        self.is_paused = False

        for key in DIK_CODES.keys():
            self.hw_key_up(key)
        for key in ["w", "e", "y", "enter", "esc", "up", "down", "left", "right", "space", "backspace"]:
            self.hw_key_up(key)

        try:
            self.mouse.mouseUp()
        except Exception:
            pass

        self.log("!!! 任务已停止，所有物理按键状态已强制重置")
        self.destroy()

    def toggle_pause(self):
        if not self.is_running:
            return

        self.is_paused = not self.is_paused
        if self.is_paused:
            self.log("⏸ 任务已暂停 (按 F9 或点击按钮恢复)")
            for key in ["w", "e", "y", "enter", "esc", "up", "down", "left", "right", "space", "backspace"]:
                self.hw_key_up(key)
            try:
                self.mouse.mouseUp()
            except Exception:
                pass
        else:
            self.log("▶ 任务已恢复")

    def check_pause(self):
        while self.is_paused and self.is_running:
            time.sleep(0.1)

    def set_english_input(self):
        return self.game_session.set_english_input()

    def check_and_focus_game(self):
        return self.game_session.check_and_focus_game()

    def _is_auto_restart_enabled(self):
        return bool(self.config.get("auto_restart", False))

    def _get_restart_command(self):
        return self.config.get("restart_cmd", "start steam://run/2483190")

    def attempt_recovery(self):
        return self.recovery.attempt_recovery()
