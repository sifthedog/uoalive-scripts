import unittest

from potionkeg.config import HOOPS, KEG, LID, POTION_KEG, STAGES, STAVES, TAP
from potionkeg.plan import next_stage


def row(stage):
    return stage[0]


class NextStageTest(unittest.TestCase):
    def test_an_empty_pack_starts_with_the_staves(self):
        self.assertEqual(row(next_stage(STAGES, {})), STAVES)

    def test_parts_already_in_the_pack_are_skipped(self):
        self.assertEqual(row(next_stage(STAGES, {STAVES: 3, LID: 2})), HOOPS)
        self.assertEqual(row(next_stage(STAGES, {STAVES: 3, LID: 2, HOOPS: 1})), TAP)
        self.assertEqual(row(next_stage(STAGES, {STAVES: 3, LID: 2, HOOPS: 1, TAP: 1})), KEG)

    def test_two_of_three_staves_asks_for_one_more(self):
        self.assertEqual(row(next_stage(STAGES, {STAVES: 2, LID: 2, HOOPS: 1, TAP: 1})), STAVES)

    def test_a_keg_in_the_pack_wants_no_more_staves_or_hoops(self):
        self.assertEqual(row(next_stage(STAGES, {KEG: 1, LID: 1, TAP: 1})), POTION_KEG)

    def test_a_keg_in_the_pack_still_wants_the_lid_the_potion_keg_takes(self):
        self.assertEqual(row(next_stage(STAGES, {KEG: 1, TAP: 1})), LID)
