import unittest

from bod.config import TRADES


class TradesTest(unittest.TestCase):
    """A missing key is a KeyError in the client, half way through a deed, not one at import."""

    def test_every_trade_carries_the_same_keys(self):
        wanted = set(TRADES[0][1])

        for name, trade in TRADES:
            self.assertEqual(set(trade), wanted, name)

    def test_only_a_trade_with_no_material_page_has_no_plain(self):
        for name, trade in TRADES:
            self.assertEqual(trade["plain"] is None, trade["material_order"] == [], name)

    def test_every_material_the_page_offers_is_one_the_pack_is_read_for(self):
        for name, trade in TRADES:
            if trade["plain"] is None:
                continue

            self.assertIn(trade["plain"], trade["materials"], name)

            for material in trade["material_order"]:
                self.assertIn(material, trade["materials"], name)

    def test_a_number_cost_needs_a_noun_to_be_counted_under(self):
        for name, trade in TRADES:
            numbers = [item for item, cost in trade["costs"].items() if not isinstance(cost, dict)]

            if len(numbers) > 0:
                self.assertIsNotNone(trade["stock_noun"], name)

    # stock_counts keys the trade's own pool as '<material> <noun>' before it ever reaches kind_of,
    # so a kind by that name would be counted twice over and never on its own
    def test_no_kind_is_named_the_way_the_pool_is(self):
        for name, trade in TRADES:
            if trade["stock_noun"] is None:
                continue

            for kind in trade["kinds"]:
                self.assertFalse(kind.endswith(" " + trade["stock_noun"]), "%s: %s" % (name, kind))

    # trade_of takes the first trade making every entry, so an overlap would make a deed ambiguous
    def test_no_two_trades_make_an_item_of_the_same_name(self):
        for index, (name, trade) in enumerate(TRADES):
            for other_name, other in TRADES[index + 1:]:
                shared = set(trade["recipes"]) & set(other["recipes"])

                self.assertEqual(shared, set(), "%s and %s" % (name, other_name))

    def test_failed_is_read_before_made_and_throttled_last(self):
        for name, trade in TRADES:
            names = [bucket for bucket, _phrases in trade["outcome_text"]]

            self.assertLess(names.index("failed"), names.index("made"), name)
            self.assertEqual(names[-1], "throttled", name)
