import unittest

from carpentry.config import BANDS, DEED_GRAPHICS, OUTCOME_TEXT, PRODUCTS, RECIPES, WOOD_COST
from uo.stages import band_for


class BandsTest(unittest.TestCase):
    def test_the_rows_hand_over_on_the_exclusive_edge(self):
        self.assertEqual(band_for(BANDS, 0.0), "barrel staves")
        self.assertEqual(band_for(BANDS, 10.9), "barrel staves")
        self.assertEqual(band_for(BANDS, 11.0), "barrel lid")
        self.assertEqual(band_for(BANDS, 42.1), "dark wooden sign hanger")
        self.assertEqual(band_for(BANDS, 70.0), "bokuto")
        self.assertEqual(band_for(BANDS, 94.9), "quarter staff")
        self.assertEqual(band_for(BANDS, 95.0), "gnarled staff")
        self.assertEqual(band_for(BANDS, 119.6), "rustic bench (south)")
        self.assertEqual(band_for(BANDS, 119.7), "small display case (south)")
        self.assertEqual(band_for(BANDS, 120.0), "small display case (south)")

    def test_every_band_has_a_product_and_a_cost(self):
        for _ceiling, product in BANDS:
            self.assertIn(product, PRODUCTS)
            self.assertIn(product, WOOD_COST)

    def test_every_band_has_a_recipe(self):
        for _ceiling, product in BANDS:
            self.assertIn(product, RECIPES)

    def test_the_ceilings_climb(self):
        ceilings = [ceiling for ceiling, _product in BANDS if ceiling is not None]

        self.assertEqual(ceilings, sorted(ceilings))
        self.assertIsNone(BANDS[-1][0])

    def test_the_deeds_share_one_art(self):
        for product in ("dartboard (south)", "ballot box", "rustic bench (south)"):
            self.assertEqual(PRODUCTS[product], DEED_GRAPHICS)

    def test_the_sign_hanger_is_not_a_deed(self):
        self.assertEqual(PRODUCTS["dark wooden sign hanger"], set([0x0B97]))


class OutcomeOrderTest(unittest.TestCase):
    def test_failed_is_read_before_made_and_throttled_last(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertLess(names.index("failed"), names.index("made"))
        self.assertEqual(names[-1], "throttled")
