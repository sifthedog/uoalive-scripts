import unittest

from mining.combine import Combiner, hue_key, hue_tells_apart, serial_key
from mining.ore import OrePack
from test_support.uo import install, item

GRAPHIC = 0x19B7
DIFFERENT = ["You cannot combine ores of different metals"]


class Book(object):
    """A metal book that answers from a table, so the pairing is what the test is about."""

    def __init__(self, table=None, pending=None):
        self._table = table or {}
        self._pending = pending or set()
        self.doubted = []
        self.passes = 0
        self.forgotten = []

    def of(self, item):
        return self._table.get(item.Serial)

    def pending(self, item):
        return item.Serial in self._pending

    def start_pass(self):
        self.passes += 1

    def doubt(self, metal):
        self.doubted.append(metal)

    def forget_missing(self, piles):
        self.forgotten.append([pile.Serial for pile in piles])


class KeysTest(unittest.TestCase):
    def test_a_pair_keys_the_same_either_way_round(self):
        a = item(serial=1)
        b = item(serial=2)

        self.assertEqual(serial_key(a, b), serial_key(b, a))

    def test_hues_key_the_same_either_way_round(self):
        self.assertEqual(hue_key(item(hue=3), item(hue=9)), hue_key(item(hue=9), item(hue=3)))

    def test_hue_zero_never_tells_two_piles_apart(self):
        self.assertFalse(hue_tells_apart(item(hue=0), item(hue=9)))

    def test_two_real_hues_tell_them_apart(self):
        self.assertTrue(hue_tells_apart(item(hue=3), item(hue=9)))


class CombinerTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []

    def build(self, book):
        ore = OrePack(set([GRAPHIC]), "ore", 2, self.said.append)

        return Combiner(ore, book, {
            "attempts": 12,
            "delay": 0.7,
            "timeout": 2.0,
            "poll": 0.2,
            "target_timeout": 2.0,
            "different_text": DIFFERENT,
            "throttled_text": ["You must wait"],
        }, self.said.append), ore

    def _piles(self, *piles):
        self.api.hold(*piles)

    def test_one_pile_is_never_paired(self):
        combiner, _ore = self.build(Book())
        self._piles(item(serial=1, graphic=GRAPHIC, hue=0, amount=10))
        combiner.group()

        self.assertEqual(self.api.used, [])

    def test_two_piles_of_one_metal_are_combined(self):
        combiner, _ore = self.build(Book({1: "iron", 2: "iron"}))
        self._piles(item(serial=1, graphic=GRAPHIC, amount=40),
                    item(serial=2, graphic=GRAPHIC, amount=5))
        self.api.has_target = True
        combiner.group()

        self.assertEqual(self.api.used[0], 2)
        self.assertEqual(self.api.targeted[0], (1,))

    def test_two_metals_are_never_paired(self):
        combiner, _ore = self.build(Book({1: "iron", 2: "valorite"}))
        self._piles(item(serial=1, graphic=GRAPHIC, amount=40),
                    item(serial=2, graphic=GRAPHIC, amount=5))
        combiner.group()

        self.assertEqual(self.api.used, [])

    def test_a_pile_still_awaiting_its_tooltip_is_paired_with_nothing(self):
        combiner, _ore = self.build(Book({1: "iron"}, pending=set([2])))
        self._piles(item(serial=1, graphic=GRAPHIC, amount=40),
                    item(serial=2, graphic=GRAPHIC, amount=5))
        combiner.group()

        self.assertEqual(self.api.used, [])

    def test_a_refusal_doubts_the_metal_both_piles_read_as(self):
        book = Book({1: "iron", 2: "iron"})
        combiner, _ore = self.build(book)
        self._piles(item(serial=1, graphic=GRAPHIC, amount=40),
                    item(serial=2, graphic=GRAPHIC, amount=5))
        self.api.has_target = True
        self.api.Pause = lambda seconds: self.api.journal.append(DIFFERENT[0])
        combiner.group()

        self.assertEqual(book.doubted, ["iron"])

    def test_a_refused_pair_is_not_tried_again(self):
        combiner, _ore = self.build(Book({1: "iron", 2: "iron"}))
        self._piles(item(serial=1, graphic=GRAPHIC, amount=40),
                    item(serial=2, graphic=GRAPHIC, amount=5))
        self.api.has_target = True
        self.api.Pause = lambda seconds: self.api.journal.append(DIFFERENT[0])
        combiner.group()

        self.assertEqual(len(self.api.used), 1)

    def test_no_cursor_leaves_the_pair_alone_for_this_call(self):
        combiner, _ore = self.build(Book({1: "iron", 2: "iron"}))
        self._piles(item(serial=1, graphic=GRAPHIC, amount=40),
                    item(serial=2, graphic=GRAPHIC, amount=5))
        combiner.group()

        self.assertEqual(len(self.api.used), 1)
        self.assertTrue(any("no target cursor" in line for line in self.said))

    def test_a_throttle_leaves_the_two_of_them_paired(self):
        combiner, _ore = self.build(Book({1: "iron", 2: "iron"}))
        self._piles(item(serial=1, graphic=GRAPHIC, amount=40),
                    item(serial=2, graphic=GRAPHIC, amount=5))
        self.api.has_target = True
        self.api.Pause = lambda seconds: self.api.journal.append("You must wait")
        combiner.group()

        self.assertIn("the shard says wait, leaving the two of them paired", self.said)

    def test_falls_back_to_hue_when_no_tooltip_named_the_metal(self):
        combiner, _ore = self.build(Book())
        self._piles(item(serial=1, graphic=GRAPHIC, hue=0x096D, amount=40),
                    item(serial=2, graphic=GRAPHIC, hue=0x096D, amount=5))
        self.api.has_target = True
        combiner.group()

        self.assertEqual(self.api.used[0], 2)

    def test_starts_a_metal_pass_and_forgets_reissued_serials(self):
        book = Book()
        combiner, _ore = self.build(book)
        self._piles(item(serial=1, graphic=GRAPHIC, amount=10))
        combiner.group()

        self.assertEqual(book.passes, 1)
        self.assertEqual(book.forgotten, [[1]])
