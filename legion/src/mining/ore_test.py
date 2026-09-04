import unittest

from mining.ore import OrePack
from test_support.uo import install, item

GRAPHICS = set([0x19B7, 0x19BA])


class OrePackTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.graphics = set(GRAPHICS)
        self.ore = OrePack(self.graphics, "ore", 2, self.said.append)

    def test_matches_a_known_art(self):
        self.assertTrue(self.ore.is_ore(item(graphic=0x19B7)))

    def test_learns_an_art_from_a_whole_word_in_the_name(self):
        self.assertTrue(self.ore.is_ore(item(graphic=0x1234, name="iron ore")))
        self.assertIn(0x1234, self.graphics)

    def test_does_not_learn_from_a_word_it_is_only_inside(self):
        self.assertFalse(self.ore.is_ore(item(graphic=0x1234, name="sycamore board")))
        self.assertNotIn(0x1234, self.graphics)

    def test_says_what_it_learned_once(self):
        self.ore.is_ore(item(graphic=0x1234, name="iron ore"))
        self.ore.is_ore(item(graphic=0x1234, name="iron ore"))

        self.assertEqual(len(self.said), 1)

    def test_totals_every_pile_whatever_the_hue(self):
        self.api.hold(item(serial=1, graphic=0x19B7, hue=0, amount=10),
                      item(serial=2, graphic=0x19B7, hue=0x096D, amount=5))

        self.assertEqual(self.ore.total(), 15)

    def test_lists_the_biggest_pile_first(self):
        self.api.hold(item(serial=1, graphic=0x19B7, amount=5),
                      item(serial=2, graphic=0x19B7, amount=40))

        self.assertEqual([pile.Serial for pile in self.ore.piles()], [2, 1])

    def test_an_unreported_stack_is_worth_one_attempt(self):
        self.assertTrue(self.ore.big_enough(item(amount=0)))

    def test_a_stack_of_one_is_not_worth_smelting(self):
        self.assertFalse(self.ore.big_enough(item(amount=1)))

    def test_skips_a_written_off_hue(self):
        self.api.hold(item(serial=1, graphic=0x19B7, hue=0x096D, amount=10))

        self.assertIsNone(self.ore.next_ore(set([0x096D])))

    def test_says_why_a_pile_was_skipped(self):
        self.assertEqual(self.ore.describe_skipped(item(hue=5, amount=9), set([5])),
                         "9 hue 5 (written off)")
        self.assertEqual(self.ore.describe_skipped(item(hue=5, amount=1), set()),
                         "1 hue 5 (too small)")

    def test_reads_the_delivery_before_it_waits(self):
        self.api.hold(item(serial=1, graphic=0x19B7, amount=10))

        self.assertTrue(self.ore.wait_for_ore(0, 2.0, 0.15))
        self.assertEqual(self.api.paused, 0.0)

    def test_gives_up_when_nothing_arrives(self):
        self.assertFalse(self.ore.wait_for_ore(0, 1.5, 0.5))
        self.assertAlmostEqual(self.api.paused, 1.5)
