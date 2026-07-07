from .automation_context import AutomationContext
from .buy_car_task import BuyCarTask
from .config_runtime import ConfigPipelineRuntime
from .pipeline_runner import PipelineRunner
from .pipeline_tasks import create_pipeline_tasks
from .race_task import RaceTask
from .sell_car_task import SellCarTask
from .tasks import task_settings_from_config
from .wheelspin_task import WheelspinTask


def create_headless_pipeline(bot):
    context = AutomationContext(bot)
    task_objects = {
        "race": RaceTask(context),
        "buy": BuyCarTask(context),
        "cj": WheelspinTask(context),
        "sell": SellCarTask(context),
    }
    tasks = create_pipeline_tasks(task_objects, settings_provider=lambda: task_settings_from_config(bot.config))
    runner = PipelineRunner(
        runtime=ConfigPipelineRuntime(bot),
        tasks=tasks,
    )
    return tasks, runner, task_objects
