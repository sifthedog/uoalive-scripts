import unittest

from bod.combine import DeedCombiner
from bod.config import COMBINE_TEXT
from test_support.uo import install, item

DEED = 0x40001234
GORGET = 0x40005678

CONFIG = {
    "combine_button": 2,
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

    def test_opens_the_deed_presses_combine_and_targets_the_item(self):
        self.answer("The item has been combined with the deed.")

        self.assertEqual(self.combiner.combine(GORGET), "combined")
        self.assertEqual(self.api.used, [DEED])
        self.assertEqual(self.api.replies, [(2, 99)])
        self.assertEqual(self.api.targeted, [(GORGET,)])
        self.assertEqual(self.api.closed_gumps, 1)

    def test_the_item_leaving_the_pack_is_proof_enough(self):
        self.api.Target = lambda serial: self.api.take(serial)

        self.assertEqual(self.combiner.combine(GORGET), "combined")

    def test_a_gump_in_the_way_is_closed_first(self):
        self.api.gump = 88
        self.answer("The item has been combined with the deed.")

        self.combiner.combine(GORGET)

        self.assertEqual(self.api.closed_gumps, 2)

    def test_no_cursor(self):
        self.api.has_target = False

        self.assertEqual(self.combiner.combine(GORGET), "noCursor")
        self.assertEqual(self.api.targeted, [])
        self.assertTrue(any("no cursor" in line for line in self.said))

    def test_no_gump(self):
        del self.api.opens[DEED]

        self.assertEqual(self.combiner.combine(GORGET), "noGump")
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

            self.assertEqual(self.combiner.combine(GORGET), outcome, wording)

    def test_nothing_readable_is_none_and_said(self):
        self.assertIsNone(self.combiner.combine(GORGET))
        self.assertTrue(any("nothing readable" in line for line in self.said))
