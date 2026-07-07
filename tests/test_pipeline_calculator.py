import unittest

from fh6auto_core.pipeline_calculator import (
    PipelineCalculation,
    PipelineCalculationError,
    calculate_pipeline,
)


class PipelineCalculatorTests(unittest.TestCase):
    def test_calculates_single_loop_when_total_races_under_cap(self):
        result = calculate_pipeline(target_cr=81700 * 10, cost_per_car=81700, sp_per_car=30)

        self.assertEqual(PipelineCalculation(10, 30, 1, 30, 10), result)

    def test_balances_large_work_when_average_is_high_enough(self):
        result = calculate_pipeline(target_cr=81700 * 300, cost_per_car=81700, sp_per_car=30)

        self.assertEqual(PipelineCalculation(300, 900, 10, 90, 30), result)

    def test_uses_full_99_races_when_average_would_be_too_low(self):
        result = calculate_pipeline(target_cr=81700 * 34, cost_per_car=81700, sp_per_car=30)

        self.assertEqual(PipelineCalculation(34, 102, 1, 99, 33), result)

    def test_rejects_non_positive_inputs(self):
        with self.assertRaises(PipelineCalculationError) as ctx:
            calculate_pipeline(target_cr=100, cost_per_car=0, sp_per_car=30)

        self.assertEqual("non_positive_inputs", ctx.exception.code)

    def test_reports_insufficient_target_with_total_car_count(self):
        with self.assertRaises(PipelineCalculationError) as ctx:
            calculate_pipeline(target_cr=100, cost_per_car=81700, sp_per_car=30)

        self.assertEqual("insufficient_target", ctx.exception.code)
        self.assertEqual(0, ctx.exception.total_cars)


if __name__ == "__main__":
    unittest.main()
