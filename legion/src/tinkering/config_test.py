import unittest

from tinkering.config import (BANDS, INGOT_COST, OUTCOME_TEXT, OUTPUT_CHOICE, OUTPUT_OPTIONS,
                              PRODUCTS, VENDORS)
from uo.stages import band_for


class BandsTest(unittest.TestCase):
    def test_the_rows_hand_over_on_the_exclusive_edge(self):
        self.assertEqual(band_for(BANDS, 20.0), "iron key")
        self.assertEqual(band_for(BANDS, 29.9), "iron key")
        self.assertEqual(band_for(BANDS, 30.0), "hammer")
        self.assertEqual(band_for(BANDS, 44.9), "tongs")
        self.assertEqual(band_for(BANDS, 45.0), "lockpick")
        self.assertEqual(band_for(BANDS, 111.7), "ring")
        self.assertEqual(band_for(BANDS, 111.8), "fancy wind chimes")
        self.assertEqual(band_for(BANDS, 120.0), "fancy wind chimes")

    def test_every_band_has_a_product_a_cost_and_a_buyer_or_none(self):
        for _ceiling, product in BANDS:
            self.assertIn(product, PRODUCTS)
            self.assertIn(product, INGOT_COST)
            self.assertIn(product, VENDORS)

        self.assertIsNone(VENDORS["fancy wind chimes"])


class OutcomeOrderTest(unittest.TestCase):
    def test_failed_is_read_before_made_and_throttled_last(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertLess(names.index("failed"), names.index("made"))
        self.assertEqual(names[-1], "throttled")


class OutputChoiceTest(unittest.TestCase):
    def test_every_button_answers_with_a_key_the_loop_branches_on(self):
        self.assertEqual([key for key, _caption in OUTPUT_OPTIONS], ["sell", "unload", "keep"])
        self.assertEqual(sorted(OUTPUT_CHOICE), ["hue", "poll", "text", "timeout"])
