import unittest

from assembly.config import (ASSEMBLIES, CLOCK, CLOCK_FRAME, CLOCK_PARTS, HOOPS, KEG, LID,
                             POTION_KEG, STAVES, TAP)
from assembly.plan import next_stage


def stages_for(key):
    return [row[2] for row in ASSEMBLIES if row[0] == key][0]


KEG_STAGES = stages_for("keg")
POTION_KEG_STAGES = stages_for("potion keg")
CLOCK_STAGES = stages_for("clock")


def row(stage):
    return stage[0]


class NextStageTest(unittest.TestCase):
    def test_an_empty_pack_starts_with_the_staves(self):
        self.assertEqual(row(next_stage(POTION_KEG_STAGES, {})), STAVES)

    def test_parts_already_in_the_pack_are_skipped(self):
        self.assertEqual(row(next_stage(POTION_KEG_STAGES, {STAVES: 3, LID: 2})), HOOPS)
        self.assertEqual(row(next_stage(POTION_KEG_STAGES, {STAVES: 3, LID: 2, HOOPS: 1})), TAP)
        self.assertEqual(row(next_stage(POTION_KEG_STAGES,
                                        {STAVES: 3, LID: 2, HOOPS: 1, TAP: 1})), KEG)

    def test_two_of_three_staves_asks_for_one_more(self):
        self.assertEqual(row(next_stage(POTION_KEG_STAGES,
                                        {STAVES: 2, LID: 2, HOOPS: 1, TAP: 1})), STAVES)

    def test_a_keg_in_the_pack_wants_no_more_staves_or_hoops(self):
        self.assertEqual(row(next_stage(POTION_KEG_STAGES, {KEG: 1, LID: 1, TAP: 1})), POTION_KEG)

    def test_a_keg_in_the_pack_still_wants_the_lid_the_potion_keg_takes(self):
        self.assertEqual(row(next_stage(POTION_KEG_STAGES, {KEG: 1, TAP: 1})), LID)


class ProductInStockTest(unittest.TestCase):
    def test_a_made_keg_does_not_answer_the_next_keg(self):
        self.assertEqual(row(next_stage(KEG_STAGES, {KEG: 1})), STAVES)

    def test_a_made_keg_leaves_the_parts_beside_it_alone(self):
        self.assertEqual(row(next_stage(KEG_STAGES, {KEG: 1, STAVES: 3, LID: 1})), HOOPS)

    def test_a_made_clock_does_not_answer_the_next_clock(self):
        self.assertEqual(row(next_stage(CLOCK_STAGES, {CLOCK: 2})), CLOCK_PARTS)


class ClockTest(unittest.TestCase):
    def test_an_empty_pack_starts_with_the_clock_parts(self):
        self.assertEqual(row(next_stage(CLOCK_STAGES, {})), CLOCK_PARTS)

    def test_clock_parts_in_the_pack_leave_only_the_frame(self):
        self.assertEqual(row(next_stage(CLOCK_STAGES, {CLOCK_PARTS: 1})), CLOCK_FRAME)

    def test_a_frame_and_parts_press_the_clock(self):
        self.assertEqual(row(next_stage(CLOCK_STAGES, {CLOCK_PARTS: 1, CLOCK_FRAME: 1})), CLOCK)

    def test_a_frame_alone_still_wants_the_parts(self):
        self.assertEqual(row(next_stage(CLOCK_STAGES, {CLOCK_FRAME: 1})), CLOCK_PARTS)
