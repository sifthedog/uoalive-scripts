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

    def test_a_one_line_menu_has_no_rows_and_matches_the_phrase_in_any_case(self):
        self._gump("<CENTER>INSCRIPTION MENU</CENTER> LAST TEN Bless Lightning NEXT PAGE Recall")

        self.assertEqual(self.menu.item_rows(88), [])
        self.assertTrue(self.menu.page_has("lightning", 88))
        self.assertFalse(self.menu.page_has("chain lightning", 88))

    def test_says_once_when_no_row_is_named(self):
        self._gump("Weapons")
        self.menu.candidate_buttons("crossbow", 88)
        self.menu.candidate_buttons("crossbow", 88)

        self.assertEqual(self.said, ["no SELECTIONS row reads 'crossbow' - walking the rows",
                                     "rows seen: none"])


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

    def test_a_button_reads_as_its_label_or_nothing(self):
        self.assertEqual(self.menu.label_of(222, 88), "crossbow")
        self.assertIsNone(self.menu.label_of(223, 88))
        self.assertIsNone(self.menu.label_of(41, 88))

    def test_a_row_past_the_first_page_is_named_by_its_own_button(self):
        self.assertEqual(self.menu.named_row("crossbow", 88), 222)
        self.assertEqual(self.menu.named_row("heavy crossbow", 88), 202)
        self.assertIsNone(self.menu.named_row("yumi", 88))

    def test_the_category_is_matched_whole_row_not_by_the_one_line_text(self):
        self.assertTrue(self.menu.page_has("crossbow", 88))
        self.assertTrue(self.menu.page_has("heavy crossbow", 88))
        self.assertFalse(self.menu.page_has("bolt", 88))

    def test_candidates_are_the_named_row_then_the_rows_carrying_the_name_then_the_rest(self):
        self.assertEqual(self.menu.candidate_buttons("crossbow", 88)[:4], [222, 22, 202, 2])
        self.assertEqual(self.menu.candidate_buttons("bow", 88)[:2], [2, 22])
        self.assertEqual(self.said, [])

    def test_every_row_is_still_walked_after_the_named_ones(self):
        del self.api.gump_controls[88]
        self.api.gump_controls[88] = [FakeButton(2), FakeHtml("bow"), FakeButton(22),
                                      FakeHtml("crossbow")] + [FakeButton(2 + n * 20)
                                                               for n in range(12)]

        self.assertEqual(self.menu.candidate_buttons("crossbow", 88)[:2], [22, 2])
        self.assertEqual(len(self.menu.candidate_buttons("crossbow", 88)), 12)

    def test_a_row_the_controls_do_not_name_is_said_once_with_the_rows_seen(self):
        self.menu.candidate_buttons("yumi", 88)
        self.menu.candidate_buttons("yumi", 88)

        self.assertEqual(self.said, ["no SELECTIONS row reads 'yumi' - walking the rows",
                                     "rows seen: bow, crossbow bolt, heavy crossbow, crossbow"])

    def test_unreadable_controls_leave_the_text_to_answer(self):
        del self.api.gump_controls[88]

        self.assertEqual(self.menu.rows_of(88), [])
        self.assertEqual(self.menu.item_rows(88), [])
        self.assertTrue(self.menu.page_has("crossbow", 88))


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
        self.api.gump_buttons[88] = set([41, 2, 22, 42])

        self.assertEqual(self.menu.candidate_buttons("crossbow", 88), [2, 22, 42])

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


