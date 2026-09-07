import unittest

from bod.config import ARTICLES, DEED_TEXT, PLAIN_MATERIAL
from bod.deed import Deed, parse_deed
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

    def test_a_large_deed_is_refused(self):
        request, why = parse_deed(["large bulk order", "amount to make: 15"], CONFIG)

        self.assertIsNone(request)
        self.assertIn("large", why)

    def test_two_item_lines_are_a_large_deed(self):
        request, why = parse_deed(["amount to make: 15", "bascinet: 0", "close helmet: 0"], CONFIG)

        self.assertIsNone(request)
        self.assertIn("large", why)

    def test_no_amount_is_unreadable(self):
        request, why = parse_deed(["a bulk order deed", "platemail gorget: 3"], CONFIG)

        self.assertIsNone(request)
        self.assertIn("platemail gorget: 3", why)


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
