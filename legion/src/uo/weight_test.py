import unittest

from test_support.uo import install
from uo.weight import over_buffer, too_heavy


class OverBufferTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_is_false_below_the_buffer(self):
        self.api.Player.Weight = 300
        self.api.Player.WeightMax = 400

        self.assertFalse(over_buffer(50))

    def test_is_true_inside_the_buffer(self):
        self.api.Player.Weight = 380
        self.api.Player.WeightMax = 400

        self.assertTrue(over_buffer(50))

    def test_a_weightmax_of_zero_is_not_overweight(self):
        self.api.Player.Weight = 436
        self.api.Player.WeightMax = 0

        self.assertFalse(over_buffer(50))

    def test_an_unknown_player_is_not_overweight(self):
        self.api.Player = None

        self.assertFalse(over_buffer(50))

    def test_too_heavy_is_the_ceiling_itself(self):
        self.api.Player.Weight = 401
        self.api.Player.WeightMax = 400

        self.assertTrue(too_heavy())
