import unittest

from uo.craft import Crafter
from test_support.uo import install, item

BOW = 0x13B2
CROSSBOW = 0x0F50
MAKE_LAST = 47

CONFIG = {
    "recipes": {"bow": (41, 2)},
    "make_last_button": MAKE_LAST,
    "gump_timeout": 1.0,
    "craft_timeout": 1.0,
    "craft_poll": 0.2,
    "max_reports": 2,
    "text_limit": 160,
    "tail_seconds": 20.0,
    "tail_lines": 4,
    "material": "regular",
}


class Tools(object):
    def serial(self):
        return 7


class Stock(object):
    def hue_report(self):
        return "no wood"


class Menu(object):
    """Answers every press with the same gump, and lands whatever the test says the press makes."""

    def __init__(self, api):
        self._api = api
        self.presses = []
        self.makes = {}
        self.labels = {}
        self.missing = set()

    def open(self):
        return 88

    def current_id(self):
        return 88

    def has_button(self, button, gump):
        return button not in self.missing

    def press(self, button, gump, timeout):
        self.presses.append(button)
        graphic = self.makes.get(button)

        if graphic is not None:
            held = list(self._api.containers.get(self._api.Backpack, []))
            held.append(item(serial=100 + len(held), graphic=graphic))
            self._api.hold(*held)
            self._api.hear("You create the item")

        return 88

    def label_of(self, button, gump):
        return self.labels.get(button)

    def lines(self, gump):
        return []


class CraftTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.menu = Menu(self.api)
        self.said = []
        self.crafter = Crafter(Tools(), self.menu, Stock(), [("made", ["You create the item"])],
                               CONFIG, self.said.append)

    def test_the_table_row_is_pressed_then_make_last(self):
        self.menu.makes = {2: BOW, MAKE_LAST: BOW}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.menu.presses, [41, 2, MAKE_LAST])

    def test_the_row_is_pressed_when_the_menu_has_no_make_last(self):
        self.menu.makes = {2: BOW}
        self.menu.missing = set([MAKE_LAST])

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.menu.presses, [41, 2, 41, 2])
        self.assertEqual(len([line for line in self.said if "no MAKE LAST" in line]), 1)

    def test_a_label_that_reads_otherwise_is_pressed_anyway(self):
        self.menu.labels = {2: "crossbow"}
        self.menu.makes = {2: BOW}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.menu.presses, [41, 2])

    def test_a_button_the_menu_lacks_is_pressed_anyway(self):
        self.menu.missing = set([41, 2])
        self.menu.makes = {2: BOW}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.menu.presses, [41, 2])

    def test_the_wrong_graphic_landing_is_still_made(self):
        self.menu.makes = {2: CROSSBOW}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.said, [])

    def test_nothing_landing_is_made_when_the_journal_says_so(self):
        self.menu.press = lambda button, gump, timeout: (self.api.hear("You create the item"), 88)[1]

        self.assertEqual(self.crafter.craft_once("bow"), "made")

    def test_a_product_not_in_the_table_is_no_row(self):
        self.assertEqual(self.crafter.craft_once("crossbow"), "noRow")
        self.assertEqual(self.menu.presses, [])

    def test_nothing_readable_after_make_last_presses_the_row_next(self):
        self.menu.makes = {2: BOW}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertIsNone(self.crafter.craft_once("bow"))
        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.menu.presses, [41, 2, MAKE_LAST, 41, 2])

    def test_a_category_press_that_answers_nothing_is_no_gump(self):
        self.menu.press = lambda button, gump, timeout: 0

        self.assertEqual(self.crafter.craft_once("bow"), "noGump")


class NoticeTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.menu = Menu(self.api)
        self.said = []
        self.crafter = Crafter(Tools(), self.menu, Stock(),
                               [("failed", ["You fail to inscribe the scroll"])],
                               CONFIG, self.said.append)

    def test_a_notice_in_the_gump_text_is_read_in_any_case(self):
        self.api.gump_contents[88] = ("<CENTER>NOTICES</CENTER> LAST TEN You fail to inscribe "
                                      "the scroll, and the scroll is ruined First - Second Circle")
        self.api.GumpContains = lambda text, gump=None: False

        self.assertEqual(self.crafter.craft_once("bow"), "failed")

    def test_a_notice_only_the_clients_search_sees_is_read(self):
        self.api.gump_contents[88] = ""
        self.api.GumpContains = lambda text, gump=None: text == "You fail to inscribe the scroll"

        self.assertEqual(self.crafter.craft_once("bow"), "failed")
