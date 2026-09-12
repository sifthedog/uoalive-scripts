import unittest

from fishing.direction import facing, tile_ahead, turn_toward_water, water_direction
from test_support.uo import FakeLand, install, static

FALLBACK_GRAPHIC = 1337
LAND_WATER = set([0x00A8])
STATIC_WATER = set([0x1797])

# direction name -> (dx, dy), same order as fishing.direction.DELTAS
CASES = [
    ("North", (0, -1)),
    ("Right", (1, -1)),
    ("East", (1, 0)),
    ("Down", (1, 1)),
    ("South", (0, 1)),
    ("Left", (-1, 1)),
    ("West", (-1, 0)),
    ("Up", (-1, -1)),
]


class FacingTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_each_name_is_matched_case_insensitively(self):
        self.api.Player.Direction = "east"
        self.assertEqual(facing(), 2)

        self.api.Player.Direction = "EAST"
        self.assertEqual(facing(), 2)

    def test_a_running_word_alongside_the_name_does_not_change_the_match(self):
        self.api.Player.Direction = "North, Running"
        self.assertEqual(facing(), 0)

    def test_an_unrecognised_value_falls_back_to_north(self):
        self.api.Player.Direction = "something else"
        self.assertEqual(facing(), 0)

    def test_none_falls_back_to_north(self):
        self.api.Player.Direction = None
        self.assertEqual(facing(), 0)


class TileAheadTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 100
        self.api.Player.Y = 100
        self.api.Player.Z = -5
        self.api.Player.Direction = "East"

    def find(self, tiles_ahead=4):
        return tile_ahead(tiles_ahead, LAND_WATER, STATIC_WATER, FALLBACK_GRAPHIC)

    def test_each_direction_projects_the_matching_offset(self):
        for direction, (dx, dy) in CASES:
            self.api.Player.Direction = direction
            tile = self.find()

            self.assertEqual((tile["x"], tile["y"]), (100 + dx * 4, 100 + dy * 4))

    def test_a_water_static_wins_over_the_land_tile_it_sits_on(self):
        self.api.land[(104, 100)] = FakeLand(0, 3)  # plain grass under it
        self.api.statics[(104, 100)] = [static(104, 100, -3, 0x1797, "water")]

        tile = self.find()

        self.assertEqual((tile["z"], tile["graphic"], tile["source"]), (-3, 0x1797, "static"))

    def test_a_non_water_static_does_not_override_the_land_tile(self):
        self.api.land[(104, 100)] = FakeLand(0, 0x00A8)
        self.api.statics[(104, 100)] = [static(104, 100, 0, 0x0DBF, "dock")]

        tile = self.find()

        self.assertEqual((tile["z"], tile["graphic"], tile["source"]), (0, 0x00A8, "land"))

    def test_a_land_tile_with_no_static_is_used_even_when_not_recognized_as_water(self):
        self.api.land[(104, 100)] = FakeLand(0, 3)

        tile = self.find()

        self.assertEqual((tile["z"], tile["graphic"], tile["source"]), (0, 3, "land (unrecognized)"))

    def test_no_land_data_falls_back_to_the_player_s_height_and_graphic(self):
        tile = self.find()

        self.assertEqual((tile["z"], tile["graphic"], tile["source"]),
                         (-5, FALLBACK_GRAPHIC, "fallback"))

    def test_a_running_word_does_not_change_the_tile(self):
        self.api.Player.Direction = "South, Running"
        tile = tile_ahead(3, LAND_WATER, STATIC_WATER, FALLBACK_GRAPHIC)

        self.assertEqual((tile["x"], tile["y"]), (100, 103))


class WaterDirectionTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 100
        self.api.Player.Y = 100
        self.api.Player.Direction = "East"  # (104, 100) - land, not water

    def test_the_current_facing_wins_when_it_is_already_water(self):
        self.api.land[(104, 100)] = FakeLand(0, 0x00A8)
        self.api.land[(100, 96)] = FakeLand(0, 0x00A8)  # north would also match

        self.assertEqual(water_direction(4, LAND_WATER, STATIC_WATER), 2)

    def test_another_direction_is_used_when_the_current_facing_is_not_water(self):
        self.api.land[(100, 104)] = FakeLand(0, 0x00A8)  # south, DELTAS index 4

        self.assertEqual(water_direction(4, LAND_WATER, STATIC_WATER), 4)

    def test_a_water_static_counts_the_same_as_a_water_land_tile(self):
        self.api.land[(104, 96)] = FakeLand(0, 3)  # plain grass under it
        self.api.statics[(104, 96)] = [static(104, 96, -3, 0x1797, "water")]  # northeast

        self.assertEqual(water_direction(4, LAND_WATER, STATIC_WATER), 1)

    def test_none_when_nothing_in_any_direction_matches(self):
        self.assertIsNone(water_direction(4, LAND_WATER, STATIC_WATER))


class TurnTowardWaterTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 100
        self.api.Player.Y = 100
        self.api.Player.Direction = "East"  # (104, 100) - land, not water

    def test_turns_toward_the_nearest_water_direction(self):
        self.api.land[(100, 104)] = FakeLand(0, 0x00A8)  # south

        self.assertEqual(turn_toward_water(4, LAND_WATER, STATIC_WATER, 0.5), 4)
        self.assertEqual(self.api.Player.Direction, "South")
        self.assertEqual(self.api.turned, ["south"])
        self.assertEqual(self.api.pauses, [0.5])

    def test_does_nothing_when_already_facing_water(self):
        self.api.land[(104, 100)] = FakeLand(0, 0x00A8)

        self.assertEqual(turn_toward_water(4, LAND_WATER, STATIC_WATER, 0.5), 2)
        self.assertEqual(self.api.Player.Direction, "East")
        self.assertEqual(self.api.turned, [])
        self.assertEqual(self.api.pauses, [])

    def test_does_nothing_when_no_direction_matches(self):
        self.assertIsNone(turn_toward_water(4, LAND_WATER, STATIC_WATER, 0.5))
        self.assertEqual(self.api.Player.Direction, "East")
        self.assertEqual(self.api.turned, [])
