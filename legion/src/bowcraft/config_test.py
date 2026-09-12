import unittest

from bowcraft.config import (BANDS, OUTCOME_TEXT, OUTPUT_OPTIONS, PRODUCTS, RECIPES, SETUP,
                             TOOL_MODES, VENDORS, WOOD_COST)
from uo.stages import band_for


class BandsTest(unittest.TestCase):
    def test_the_rows_hand_over_on_the_exclusive_edge(self):
        self.assertEqual(band_for(BANDS, 29.9), "bow")
        self.assertEqual(band_for(BANDS, 30.0), "bow")
        self.assertEqual(band_for(BANDS, 59.9), "bow")
        self.assertEqual(band_for(BANDS, 60.0), "crossbow")
        self.assertEqual(band_for(BANDS, 69.9), "crossbow")
        self.assertEqual(band_for(BANDS, 70.0), "composite bow")
        self.assertEqual(band_for(BANDS, 80.0), "heavy crossbow")
        self.assertEqual(band_for(BANDS, 90.0), "repeating crossbow")
        self.assertEqual(band_for(BANDS, 99.9), "repeating crossbow")
        self.assertEqual(band_for(BANDS, 100.0), "yumi")
        self.assertEqual(band_for(BANDS, 120.0), "yumi")

    def test_every_band_has_a_product_a_row_and_a_buyer_or_none(self):
        for _ceiling, product in BANDS:
            self.assertIn(product, PRODUCTS)
            self.assertIn(product, RECIPES)
            self.assertIn(product, VENDORS)
            self.assertIn(product, WOOD_COST)

        self.assertIsNone(VENDORS["yumi"])


class OutcomeOrderTest(unittest.TestCase):
    def test_failed_is_read_before_made_and_throttled_last(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertLess(names.index("failed"), names.index("made"))
        self.assertEqual(names[-1], "throttled")


class SetupTest(unittest.TestCase):
    def test_every_choice_answers_with_a_key_the_loop_branches_on(self):
        self.assertEqual([key for key, _caption in OUTPUT_OPTIONS], ["sell", "unload", "keep"])
        self.assertEqual([key for key, _caption in TOOL_MODES], ["stop", "fetch"])
        self.assertEqual(sorted(SETUP), ["hue", "outputs", "poll", "timeout", "title",
                                         "tool_modes", "tool_noun", "unsold_hint"])
