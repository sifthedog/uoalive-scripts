import unittest

from test_support.uo import install
from uo.vitals import mana_reading, position_and_mana, position_and_weight, weight_reading


class VitalsTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player.X = 1420
        self.api.Player.Y = 990

    def test_reads_weight(self):
        self.api.Player.Weight = 380
        self.api.Player.WeightMax = 400

        self.assertEqual(weight_reading(), "380/400")

    def test_reads_mana(self):
        self.api.Player.Mana = 12
        self.api.Player.ManaMax = 50

        self.assertEqual(mana_reading(), "12/50 mana")

    def test_an_unknown_player_reads_as_question_marks(self):
        self.api.Player = None

        self.assertEqual(weight_reading(), "?/?")
        self.assertEqual(position_and_weight(), "somewhere, ?/?")

    def test_joins_the_position_to_the_reading(self):
        self.api.Player.Weight = 100
        self.api.Player.WeightMax = 400

        self.assertEqual(position_and_weight(), "at 1420,990, 100/400")

    def test_joins_the_position_to_mana(self):
        self.api.Player.Mana = 12
        self.api.Player.ManaMax = 50

        self.assertEqual(position_and_mana(), "at 1420,990, 12/50 mana")
