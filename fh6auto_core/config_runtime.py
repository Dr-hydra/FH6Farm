import os
import time

from .pipeline_config import pipeline_settings_from_config


class ConfigPipelineRuntime:
    """Pipeline runtime backed directly by normalized config values."""

    def __init__(self, bot):
        self.bot = bot

    def is_running(self):
        return self.bot.is_running

    def focus_game(self):
        return self.bot.check_and_focus_game()

    def stop_all(self):
        self.bot.stop_all()

    def log(self, message):
        self.bot.log(message)

    def attempt_recovery(self):
        return self.bot.attempt_recovery()

    def get_total_loops(self):
        return self._pipeline_settings().total_loops

    def set_current_loop(self, value, total_loops):
        self.bot.global_loop_current = value
        self.update_loop_label(total_loops)

    def increment_loop(self, total_loops):
        self.bot.global_loop_current += 1
        return self.bot.global_loop_current

    def update_loop_label(self, total_loops):
        self.bot.last_loop_status = (self.bot.global_loop_current, total_loops)

    def reset_task_counters(self):
        self.bot.race_counter = 0
        self.bot.car_counter = 0
        self.bot.cj_counter = 0
        self.bot.sc_count = 0

    def get_next_index(self, curr_idx):
        return self._pipeline_settings().get_next_index(curr_idx)

    def _pipeline_settings(self):
        return pipeline_settings_from_config(self.bot.config)

    def on_finished_normally(self):
        if self.bot.config.get("auto_close_game", False):
            self.log("【任务圆满完成】已开启自动退游，30秒后强制关闭游戏...")
            for _ in range(30):
                if not self.is_running():
                    break
                time.sleep(1)
            if self.is_running():
                try:
                    os.system("taskkill /F /IM forzahorizon6.exe /T")
                    self.log("已强行杀死游戏进程。")
                    time.sleep(2)
                except Exception as e:
                    self.log(f"关闭游戏失败: {e}")

        if self.bot.config.get("auto_shutdown", False) and self.is_running():
            self.log("【任务圆满完成】触发自动关机！系统将在 3 分钟后关闭！")
            self.log("提示：如需取消关机，请按 Win+R 键，输入 shutdown -a 并回车。")
            os.system("shutdown -s -t 180")
