import unittest

from bod.craft import DeedCrafter
from test_support.uo import install, item

CONFIG = {
    "recipes": {"dagger": (61, 82)},
    "make_number_button": 2,
    "cancel_button": 227,
    "prompt_delay": 0.1,
    "craft_interval": 1.0,
    "batch_idle": 1.0,
    "gump_timeout": 1.0,
    "craft_timeout": 1.0,
    "craft_poll": 0.2,
    "craft_settle": 0.4,
    "max_categories": 10,
    "max_reports": 2,
    "text_limit": 160,
    "tail_seconds": 20.0,
    "tail_lines": 4,
}

BUCKETS = [
    ("failed", ["You failed"]),
    ("made", ["You create the item"]),
    ("noMaterial", ["not enough ingots"]),
    ("noAnvil", ["near an anvil and a forge"]),
]


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

    def name_of(self, serial):
        return "something"


class FakeMenu(object):
    """Answers every press with the same gump, and lands whatever the test says the press makes."""

    def __init__(self, api, items):
        self._api = api
        self._items = items
        self.presses = []
        self.makes = {}
        self.says = []
        self.category = 1
        self.rows = {"axe": 2}

    def open(self):
        return 88

    def land(self, name):
        held = list(self._api.containers.get(self._api.Backpack, []))
        serial = 100 + len(held)
        held.append(item(serial=serial))
        self._api.hold(*held)
        self._items.names[serial] = None if name == "unknown" else name == "product"

    def press(self, button, gump, timeout):
        self.presses.append(button)
        self._api.hear(*self.says)
        name = self.makes.get(button)

        if name is not None:
            self.land(name)
            self._api.hear("You create the item")

        return 88

    def find_category(self, product, gump):
        return (88, self.category)

    def named_row(self, product, gump):
        return self.rows.get(product)

    def remember_category(self, product, button):
        pass

    def lines(self, gump):
        return ["Metal Armor", "ringmail tunic"]


class DeedCrafterTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.items = FakeItems(self.api)
        self.menu = FakeMenu(self.api, self.items)
        self.picker = FakePicker()
        self.crafter = DeedCrafter(FakeTool(), self.menu, self.items, self.picker, BUCKETS,
                                   CONFIG, self.said.append)

    def test_the_material_is_selected_once(self):
        self.menu.makes = {2: "product"}

        self.crafter.craft_once("axe", "copper")
        self.crafter.craft_once("axe", "copper")

        self.assertEqual(self.picker.selected, ["copper"])

    def test_a_craft_that_made_the_product_proves_the_row(self):
        self.menu.makes = {2: "product"}

        self.assertFalse(self.crafter.proven("axe"))
        self.assertEqual(self.crafter.craft_once("axe", "iron"), "made")
        self.assertTrue(self.crafter.proven("axe"))

    def test_a_row_that_made_something_else_is_a_wrong_row_and_nothing_more_is_pressed(self):
        self.menu.makes = {2: "other"}

        self.assertEqual(self.crafter.craft_once("axe", "iron"), "wrongRow")
        self.assertEqual(self.menu.presses, [2])
        self.assertTrue(any("not a 'axe'" in line for line in self.said))

    def test_a_known_recipe_presses_its_category_then_its_row(self):
        self.menu.makes = {82: "product"}

        self.assertEqual(self.crafter.craft_once("dagger", "iron"), "made")
        self.assertEqual(self.menu.presses, [61, 82])

    def test_a_row_the_page_does_not_name_is_never_guessed(self):
        self.assertEqual(self.crafter.craft_once("ringmail tunic", "iron"), "noRow")
        self.assertEqual(self.menu.presses, [])
        self.assertTrue(any("the page says" in line for line in self.said))

    def test_an_unjudged_item_is_taken_as_the_product(self):
        self.menu.makes = {2: "unknown"}

        self.assertEqual(self.crafter.craft_once("axe", "iron"), "made")
        self.assertTrue(any("tooltip did not arrive" in line for line in self.said))

    def test_the_shard_refusing_the_anvil(self):
        self.menu.says = ["You must be near an anvil and a forge to smith items."]

        self.assertEqual(self.crafter.craft_once("axe", "iron"), "noAnvil")

    def test_a_material_row_that_is_missing_ends_the_craft(self):
        self.picker.answer = "noMaterialRow"

        self.assertEqual(self.crafter.craft_once("axe", "copper"), "noMaterialRow")
        self.assertEqual(self.menu.presses, [])


class BatchTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.items = FakeItems(self.api)
        self.menu = FakeMenu(self.api, self.items)
        self.crafter = DeedCrafter(FakeTool(), self.menu, self.items, FakePicker(), BUCKETS,
                                   CONFIG, self.said.append)
        self.menu.makes = {2: "product"}
        self.crafter.craft_once("axe", "iron")
        self.menu.presses = []
        self.answers = []
        self.api.PromptResponse = self.answers.append
        self.api.gump = 88
        self.landing = []

        def pause(seconds):
            self.api.paused += seconds

            if self.landing:
                step = self.landing.pop(0)

                if step == "failed":
                    self.api.hear("You failed to create the item")
                elif step is not None:
                    self.menu.land(step)

        self.api.Pause = pause

    def test_presses_details_then_make_number_and_answers_the_prompt(self):
        self.landing = [None, "product", "product", "failed"]

        outcome, made, failed = self.crafter.craft_batch("axe", "iron", 3)

        self.assertEqual((outcome, made, failed), ("made", 2, 1))
        self.assertEqual(self.menu.presses, [3])
        self.assertEqual(self.api.replies[-1], (2, 88))
        self.assertEqual(self.answers, ["3"])

    def test_a_batch_that_goes_quiet_ends_on_the_idle_limit(self):
        self.landing = [None, "product"]

        outcome, made, failed = self.crafter.craft_batch("axe", "iron", 3)

        self.assertEqual((outcome, made, failed), ("made", 1, 0))

    def test_a_batch_that_made_nothing_is_unreadable(self):
        outcome, made, failed = self.crafter.craft_batch("axe", "iron", 3)

        self.assertEqual((outcome, made, failed), (None, 0, 0))
        self.assertTrue(any("made nothing" in line for line in self.said))

    def test_a_refusal_cancels_the_batch(self):
        self.landing = [None, "product"]
        self.api.gump_text = ["There are not enough ingots"]
        self.api.hear("not enough ingots")

        outcome, made, failed = self.crafter.craft_batch("axe", "iron", 5)

        self.assertEqual(outcome, "noMaterial")
        self.assertIn((227, 88), self.api.replies)

    def test_a_batch_of_the_wrong_thing_forgets_the_row(self):
        self.landing = [None, "other", "other"]

        outcome, made, failed = self.crafter.craft_batch("axe", "iron", 2)

        self.assertEqual(outcome, "wrongRow")
        self.assertFalse(self.crafter.proven("axe"))
