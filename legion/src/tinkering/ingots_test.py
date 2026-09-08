import unittest

from tinkering.ingots import cost_of, short_by

COSTS = {"iron key": 3, "fancy wind chimes": 15}


class CostTest(unittest.TestCase):
    def test_reads_the_table(self):
        self.assertEqual(cost_of("fancy wind chimes", COSTS, 1), 15)

    def test_a_product_the_table_lacks_costs_the_fallback(self):
        self.assertEqual(cost_of("scissors", COSTS, 1), 1)


class ShortByTest(unittest.TestCase):
    def test_is_what_the_pack_is_missing(self):
        self.assertEqual(short_by("iron key", 1, COSTS, 1), 2)

    def test_is_zero_with_enough(self):
        self.assertEqual(short_by("iron key", 3, COSTS, 1), 0)
        self.assertEqual(short_by("iron key", 300, COSTS, 1), 0)

    def test_an_unknown_product_wants_the_fallback(self):
        self.assertEqual(short_by("scissors", 0, COSTS, 1), 1)
