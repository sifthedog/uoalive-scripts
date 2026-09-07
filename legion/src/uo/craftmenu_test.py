import unittest

from uo.craftmenu import CraftMenu
from test_support.uo import install

CONFIG = {
    "stride": 20,
    "category_type": 0,
    "item_type": 1,
    "category_names": ["materials", "ammunition", "weapons"],
    "last_ten_label": "LAST TEN",
    "title": "BOWCRAFT AND FLETCHING",
    "title_text": ["BOWCRAFT AND FLETCHING", "BOWCRAFT", "FLETCHING"],
    "title_fragments": ["bowcraft and fletching", "bowcraft", "fletching"],
    "tool_noun": "tools",
    "gump_timeout": 5.0,
    "gump_poll": 0.15,
    "max_categories": 6,
    "max_item_rows": 12,
}


class FakeTool(object):
    def __init__(self, serial=7):
        self._serial = serial

    def serial(self):
        return self._serial


class ButtonIdTest(unittest.TestCase):
    def setUp(self):
        install()
        self.menu = CraftMenu(FakeTool(), CONFIG, [].append)

    def test_categories_are_type_zero(self):
        self.assertEqual([self.menu.button_id(0, n) for n in range(3)], [1, 21, 41])

    def test_item_rows_are_type_one(self):
        self.assertEqual([self.menu.button_id(1, n) for n in range(3)], [2, 22, 42])


class ItemRowsTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.menu = CraftMenu(FakeTool(), CONFIG, self.said.append)

    def _gump(self, *lines):
        self.api.gump = 88
        self.api.GetGumpContents = lambda ident: "\n".join(lines)

    def test_everything_past_the_last_group_name_is_a_row(self):
        self._gump("BOWCRAFT AND FLETCHING", "Materials", "Ammunition", "Weapons",
                   "bow", "crossbow")

        self.assertEqual(self.menu.item_rows(88), ["bow", "crossbow"])

    def test_a_gump_with_no_group_names_has_no_rows(self):
        self._gump("BOWCRAFT AND FLETCHING", "bow")

        self.assertEqual(self.menu.item_rows(88), [])

    def test_a_whole_row_matches_and_a_substring_does_not(self):
        self._gump("Weapons", "crossbow bolt")

        self.assertFalse(self.menu.page_has("crossbow", 88))

        self._gump("Weapons", "crossbow")

        self.assertTrue(self.menu.page_has("crossbow", 88))

    def test_the_named_row_is_tried_first(self):
        self._gump("Weapons", "bow", "crossbow")
        order = self.menu.candidate_buttons("crossbow", 88)

        self.assertEqual(order[0], 22)

    def test_every_row_is_still_walked_after_the_named_one(self):
        self._gump("Weapons", "bow", "crossbow")

        self.assertEqual(len(self.menu.candidate_buttons("crossbow", 88)), 12)

    def test_says_once_when_the_text_names_no_row(self):
        self._gump("Weapons")
        self.menu.candidate_buttons("crossbow", 88)
        self.menu.candidate_buttons("crossbow", 88)

        self.assertEqual(len([line for line in self.said if "walking the rows" in line]), 1)


class IsCraftGumpTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.menu = CraftMenu(FakeTool(), CONFIG, [].append)

    def test_nothing_is_not_a_craft_gump(self):
        self.assertFalse(self.menu.is_craft_gump(0))

    def test_recognises_it_by_its_text(self):
        self.api.GetGumpContents = lambda ident: "BOWCRAFT AND FLETCHING"

        self.assertTrue(self.menu.is_craft_gump(88))

    def test_falls_back_to_the_clients_own_search(self):
        self.api.GetGumpContents = lambda ident: ""
        self.api.gump_text = ["BOWCRAFT"]

        self.assertTrue(self.menu.is_craft_gump(88))


class FindCategoryTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.menu = CraftMenu(FakeTool(), CONFIG, self.said.append)
        self.pages = {}
        self.api.GetGumpContents = lambda ident: self.pages.get(ident, "")

        # Every category answers with a page; which of them lists the product is what is under test
        def reply(button, gump=None):
            self.api.gump = 100 + button

            return True

        self.api.ReplyGump = reply

    def test_walks_the_categories_until_one_lists_the_product(self):
        self.pages[141] = "Weapons\ncrossbow"
        gump, button = self.menu.find_category("crossbow", 88)

        self.assertEqual(button, 41)
        self.assertEqual(gump, 141)

    def test_remembers_the_category_it_found(self):
        self.pages[141] = "Weapons\ncrossbow"
        self.menu.find_category("crossbow", 88)
        self.said[:] = []
        self.menu.find_category("crossbow", 88)

        self.assertEqual(self.said, [])

    def test_no_category_lists_it_and_it_says_so_once(self):
        gump, button = self.menu.find_category("crossbow", 88)

        self.assertIsNone(button)
        self.assertEqual(len([line for line in self.said if "no category lists" in line]), 1)

    def test_a_press_that_answers_nothing_is_not_a_verdict(self):
        self.api.ReplyGump = lambda button, gump=None: False
        gump, button = self.menu.find_category("crossbow", 88)

        self.assertEqual((gump, button), (0, 0))