class FindRowTest(unittest.TestCase):
    """The menu reads as one line, the pen is 7, and a details press replaces the menu with 200."""

    def setUp(self):
        self.api = install()
        self.said = []
        self.menu = CraftMenu(FakeTool(), CONFIG, self.said.append)
        self.details = {}
        self.api.gump = 88
        self.api.opens[7] = 88
        self.api.gump_contents[88] = "BOWCRAFT AND FLETCHING Materials Ammunition Weapons"
        self.api.gump_buttons[88] = set([1, 21, 41] + [2 + n * 20 for n in range(12)]
                                        + [3 + n * 20 for n in range(12)])
        self.menu.open()

        def reply(button, gump=None):
            self.api.replies.append((button, gump))

            if button in self.details:
                self.api.gump = 200
                self.api.gump_contents[200] = self.details[button]
            elif button == 41:
                self.api.gump_contents[88] = ("BOWCRAFT AND FLETCHING Materials Ammunition Weapons "
                                              "bow NEXT PAGE PREV PAGE crossbow")

            return True

        self.api.ReplyGump = reply
        self.menu.find_category("crossbow", 88)
        self.api.replies[:] = []
        self.said[:] = []

    def pressed(self):
        return [button for button, _gump in self.api.replies]

    def test_the_details_page_that_names_the_product_is_the_row(self):
        self.details = {3: "ITEM bow SKILLS MATERIALS BACK", 23: "ITEM crossbow SKILLS BACK"}

        self.assertEqual(self.menu.find_row("crossbow", 88), (88, 22))
        self.assertEqual(self.pressed(), [3, 41, 23, 41])
        self.assertEqual(self.api.used, [7, 7])
        self.assertEqual(self.said, ["'crossbow' is the row on button 22 - its details page names it"])

    def test_rows_past_the_first_page_are_reached(self):
        self.details = dict((3 + n * 20, "ITEM bow BACK") for n in range(12))
        self.details[203] = "ITEM crossbow BACK"

        self.assertEqual(self.menu.find_row("crossbow", 88), (88, 202))

    def test_a_category_with_no_such_row_answers_no_button(self):
        self.details = dict((3 + n * 20, "ITEM bow BACK") for n in range(12))

        self.assertEqual(self.menu.find_row("crossbow", 88), (88, None))
        self.assertEqual(len(self.pressed()), 24)

    def test_unreadable_buttons_send_it_to_the_walk(self):
        del self.api.gump_buttons[88]

        self.assertIsNone(self.menu.find_row("crossbow", 88))
        self.assertEqual(self.pressed(), [])

    def test_a_menu_without_details_buttons_sends_it_to_the_walk(self):
        self.api.gump_buttons[88] = set([1, 21, 41, 2, 22])

        self.assertIsNone(self.menu.find_row("crossbow", 88))
        self.assertEqual(self.pressed(), [])

    def test_a_details_button_that_redraws_nothing_sends_it_to_the_walk_and_says_so_once(self):
        self.assertIsNone(self.menu.find_row("crossbow", 88))
        self.assertIsNone(self.menu.find_row("crossbow", 88))
        self.assertEqual(self.pressed(), [3, 3])
        self.assertEqual(self.said, ["button 3 opened no details page, walking the rows instead"])

    def test_a_menu_that_does_not_come_back_is_no_gump(self):
        self.details = {3: "ITEM bow BACK"}
        del self.api.opens[7]

        self.assertEqual(self.menu.find_row("crossbow", 88), (0, None))

    def test_a_product_whose_category_is_unknown_goes_to_the_walk(self):
        self.assertIsNone(self.menu.find_row("yumi", 88))

    def _controls(self, *rows):
        found = [FakeButton(0), FakeButton(41), FakeHtml("Weapons")]

        for index, label in enumerate(rows):
            button = 2 + index * 20
            found += [FakeButton(button), FakeHtml(label), FakeButton(button + 1)]

            if index % 10 == 9:
                found += [FakeButton(0), FakeHtml("NEXT PAGE"), FakeButton(0), FakeHtml("PREV PAGE")]

        self.api.gump_controls[88] = found

    def test_a_row_the_controls_name_is_taken_without_its_details_page(self):
        self._controls(*(["bow"] * 18 + ["crossbow"]))

        self.assertEqual(self.menu.find_row("crossbow", 88), (88, 362))
        self.assertEqual(self.pressed(), [])
        self.assertEqual(self.said, ["'crossbow' is the row on button 362 - the menu names it there"])

    def test_the_rows_carrying_the_name_have_their_details_opened_first(self):
        self._controls("bow", "yumi", "heavy crossbow")
        self.details = {3: "ITEM bow BACK", 23: "ITEM yumi BACK", 43: "ITEM heavy crossbow BACK"}

        self.assertEqual(self.menu.find_row("crossbow", 88), (88, 42))
        self.assertEqual(self.pressed(), [43, 41])
        self.assertEqual(self.said[0], "no SELECTIONS row reads 'crossbow' - walking the rows")
        self.assertEqual(self.said[1], "rows seen: bow, yumi, heavy crossbow")

    def test_rows_whose_names_lack_the_product_have_no_details_opened(self):
        self._controls("bow", "yumi")
        self.details = {3: "ITEM bow BACK", 23: "ITEM yumi BACK"}

        self.assertEqual(self.menu.find_row("crossbow", 88), (88, None))
        self.assertEqual(self.pressed(), [])
