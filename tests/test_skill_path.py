import unittest

from fh6auto_core.skill_path import cells_to_directions, directions_to_cells, normalize_skill_dirs


class SkillPathTests(unittest.TestCase):
    def test_directions_to_cells_starts_at_legacy_bottom_left_cell(self):
        cells, directions = directions_to_cells(["right", "up", "up", "up", "left"])

        self.assertEqual([12, 13, 9, 5, 1, 0], cells)
        self.assertEqual(["right", "up", "up", "up", "left"], directions)

    def test_directions_to_cells_stops_on_out_of_bounds_move(self):
        cells, directions = directions_to_cells(["left", "up"])

        self.assertEqual([12], cells)
        self.assertEqual([], directions)

    def test_directions_to_cells_stops_on_repeated_cell(self):
        cells, directions = directions_to_cells(["right", "left", "up"])

        self.assertEqual([12, 13], cells)
        self.assertEqual(["right"], directions)

    def test_normalize_skill_dirs_skips_unknown_directions_before_valid_moves(self):
        self.assertEqual(["right", "up"], normalize_skill_dirs(["bad", "right", "up"]))

    def test_cells_to_directions_converts_adjacent_path(self):
        self.assertEqual(["right", "up", "left"], cells_to_directions([12, 13, 9, 8]))


if __name__ == "__main__":
    unittest.main()
