import unittest

from inscription.config import (BANDS, KIND_ORDER, MANA, MANA_BY_CIRCLE, NEEDS, OUTCOME_TEXT,
                                PRODUCTS, RECIPES, SPELLS, STOCK_KINDS)
from uo.stages import band_for


class BandsTest(unittest.TestCase):
    def test_the_rows_hand_over_on_the_exclusive_edge(self):
        self.assertEqual(band_for(BANDS, 30.0), "lightning")
        self.assertEqual(band_for(BANDS, 54.9), "lightning")
        self.assertEqual(band_for(BANDS, 55.0), "magic reflection")
        self.assertEqual(band_for(BANDS, 64.9), "magic reflection")
        self.assertEqual(band_for(BANDS, 65.0), "reveal")
        self.assertEqual(band_for(BANDS, 84.9), "reveal")
        self.assertEqual(band_for(BANDS, 85.0), "flamestrike")
        self.assertEqual(band_for(BANDS, 93.9), "flamestrike")
        self.assertEqual(band_for(BANDS, 94.0), "resurrection")
        self.assertEqual(band_for(BANDS, 120.0), "resurrection")

    def test_every_band_is_a_spell_with_a_scroll_a_recipe_and_a_mana_cost(self):
        for _ceiling, product in BANDS:
            self.assertIn(product, SPELLS)
            self.assertIn(product, PRODUCTS)
            self.assertIn(product, NEEDS)
            self.assertIn(product, MANA)

    def test_every_spell_is_a_row_on_the_menu(self):
        for name in SPELLS:
            self.assertIn(name, RECIPES)

    def test_the_bands_climb_a_circle_at_a_time_from_the_fourth(self):
        circles = [SPELLS[product][0] for _ceiling, product in BANDS]

        self.assertEqual(circles, [4, 5, 6, 7, 8])
        self.assertEqual([MANA[product] for _ceiling, product in BANDS], [11, 14, 20, 40, 50])

    def test_the_ceilings_climb(self):
        ceilings = [ceiling for ceiling, _product in BANDS[:-1]]

        self.assertEqual(ceilings, sorted(ceilings))
        self.assertIsNone(BANDS[-1][0])


class SpellsTest(unittest.TestCase):
    def test_every_recipe_wants_a_blank_scroll_and_one_of_each_reagent(self):
        for name in SPELLS:
            self.assertEqual(NEEDS[name]["blank scrolls"], 1)
            self.assertEqual(sorted(NEEDS[name]), sorted(["blank scrolls"] + SPELLS[name][2]))

            for kind in SPELLS[name][2]:
                self.assertEqual(NEEDS[name][kind], 1)

    def test_every_reagent_named_is_a_stock_kind(self):
        kinds = [kind for kind, _graphics, _words in STOCK_KINDS]

        for name in SPELLS:
            for kind in SPELLS[name][2]:
                self.assertIn(kind, kinds)

        self.assertEqual(KIND_ORDER, kinds)

    def test_every_circle_has_eight_spells_with_their_own_art(self):
        for circle in MANA_BY_CIRCLE:
            spells = [name for name in SPELLS if SPELLS[name][0] == circle]
            arts = set(SPELLS[name][1] for name in spells)

            self.assertEqual(len(spells), 8)
            self.assertEqual(len(arts), 8)

    def test_the_art_is_the_stock_offset_from_the_spell_id(self):
        self.assertEqual(SPELLS["lightning"][1], 8010)
        self.assertEqual(SPELLS["recall"][1], 0x1F4C)
        self.assertEqual(SPELLS["energy bolt"][1], 0x1F56)
        self.assertEqual(SPELLS["gate travel"][1], 0x1F60)


class OutcomeOrderTest(unittest.TestCase):
    def test_failed_is_read_before_made_and_throttled_last(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertLess(names.index("failed"), names.index("made"))
        self.assertIn("noMana", names)
        self.assertEqual(names[-1], "throttled")
