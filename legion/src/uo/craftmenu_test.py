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

    def test_named_row_is_text_only(self):
        self._gump("Weapons", "bow", "crossbow")

        self.assertEqual(self.menu.named_row("crossbow", 88), 22)
        self.assertIsNone(self.menu.named_row("yumi", 88))

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
        self.api.gump = 88
        self.api.gump_contents[88] = "BOWCRAFT AND FLETCHING"
        self.menu.open()

        # Every page shares the menu's id; a category press redraws it with that category's rows
        def reply(button, gump=None):
            self.api.replies.append((button, gump))
            self.api.gump_contents[88] = self.pages.get(button, "")

            return True

        self.api.ReplyGump = reply

    def test_walks_the_categories_until_one_lists_the_product(self):
        self.pages[41] = "Weapons\ncrossbow"
        gump, button = self.menu.find_category("crossbow", 88)

        self.assertEqual(button, 41)
        self.assertEqual(gump, 88)
        self.assertEqual([pressed for pressed, _gump in self.api.replies], [1, 21, 41])

    def test_remembers_the_category_it_found(self):
        self.pages[41] = "Weapons\ncrossbow"
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

    def test_only_the_category_buttons_the_gump_has_are_pressed(self):
        self.api.gump_buttons[88] = set([1, 21, 41, 2, 22])
        gump, button = self.menu.find_category("crossbow", 88)

        self.assertIsNone(button)
        self.assertEqual([pressed for pressed, _gump in self.api.replies], [1, 21, 41])


class OpenTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.menu = CraftMenu(FakeTool(), CONFIG, self.said.append)
        self.api.gump_contents[0x13e7a7f3] = "[15:09] Someone: it takes a space"
        self.api.gump_contents[88] = "BOWCRAFT AND FLETCHING\nMaterials\nAmmunition\nWeapons"

    def test_a_menu_that_is_up_but_not_last_is_found(self):
        self.api.gump = 0x13e7a7f3
        self.api.open_gumps = set([88])

        self.assertEqual(self.menu.open(), 88)
        self.assertEqual(self.api.used, [])
        self.assertEqual(self.api.closed_gumps, 0)

    def test_the_tools_are_used_when_no_menu_is_up_and_the_last_gump_is_ignored(self):
        self.api.gump = 0x13e7a7f3
        self.api.opens[7] = 88

        self.assertEqual(self.menu.open(), 88)
        self.assertEqual(self.api.used, [7])
        self.assertEqual(self.api.closed_gumps, 0)
        self.assertEqual(len([line for line in self.said if "ignoring gump 0x13e7a7f3" in line]),
                         1)

    def test_the_ignored_gump_is_reported_once(self):
        self.api.gump = 0x13e7a7f3
        self.api.opens[7] = 88

        self.menu.open()
        self.api.gump = 0x13e7a7f3
        self.api.open_gumps = set([88])
        self.menu.open()

        self.assertEqual(len([line for line in self.said if "ignoring gump" in line]), 1)

    def test_a_menu_already_adopted_is_answered_without_reading_it(self):
        self.api.gump = 88
        self.menu.open()
        self.api.gump_contents[88] = ""
        self.api.gump = 0x13e7a7f3
        self.api.open_gumps = set([88])

        self.assertEqual(self.menu.open(), 88)
        self.assertEqual(self.api.used, [])

    def test_an_unrecognised_newcomer_is_used_and_said_once(self):
        self.api.gump = 0x13e7a7f3
        self.api.opens[7] = 89

        self.assertEqual(self.menu.open(), 89)
        self.menu._id = 0
        self.api.gump = 0x13e7a7f3
        self.menu.open()

        self.assertEqual(len([line for line in self.said if "does not name" in line]), 1)

    def test_a_foreign_gump_re_sent_during_the_wait_is_not_taken_for_the_menu(self):
        self.api.gump = 0x13e7a7f3
        self.menu.open()
        self.api.gump = 0
        self.api.opens[7] = 0x13e7a7f3

        self.assertIsNone(self.menu.open())

    def test_nothing_new_is_no_menu(self):
        self.api.gump = 0x13e7a7f3

        self.assertIsNone(self.menu.open())
        self.assertEqual(self.api.used, [7])

    def test_recognised_by_its_group_rows_alone(self):
        self.api.gump = 88
        self.api.gump_contents[88] = "Materials\nAmmunition\nWeapons\nbow"

        self.assertEqual(self.menu.open(), 88)


class PressTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.menu = CraftMenu(FakeTool(), CONFIG, self.said.append)
        self.api.gump = 88
        self.api.gump_contents[88] = "BOWCRAFT AND FLETCHING"
        self.menu.open()

    def test_presses_the_menu_and_waits_for_it_to_come_back(self):
        self.assertEqual(self.menu.press(41, 88, 1.0), 88)
        self.assertEqual(self.api.replies, [(41, 88)])

    def test_a_menu_that_does_not_come_back_is_nothing(self):
        def reply(button, gump=None):
            self.api.replies.append((button, gump))
            self.api.gump = 0

            return True

        self.api.ReplyGump = reply

        self.assertEqual(self.menu.press(41, 88, 1.0), 0)

    def test_a_gump_that_is_not_the_menu_is_never_pressed(self):
        self.assertEqual(self.menu.press(41, 0x13e7a7f3, 1.0), 0)
        self.assertEqual(self.menu.press(47, 0, 1.0), 0)
        self.assertEqual(self.api.replies, [])
        self.assertEqual(len([line for line in self.said if "not the craft menu" in line]), 1)

    def test_a_button_the_menu_lacks_is_never_pressed(self):
        self.api.gump_buttons[88] = set([1, 21, 41, 2])

        self.assertEqual(self.menu.press(47, 88, 1.0), 0)
        self.assertEqual(self.menu.press(47, 88, 1.0), 0)
        self.assertEqual(self.api.replies, [])
        self.assertEqual(len([line for line in self.said if "no button 47" in line]), 1)
        self.assertTrue(self.menu.has_button(41, 88))
        self.assertFalse(self.menu.has_button(61, 88))

    def test_unreadable_buttons_do_not_block_a_press(self):
        self.assertTrue(self.menu.has_button(47, 88))
        self.assertEqual(self.menu.press(47, 88, 1.0), 88)

    def test_candidate_rows_the_gump_lacks_are_dropped(self):
        self.api.gump_contents[88] = "Weapons\nbow\ncrossbow"
        self.api.gump_buttons[88] = set([41, 2, 22, 42])

        self.assertEqual(self.menu.candidate_buttons("crossbow", 88), [22, 2, 42])

    def test_a_page_press_answers_with_the_gump_that_appeared(self):
        def reply(button, gump=None):
            self.api.replies.append((button, gump))
            self.api.gump = 200

            return True

        self.api.ReplyGump = reply

        self.assertEqual(self.menu.press_page(3, 88, 1.0), 200)
        self.assertTrue(self.menu.reply_page(2, 200))
        self.assertFalse(self.menu.reply_page(2, 88))
        self.assertEqual(self.api.replies, [(3, 88), (2, 200)])

    def test_a_page_press_the_menu_answers_itself(self):
        self.assertEqual(self.menu.press_page(3, 88, 1.0), 88)
