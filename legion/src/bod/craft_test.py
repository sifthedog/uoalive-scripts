import unittest

from bod.craft import DeedCrafter
from test_support.uo import install, item

MAKE_LAST = 47

CONFIG = {
    "make_last_button": MAKE_LAST,
    "craft_timeout": 1.0,
    "craft_poll": 0.2,
    "craft_settle": 0.4,
    "max_probes": 4,
    "max_categories": 10,
    "max_reports": 2,
    "text_limit": 160,
    "tail_seconds": 20.0,
    "tail_lines": 4,
}


class FakeTool(object):
    def serial(self):
        return 7


class FakePicker(object):
    def __init__(self):
        self.selected = []
        self.answer = None

    def needs(self, material):
        return material not in self.selected

    def select(self, material, gump):
        if self.answer is not None:
            return gump, self.answer

        self.selected.append(material)

        return gump, None


class FakeItems(object):
    def __init__(self, api):
        self._api = api
        self.names = {}

    def serials(self):
        return set(held.Serial for held in self._api.containers.get(self._api.Backpack, []))

    def new_since(self, before):
        return [held for held in self._api.containers.get(self._api.Backpack, [])
                if held.Serial not in before]

    def is_product(self, serial):
        return self.names.get(serial)


class FakeMenu(object):
    """Answers every press with the same gump, and lands whatever the test says the press makes."""

    def __init__(self, api, items):
        self._api = api
        self._items = items
        self.presses = []
        self.makes = {}
        self.says = []
        self.category = 1
        self.rows = [2, 22, 42]

    def open(self):
        return 88

    def press(self, button, gump, timeout):
        self.presses.append(button)
        self._api.hear(*self.says)
        name = self.makes.get(button)

        if name is not None:
            held = list(self._api.containers.get(self._api.Backpack, []))
            serial = 100 + len(held)
            held.append(item(serial=serial))
            self._api.hold(*held)
            self._items.names[serial] = None if name == "unknown" else name == "product"
            self._api.hear("You create the item")

        return 88

    def find_category(self, product, gump):
        return (88, self.category)

    def candidate_buttons(self, product, gump):
        return list(self.rows)

    def reject_category(self, product, button):
        return 1

    def forget_category(self, product):
        pass

    def lines(self, gump):
        return []


class DeedCrafterTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.items = FakeItems(self.api)
        self.menu = FakeMenu(self.api, self.items)
        self.picker = FakePicker()
        self.crafter = DeedCrafter(FakeTool(), self.menu, self.items, self.picker,
                                   [("failed", ["You failed"]), ("made", ["You create the item"]),
                                    ("noAnvil", ["near an anvil and a forge"])],
                                   CONFIG, self.said.append)

    def test_the_material_is_selected_once(self):
        self.menu.makes = {2: "product", MAKE_LAST: "product"}

        self.crafter.craft_once("platemail gorget", "copper")
        self.crafter.craft_once("platemail gorget", "copper")

        self.assertEqual(self.picker.selected, ["copper"])

    def test_a_proven_row_is_pressed_as_make_last_from_then_on(self):
        self.menu.makes = {2: "product", MAKE_LAST: "product"}

        self.assertEqual(self.crafter.craft_once("platemail gorget", "iron"), "made")
        self.assertEqual(self.crafter.craft_once("platemail gorget", "iron"), "made")
        self.assertEqual(self.menu.presses, [2, MAKE_LAST])

    def test_a_row_that_made_something_else_is_a_wrong_row(self):
        self.menu.makes = {2: "other", 22: "product"}

        self.assertEqual(self.crafter.craft_once("platemail gorget", "iron"), "wrongRow")
        self.assertEqual(self.crafter.craft_once("platemail gorget", "iron"), "made")
        self.assertEqual(self.menu.presses, [2, 22])

    def test_an_unjudged_item_is_taken_as_the_product(self):
        self.menu.makes = {2: "unknown"}

        self.assertEqual(self.crafter.craft_once("platemail gorget", "iron"), "made")
        self.assertTrue(any("tooltip did not arrive" in line for line in self.said))

    def test_the_shard_refusing_the_anvil(self):
        self.menu.says = ["You must be near an anvil and a forge to smith items."]

        self.assertEqual(self.crafter.craft_once("platemail gorget", "iron"), "noAnvil")

    def test_a_material_row_that_is_missing_ends_the_craft(self):
        self.picker.answer = "noMaterialRow"

        self.assertEqual(self.crafter.craft_once("platemail gorget", "copper"), "noMaterialRow")
        self.assertEqual(self.menu.presses, [])
