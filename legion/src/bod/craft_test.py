import unittest

from bod.craft import DeedCrafter
from test_support.uo import install, item

CONFIG = {
    "recipes": {"axe": (81, 2), "dagger": (61, 82)},
    "make_number_button": 2,
    "cancel_button": 227,
    "prompt_delay": 0.1,
    "craft_interval": 1.0,
    "batch_idle": 1.0,
    "gump_timeout": 1.0,
    "craft_timeout": 1.0,
    "craft_poll": 0.2,
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

    def serials(self):
        return set(held.Serial for held in self._api.containers.get(self._api.Backpack, []))

    def new_since(self, before):
        return [held for held in self._api.containers.get(self._api.Backpack, [])
                if held.Serial not in before]


class FakeMenu(object):
    """Answers every press with the same gump."""

    def __init__(self, api):
        self._api = api
        self.presses = []

    def open(self):
        return 88

    def land(self):
        held = list(self._api.containers.get(self._api.Backpack, []))
        held.append(item(serial=100 + len(held)))
        self._api.hold(*held)

    def current_id(self):
        return 88

    def reply(self, button, gump):
        return self._api.ReplyGump(button, gump)

    def reply_page(self, button, page):
        return self._api.ReplyGump(button, page)

    def press(self, button, gump, timeout):
        self.presses.append(button)

        return 88

    def press_page(self, button, gump, timeout):
        return self.press(button, gump, timeout)

    def lines(self, gump):
        return ["Metal Armor", "ringmail tunic"]


class BatchTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.items = FakeItems(self.api)
        self.menu = FakeMenu(self.api)
        self.picker = FakePicker()
        self.crafter = DeedCrafter(FakeTool(), self.menu, self.items, self.picker, BUCKETS,
                                   CONFIG, self.said.append)
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
                    self.menu.land()

        self.api.Pause = pause

    def test_presses_the_category_the_details_page_then_make_number_and_answers_the_prompt(self):
        self.landing = [None, "product", "product", "failed"]

        outcome, made, failed = self.crafter.craft_batch("axe", "iron", 3)

        self.assertEqual((outcome, made, failed), ("made", 2, 1))
        self.assertEqual(self.menu.presses, [81, 3])
        self.assertEqual(self.api.replies[-1], (2, 88))
        self.assertEqual(self.answers, ["3"])

    def test_the_material_is_selected_once(self):
        self.crafter.craft_batch("axe", "copper", 1)
        self.crafter.craft_batch("axe", "copper", 1)

        self.assertEqual(self.picker.selected, ["copper"])

    def test_a_product_not_in_the_table_is_no_row_and_nothing_is_pressed(self):
        self.assertEqual(self.crafter.craft_batch("ringmail tunic", "iron", 3), ("noRow", 0, 0))
        self.assertEqual(self.menu.presses, [])

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

    def test_the_shard_refusing_the_anvil(self):
        self.api.gump_text = ["You must be near an anvil and a forge to smith items."]

        self.assertEqual(self.crafter.craft_batch("axe", "iron", 3)[0], "noAnvil")

    def test_a_material_row_that_is_missing_ends_the_craft(self):
        self.picker.answer = "noMaterialRow"

        self.assertEqual(self.crafter.craft_batch("axe", "copper", 3), ("noMaterialRow", 0, 0))
        self.assertEqual(self.menu.presses, [])
