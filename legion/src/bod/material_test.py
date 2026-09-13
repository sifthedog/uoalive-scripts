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
}

CONFIG = {
    "aliases": {"shadow iron": ["shadow"]},
    "order": ["iron", "dull copper", "shadow iron", "copper"],
    "rows_after": "do not color",
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
        self.menu.open()

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

    def test_the_one_line_page_is_split_on_the_counts(self):
        text = ("<CENTER>BLACKSMITHING MENU</CENTER> EXIT CANCEL MAKE SMELT ITEM BRONZE (187) "
                "RED SCALES (0) LAST TEN Metal Armor Helmets Shields DO NOT COLOR IRON (1587) "
                "DULL COPPER (111) SHADOW (185) COPPER (0) BRONZE (187) GOLD (0) AGAPITE (59) "
                "VERITE (48) VALORITE (47)")

        self.assertEqual(self.picker.rows_from_text(text), [
            "IRON (1587)", "DULL COPPER (111)", "SHADOW (185)", "COPPER (0)", "BRONZE (187)",
            "GOLD (0)", "AGAPITE (59)", "VERITE (48)", "VALORITE (47)"])

    def test_a_one_line_page_finds_the_row_by_text(self):
        self.api.gump_contents[88] = ("EXIT DO NOT COLOR IRON (1587) DULL COPPER (111) "
                                      "SHADOW (185) COPPER (0) BRONZE (187)")
        opened, why = self.picker.select("bronze", 88)

        self.assertIsNone(why)
        self.assertEqual([button for button, _gump in self.api.replies], [7, 86])
        self.assertFalse(any("stock order" in line for line in self.said))

    def test_a_page_with_no_rows_falls_back_to_the_stock_order(self):
        self.api.gump_contents[88] = "BLACKSMITHY"
        opened, why = self.picker.select("copper", 88)

        self.assertIsNone(why)
        self.assertEqual([button for button, _gump in self.api.replies], [7, 66])
        self.assertTrue(any("stock order" in line for line in self.said))

    def test_a_page_with_no_rows_and_no_stock_row(self):
        self.api.gump_contents[88] = ""
        _opened, why = self.picker.select("valorite", 88)

        self.assertEqual(why, "noMaterialRow")

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
