import unittest

import uo.clock
from mining.plan import Planner, ascii_map, cover, footprint, route
from mining.vein import Veins
from test_support.uo import FakeLand, install, point, static
from uo.terrain import Terrain
from uo.tiles import TileMemory


class Frozen(object):
    def __init__(self, at):
        self.at = at

    def time(self):
        return self.at


class FootprintTest(unittest.TestCase):
    def test_reach_one_is_the_nine_around(self):
        found = footprint(5, 5, 1)

        self.assertEqual(len(found), 9)
        self.assertIn((5, 5), found)
        self.assertIn((4, 4), found)
        self.assertIn((6, 6), found)
        self.assertNotIn((7, 5), found)

    def test_reach_zero_is_the_coordinate(self):
        self.assertEqual(footprint(5, 5, 0), [(5, 5)])


class CoverTest(unittest.TestCase):
    def _grid(self, x1, y1, x2, y2):
        return [(x, y) for x in range(x1, x2 + 1) for y in range(y1, y2 + 1)]

    def test_no_ore_plans_nothing(self):
        self.assertEqual(cover(set(), self._grid(0, 0, 10, 10), 1, 1, (5, 5)), [])

    def test_one_tile_is_covered_from_the_candidate_nearest_the_start(self):
        found = cover(set([(9, 5)]), self._grid(0, 0, 10, 10), 1, 1, (5, 5))

        self.assertEqual(found, [(8, 4)])

    def test_two_clusters_apart_take_two_spots(self):
        ore = set([(2, 2), (2, 3), (12, 12), (13, 12)])
        found = cover(ore, self._grid(0, 0, 15, 15), 1, 1, (0, 0))

        self.assertEqual(len(found), 2)

    def test_covering_three_beats_covering_one(self):
        ore = set([(10, 0), (10, 1), (10, 2), (0, 10)])
        found = cover(ore, self._grid(0, 0, 12, 12), 1, 1, (0, 9))

        self.assertEqual(found[0], (9, 1))

    def test_min_ore_leaves_an_isolated_tile_unplanned(self):
        ore = set([(2, 2), (2, 3), (12, 12)])
        found = cover(ore, self._grid(0, 0, 15, 15), 1, 2, (0, 0))

        self.assertEqual(len(found), 1)
        self.assertNotIn((12, 12), found)

    def test_ore_that_is_no_candidate_is_covered_from_a_neighbour(self):
        candidates = [xy for xy in self._grid(0, 0, 10, 10) if xy != (5, 5)]
        found = cover(set([(5, 5)]), candidates, 1, 1, (5, 5))

        self.assertEqual(len(found), 1)
        self.assertIn((5, 5), footprint(found[0][0], found[0][1], 1))

    def test_a_full_tie_is_broken_by_y_then_x(self):
        found = cover(set([(5, 5)]), self._grid(0, 0, 10, 10), 1, 1, (5, 8))

        self.assertEqual(found, [(4, 6)])


class RouteTest(unittest.TestCase):
    def test_starts_with_the_spot_nearest_the_start(self):
        self.assertEqual(route([(9, 9), (2, 2)], (0, 0)), [(2, 2), (9, 9)])

    def test_walks_to_the_nearest_next(self):
        self.assertEqual(route([(0, 9), (5, 0), (6, 1)], (0, 0)), [(5, 0), (6, 1), (0, 9)])

    def test_nothing_in_is_nothing_out(self):
        self.assertEqual(route([], (0, 0)), [])


class AsciiMapTest(unittest.TestCase):
    def test_marks_the_player_the_ore_and_the_spots_in_order(self):
        rows = ascii_map((0, 0, 3, 2), set([(3, 0), (0, 2)]), [(1, 1), (0, 2)], (0, 0))

        self.assertEqual(rows, ["@..#", ".1..", "2..."])

    def test_past_the_letters_a_spot_is_a_plus(self):
        spots = [(n, 0) for n in range(36)]
        rows = ascii_map((0, 0, 35, 0), set(), spots, (40, 40))

        self.assertEqual(rows[0][-2:], "z+")


ORE = 231
GROUND = 3


