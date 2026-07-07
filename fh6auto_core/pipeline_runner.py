STEPS = ("race", "buy", "cj", "sell")


class PipelineRunner:
    def __init__(self, runtime, tasks, steps=STEPS, max_recoveries=10):
        self.runtime = runtime
        self.tasks = tasks
        self.steps = list(steps)
        self.max_recoveries = max_recoveries

    def run(self, start_step):
        task_finished_normally = False

        if start_step not in self.steps:
            raise ValueError(f"unknown pipeline step: {start_step}")

        if not self.runtime.focus_game():
            self.runtime.stop_all()
            return False

        curr_idx = self.steps.index(start_step)
        total_loops = self.runtime.get_total_loops()
        self.runtime.set_current_loop(1, total_loops)
        continuous_failures = 0

        while self.runtime.is_running():
            step_name = self.steps[curr_idx]
            success = self._run_task(step_name)

            if not self.runtime.is_running():
                break

            if not success:
                continuous_failures += 1
                if continuous_failures > self.max_recoveries:
                    self.runtime.log(f"!!! 警告：连续 {continuous_failures} 次触发断点恢复仍未能解决问题！")
                    self.runtime.log("为防止游戏陷入死循环，强制终止当前所有任务，请人工检查游戏状态。")
                    break

                self.runtime.log(f"正在进行全局恢复 (第 {continuous_failures}/{self.max_recoveries} 次允许的重试)...")
                if self.runtime.attempt_recovery():
                    continue

                self.runtime.log("致命错误：连退回菜单/重启也失败了，彻底停止。")
                break

            continuous_failures = 0
            next_idx = self.runtime.get_next_index(curr_idx)
            if next_idx is None:
                break

            if next_idx <= curr_idx:
                current_loop = self.runtime.increment_loop(total_loops)
                if current_loop > total_loops:
                    self.runtime.log("达到设定的总循环次数，任务圆满结束。")
                    task_finished_normally = True
                    break

                self.runtime.log(f"开启新一轮大循环 ({current_loop}/{total_loops})")
                self.runtime.update_loop_label(total_loops)
                self.runtime.reset_task_counters()

            curr_idx = next_idx

        if task_finished_normally and self.runtime.is_running():
            self.runtime.on_finished_normally()

        self.runtime.stop_all()
        return task_finished_normally

    def _run_task(self, step_name):
        try:
            return self.tasks[step_name].run()
        except Exception as e:
            self.runtime.log(f"执行模块 {step_name} 时异常: {e}")
            return False
