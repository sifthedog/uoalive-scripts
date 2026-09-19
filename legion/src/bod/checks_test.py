import unittest

from bod.checks import material_of, preflight, stock_counts, stock_report, uses_of
from test_support.uo import install, item

CONFIG = {
    "stock_graphics": set([0x1BF2]),
    "stock_words": ["ingot", "ingots"],
    "stock_noun": "ingots",
    "materials": ["iron", "dull copper", "shadow iron", "copper", "valorite"],
    "hues": {0: "iron", 0x973: "dull copper"},
    "costs": {"axe": 14, "platemail gorget": 10,
              "greater heal potion": {"empty bottle": 1, "ginseng": 7}},
    "kinds": {"empty bottle": set([0x0F0E]), "ginseng": set([0x0F85])},
    "uses_text": "uses remaining",
    "opl_timeout": 1,
}


# A trade whose stock is one pool told apart by material, with no kinds at all
BOARDS = {
    "stock_graphics": set([0x1BD7]),
    "stock_words": [],
    "stock_noun": "boards",
    "materials": ["regular", "oak", "ash", "yew"],
    "hues": {0: "regular"},
    "costs": {"wooden shield": 9},
    "kinds": {},
    "uses_text": "uses remaining",
    "opl_timeout": 1,
}


def request(item="axe", owed=10, exceptional=False, material="iron"):
    return {"item": item, "done": 0, "total": owed, "exceptional": exceptional,
            "material": material}


class MaterialOfTest(unittest.TestCase):
    def test_named_ingots_by_the_name(self):
        self.assertEqual(material_of(item(name="Dull Copper Ingots", hue=0), CONFIG),
                         "dull copper")
        self.assertEqual(material_of(item(name="Copper Ingots", hue=0), CONFIG), "copper")

    def test_plain_ingots_by_the_hue(self):
        self.assertEqual(material_of(item(name="Ingots", hue=0), CONFIG), "iron")
        self.assertEqual(material_of(item(name="Ingots", hue=0x973), CONFIG), "dull copper")

    def test_an_unknown_hue_is_reported_as_a_hue(self):
        self.assertEqual(material_of(item(name="Ingots", hue=0x123), CONFIG), "hue 0x123")


class StockCountsTest(unittest.TestCase):
    def test_counts_ingots_by_material_and_kinds_by_art(self):
        api = install()
        api.hold(item(serial=1, graphic=0x1BF2, name="Ingots", amount=100),
                 item(serial=2, graphic=0x1BF2, name="Ingots", amount=50),
                 item(serial=3, graphic=0x1BF2, name="Valorite Ingots", hue=0x8AB, amount=7),
                 item(serial=4, graphic=0x0F3F, name="arrow", amount=200),
                 item(serial=5, graphic=0x0F85, name="Ginseng", amount=30),
                 item(serial=6, graphic=0x0F0E, name="Empty Bottle", amount=3))

        self.assertEqual(stock_counts(CONFIG),
                         {"iron ingots": 150, "valorite ingots": 7, "ginseng": 30,
                          "empty bottle": 3})
        self.assertEqual(stock_report(CONFIG),
                         "3 empty bottle, 30 ginseng, 150 iron ingots, 7 valorite ingots")

    def test_counts_another_trades_stock_under_its_own_noun(self):
        api = install()
        api.hold(item(serial=1, graphic=0x1BD7, name="Oak Boards", hue=2010, amount=60),
                 item(serial=2, graphic=0x1BD7, name="Boards", amount=40),
                 item(serial=3, graphic=0x1BF2, name="Ingots", amount=100))

        self.assertEqual(stock_counts(BOARDS), {"oak boards": 60, "regular boards": 40})

    def test_nothing_is_no_stock(self):
        install()

        self.assertEqual(stock_report(CONFIG), "no stock")


class UsesOfTest(unittest.TestCase):
    def test_reads_the_line(self):
        self.assertEqual(uses_of("tongs\nUses Remaining: 42\nWeight: 2", CONFIG), 42)

    def test_none_without_the_line(self):
        self.assertIsNone(uses_of("tongs\nWeight: 2", CONFIG))
        self.assertIsNone(uses_of("", CONFIG))


class PreflightTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.hold(item(serial=1, graphic=0x1BF2, name="Ingots", amount=140))
        self.api.props[7] = "tongs\nUses Remaining: 12"

    def test_enough_of_both_is_notes_only(self):
        problems, notes = preflight([request()], [7], CONFIG)

        self.assertEqual(problems, [])
        self.assertEqual(len(notes), 2)

    def test_short_of_ingots(self):
        problems, _notes = preflight([request(owed=11)], [7], CONFIG)

        self.assertEqual(len(problems), 1)
        self.assertIn("154 iron ingots", problems[0])
        self.assertIn("holds 140", problems[0])

    def test_several_requests_are_summed(self):
        problems, notes = preflight([request(owed=5), request(item="platemail gorget", owed=8),
                                     request(item="tessen", owed=2)], [7], CONFIG)

        self.assertIn("150 iron ingots for the 15 pieces owed", problems[0])
        self.assertIn("12 uses left across 1 tool(s) for 15 pieces owed", problems[1])
        self.assertTrue(any("'tessen'" in note for note in notes))

    def test_short_of_uses_across_the_tools(self):
        self.api.props[8] = "smith's hammer\nUses Remaining: 3"
        problems, _notes = preflight([request(owed=16)], [7, 8], CONFIG)

        self.assertEqual(len(problems), 2)
        self.assertIn("15 uses left across 2 tool(s)", problems[1])

    def test_an_unknown_item_skips_the_stock_check(self):
        problems, notes = preflight([request(item="tessen")], [7], CONFIG)

        self.assertEqual(problems, [])
        self.assertTrue(any("no cost is known" in note for note in notes))

    def test_a_dict_cost_is_checked_per_kind(self):
        self.api.hold(item(serial=2, graphic=0x0F0E, name="Empty Bottle", amount=10),
                      item(serial=3, graphic=0x0F85, name="Ginseng", amount=50))
        problems, notes = preflight([request(item="greater heal potion", material=None)], [7],
                                    CONFIG)

        self.assertEqual(len(problems), 1)
        self.assertIn("70 ginseng for the 10 pieces owed, and the pack holds 50", problems[0])
        self.assertTrue(any("10 empty bottle cover" in note for note in notes))

    def test_a_number_cost_is_checked_under_the_trades_noun(self):
        self.api.hold(item(serial=2, graphic=0x1BD7, name="Oak Boards", hue=2010, amount=50))
        problems, _notes = preflight([request(item="wooden shield", owed=10, material="oak")],
                                     [7], BOARDS)

        self.assertEqual(len(problems), 1)
        self.assertIn("90 oak boards for the 10 pieces owed, and the pack holds 50", problems[0])

    def test_tools_that_say_nothing_skip_the_uses_check(self):
        problems, notes = preflight([request()], [9], CONFIG)

        self.assertEqual(problems, [])
        self.assertTrue(any("not checked" in note for note in notes))

    def test_an_exceptional_deed_is_warned_about(self):
        _problems, notes = preflight([request(exceptional=True)], [7], CONFIG)

        self.assertTrue(any("exceptional" in note for note in notes))

    def test_the_material_counted_is_the_deeds(self):
        problems, _notes = preflight([request(material="valorite")], [7], CONFIG)

        self.assertIn("holds 0", problems[0])