class PlannerCase(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 1000
        self.api.Player.Y = 1000
        self.api.Player.Z = 0
        self.saved = uo.clock.time
        uo.clock.time = Frozen(1000.0)

        for x in range(990, 1011):
            for y in range(990, 1011):
                self.api.land[(x, y)] = FakeLand(0, GROUND)

        self.logged = []
        self.memory = TileMemory(1500.0, 300.0, "vein", "mined", self.logged.append)
        self.spots = TileMemory(1500.0, 300.0, "spot", "stood on", self.logged.append)
        self.terrain = Terrain()
        self.veins = Veins(self.terrain, self.memory, {
            "tile_graphics": set([ORE]),
            "not_ore_graphics": set(),
            "static_names": ["cave"],
            "z_range": 20,
        }, self.logged.append)
        self.planner = self._planner(24, False, 4)

    def tearDown(self):
        uo.clock.time = self.saved

    def _planner(self, probes, show_map, radius, connected=False):
        return Planner(self.veins, self.terrain, self.memory, self.spots, {
            "reach": 1,
            "scan_radius": radius,
            "probes": probes,
            "min_ore": 1,
            "connected": connected,
            "map": show_map,
            "respawn_delay": 1500.0,
        }, self.logged.append)

    def _ore(self, *coords):
        for x, y in coords:
            self.api.land[(x, y)] = FakeLand(0, ORE)

    def _walkable(self, *coords):
        for x, y in coords:
            self.api.paths[(x, y)] = [1, 2]

    def _route(self, spot, *points):
        self.api.paths[spot] = [point(1000, 1000)] + [point(x, y) for x, y in points]

    def _ore_tile(self, x, y):
        return {"x": x, "y": y, "z": 0, "graphic": ORE, "is_land": True, "name": ""}

    def _xy(self, spot):
        return (spot["x"], spot["y"])


class PlannerTest(PlannerCase):
    def test_plans_once_and_hands_out_the_first_spot_with_its_distance(self):
        self._ore((1004, 1000))
        self._walkable((1003, 999))

        spot, cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (1003, 999))
        self.assertEqual(spot["distance"], 3)
        self.assertIsNone(cooling)
        self.assertEqual(self.api.path_probes, [(1003, 999)])
        self.assertEqual(self.planner.stats["spots"], 1)

    def test_standing_on_the_spot_costs_no_probe(self):
        self._ore((1001, 1000))

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (1000, 1000))
        self.assertEqual(spot["distance"], 0)
        self.assertEqual(self.api.path_probes, [])

    def test_keeps_the_spot_across_a_move_without_reading_or_probing_again(self):
        self._ore((1004, 1000))
        self._walkable((1003, 999))
        self.planner.scan()
        reads = self.terrain.reads
        self.api.Player.X = 1002
        self.api.Player.Y = 999

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (1003, 999))
        self.assertEqual(spot["distance"], 1)
        self.assertEqual(self.terrain.reads, reads)
        self.assertEqual(self.api.path_probes, [(1003, 999)])

    def test_hands_out_a_copy_rather_than_the_cached_tile(self):
        self._ore((1004, 1000))
        self._walkable((1003, 999))

        self.planner.scan()

        self.assertNotIn("distance", self.terrain.at(1003, 999)[0])

    def test_a_spot_with_no_route_is_parked_as_a_spot_and_the_next_one_comes_back(self):
        self._ore((1004, 1000))
        self._walkable((1003, 1000))

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (1003, 1000))
        self.assertEqual(self.spots.blocked_until({"x": 1003, "y": 999, "z": 0, "graphic": GROUND,
                                                   "is_land": True, "name": ""}), 1300.0)
        self.assertFalse(self.memory.is_blocked(self._ore_tile(1004, 1000)))
        self.assertEqual(self.planner.skipped_unreachable(), 1)
        self.assertEqual(self.planner.stats["walled"], 1)
        self.assertEqual(self.api.path_probes, [(1003, 999), (1003, 999), (1003, 1000)])

    def test_past_the_probe_budget_the_next_spot_goes_out_unprobed(self):
        self.planner = self._planner(1, False, 6)
        self._ore((1004, 1000), (1000, 1004))

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (999, 1003))
        self.assertEqual(self.api.path_probes, [(1003, 999), (1003, 999)])

    def test_a_refusal_on_bare_land_that_can_be_reached_beside_rules_out_the_art(self):
        self.planner = self._planner(24, False, 6)
        self._ore(*footprint(1004, 1000, 1))
        self.api.paths[(1004, 1000, 1)] = [1, 2]
        self._walkable((1002, 1000))

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (1002, 1000))
        self.assertEqual([line for line in self.logged if "cannot be stood on" in line],
                         ["land 0xe7 cannot be stood on, planning beside it from here on"])
        self.assertFalse(self.spots.is_blocked(self._ore_tile(1004, 1000)))
        self.assertEqual(self.api.path_probes, [(1004, 1000), (1004, 1000), (1002, 1000)])

    def test_a_refusal_over_a_static_parks_the_spot_and_learns_nothing(self):
        self._ore((1004, 1000))
        self.api.statics[(1003, 999)] = [static(1003, 999, 0, 0xD00, "bush")]
        self.api.paths[(1003, 999, 1)] = [1, 2]
        self._walkable((1003, 1000))

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (1003, 1000))
        self.assertEqual([line for line in self.logged if "cannot be stood on" in line], [])
        self.assertTrue(self.spots.is_blocked({"x": 1003, "y": 999, "z": 0, "graphic": GROUND,
                                               "is_land": True, "name": ""}))

    def test_exhausted_parks_the_three_by_three_around_the_player_and_drops_the_spot(self):
        self._ore((1001, 1000), (1001, 1001), (1002, 1000))
        self._walkable((1001, 1000))
        self.planner.scan()
        self.api.Player.X = 1001
        self.api.Player.Y = 1000
        self.api.Player.X = 1000

        parked = self.planner.exhausted()

        self.assertEqual(parked, 2)
        self.assertTrue(self.memory.is_blocked(self._ore_tile(1001, 1000)))
        self.assertTrue(self.memory.is_blocked(self._ore_tile(1001, 1001)))
        self.assertFalse(self.memory.is_blocked(self._ore_tile(1002, 1000)))
        self.assertIn("worked out at 1000,1000, parking 2 ore tile(s) in the 3x3 for 25m, 0 spot(s) left",
                      self.logged)

    def test_after_exhausted_the_rest_is_planned_from_the_cache(self):
        self._ore((1001, 1000), (1001, 1001), (1002, 1000))
        self._walkable((1001, 1000), (1001, 999))
        self.planner.scan()
        self.planner.exhausted()
        reads = self.terrain.reads

        spot, _cooling = self.planner.scan()

        self.assertIn((1002, 1000), footprint(spot["x"], spot["y"], 1))
        self.assertEqual(self.terrain.reads, reads)

    def test_a_queued_spot_whose_ore_was_parked_is_skipped_without_a_probe(self):
        self._ore((1001, 1000), (1000, 1005))
        self.planner = self._planner(24, False, 6)

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (1000, 1000))
        self.memory.mark_depleted(self._ore_tile(1000, 1005))
        self.planner.exhausted()

        found, cooling = self.planner.scan()

        self.assertIsNone(found)
        self.assertEqual(cooling, 2500.0)
        self.assertEqual(self.api.path_probes, [])

    def test_a_spot_roam_wrote_off_is_dropped_on_the_next_scan(self):
        self._ore((1004, 1000))
        self._walkable((1003, 999), (1003, 1000))
        spot, _cooling = self.planner.scan()
        self.spots.mark_unreachable(spot)

        found, _cooling = self.planner.scan()

        self.assertEqual(self._xy(found), (1003, 1000))

    def test_everything_parked_is_a_cooling_time(self):
        self._ore((1004, 1000))
        self.memory.mark_depleted(self._ore_tile(1004, 1000))

        found, cooling = self.planner.scan()

        self.assertIsNone(found)
        self.assertEqual(cooling, 2500.0)
        self.assertEqual(self.api.path_probes, [])

    def test_a_plan_emptied_by_walled_spots_is_the_soonest_spot_cooling(self):
        self.planner = self._planner(24, False, 6)
        self._ore((1004, 1000))

        found, cooling = self.planner.scan()

        self.assertIsNone(found)
        self.assertEqual(cooling, 1300.0)
        self.assertEqual(self.planner.skipped_unreachable(), 9)

    def test_ore_on_the_box_edge_is_only_covered_from_inside_it(self):
        self._ore((1004, 1000))

        self.planner.scan()

        self.assertEqual(self.planner.skipped_unreachable(), 3)

    def test_an_empty_box_is_a_dead_end_read_once(self):
        self.planner = self._planner(24, True, 12)

        for x in range(976, 1025):
            for y in range(976, 1025):
                self.api.land[(x, y)] = FakeLand(0, GROUND)

        found, cooling = self.planner.scan()

        self.assertIsNone(found)
        self.assertIsNone(cooling)
        self.assertEqual(self.terrain.reads, 625 + 1)
        self.assertEqual(self.planner.stats["reads"], 625 + 1)
        self.assertEqual([line for line in self.logged if line.startswith("map:")], [])

    def test_a_cave_floor_spot_is_the_static(self):
        self.api.statics[(1000, 1000)] = [static(1000, 1000, 5, 1339, "cave floor")]

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (1000, 1000))
        self.assertEqual(spot["z"], 5)
        self.assertEqual(spot["graphic"], 1339)
        self.assertFalse(spot["is_land"])

    def test_the_map_is_logged_once_per_plan(self):
        self.planner = self._planner(24, True, 2)
        self._ore((1001, 1000))

        self.planner.scan()
        rows = [line for line in self.logged if len(line) == 5 and set(line) <= set(".#@1")]

        self.assertEqual(rows, [".....", ".....", "..@#.", ".....", "....."])

        self.planner.scan()

        self.assertEqual(len([line for line in self.logged if line.startswith("map:")]), 1)

    def test_the_map_can_be_turned_off(self):
        self._ore((1001, 1000))

        self.planner.scan()

        self.assertEqual([line for line in self.logged if line.startswith("map:")], [])

    def test_lone_ore_art_is_the_one_art_in_reach(self):
        self._ore((1001, 1000))
        self.api.statics[(999, 1000)] = [static(999, 1000, 0, 1339, "cave floor")]

        self.assertIsNone(self.planner.lone_ore_art())

        self.api.statics[(999, 1000)] = []
        self.terrain = Terrain()
        self.veins._terrain = self.terrain
        self.planner = self._planner(24, False, 4)

        self.assertEqual(self.planner.lone_ore_art()["graphic"], ORE)

    def test_the_stop_button_ends_the_scan_as_a_dead_end(self):
        self._ore((1004, 1000))
        self._walkable((1003, 999))
        self.api.StopRequested = True

        found, cooling = self.planner.scan()

        self.assertIsNone(found)
        self.assertIsNone(cooling)
        self.assertEqual(self.api.path_probes, [])


