import unittest

import uo.clock
from test_support.uo import install, tile
from uo.parked import Parked
from uo.tiles import TileMemory


class Frozen(object):
    def __init__(self, at):
        self.at = at

    def time(self):
        return self.at


class FakeStore(object):
    def __init__(self, rows=None, on=True):
        self.rows = list(rows or [])
        self.appended = []
        self.rewritten = None
        self._on = on

    def on(self):
        return self._on

    def load(self):
        return list(self.rows)

    def append(self, rows):
        self.appended.extend(rows)

    def rewrite(self, rows):
        self.rewritten = list(rows)


class ParkedTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.map = 1
        self.saved = uo.clock.time
        uo.clock.time = Frozen(1000.0)
        self.said = []

    def tearDown(self):
        uo.clock.time = self.saved

    def _memory(self, parked):
        return TileMemory(1500.0, 300.0, "vein", "mined", self.said.append, parked.save)

    def test_a_timed_parking_is_saved_with_the_map(self):
        store = FakeStore()
        memory = self._memory(Parked(store, self.said.append))

        memory.mark_depleted(tile(1, 2, 3, 231))

        self.assertEqual(store.appended, [{"m": 1, "t": "1,2,3,land:231", "u": 2500.0}])

    def test_a_permanent_write_off_is_not_saved(self):
        store = FakeStore()
        memory = self._memory(Parked(store, self.said.append))

        memory.mark_unusable(tile(1, 2, 3, 231), "cannot be mined")

        self.assertEqual(store.appended, [])

    def test_loads_what_is_still_parked_on_this_map_and_prunes_the_rest(self):
        store = FakeStore([
            {"m": 1, "t": "1,2,3,land:231", "u": 2500.0},
            {"m": 1, "t": "4,5,6,land:231", "u": 900.0},
            {"m": 0, "t": "7,8,9,land:231", "u": 2500.0},
            {"m": 1, "t": "1,2,3,land:231", "u": 2600.0},
            {"t": "no until"},
        ])
        parked = Parked(store, self.said.append)
        memory = self._memory(parked)

        self.assertEqual(parked.load(memory), 1)
        self.assertEqual(memory.blocked_until(tile(1, 2, 3, 231)), 2600.0)
        self.assertIsNone(memory.blocked_until(tile(4, 5, 6, 231)))
        self.assertIsNone(memory.blocked_until(tile(7, 8, 9, 231)))
        self.assertEqual(sorted(row["t"] for row in store.rewritten),
                         ["1,2,3,land:231", "7,8,9,land:231"])
        self.assertEqual(store.appended, [])
        self.assertEqual(self.said, ["1 tile(s) still parked from the last run"])

    def test_off_loads_nothing_and_saves_nothing(self):
        store = FakeStore([{"m": 1, "t": "1,2,3,land:231", "u": 2500.0}], False)
        parked = Parked(store, self.said.append)
        memory = self._memory(parked)

        self.assertEqual(parked.load(memory), 0)
        self.assertIsNone(store.rewritten)
        self.assertEqual(self.said, [])
