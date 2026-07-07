import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineCalculation:
    total_cars: int
    total_races: int
    global_loops: int
    race_count: int
    action_count: int


class PipelineCalculationError(ValueError):
    def __init__(self, code, total_cars=None):
        super().__init__(code)
        self.code = code
        self.total_cars = total_cars


def calculate_pipeline(target_cr, cost_per_car=81700, sp_per_car=30):
    if cost_per_car <= 0 or sp_per_car <= 0:
        raise PipelineCalculationError("non_positive_inputs")

    total_cars = target_cr // cost_per_car
    total_races = (total_cars * sp_per_car) // 10

    if total_races <= 0:
        raise PipelineCalculationError("insufficient_target", total_cars=total_cars)

    if total_races <= 99:
        final_loops = 1
        final_races_per_loop = total_races
    else:
        loops = math.ceil(total_races / 99)
        avg_races = total_races // loops

        if avg_races >= 70:
            final_loops = loops
            final_races_per_loop = avg_races
        else:
            final_races_per_loop = 99
            final_loops = total_races // 99

    cars_per_loop = (final_races_per_loop * 10) // sp_per_car

    if final_loops <= 0:
        raise PipelineCalculationError("zero_loops")

    return PipelineCalculation(
        total_cars=total_cars,
        total_races=total_races,
        global_loops=final_loops,
        race_count=final_races_per_loop,
        action_count=cars_per_loop,
    )
