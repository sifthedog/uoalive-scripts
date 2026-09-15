import unittest

from assembly.config import ASSEMBLIES, MENUS, PART_ORDER, START_PROMPT


class AssembliesTest(unittest.TestCase):
    def test_every_row_is_a_recipe_on_the_menu_it_names(self):
        for key, _caption, stages in ASSEMBLIES:
            for row, menu, _needs in stages:
                self.assertIn(menu, MENUS, "%s: no '%s' menu" % (key, menu))
                self.assertIn(row, MENUS[menu]["recipes"],
                              "%s: '%s' is not a %s row" % (key, row, menu))

    def test_every_part_spent_is_counted_in_the_pack(self):
        for key, _caption, stages in ASSEMBLIES:
            for row, _menu, needs in stages:
                for part in needs:
                    self.assertIn(part, PART_ORDER, "%s: '%s' for the %s is not a kind"
                                  % (key, part, row))

    def test_a_part_is_always_above_whatever_spends_it(self):
        for key, _caption, stages in ASSEMBLIES:
            made = []

            for row, _menu, needs in stages:
                for part in needs:
                    if part in [name for name, _menu, _needs in stages]:
                        self.assertIn(part, made, "%s: '%s' is made after the %s that spends it"
                                      % (key, part, row))

                made.append(row)

    def test_the_prompt_offers_every_assembly_and_defaults_to_one_of_them(self):
        keys = [key for key, _caption, _stages in ASSEMBLIES]

        self.assertEqual([key for key, _caption in START_PROMPT["options"]], keys)
        self.assertIn(START_PROMPT["assembly_default"], keys)
