import unittest

from fishing.water import is_water, nearest_water
from test_support.uo import FakeLand, install, static, tile
from uo.terrain import Terrain

LAND_WATER = set([0x00A8])
STATIC_WATER = set([0x1797])


class IsWaterTest(unittest.TestCase):
    def test_a_land_art_is_read_against_the_land_table(self):
        self.assertTrue(is_water(tile(1, 1, graphic=0x00A8), LAND_WATER, STATIC_WATER))
        self.assertFalse(is_water(tile(1, 1, graphic=0x1797), LAND_WATER, STATIC_WATER))

    def test_a_static_art_is_read_against_the_static_table(self):
        self.assertTrue(is_water(tile(1, 1, graphic=0x1797, is_land=False), LAND_WATER,
                                 STATIC_WATER))
        self.assertFalse(is_water(tile(1, 1, graphic=0x00A8, is_land=False), LAND_WATER,
                                  STATIC_WATER))


class NearestWaterTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 100
        self.api.Player.Y = 100

        for x in range(96, 105):
            for y in range(96, 105):
                self.api.land[(x, y)] = FakeLand(0, 3)

    def find(self, radius=4):
        return nearest_water(Terrain(), radius, LAND_WATER, STATIC_WATER)

    def test_nothing_in_range_is_none(self):
        self.assertIsNone(self.find())

    def test_the_nearest_of_two_water_tiles_wins(self):
        self.api.land[(104, 100)] = FakeLand(-5, 0x00A8)
        self.api.land[(100, 98)] = FakeLand(-5, 0x00A8)

        found = self.find()

        self.assertEqual((found["x"], found["y"], found["z"]), (100, 98, -5))
        self.assertEqual(found["graphic"], 0x00A8)
        self.assertTrue(found["is_land"])

    def test_a_water_static_is_found_with_its_own_art_and_height(self):
        self.api.statics[(102, 101)] = [static(102, 101, -3, 0x1797, "water")]

        found = self.find()

        self.assertEqual((found["x"], found["y"], found["z"]), (102, 101, -3))
        self.assertFalse(found["is_land"])

    def test_a_static_that_is_not_water_is_skipped(self):
        self.api.statics[(101, 100)] = [static(101, 100, 0, 0x0DBF, "dock")]

        self.assertIsNone(self.find())

    def test_water_past_the_range_is_not_seen(self):
        self.api.land[(100, 95)] = FakeLand(-5, 0x00A8)

        self.assertIsNone(self.find())
