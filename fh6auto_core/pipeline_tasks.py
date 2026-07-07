from .tasks import AutomationTask


def create_pipeline_tasks(task_objects, settings_provider):
    def sell_task():
        settings = settings_provider()
        if settings.sell_mode == 1:
            return task_objects["sell"].run_filtered(settings.sc_count)
        return task_objects["sell"].run_recent(settings.sc_count)

    return {
        "race": AutomationTask(
            step="race",
            label="循环跑图",
            run=lambda: task_objects["race"].run(settings_provider().race_count),
        ),
        "buy": AutomationTask(
            step="buy",
            label="批量买车",
            run=lambda: task_objects["buy"].run(settings_provider().buy_count),
        ),
        "cj": AutomationTask(
            step="cj",
            label="超级抽奖",
            run=lambda: task_objects["cj"].run(settings_provider().cj_count),
        ),
        "sell": AutomationTask(
            step="sell",
            label="清理车辆",
            run=sell_task,
        ),
    }
