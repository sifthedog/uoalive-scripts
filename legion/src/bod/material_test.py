import unittest

from bod.material import MaterialPicker
from test_support.uo import install
from uo.craftmenu import CraftMenu

MENU = {
    "stride": 20,
    "category_type": 0,
    "item_type": 1,
    "category_names": ["metal armor", "helmets"],
    "last_ten_label": "LAST TEN",
    "title": "BLACKSMITHY",
    "title_text": ["BLACKSMITHY"],
    "title_fragments": ["blacksmithy"],
    "tool_noun": "smith's tools",
    "gump_timeout": 1.0,
    "gump_poll": 0.2,
    "max_categories": 10,
    "max_item_rows": 20,
}

CONFIG = {
    "aliases": {"shadow iron": ["shadow"]},
    "button_type": 6,
    "row_type": 5,
    "max_rows": 12,
    "gump_timeout": 1.0,
}

ROWS = ["IRON (300)", "DULL COPPER (12)", "SHADOW (0)", "COPPER (40)"]


class FakeTool(object):
    def serial(self):
        return 7


class MaterialPickerTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.menu = CraftMenu(FakeTool(), MENU, self.said.append)
        self.picker = MaterialPicker(self.menu, CONFIG, self.said.append)
        self.api.gump = 88
        self.api.gump_contents[88] = "\n".join(["Metal Armor", "Helmets"] + ROWS)

    def test_rows_are_matched_on_their_leading_words(self):
        self.assertEqual(self.picker.row_of("copper", ROWS), 3)
        self.assertEqual(self.picker.row_of("dull copper", ROWS), 1)
        self.assertEqual(self.picker.row_of("iron", ROWS), 0)

    def test_an_alias_finds_the_row(self):
        self.assertEqual(self.picker.row_of("shadow iron", ROWS), 2)

    def test_presses_the_page_then_the_row(self):
        opened, why = self.picker.select("copper", 88)

        self.assertIsNone(why)
        self.assertEqual(opened, 88)
        self.assertEqual([button for button, _gump in self.api.replies], [7, 66])
        self.assertFalse(self.picker.needs("copper"))
        self.assertTrue(self.picker.needs("iron"))

    def test_no_row_says_what_it_saw(self):
        _opened, why = self.picker.select("valorite", 88)

        self.assertEqual(why, "noMaterialRow")
        self.assertTrue(any("DULL COPPER" in line for line in self.said))
        self.assertTrue(self.picker.needs("valorite"))

    def test_forget_asks_again(self):
        self.picker.select("copper", 88)
        self.picker.forget()

        self.assertTrue(self.picker.needs("copper"))

    def test_a_page_that_never_opened(self):
        self.api.gump = 0

        self.assertEqual(self.picker.select("copper", 88), (0, "noGump"))
