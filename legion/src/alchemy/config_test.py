import unittest

from alchemy.config import (BANDS, BOTTLE, KIND_ORDER, NEEDS, OUTCOME_TEXT, POTIONS, PRODUCTS,
                            RECIPES, STOCK_KINDS)
from uo.stages import band_for


class BandsTest(unittest.TestCase):
    def test_the_rows_hand_over_on_the_exclusive_edge(self):
        self.assertEqual(band_for(BANDS, 0.0), "lesser poison")
        self.assertEqual(band_for(BANDS, 14.9), "lesser poison")
        self.assertEqual(band_for(BANDS, 15.0), "poison")
        self.assertEqual(band_for(BANDS, 34.9), "poison")
        self.assertEqual(band_for(BANDS, 35.0), "greater agility")
        self.assertEqual(band_for(BANDS, 74.9), "greater agility")
        self.assertEqual(band_for(BANDS, 75.0), "greater poison")
        self.assertEqual(band_for(BANDS, 89.9), "greater poison")
        self.assertEqual(band_for(BANDS, 90.0), "deadly poison")
        self.assertEqual(band_for(BANDS, 120.0), "deadly poison")

    def test_every_band_is_a_potion_with_an_art_a_recipe_and_its_needs(self):
        for _ceiling, product in BANDS:
            self.assertIn(product, POTIONS)
            self.assertIn(product, PRODUCTS)
            self.assertIn(product, NEEDS)
            self.assertIn(product, RECIPES)

    def test_the_ceilings_climb(self):
        ceilings = [ceiling for ceiling, _product in BANDS[:-1]]

        self.assertEqual(ceilings, sorted(ceilings))
        self.assertIsNone(BANDS[-1][0])


class PotionsTest(unittest.TestCase):
    def test_every_recipe_wants_one_bottle_and_one_kind_of_reagent(self):
        for name in POTIONS:
            _art, reagent, count = POTIONS[name]

            self.assertEqual(NEEDS[name], {BOTTLE: 1, reagent: count})
            self.assertIn(reagent, KIND_ORDER)

        self.assertEqual(KIND_ORDER, [kind for kind, _graphics, _words in STOCK_KINDS])

    def test_every_poison_lands_as_the_one_art(self):
        for name in ("lesser poison", "poison", "greater poison", "deadly poison"):
            self.assertEqual(PRODUCTS[name], set([0x0F0A]))


class OutcomeOrderTest(unittest.TestCase):
    def test_failed_is_read_before_made_and_throttled_last(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertLess(names.index("failed"), names.index("made"))
        self.assertEqual(names[-1], "throttled")
