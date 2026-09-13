import unittest

from uo.craft import Crafter
from test_support.uo import install, item

BOW = 0x13B2
CROSSBOW = 0x0F50
SIGNPOST = 0x0B97
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
        self.names = {}
        self.props = {}
        self.named = {}
        self.missing = set()

    def open(self):
        return 88

        self.found = None

    def current_id(self):
        return 88

    def find_category(self, product, gump):
        return 88, 41

    def find_row(self, product, gump):
        return self.found

    def candidate_buttons(self, product, gump):
        return []

    def reject_category(self, product, button):
        return 1

    def forget_category(self, product):
        pass

    def has_button(self, button, gump):
        return button not in self.missing

    def press(self, button, gump, timeout):
        self.presses.append(button)
        graphic = self.makes.get(button)

        if graphic is not None:
            held = list(self._api.containers.get(self._api.Backpack, []))
            serial = 100 + len(held)
            held.append(item(serial=serial, graphic=graphic, name=self.names.get(graphic, "")))
            self._api.hold(*held)

            if graphic in self.props:
                self._api.props[serial] = self.props[graphic]
            self._api.hear("You create the item")

        return 88

    def remember_category(self, product, button):
        pass

    def named_button(self, product):
        return self.named.get(product)

    def lines(self, gump):
        return []


class MakeLastTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.menu = Menu(self.api)
        self.said = []
        self.crafter = Crafter(Tools(), self.menu, Stock(), [("made", ["You create the item"])],
                               CONFIG, self.said.append)

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

    def test_the_row_is_pressed_when_the_menu_has_no_make_last(self):
        self.menu.makes = {2: BOW}
        self.menu.missing = set([MAKE_LAST])

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.menu.presses, [41, 2, 41, 2])
        self.assertEqual(len([line for line in self.said if "no MAKE LAST" in line]), 1)

    def test_a_recipe_button_the_menu_lacks_is_walked_for_and_never_pressed(self):
        self.menu.missing = set([2])

        self.assertEqual(self.crafter.craft_once("bow"), "wrongRow")
        self.assertEqual(self.menu.presses, [41])
        self.assertEqual(self.crafter._walked, set(["bow"]))


class DetailsRowTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.menu = Menu(self.api)
        self.said = []
        config = dict(CONFIG)
        config["recipes"] = {}
        self.crafter = Crafter(Tools(), self.menu, Stock(), [("made", ["You create the item"])],
                               config, self.said.append)

    def test_the_row_the_details_pages_named_is_pressed_and_kept(self):
        self.menu.found = (88, 22)
        self.menu.makes = {22: BOW, MAKE_LAST: BOW}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.menu.presses, [22, MAKE_LAST])
        self.assertEqual(self.crafter._item_buttons, {"bow": 22})

    def test_a_category_the_details_pages_rule_out_is_left_without_a_craft(self):
        self.menu.found = (88, None)

        self.assertEqual(self.crafter.craft_once("bow"), "wrongRow")
        self.assertEqual(self.menu.presses, [])

    def test_a_menu_that_went_away_is_no_gump(self):
        self.menu.found = (0, None)

        self.assertEqual(self.crafter.craft_once("bow"), "noGump")

    def test_a_row_the_details_named_wrongly_goes_to_the_walk_next(self):
        self.menu.found = (88, 22)
        self.menu.makes = {22: CROSSBOW}

        self.assertEqual(self.crafter.craft_once("bow"), "wrongRow")
        self.menu.found = (88, 2)

        self.assertEqual(self.crafter.craft_once("bow"), "wrongRow")
        self.assertEqual(self.menu.presses, [22])


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


class HeardTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.menu = Menu(self.api)
        self.said = []
        self.crafter = Crafter(Tools(), self.menu, Stock(), [("made", ["You create the item"])],
                               CONFIG, self.said.append)

    def test_a_made_that_never_landed_says_what_was_believed(self):
        self.menu.makes = {2: CROSSBOW}

        self.assertEqual(self.crafter.craft_once("bow"), "wrongRow")
        self.assertIn("button 2 did not make a 'bow' - the journal said 'You create the item' - "
                      "trying the next row", self.said)

    def test_a_notice_names_the_gump(self):
        self.api.gump_contents[88] = "NOTICES You create the item"

        self.assertEqual(self.crafter.craft_once("bow"), "wrongRow")
        self.assertIn("button 2 did not make a 'bow' - the gump said 'You create the item' - "
                      "trying the next row", self.said)


class LearnArtTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.menu = Menu(self.api)
        self.said = []
        config = dict(CONFIG)
        config["products"] = {"bow": set([BOW])}
        self.crafter = Crafter(Tools(), self.menu, Stock(), [("made", ["You create the item"])],
                               config, self.said.append)

    def test_a_new_art_named_for_the_product_is_it_under_another_number(self):
        self.menu.makes = {2: 0x1234}
        self.menu.names = {0x1234: "bow"}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.crafter._item_buttons, {"bow": 2})
        self.assertIn("'bow' landed as 0x1234, not the art in the table - put 0x1234 in it",
                      self.said)

        self.menu.makes = {MAKE_LAST: 0x1234}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.menu.presses, [41, 2, MAKE_LAST])

    def test_the_tooltip_names_it_when_the_item_does_not(self):
        self.menu.makes = {2: 0x1234}
        self.menu.props = {0x1234: "a bow\nweight 6 stones"}

        self.assertEqual(self.crafter.craft_once("bow"), "made")

    def test_a_new_art_named_for_something_else_is_a_wrong_row(self):
        self.menu.makes = {2: 0x1234}
        self.menu.names = {0x1234: "crossbow bolt"}

        self.assertEqual(self.crafter.craft_once("bow"), "wrongRow")
        self.assertEqual(self.crafter._item_buttons, {})

    def test_nothing_new_in_the_pack_is_still_a_wrong_row(self):
        self.api.gump_contents[88] = "NOTICES You create the item"
        self.menu.makes = {}

        self.assertEqual(self.crafter.craft_once("bow"), "wrongRow")


class TrustedRowTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.menu = Menu(self.api)
        self.said = []
        self.config = dict(CONFIG)
        self.config["products"] = {"bow": set([BOW])}
        self.crafter = Crafter(Tools(), self.menu, Stock(), [("made", ["You create the item"])],
                               self.config, self.said.append)

    def test_a_made_the_pack_cannot_prove_keeps_the_row_the_menu_named(self):
        self.menu.named = {"bow": 2}
        self.menu.makes = {2: SIGNPOST}
        self.menu.names = {SIGNPOST: "Wooden Signpost"}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.crafter._item_buttons, {"bow": 2})
        self.assertIn("'bow' landed as 0xb97, which the product table does not list - counting the "
                      "row the menu named as made; put it in the table", self.said)

    def test_make_last_is_trusted_once_the_named_row_is(self):
        self.menu.named = {"bow": 2}
        self.menu.makes = {2: SIGNPOST, MAKE_LAST: SIGNPOST}
        self.menu.names = {SIGNPOST: "Wooden Signpost"}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.menu.presses, [41, 2, MAKE_LAST])
        self.assertEqual(self.crafter._item_buttons, {"bow": 2})
        self.assertEqual(len([line for line in self.said if "product table" in line]), 1)

    def test_a_row_the_menu_did_not_name_is_still_a_wrong_row(self):
        self.menu.makes = {2: SIGNPOST}
        self.menu.names = {SIGNPOST: "Wooden Signpost"}

        self.assertEqual(self.crafter.craft_once("bow"), "wrongRow")
        self.assertEqual(self.crafter._item_buttons, {})

    def test_a_learned_art_does_not_reach_a_product_sharing_the_set(self):
        deeds = set([0x14F0])
        self.config["products"] = {"bow": deeds, "crossbow": deeds}
        self.menu.makes = {2: 0x1234}
        self.menu.names = {0x1234: "bow"}

        self.assertEqual(self.crafter.craft_once("bow"), "made")
        self.assertEqual(self.config["products"]["bow"], set([0x14F0, 0x1234]))
        self.assertEqual(self.config["products"]["crossbow"], set([0x14F0]))
