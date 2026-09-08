import unittest

from fishing.pole import find_pole
from test_support.uo import install, item

GRAPHICS = set([0x0DBF])
WORDS = ["fishing", "pole"]
LAYERS = ["twohanded", "onehanded"]


class FindPoleTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []

    def find(self):
        return find_pole(set(GRAPHICS), WORDS, LAYERS, self.said.append)

    def test_nothing_anywhere_is_none(self):
        self.assertIsNone(self.find())

    def test_a_pole_in_hand_beats_one_in_the_pack(self):
        self.api.layers["twohanded"] = item(serial=0x1, graphic=0x0DBF)
        self.api.hold(item(serial=0x2, graphic=0x0DBF))

        self.assertEqual(self.find(), 0x1)

    def test_something_else_in_hand_does_not_count(self):
        self.api.layers["twohanded"] = item(serial=0x1, graphic=0x13B2, name="a bow")
        self.api.hold(item(serial=0x2, graphic=0x0DBF))

        self.assertEqual(self.find(), 0x2)

    def test_a_held_pole_is_known_by_name_as_well(self):
        self.api.layers["onehanded"] = item(serial=0x1, graphic=0x9999, name="a fishing pole")

        self.assertEqual(self.find(), 0x1)

    def test_a_pole_in_the_pack_is_known_by_name_as_well(self):
        self.api.hold(item(serial=0x3, graphic=0x9999, name="a Fishing Pole"))

        self.assertEqual(self.find(), 0x3)
        self.assertEqual(len(self.said), 1)
