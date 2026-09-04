import unittest

from test_support.uo import install
from uo.retry import settled


class SettledTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_is_false_when_nothing_lands(self):
        self.assertFalse(settled(1.0, 0.25, lambda: False))

    def test_waits_before_the_first_look(self):
        looks = []

        settled(1.0, 0.5, lambda: looks.append(self.api.paused) or True)

        self.assertEqual(looks, [0.5])

    def test_stops_as_soon_as_it_lands(self):
        calls = [0]

        def landed():
            calls[0] += 1

            return calls[0] == 2

        self.assertTrue(settled(10.0, 0.5, landed))
        self.assertAlmostEqual(self.api.paused, 1.0)

    def test_spends_the_whole_timeout_otherwise(self):
        settled(1.0, 0.25, lambda: False)

        self.assertAlmostEqual(self.api.paused, 1.0)