class ConnectedGroundTest(PlannerCase):
    def setUp(self):
        PlannerCase.setUp(self)
        self.planner = self._planner(1, False, 4, connected=True)

    def test_a_route_that_stays_in_the_box_is_on_your_ground(self):
        self._ore((1004, 1000))
        self._route((1003, 999), (1001, 1000), (1002, 999), (1003, 999))

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (1003, 999))
        self.assertNotIn("off_ground", self.planner.stats)

    def test_a_route_that_leaves_the_box_parks_the_spot_and_the_next_comes_back(self):
        self._ore((1004, 1000))
        self._route((1003, 999), (1000, 995), (1003, 995), (1003, 999))
        self._route((1003, 1000), (1001, 1000), (1002, 1000))

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (1003, 1000))
        self.assertEqual(self.planner.stats["off_ground"], 1)
        self.assertEqual(self.planner.skipped_unreachable(), 1)
        self.assertTrue(self.spots.is_blocked({"x": 1003, "y": 999, "z": 0, "graphic": GROUND,
                                               "is_land": True, "name": ""}))
        self.assertIn("the spot at 1003,999 is off your ground, the route to it leaves the box",
                      self.logged)

    def test_every_spot_is_probed_past_the_budget(self):
        self._ore((1004, 1000), (1000, 1004))
        self._route((1003, 999), (1000, 995), (1003, 999))
        self._route((999, 1003), (999, 1001), (999, 1003))

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (999, 1003))
        self.assertEqual(self.api.path_probes, [(1003, 999), (999, 1003)])

    def test_no_route_at_all_is_still_walled(self):
        self._ore((1004, 1000))
        self._route((1003, 1000), (1002, 1000))

        spot, _cooling = self.planner.scan()

        self.assertEqual(self._xy(spot), (1003, 1000))
        self.assertEqual(self.planner.stats["walled"], 1)
        self.assertNotIn("off_ground", self.planner.stats)
