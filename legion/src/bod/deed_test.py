import unittest

from bod.config import ARTICLES, DEED_TEXT, PLAIN_MATERIAL
from bod.deed import Deed, entry_request, parse_deed, trade_of
from test_support.uo import install

CONFIG = {
    "text": DEED_TEXT,
    "plain": PLAIN_MATERIAL,
    "articles": ARTICLES,
    "opl_timeout": 1,
    "reread_settle": 1.0,
    "reread_poll": 0.5,
}

STOCK = [
    "a bulk order deed",
    "small bulk order",
    "amount to make: 20",
    "platemail gorget: 3",
    "All items must be exceptional.",
    "All items must be made with dull copper ingots.",
]


class ParseDeedTest(unittest.TestCase):
    def test_reads_the_stock_tooltip(self):
        request, why = parse_deed(STOCK, CONFIG)

        self.assertIsNone(why)
        self.assertEqual(request, {
            "large": False,
            "entries": [("platemail gorget", 3)],
            "item": "platemail gorget",
            "done": 3,
            "total": 20,
            "exceptional": True,
            "material": "dull copper",
        })

    def test_no_material_line_is_iron(self):
        request, _why = parse_deed(STOCK[:4], CONFIG)

        self.assertEqual(request["material"], "iron")
        self.assertFalse(request["exceptional"])

    def test_strips_the_article(self):
        request, _why = parse_deed(["amount to make: 10", "a dagger: 0"], CONFIG)

        self.assertEqual(request["item"], "dagger")

    def test_a_large_deed_lists_its_entries(self):
        request, why = parse_deed(["a bulk order deed", "large bulk order", "amount to make: 15",
                                   "ringmail gloves: 15", "ringmail leggings: 0",
                                   "ringmail sleeves: 0", "All items must be exceptional."],
                                  CONFIG)

        self.assertIsNone(why)
        self.assertTrue(request["large"])
        self.assertEqual(request["entries"], [("ringmail gloves", 15), ("ringmail leggings", 0),
                                              ("ringmail sleeves", 0)])
        self.assertNotIn("item", request)

    def test_two_item_lines_are_a_large_deed(self):
        request, _why = parse_deed(["amount to make: 15", "bascinet: 0", "close helmet: 0"], CONFIG)

        self.assertTrue(request["large"])

    def test_entry_request_is_a_small_of_the_large(self):
        large, _why = parse_deed(["large bulk order", "amount to make: 15", "bascinet: 0",
                                  "All items must be made with valorite ingots."], CONFIG)
        small = entry_request(large, "bascinet", 4)

        self.assertEqual(small["item"], "bascinet")
        self.assertEqual(small["done"], 4)
        self.assertEqual(small["total"], 15)
        self.assertEqual(small["material"], "valorite")
        self.assertFalse(small["large"])

    def test_a_wood_material_loses_its_own_noun(self):
        request, _why = parse_deed(["amount to make: 10", "wooden shield: 0",
                                    "All items must be made with oak boards."], CONFIG)

        self.assertEqual(request["material"], "oak")

    def test_no_amount_is_unreadable(self):
        request, why = parse_deed(["a bulk order deed", "platemail gorget: 3"], CONFIG)

        self.assertIsNone(request)
        self.assertIn("platemail gorget: 3", why)

    def test_no_material_line_and_no_plain_is_none(self):
        config = dict(CONFIG)
        config["plain"] = None
        request, _why = parse_deed(["amount to make: 10", "greater heal potion: 0"], config)

        self.assertIsNone(request["material"])


class TradeOfTest(unittest.TestCase):
    TRADES = [("smith", {"recipes": {"axe": (81, 2), "dagger": (61, 82)}}),
              ("alchemy", {"recipes": {"greater heal potion": (1, 82)}}),
              ("carpentry", {"recipes": {"wooden shield": (81, 2), "keg": (41, 382)}})]

    def test_the_trade_whose_recipes_make_every_entry(self):
        self.assertEqual(trade_of({"entries": [("axe", 0), ("dagger", 2)]}, self.TRADES), "smith")
        self.assertEqual(trade_of({"entries": [("greater heal potion", 0)]}, self.TRADES),
                         "alchemy")
        self.assertEqual(trade_of({"entries": [("wooden shield", 0), ("keg", 1)]}, self.TRADES),
                         "carpentry")

    def test_no_trade_makes_it(self):
        self.assertIsNone(trade_of({"entries": [("axe", 0), ("greater heal potion", 0)]},
                                   self.TRADES))
        self.assertIsNone(trade_of({"entries": [("tessen", 0)]}, self.TRADES))


class DeedTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.deed = Deed(0x40001234, CONFIG, self.said.append)

    def test_read_refuses_an_empty_tooltip(self):
        request, why = self.deed.read()

        self.assertIsNone(request)
        self.assertIn("could not read", why)

    def test_read_keeps_the_request(self):
        self.api.props[0x40001234] = "\n".join(STOCK)
        request, _why = self.deed.read()

        self.assertEqual(request["done"], 3)
        self.assertEqual(self.deed.describe(),
                         "platemail gorget x20, 3 done, exceptional, dull copper")

    def test_describe_a_large_deed(self):
        self.api.props[0x40001234] = "large bulk order\namount to make: 15\nbascinet: 15\nhelmet: 0"
        self.deed.read()

        self.assertEqual(self.deed.describe(),
                         "large deed x15: bascinet (15 done), helmet (0 done), iron")

    def test_describe_says_no_material(self):
        self.deed._config = dict(CONFIG, plain=None)
        self.api.props[0x40001234] = "amount to make: 10\ngreater heal potion: 2"
        self.deed.read()

        self.assertEqual(self.deed.describe(), "greater heal potion x10, 2 done, no material")

    def test_a_tooltip_that_caught_up_is_taken(self):
        self.api.props[0x40001234] = "\n".join(STOCK)
        self.deed.read()
        self.api.props[0x40001234] = "\n".join(STOCK).replace("gorget: 3", "gorget: 4")

        self.assertEqual(self.deed.settle_after_combine(4), 4)
        self.assertEqual(self.said, [])

    def test_a_tooltip_that_is_behind_never_lowers_the_count(self):
        self.api.props[0x40001234] = "\n".join(STOCK)
        self.deed.read()

        self.assertEqual(self.deed.settle_after_combine(4), 4)
        self.assertEqual(self.deed.request["done"], 4)
        self.assertEqual(len([line for line in self.said if "behind" in line]), 1)

    def test_a_tooltip_that_went_blank_is_a_miss(self):
        self.api.props[0x40001234] = "\n".join(STOCK)
        self.deed.read()
        self.api.props[0x40001234] = ""

        self.assertEqual(self.deed.settle_after_combine(4), 4)
