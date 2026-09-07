import unittest

import uo.clock
from mining.vein import Veins
from test_support.uo import FakeLand, install, static
from uo.terrain import Terrain
from uo.tiles import TileMemory


class Frozen(object):
    def __init__(self, at):
        self.at = at

    def time(self):
        return self.at


class MarkAreaDepletedTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 1006
        self.api.Player.Y = 1003
        self.api.Player.Z = 0
        self.saved = uo.clock.time
        uo.clock.time = Frozen(1000.0)

        for x in range(990, 1020):
            for y in range(990, 1020):
                self.api.land[(x, y)] = FakeLand(0, 231)

        self.memory = TileMemory(1500.0, 300.0, "vein", "mined", [].append)
        self.veins = Veins(Terrain(), self.memory, {
            "tile_graphics": set([231]),
            "not_ore_graphics": set(),
            "static_names": [],
            "z_range": 20,
            "range": 2,
            "scan_radius": 12,
            "probes": 24,
            "respawn_delay": 1500.0,
            "bank": 8,
        }, [].append)

    def tearDown(self):
        uo.clock.time = self.saved

    def _blocked(self, x, y):
        return self.veins.is_parked({"x": x, "y": y, "z": 0, "graphic": 231, "is_land": True})

    def test_parks_the_whole_bank_the_character_stands_in(self):
        self.veins.mark_area_depleted(2)

        self.assertTrue(self._blocked(1000, 1000))
        self.assertTrue(self._blocked(1007, 1007))
        self.assertTrue(self._blocked(1006, 1003))

    def test_parks_the_reach_circle_over_the_bank_border(self):
        self.veins.mark_area_depleted(2)

        self.assertTrue(self._blocked(1008, 1003))
        self.assertTrue(self._blocked(1008, 1005))

    def test_leaves_the_next_bank_beyond_reach(self):
        self.veins.mark_area_depleted(2)

        self.assertFalse(self._blocked(1009, 1003))
        self.assertFalse(self._blocked(1000, 1008))

    def test_counts_the_tiles_in_reach_it_parked(self):
        self.assertEqual(self.veins.mark_area_depleted(2), 25)

    def test_parks_the_bank_without_reading_more_ground(self):
        list(self.veins._terrain.box(2))
        reads = self.veins._terrain.reads

        self.veins.mark_area_depleted(2)

        self.assertEqual(self.veins._terrain.reads, reads)

    def test_a_parked_bank_is_a_cooling_time_rather_than_a_dead_end(self):
        self.veins.mark_area_depleted(2)

        found, cooling = self.veins.scan_box(1)

        self.assertIsNone(found)
        self.assertEqual(cooling, 2500.0)


class ScanTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 1000
        self.api.Player.Y = 1000
        self.api.Player.Z = 0
        self.saved = uo.clock.time
        uo.clock.time = Frozen(1000.0)

        for x in range(980, 1021):
            for y in range(980, 1021):
                self.api.land[(x, y)] = FakeLand(0, 3)

        self.memory = TileMemory(1500.0, 300.0, "vein", "mined", [].append)
        self.terrain = Terrain()
        self.veins = Veins(self.terrain, self.memory, {
            "tile_graphics": set([231]),
            "not_ore_graphics": set(),
            "static_names": [],
            "z_range": 20,
            "range": 2,
            "scan_radius": 12,
            "probes": 24,
            "respawn_delay": 1500.0,
            "bank": 8,
        }, [].append)

    def tearDown(self):
        uo.clock.time = self.saved

    def test_reads_only_as_far_as_the_first_ring_with_a_vein(self):
        self.api.land[(1003, 1000)] = FakeLand(0, 231)
        self.api.paths[(1003, 1000)] = [1]

        found, _cooling = self.veins.scan()

        self.assertEqual((found["x"], found["y"]), (1003, 1000))
        self.assertEqual(self.terrain.reads, 49 + 2)
        self.assertEqual(self.veins.stats["reads"], 49 + 2)
        self.assertEqual(self.veins.stats["probes"], 1)

    def test_a_cave_floor_costs_no_land_reads_at_all(self):
        self.api.statics[(1002, 1000)] = [static(1002, 1000, 0, 1339, "cave floor")]
        self.veins._config["static_names"] = ["cave"]

        found, _cooling = self.veins.scan()

        self.assertEqual((found["x"], found["y"]), (1002, 1000))
        self.assertEqual(self.terrain.reads, 1)
        self.assertEqual(self.api.path_probes, [])

    def test_sweeps_the_whole_radius_when_nothing_is_near(self):
        found, cooling = self.veins.scan()

        self.assertIsNone(found)
        self.assertIsNone(cooling)
        self.assertEqual(self.terrain.reads, 625 + 11)
