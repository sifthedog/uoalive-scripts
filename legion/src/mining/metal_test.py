import unittest

from mining.metal import MetalBook
from test_support.uo import install, item


def book(log, metals=None):
    return MetalBook({
        "metals": metals if metals is not None else set(["iron", "valorite"]),
        "plain": "iron",
        "line_extra": " '-",
        "not_metal_words": set(["blessed", "weight", "ore"]),
        "asks": 3,
        "misses": 3,
        "opl_timeout": 1,
    }, log)


class MetalBookTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.book = book(self.said.append)

    def _tooltip(self, serial, text):
        self.api.props[serial] = text

    def test_an_unanswered_tooltip_names_no_metal(self):
        self.assertIsNone(self.book.of(item(serial=1, name="ore")))

    def test_reads_a_metal_it_knows(self):
        self._tooltip(1, "ore\nValorite")

        self.assertEqual(self.book.of(item(serial=1, name="ore")), "valorite")

    def test_learns_a_metal_it_has_not_heard_of(self):
        self._tooltip(1, "ore\nMythril")

        self.assertEqual(self.book.of(item(serial=1, name="ore")), "mythril")
        self.assertIn("'Mythril' is a metal too, remembering it", self.said)

    def test_a_tooltip_with_no_metal_line_is_plain_iron(self):
        self._tooltip(1, "ore\nWeight: 12 stones")

        self.assertEqual(self.book.of(item(serial=1, name="ore")), "iron")

    def test_gives_up_on_tooltips_after_enough_misses(self):
        for serial in range(1, 4):
            self.book.of(item(serial=serial, name="ore"))

        self.assertIn("tooltips are not naming the metal here, so a pair has to be refused "
                      "to be split", self.said)

    def test_a_pile_is_pending_only_once_a_tooltip_has_answered(self):
        self.assertFalse(self.book.pending(item(serial=1, name="ore")))

        self._tooltip(2, "ore\nValorite")
        self.book.of(item(serial=2, name="ore"))

        self.book.start_pass()
        self.assertTrue(self.book.pending(item(serial=3, name="ore")))

    def test_a_doubted_metal_stops_being_an_answer(self):
        self._tooltip(1, "ore\nValorite")
        self.book.of(item(serial=1, name="ore"))
        self.book.doubt("valorite")

        self.assertIsNone(self.book.of(item(serial=1, name="ore")))

    def test_doubt_is_said_once(self):
        self.book.doubt("valorite")
        self.book.doubt("valorite")

        self.assertEqual(len(self.said), 1)

    def test_forgets_a_serial_the_shard_has_reissued(self):
        self._tooltip(1, "ore\nValorite")
        pile = item(serial=1, name="ore")
        self.book.of(pile)
        self.book.forget_missing([])

        self._tooltip(1, "ore\nAgapite")

        self.assertEqual(self.book.of(pile), "agapite")

    def test_two_books_do_not_share_what_was_doubted(self):
        self.book.doubt("valorite")
        self._tooltip(1, "ore\nValorite")

        self.assertEqual(book(self.said.append).of(item(serial=1, name="ore")), "valorite")
