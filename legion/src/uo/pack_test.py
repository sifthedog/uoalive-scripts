import unittest

from test_support.uo import install, item
from uo.pack import amount_of, counts_by_graphic, diff_counts, hue_of, pack_contents, pack_top_level


class PackReadsTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_an_empty_pack_reads_as_a_list(self):
        self.assertEqual(pack_contents(), [])
        self.assertEqual(pack_top_level(), [])

    def test_a_none_from_the_client_reads_as_empty(self):
        self.api.containers[self.api.Backpack] = None

        self.assertEqual(pack_contents(), [])

    def test_reads_what_the_pack_holds(self):
        self.api.hold(item(serial=1, graphic=0x19B9))

        self.assertEqual(len(pack_top_level()), 1)


class AmountAndHueTest(unittest.TestCase):
    def test_an_empty_stack_counts_as_none(self):
        self.assertEqual(amount_of(item(amount=0)), 0)

    def test_a_stack_the_client_has_not_reported_counts_as_one(self):
        self.assertEqual(amount_of(item(amount=None)), 1)

    def test_reads_the_stack_size(self):
        self.assertEqual(amount_of(item(amount=42)), 42)

    def test_a_missing_hue_reads_as_zero(self):
        self.assertEqual(hue_of(item(hue=None)), 0)


class CountsByGraphicTest(unittest.TestCase):
    def test_sums_a_stack_per_graphic_and_hue(self):
        counts = counts_by_graphic([item(graphic=0x19B9, hue=0x096D, amount=10),
                                    item(graphic=0x19B9, hue=0x096D, amount=5)])

        self.assertEqual(counts, {(0x19B9, 0x096D): 15})

    def test_keeps_two_hues_of_one_graphic_apart(self):
        counts = counts_by_graphic([item(graphic=0x19B9, hue=0x096D, amount=10),
                                    item(graphic=0x19B9, hue=0x0000, amount=4)])

        self.assertEqual(counts, {(0x19B9, 0x096D): 10, (0x19B9, 0x0000): 4})


class DiffCountsTest(unittest.TestCase):
    def test_reports_what_arrived_and_what_left(self):
        gained, lost = diff_counts({("ore", 0): 10}, {("ore", 0): 4, ("ingot", 0): 6})

        self.assertEqual(gained, {("ingot", 0): 6})
        self.assertEqual(lost, {("ore", 0): 6})

    def test_an_unchanged_count_is_neither(self):
        gained, lost = diff_counts({("ore", 0): 10}, {("ore", 0): 10})

        self.assertEqual((gained, lost), ({}, {}))
