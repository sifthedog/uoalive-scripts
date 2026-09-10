import unittest

from mining.vein import Veins
from test_support.uo import install, tile
from uo.terrain import Terrain
from uo.tiles import TileMemory


class IsOreTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.Z = 0
        self.memory = TileMemory(1500.0, 300.0, "vein", "mined", [].append)
        self.veins = Veins(Terrain(), self.memory, {
            "tile_graphics": set([231]),
            "not_ore_graphics": set([232]),
            "static_names": ["cave"],
            "z_range": 20,
        }, [].append)

    def test_land_is_answered_by_the_table(self):
        self.assertTrue(self.veins.matches(tile(0, 0, 0, 231)))
        self.assertFalse(self.veins.matches(tile(0, 0, 0, 3)))

    def test_the_refusal_table_beats_the_land_table(self):
        self.veins._config["tile_graphics"].add(232)

        self.assertFalse(self.veins.matches(tile(0, 0, 0, 232)))

    def test_a_banned_art_is_refused(self):
        self.memory.ban_art(tile(0, 0, 0, 231))

        self.assertFalse(self.veins.matches(tile(0, 0, 0, 231)))

    def test_a_static_matches_by_name(self):
        self.assertTrue(self.veins.matches(tile(0, 0, 0, 1339, False, "cave floor")))
        self.assertFalse(self.veins.matches(tile(0, 0, 0, 1339, False, "pebbles")))

    def test_within_z_is_measured_from_the_player(self):
        self.assertTrue(self.veins.within_z(20))
        self.assertFalse(self.veins.within_z(21))
