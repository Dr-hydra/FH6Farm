from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class AutomationTask:
    step: str
    label: str
    run: Callable[[], bool]


@dataclass(frozen=True)
class TaskSettings:
    race_count: int
    buy_count: int
    cj_count: int
    sc_count: int
    sell_mode: int
    cj_mode: int


def task_settings_from_config(config):
    return task_settings_from_values(
        race_count=config.get("race_count", 99),
        buy_count=config.get("buy_count", 30),
        cj_count=config.get("cj_count", 30),
        sc_count=config.get("sc_count", 30),
        sell_mode=config.get("sell_mode", 1),
        cj_mode=config.get("cj_mode", 1),
    )


def task_settings_from_values(race_count, buy_count, cj_count, sc_count, sell_mode=1, cj_mode=1):
    return TaskSettings(
        race_count=_parse_int(race_count, 99),
        buy_count=_parse_int(buy_count, 30),
        cj_count=_parse_int(cj_count, 30),
        sc_count=_parse_int(sc_count, 30),
        sell_mode=_parse_mode(sell_mode),
        cj_mode=_parse_mode(cj_mode),
    )


def _parse_int(value, fallback):
    try:
        return int(value)
    except Exception:
        return fallback


def _parse_mode(value):
    text = str(value)
    if "模式2" in text or text == "2":
        return 2
    return 1
