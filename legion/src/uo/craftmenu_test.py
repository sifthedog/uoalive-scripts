import unittest

from uo.craftmenu import CraftMenu
from test_support.uo import FakeButton, FakeHtml, install

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


# UOAlive's menu: one line of text for every page, and each row drawn as its button, its name, then
# its details button, with the page turns between
class ControlRowsTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.menu = CraftMenu(FakeTool(), CONFIG, self.said.append)
        self.api.gump = 88
        self.api.gump_contents[88] = ("BOWCRAFT AND FLETCHING Materials Ammunition Weapons "
                                      "bow crossbow bolt NEXT PAGE PREV PAGE heavy crossbow crossbow")
        self.api.gump_controls[88] = [
            FakeButton(0), FakeButton(1), FakeHtml("Materials"), FakeButton(21),
            FakeHtml("Ammunition"), FakeButton(41), FakeHtml("Weapons"), FakeButton(47),
            FakeHtml("MAKE LAST"),
            FakeButton(2), FakeHtml("bow"), FakeButton(3),
            FakeButton(22), FakeHtml("crossbow bolt"), FakeButton(23),
            FakeButton(0), FakeHtml("NEXT PAGE"), FakeButton(0), FakeHtml("PREV PAGE"),
            FakeButton(202), FakeHtml("heavy crossbow"), FakeButton(203),
            FakeButton(222), FakeHtml("crossbow"), FakeButton(223),
        ]

    def test_rows_are_read_off_the_controls_across_the_pages(self):
        self.assertEqual(self.menu.rows_of(88), [("bow", 2), ("crossbow bolt", 22),
                                                 ("heavy crossbow", 202), ("crossbow", 222)])
        self.assertEqual(self.menu.item_rows(88),
                         ["bow", "crossbow bolt", "heavy crossbow", "crossbow"])

    def test_the_categories_pair_the_same_way(self):
        self.assertEqual(self.menu.categories_of(88),
                         [("Materials", 1), ("Ammunition", 21), ("Weapons", 41)])

    def test_unreadable_controls_leave_the_text_to_answer(self):
        del self.api.gump_controls[88]

        self.assertEqual(self.menu.rows_of(88), [])
        self.assertEqual(self.menu.item_rows(88), [])


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

    def test_a_button_the_menu_lacks_is_never_pressed_and_the_gump_is_let_go(self):
        self.api.gump_buttons[88] = set([1, 21, 41, 2])

        self.assertEqual(self.menu.press(47, 88, 1.0), 0)
        self.assertEqual(self.api.replies, [])
        self.assertEqual(len([line for line in self.said if "no button 47" in line]), 1)
        # Closed and forgotten, so the next open uses the tools rather than retrying the same gump
        self.assertEqual(self.api.closed_gumps, 1)
        self.assertEqual(self.menu.current_id(), 0)
        self.assertEqual(self.menu.press(47, 88, 1.0), 0)
        self.assertEqual(self.api.replies, [])
        self.assertTrue(self.menu.has_button(41, 88))
        self.assertFalse(self.menu.has_button(61, 88))

    def test_unreadable_buttons_do_not_block_a_press(self):
        self.assertTrue(self.menu.has_button(47, 88))
        self.assertEqual(self.menu.press(47, 88, 1.0), 88)

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
