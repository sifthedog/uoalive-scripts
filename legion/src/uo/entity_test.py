import unittest

from test_support.uo import install
from uo.entity import chebyshev, hex_of, player


class HexOfTest(unittest.TestCase):
    def test_masks_to_32_bits(self):
        self.assertEqual(hex_of(0x40000123), "0x40000123")

    def test_survives_a_negative_serial(self):
        self.assertEqual(hex_of(-1), "0xffffffff")


class PlayerTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_reads_the_player(self):
        self.assertIs(player(), self.api.Player)

    def read_through(self, stopping):
        class Absent(object):
            StopRequested = stopping

            @property
            def Player(self):
                raise Exception("between world states")

        import uo.entity

        saved = uo.entity.API
        uo.entity.API = Absent()

        try:
            return player()
        finally:
            uo.entity.API = saved

    def test_reads_as_unknown_when_the_client_throws(self):
        self.assertIsNone(self.read_through(False))

    def test_a_throw_while_stopping_is_not_swallowed(self):
        self.assertRaises(Exception, self.read_through, True)


class ChebyshevTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_measures_the_longer_axis(self):
        self.api.Player.X = 1000
        self.api.Player.Y = 1000

        self.assertEqual(chebyshev(1003, 1001, 99), 3)

    def test_reads_as_unknown_with_no_player(self):
        self.api.Player = None

        self.assertEqual(chebyshev(1003, 1001, 99), 99)
