import unittest

from uo.components import affordable, short_of, shortfall_report

NEEDS = {"blank scrolls": 1, "mandrake root": 1, "sulfurous ash": 1}
ORDER = ["blank scrolls", "black pearl", "mandrake root", "sulfurous ash"]


class ShortOfTest(unittest.TestCase):
    def test_names_only_what_is_missing(self):
        self.assertEqual(short_of(NEEDS, {"blank scrolls": 5, "mandrake root": 0}),
                         {"mandrake root": 1, "sulfurous ash": 1})

    def test_a_pack_that_covers_the_craft_is_short_of_nothing(self):
        self.assertEqual(short_of(NEEDS, {"blank scrolls": 1, "mandrake root": 1,
                                          "sulfurous ash": 3}), {})


class AffordableTest(unittest.TestCase):
    def test_the_scarcest_kind_decides(self):
        self.assertEqual(affordable(NEEDS, {"blank scrolls": 40, "mandrake root": 7,
                                            "sulfurous ash": 100}), 7)

    def test_a_kind_the_pack_lacks_pays_for_nothing(self):
        self.assertEqual(affordable(NEEDS, {"blank scrolls": 40, "mandrake root": 7}), 0)

    def test_a_recipe_wanting_several_of_a_kind_divides(self):
        self.assertEqual(affordable({"blank scrolls": 3}, {"blank scrolls": 10}), 3)

    def test_a_recipe_needing_nothing_affords_nothing(self):
        self.assertEqual(affordable({}, {"blank scrolls": 10}), 0)


class ReportTest(unittest.TestCase):
    def test_reads_in_the_kind_order_given(self):
        self.assertEqual(shortfall_report({"sulfurous ash": 2, "blank scrolls": 1}, ORDER),
                         "1 blank scrolls, 2 sulfurous ash")

    def test_a_kind_outside_the_order_still_appears(self):
        self.assertEqual(shortfall_report({"nightshade": 1, "blank scrolls": 1}, ORDER),
                         "1 blank scrolls, 1 nightshade")
