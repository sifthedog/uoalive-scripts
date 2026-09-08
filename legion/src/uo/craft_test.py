import unittest

from uo.craft import Crafter
from test_support.uo import install, item

BOW = 0x13B2
CROSSBOW = 0x0F50
MAKE_LAST = 47

CONFIG = {
    "recipes": {"bow": (41, 2)},
    "products": {"bow": set([BOW])},
    "make_last_button": MAKE_LAST,
    "gump_timeout": 1.0,
    "craft_timeout": 1.0,
    "craft_poll": 0.2,
    "craft_settle": 0.4,
    "max_probes": 8,
    "max_categories": 6,
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

    def open(self):
        return 88

    def press(self, button, gump, timeout):
        self.presses.append(button)
        graphic = self.makes.get(button)

        if graphic is not None:
            held = list(self._api.containers.get(self._api.Backpack, []))
            held.append(item(serial=100 + len(held), graphic=graphic))
            self._api.hold(*held)
            self._api.hear("You create the item")

        return 88

    def remember_category(self, product, button):
        pass

    def lines(self, gump):
        return []


class MakeLastTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.menu = Menu(self.api)
        self.crafter = Crafter(Tools(), self.menu, Stock(), [("made", ["You create the item"])],
                               CONFIG, lambda text: None)

    def test_a_proven_row_is_pressed_as_make_last_from_then_on(self):
        self.menu.makes = {2: BOW, MAKE_LAST: BOW}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.menu.presses, [41, 2, MAKE_LAST])

    def test_make_last_making_the_wrong_thing_does_not_forget_the_row(self):
        self.menu.makes = {2: BOW, MAKE_LAST: CROSSBOW}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.crafter.craft_once("bow"), "wrongRow")
        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.menu.presses, [41, 2, MAKE_LAST, 41, 2])
        self.assertEqual(self.crafter._item_buttons, {"bow": 2})
        self.assertEqual(self.crafter._walked, set())
