from dataclasses import dataclass


DEFAULT_NEXT_INDICES = (1, 2, 3, 0)


@dataclass(frozen=True)
class PipelineSettings:
    total_loops: int
    enabled_steps: tuple
    next_indices: tuple

    def get_next_index(self, curr_idx):
        if not self.enabled_steps[curr_idx]:
            return None
        return self.next_indices[curr_idx]


def pipeline_settings_from_config(config):
    return pipeline_settings_from_values(
        total_loops=config.get("global_loops", 10),
        enabled_values=(
            config.get("chk_1", True),
            config.get("chk_2", True),
            config.get("chk_3", True),
            config.get("chk_4", True),
        ),
        next_values=(
            config.get("next_1", 2),
            config.get("next_2", 3),
            config.get("next_3", 4),
            config.get("next_4", 1),
        ),
    )


def pipeline_settings_from_values(total_loops, enabled_values, next_values, fallback_total_loops=10):
    enabled_steps = tuple(_parse_bool(_value_at(enabled_values, index, True)) for index in range(4))
    next_indices = tuple(parse_next_index(True, _value_at(next_values, index, index + 1), index) for index in range(4))
    return PipelineSettings(
        total_loops=parse_total_loops(total_loops, fallback=fallback_total_loops),
        enabled_steps=enabled_steps,
        next_indices=next_indices,
    )


def parse_total_loops(value, fallback=10):
    try:
        return int(value)
    except Exception:
        return fallback


def parse_next_index(enabled, value, curr_idx, default_next=DEFAULT_NEXT_INDICES):
    if not enabled:
        return None

    try:
        return max(0, min(3, int(value) - 1))
    except Exception:
        return default_next[curr_idx]


def _parse_bool(value):
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "off"}
    return bool(value)


def _value_at(values, index, fallback):
    try:
        return values[index]
    except Exception:
        return fallback
