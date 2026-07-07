import unittest

from fh6auto_core.regions import build_screen_regions


class RegionTests(unittest.TestCase):
    def test_build_screen_regions_matches_legacy_quadrants_and_halves(self):
        regions = build_screen_regions(10, 20, 100, 80)

        self.assertEqual((10, 20, 100, 80), regions["全界面"])
        self.assertEqual((10, 20, 50, 40), regions["左上"])
        self.assertEqual((60, 20, 50, 40), regions["右上"])
        self.assertEqual((10, 60, 50, 40), regions["左下"])
        self.assertEqual((60, 60, 50, 40), regions["右下"])
        self.assertEqual((10, 20, 100, 40), regions["上"])
        self.assertEqual((10, 60, 100, 40), regions["下"])
        self.assertEqual((10, 20, 50, 80), regions["左"])
        self.assertEqual((60, 20, 50, 80), regions["右"])
        self.assertEqual((35, 40, 50, 40), regions["中间"])


if __name__ == "__main__":
    unittest.main()
