import unittest

from test_support.uo import FakeLand, install, static
from uo.terrain import Terrain


class TerrainTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 100
        self.api.Player.Y = 100
        self.calls = []

        for x in range(98, 103):
            for y in range(98, 103):
                self.api.land[(x, y)] = FakeLand(5, 231)

        self.api.statics[(101, 100)] = [static(101, 100, 7, 1339, "cave floor")]

        for name in ["GetTile", "GetStaticsAt", "GetStaticsInArea"]:
            self._count(name)

    def _count(self, name):
        real = getattr(self.api, name)

        def counted(*args):
            self.calls.append(name)

            return real(*args)

        setattr(self.api, name, counted)

    def test_a_box_reads_its_statics_in_one_call(self):
        tiles = list(Terrain().box(2))

        self.assertEqual(len(tiles), 26)
        self.assertEqual(self.calls.count("GetStaticsInArea"), 1)
        self.assertEqual(self.calls.count("GetStaticsAt"), 0)
        self.assertEqual(self.calls.count("GetTile"), 25)

    def test_a_box_answers_the_same_tiles_as_the_single_reads(self):
        boxed = list(Terrain().box(2))
        singles = []
        terrain = Terrain()

        for x in range(98, 103):
            for y in range(98, 103):
                singles.extend(terrain.at(x, y))

        self.assertEqual(boxed, singles)

    def test_a_second_box_over_read_ground_makes_no_calls(self):
        terrain = Terrain()
        list(terrain.box(2))
        del self.calls[:]

        list(terrain.box(2))

        self.assertEqual(self.calls, [])

    def test_a_statics_box_reads_no_land(self):
        tiles = list(Terrain().statics_box(2))

        self.assertEqual(len(tiles), 1)
        self.assertEqual(self.calls, ["GetStaticsInArea"])

    def test_a_wider_box_reads_only_the_new_ground(self):
        terrain = Terrain()
        list(terrain.box(1))
        del self.calls[:]

        list(terrain.box(2))

        self.assertEqual(self.calls.count("GetStaticsInArea"), 1)
        self.assertEqual(self.calls.count("GetTile"), 16)
