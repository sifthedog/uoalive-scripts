import unittest

import uo.clock
from test_support.uo import install, tile
from uo.tiles import TileMemory, art_key, tile_key


class Frozen(object):
    def __init__(self, at):
        self.at = at

    def time(self):
        return self.at


class ArtKeyTest(unittest.TestCase):
    def test_land_and_statics_are_numbered_separately(self):
        self.assertNotEqual(art_key(1339, True), art_key(1339, False))

    def test_the_tile_key_carries_the_art_kind(self):
        self.assertNotEqual(tile_key(tile(1, 2, 3, 1339, True)),
                            tile_key(tile(1, 2, 3, 1339, False)))

    def test_two_tiles_at_one_coordinate_key_apart_by_z(self):
        self.assertNotEqual(tile_key(tile(1, 2, 0, 5)), tile_key(tile(1, 2, 40, 5)))


class TileMemoryTest(unittest.TestCase):
    def setUp(self):
        install()
        self.clock = Frozen(1000.0)
        self.saved = uo.clock.time
        uo.clock.time = self.clock
        self.said = []
        self.memory = TileMemory(1500.0, 300.0, "vein", "mined", self.said.append)
        self.tile = tile(1, 2, 3, 1339)

    def tearDown(self):
        uo.clock.time = self.saved

    def test_a_fresh_tile_is_not_blocked(self):
        self.assertFalse(self.memory.is_blocked(self.tile))

    def test_a_depleted_tile_comes_back_after_the_respawn(self):
        self.memory.mark_depleted(self.tile)

        self.assertTrue(self.memory.is_blocked(self.tile))

        self.clock.at += 1500.0

        self.assertFalse(self.memory.is_blocked(self.tile))

    def test_unreachable_times_out_sooner_than_depleted(self):
        self.memory.mark_unreachable(self.tile)
        self.clock.at += 300.0

        self.assertFalse(self.memory.is_blocked(self.tile))

    def test_unusable_never_comes_back(self):
        self.memory.mark_unusable(self.tile, "cannot be mined")
        self.clock.at += 10 ** 9

        self.assertTrue(self.memory.is_blocked(self.tile))
        self.assertEqual(self.said, ["the vein at 1,2 cannot be mined"])

    def test_blocking_one_tile_leaves_its_neighbour_alone(self):
        self.memory.mark_depleted(self.tile)

        self.assertFalse(self.memory.is_blocked(tile(2, 2, 3, 1339)))

    def test_a_banned_art_covers_every_tile_wearing_it(self):
        self.memory.ban_art(self.tile)

        self.assertTrue(self.memory.art_banned(1339, True))
        self.assertFalse(self.memory.art_banned(1339, False))

    def test_the_ban_is_said_once(self):
        self.memory.ban_art(self.tile)
        self.memory.ban_art(tile(9, 9, 0, 1339))

        self.assertEqual(len(self.said), 1)

    def test_two_memories_do_not_share_what_is_blocked(self):
        self.memory.mark_depleted(self.tile)

        self.assertFalse(TileMemory(1500.0, 300.0, "vein", "mined", self.said.append)
                         .is_blocked(self.tile))
