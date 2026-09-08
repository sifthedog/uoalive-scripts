import unittest

from bod.combine import DeedCombiner
from bod.config import COMBINE_TEXT, LARGE_COMBINE_TEXT
from test_support.uo import install, item

DEED = 0x40001234
BAG = 0x40002222
GORGET = 0x40005678
SECOND = 0x40005679

CONFIG = {
    "combine_button": 4,
    "gump_text": ["bulk order", "Combine this deed"],
    "gump_timeout": 1.0,
    "gump_poll": 0.2,
    "target_timeout": 1.0,
    "combine_timeout": 1.0,
    "combine_poll": 0.2,
    "max_reports": 2,
    "text_limit": 160,
    "tail_seconds": 20.0,
    "tail_lines": 4,
}


class FakeDeed(object):
    serial = DEED


class FakeItems(object):
    def __init__(self, api):
        self._api = api

    def serials(self):
        return set(held.Serial for held in self._api.containers.get(self._api.Backpack, []))


class DeedCombinerTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.api.hold(item(serial=GORGET))
        self.api.opens[DEED] = 99
        self.api.gump_text = ["A bulk order", "Combine this deed with the item requested."]
        self.api.has_target = True
        self.combiner = DeedCombiner(FakeDeed(), FakeItems(self.api), COMBINE_TEXT, CONFIG,
                                     self.said.append)

    # The journal is cleared before the press, so the shard's answer has to land on the target
    def answer(self, wording):
        self.api.Target = lambda serial: (self.api.targeted.append((serial,)),
                                          self.api.hear(wording))

    def test_opens_the_deed_presses_combine_and_targets_the_bag(self):
        self.api.Target = lambda serial: (self.api.targeted.append((serial,)),
                                          self.api.take(GORGET))

        self.assertEqual(self.combiner.combine(BAG, [GORGET]), ("combined", [GORGET]))
        self.assertEqual(self.api.used, [DEED])
        self.assertEqual(self.api.replies, [(4, 99)])
        self.assertEqual(self.api.targeted, [(BAG,)])
        self.assertEqual(self.api.closed_gumps, 1)

    def test_counts_the_pieces_that_left(self):
        self.api.hold(item(serial=GORGET), item(serial=SECOND))
        self.api.Target = lambda serial: self.api.take(GORGET)
        self.answer("The item must be exceptional.")
        self.api.Target = lambda serial: (self.api.take(GORGET),
                                          self.api.hear("The item must be exceptional."))

        self.assertEqual(self.combiner.combine(BAG, [GORGET, SECOND]), ("combined", [GORGET]))

    def test_a_gump_already_up_is_left_alone_and_not_pressed(self):
        self.api.gump = 88
        self.api.Target = lambda serial: self.api.take(GORGET)

        self.combiner.combine(BAG, [GORGET])

        self.assertEqual(self.api.replies, [(4, 99)])
        self.assertEqual(self.api.closed_gumps, 1)

    def test_a_deed_gump_without_the_combine_button_is_not_pressed(self):
        self.api.gump_buttons[99] = set([0, 1])

        self.assertEqual(self.combiner.combine(BAG, [GORGET]), ("noGump", []))
        self.assertEqual(self.api.replies, [])
        self.assertTrue(any("has no button 4" in line for line in self.said))

    def test_no_cursor(self):
        self.api.has_target = False

        self.assertEqual(self.combiner.combine(BAG, [GORGET]), ("noCursor", []))
        self.assertEqual(self.api.targeted, [])
        self.assertTrue(any("no cursor" in line for line in self.said))

    def test_no_gump(self):
        del self.api.opens[DEED]

        self.assertEqual(self.combiner.combine(BAG, [GORGET]), ("noGump", []))
        self.assertEqual(self.api.replies, [])

    def test_each_refusal_reads_as_its_outcome(self):
        for wording, outcome in [
            ("The maximum amount of requested items have already been combined to this deed.",
             "full"),
            ("The item is not in the request.", "notRequested"),
            ("The item is not made from the requested resource.", "wrongMaterial"),
            ("The item must be exceptional.", "notExceptional"),
            ("You must have the item in your backpack to target it.", "notInPack"),
        ]:
            self.api.gump = 0
            self.api.has_target = True
            self.answer(wording)

            self.assertEqual(self.combiner.combine(BAG, [GORGET]), (outcome, []), wording)

    def test_a_success_wording_with_nothing_gone_waits_it_out(self):
        self.answer("The item has been combined with the deed.")

        self.assertEqual(self.combiner.combine(BAG, [GORGET]), (None, []))

    def test_nothing_readable_is_none_and_said(self):
        self.assertEqual(self.combiner.combine(BAG, [GORGET]), (None, []))
        self.assertTrue(any("nothing readable" in line for line in self.said))


class LargeCombineTest(unittest.TestCase):
    """The large deed's gump with the small deed as the target, and no item book."""

    def setUp(self):
        self.api = install()
        self.said = []
        self.api.hold(item(serial=GORGET, name="a bulk order deed"))
        self.api.opens[DEED] = 99
        self.api.gump_text = ["A large bulk order", "Combine this deed with the item requested."]
        self.api.has_target = True
        config = dict(CONFIG)
        config["combine_button"] = 2
        self.combiner = DeedCombiner(FakeDeed(), None, LARGE_COMBINE_TEXT, config,
                                     self.said.append)

    def test_the_small_deed_leaving_the_pack_is_the_proof(self):
        self.api.Target = lambda serial: (self.api.targeted.append((serial,)),
                                          self.api.take(GORGET))

        self.assertEqual(self.combiner.combine(GORGET, [GORGET]), ("combined", [GORGET]))
        self.assertEqual(self.api.replies, [(2, 99)])
        self.assertEqual(self.api.targeted, [(GORGET,)])

    def test_the_refusals(self):
        for wording, outcome in [
            ("The order to combine with is not completed.", "notComplete"),
            ("That is not a bulk order for this large request.", "wrongDeed"),
            ("Both orders must be of exceptional quality.", "exceptionalMismatch"),
            ("Both orders must use the same resource type.", "materialMismatch"),
            ("The two orders have different requested amounts and cannot be combined.",
             "amountMismatch"),
        ]:
            self.api.gump = 0
            self.api.has_target = True
            self.api.Target = lambda serial, wording=wording: self.api.hear(wording)

            self.assertEqual(self.combiner.combine(GORGET, [GORGET]), (outcome, []), wording)
