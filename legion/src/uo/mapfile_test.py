import unittest

from test_support.uo import FakeLand, install, static
from uo.mapfile import MapFile
from uo.terrain import Terrain


class FakeStore(object):
    def __init__(self, rows=None, on=True):
        self.rows = list(rows or [])
        self.appended = []
        self._on = on

    def on(self):
        return self._on

    def path(self):
        return "map.jsonl"

    def load(self):
        return list(self.rows)

    def append(self, rows):
        self.appended.extend(rows)


class MapFileTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 100
        self.api.Player.Y = 100
        self.api.map = 1
        self.said = []
        self.terrain = Terrain()

        for x in range(98, 103):
            for y in range(98, 103):
                self.api.land[(x, y)] = FakeLand(5, 231)

        self.api.statics[(101, 100)] = [static(101, 100, 7, 1339, "cave floor")]

    def test_a_flush_writes_the_ground_read_since_the_last_one(self):
        store = FakeStore()
        map_file = MapFile(self.terrain, store, self.said.append)
        list(self.terrain.box(1))

        self.assertEqual(map_file.flush(), 9)
        self.assertEqual(map_file.flush(), 0)
        self.assertIn({"m": 1, "x": 101, "y": 100, "l": [5, 231], "s": [[7, 1339, "cave floor"]]},
                      store.appended)
        self.assertIn({"m": 1, "x": 99, "y": 99, "l": [5, 231], "s": []}, store.appended)

    def test_ground_with_only_its_statics_read_waits_for_the_land(self):
        store = FakeStore()
        map_file = MapFile(self.terrain, store, self.said.append)
        list(self.terrain.statics_box(1))

        self.assertEqual(map_file.flush(), 0)

    def test_remembered_ground_costs_no_reads_and_is_not_written_again(self):
        store = FakeStore([
            {"m": 1, "x": 101, "y": 100, "l": [5, 231], "s": [[7, 1339, "cave floor"]]},
            {"m": 1, "x": 100, "y": 100, "l": None, "s": []},
            {"m": 0, "x": 99, "y": 100, "l": [5, 231], "s": []},
        ])
        map_file = MapFile(self.terrain, store, self.said.append)

        self.assertEqual(map_file.load(), 2)
        self.assertEqual(self.said, ["map: 2 coordinate(s) remembered from map.jsonl"])

        tiles = self.terrain.at(101, 100)

        self.assertEqual(self.terrain.reads, 0)
        self.assertEqual([tile["graphic"] for tile in tiles], [231, 1339])
        self.assertEqual(tiles[1]["name"], "cave floor")
        self.assertEqual(self.terrain.at(100, 100), [])
        self.assertEqual(map_file.flush(), 0)

        self.terrain.at(99, 100)

        self.assertEqual(self.terrain.reads, 2)

    def test_a_malformed_row_is_skipped(self):
        store = FakeStore([{"m": 1, "x": 101}, {"m": 1, "x": 100, "y": 100, "l": [5], "s": []}])
        map_file = MapFile(self.terrain, store, self.said.append)

        self.assertEqual(map_file.load(), 0)

    def test_off_reads_and_writes_nothing(self):
        store = FakeStore([{"m": 1, "x": 101, "y": 100, "l": [5, 231], "s": []}], False)
        map_file = MapFile(self.terrain, store, self.said.append)
        list(self.terrain.box(1))

        self.assertEqual(map_file.load(), 0)
        self.assertEqual(map_file.flush(), 0)
        self.assertEqual(store.appended, [])
        self.assertEqual(self.said, [])
