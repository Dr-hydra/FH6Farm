import unittest

from fh6auto_core.pipeline_runner import PipelineRunner
from fh6auto_core.tasks import AutomationTask


class FakeRuntime:
    def __init__(self, next_indices=None, total_loops=1, focus_ok=True, recovery_results=None):
        self.running = True
        self.focus_ok = focus_ok
        self.total_loops = total_loops
        self.current_loop = 0
        self.next_indices = next_indices or {}
        self.recovery_results = list(recovery_results or [])
        self.logs = []
        self.focus_calls = 0
        self.stop_calls = 0
        self.recovery_calls = 0
        self.reset_calls = 0
        self.loop_labels = []
        self.finished_normally = False

    def is_running(self):
        return self.running

    def focus_game(self):
        self.focus_calls += 1
        return self.focus_ok

    def stop_all(self):
        self.stop_calls += 1
        self.running = False

    def log(self, message):
        self.logs.append(message)

    def attempt_recovery(self):
        self.recovery_calls += 1
        if self.recovery_results:
            return self.recovery_results.pop(0)
        return False

    def get_total_loops(self):
        return self.total_loops

    def set_current_loop(self, value, total_loops):
        self.current_loop = value
        self.update_loop_label(total_loops)

    def increment_loop(self, total_loops):
        self.current_loop += 1
        return self.current_loop

    def update_loop_label(self, total_loops):
        self.loop_labels.append((self.current_loop, total_loops))

    def reset_task_counters(self):
        self.reset_calls += 1

    def get_next_index(self, curr_idx):
        return self.next_indices.get(curr_idx)

    def on_finished_normally(self):
        self.finished_normally = True


def task(step, calls, results):
    result_queue = list(results)

    def run():
        calls.append(step)
        if result_queue:
            result = result_queue.pop(0)
            if isinstance(result, Exception):
                raise result
            return result
        return True

    return AutomationTask(step=step, label=step, run=run)


class PipelineRunnerTests(unittest.TestCase):
    def test_runs_start_task_and_stops_when_next_step_disabled(self):
        calls = []
        runtime = FakeRuntime(next_indices={0: None})
        runner = PipelineRunner(
            runtime=runtime,
            tasks={"race": task("race", calls, [True])},
            steps=("race",),
        )

        self.assertFalse(runner.run("race"))

        self.assertEqual(["race"], calls)
        self.assertEqual(1, runtime.focus_calls)
        self.assertEqual(1, runtime.stop_calls)
        self.assertEqual([(1, 1)], runtime.loop_labels)
        self.assertFalse(runtime.finished_normally)

    def test_advances_steps_and_finishes_when_total_loops_reached(self):
        calls = []
        runtime = FakeRuntime(next_indices={0: 1, 1: 0}, total_loops=2)
        runner = PipelineRunner(
            runtime=runtime,
            tasks={
                "race": task("race", calls, [True, True]),
                "buy": task("buy", calls, [True, True]),
            },
            steps=("race", "buy"),
        )

        self.assertTrue(runner.run("race"))

        self.assertEqual(["race", "buy", "race", "buy"], calls)
        self.assertEqual(3, runtime.current_loop)
        self.assertEqual(1, runtime.reset_calls)
        self.assertTrue(runtime.finished_normally)
        self.assertEqual(1, runtime.stop_calls)

    def test_recovers_after_task_failure_and_retries_same_step(self):
        calls = []
        runtime = FakeRuntime(next_indices={0: None}, recovery_results=[True])
        runner = PipelineRunner(
            runtime=runtime,
            tasks={"race": task("race", calls, [False, True])},
            steps=("race",),
        )

        self.assertFalse(runner.run("race"))

        self.assertEqual(["race", "race"], calls)
        self.assertEqual(1, runtime.recovery_calls)
        self.assertTrue(any("全局恢复" in message for message in runtime.logs))

    def test_stops_after_max_recovery_failures(self):
        calls = []
        runtime = FakeRuntime(recovery_results=[True, True])
        runner = PipelineRunner(
            runtime=runtime,
            tasks={"race": task("race", calls, [False, False, False])},
            steps=("race",),
            max_recoveries=2,
        )

        self.assertFalse(runner.run("race"))

        self.assertEqual(["race", "race", "race"], calls)
        self.assertEqual(2, runtime.recovery_calls)
        self.assertTrue(any("连续 3 次" in message for message in runtime.logs))
        self.assertEqual(1, runtime.stop_calls)

    def test_stops_without_running_task_when_focus_fails(self):
        calls = []
        runtime = FakeRuntime(focus_ok=False)
        runner = PipelineRunner(
            runtime=runtime,
            tasks={"race": task("race", calls, [True])},
            steps=("race",),
        )

        self.assertFalse(runner.run("race"))

        self.assertEqual([], calls)
        self.assertEqual(1, runtime.focus_calls)
        self.assertEqual(1, runtime.stop_calls)

    def test_task_exception_is_treated_as_failure(self):
        calls = []
        runtime = FakeRuntime(recovery_results=[False])
        runner = PipelineRunner(
            runtime=runtime,
            tasks={"race": task("race", calls, [RuntimeError("boom")])},
            steps=("race",),
        )

        self.assertFalse(runner.run("race"))

        self.assertEqual(["race"], calls)
        self.assertEqual(1, runtime.recovery_calls)
        self.assertTrue(any("执行模块 race 时异常" in message for message in runtime.logs))


if __name__ == "__main__":
    unittest.main()
