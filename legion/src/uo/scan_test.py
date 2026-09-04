import unittest

import uo.clock
from test_support.uo import install, tile
from uo.scan import chebyshev_to, pick_nearest
from uo.tiles import TileMemory


class Frozen(object):
    def __init__(self, at):
        self.at = at

    def time(self):
        return self.at


class ChebyshevToTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 100
        self.api.Player.Y = 100

    def test_measures_the_longer_axis(self):
        self.assertEqual(chebyshev_to(tile(104, 101)), 4)


class PickNearestTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 100
        self.api.Player.Y = 100
        self.clock = Frozen(1000.0)
        self.saved = uo.clock.time
        uo.clock.time = self.clock
        self.memory = TileMemory(1500.0, 300.0, "vein", "mined", [].append)

    def tearDown(self):
        uo.clock.time = self.saved

    def _walkable(self, *coords):
        for x, y, steps in coords:
            self.api.paths[(x, y)] = list(range(steps))

    def test_finds_nothing_among_no_candidates(self):
        best, cooling, walled = pick_nearest([], self.memory, 24, 2)

        self.assertIsNone(best)
        self.assertIsNone(cooling)

    def test_prefers_the_shortest_route_not_the_nearest_crow_flight(self):
        near = tile(101, 100)
        far = tile(105, 100)
        self._walkable((101, 100, 9), (105, 100, 3))

        best, _cooling, _walled = pick_nearest([far, near], self.memory, 24, 2)

        self.assertEqual((best["x"], best["y"]), (105, 100))

    def test_counts_the_ones_with_no_route(self):
        self._walkable((105, 100, 3))

        best, _cooling, walled = pick_nearest([tile(101, 100), tile(105, 100)],
                                              self.memory, 24, 2)

        self.assertEqual(walled, 1)
        self.assertEqual((best["x"], best["y"]), (105, 100))

    def test_reports_the_distance_it_settled_on(self):
        self._walkable((105, 100, 3))

        best, _cooling, _walled = pick_nearest([tile(105, 100)], self.memory, 24, 2)

        self.assertEqual(best["distance"], 5)

    def test_leaves_out_a_blocked_tile_and_says_when_it_is_back(self):
        blocked = tile(101, 100)
        self.memory.mark_depleted(blocked)
        self._walkable((101, 100, 1))

        best, cooling, _walled = pick_nearest([blocked], self.memory, 24, 2)

        self.assertIsNone(best)
        self.assertEqual(cooling, 2500.0)

    def test_a_permanently_unusable_tile_never_becomes_a_cooling_time(self):
        blocked = tile(101, 100)
        self.memory.mark_unusable(blocked, "cannot be mined")

        _best, cooling, _walled = pick_nearest([blocked], self.memory, 24, 2)

        self.assertIsNone(cooling)

    def test_asks_for_a_route_only_as_far_as_the_probe_budget(self):
        candidates = [tile(100 + n, 100) for n in range(1, 10)]
        pick_nearest(candidates, self.memory, 3, 2)

        self.assertEqual(len(self.api.paths), 0)
