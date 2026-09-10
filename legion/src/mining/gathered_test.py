import unittest

from mining.gathered import Gathered
from mining.ore import OrePack
from test_support.uo import install, item, skill
from uo.guards import skill_capped
from uo.record import AttemptLog
from uo.skill import SkillReader

ORE = 0x19B9
ORE_SMALL = 0x19B7
INGOT = 0x1BF2


class Sink(object):
    def __init__(self):
        self.lines = []

    def append(self, path, line):
        self.lines.append(line)


class Book(object):
    def __init__(self, table=None):
        self._table = table or {}

    def of(self, item):
        return self._table.get(item.Serial)


class GatheredTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.skills["Mining"] = skill(61.3, 100.0)
        self.sink = Sink()
        self.said = []

    def build(self, path="attempts.jsonl", book=None):
        graphics = set([ORE, ORE_SMALL])
        recorder = AttemptLog(path, "Kaldor", 0x40012345, "Mining", self.said.append,
                              append=self.sink.append)
        return Gathered(recorder, SkillReader("Mining"), OrePack(graphics, "ore", 2, self.said.append),
                        book or Book(), skill_capped("Mining"), graphics, self.said.append)


class RecordingTest(GatheredTest):
    def test_records_below_the_cap(self):
        self.assertTrue(self.build().recording())

    def test_records_nothing_at_the_cap(self):
        self.api.skills["Mining"] = skill(100.0, 100.0)

        self.assertFalse(self.build().recording())
        self.assertIsNone(self.build().before_swing())

    def test_records_nothing_without_a_path(self):
        self.assertFalse(self.build("").recording())


class SwingTest(GatheredTest):
    def test_a_dug_row_carries_the_ore_per_hue_named_off_the_tooltip(self):
        gathered = self.build(book=Book({1: "shadow iron"}))
        self.api.hold(item(serial=1, graphic=ORE, hue=2406, amount=10))
        before = gathered.before_swing()

        self.api.hold(item(serial=1, graphic=ORE, hue=2406, amount=12),
                      item(serial=2, graphic=ORE_SMALL, hue=0, amount=1))
        gathered.after_swing(61.3, "dug", before)
        gathered.settle()

        self.assertIn('"used":"pickaxe"', self.sink.lines[0])
        self.assertIn('"outcome":"dug"', self.sink.lines[0])
        self.assertIn('"gained":[{"name":"ore","graphic":"0x19b7","hue":0,"qty":1},'
                      '{"name":"shadow iron ore","graphic":"0x19b9","hue":2406,"qty":2}]',
                      self.sink.lines[0])

    def test_a_merge_that_changes_the_art_is_not_a_gain(self):
        gathered = self.build()
        self.api.hold(item(serial=1, graphic=ORE_SMALL, hue=0, amount=1),
                      item(serial=2, graphic=ORE_SMALL, hue=0, amount=1))
        before = gathered.before_swing()

        self.api.hold(item(serial=1, graphic=ORE, hue=0, amount=2))
        gathered.after_swing(61.3, "dug", before)
        gathered.settle()

        self.assertNotIn('"gained"', self.sink.lines[0])

    def test_a_failed_swing_is_a_row_with_nothing_gained(self):
        gathered = self.build()
        before = gathered.before_swing()

        gathered.after_swing(61.3, "failed", before)
        gathered.settle()

        self.assertIn('"outcome":"failed"', self.sink.lines[0])
        self.assertNotIn('"gained"', self.sink.lines[0])

    def test_the_gain_lands_in_the_row_at_the_next_settle(self):
        gathered = self.build()
        before = gathered.before_swing()

        gathered.after_swing(61.3, "failed", before)
        self.api.skills["Mining"] = skill(61.4, 100.0)
        self.assertEqual(gathered.settle(), 61.4)

        self.assertIn('"from":61.3,"to":61.4', self.sink.lines[0])


class SmeltTest(GatheredTest):
    def test_a_smelt_row_carries_the_ore_spent_and_the_ingots_made(self):
        gathered = self.build(book=Book({1: "shadow iron"}))
        self.api.hold(item(serial=1, graphic=ORE, hue=2406, amount=10))
        gathered.before_swing()

        gathered.before_smelt()
        self.api.hold(item(serial=3, graphic=INGOT, hue=2406, amount=5, name="ingots"))
        gathered.after_smelt({(INGOT, 2406): 5}, {(ORE, 2406): 10})
        gathered.settle()

        self.assertIn('"used":"fire beetle"', self.sink.lines[0])
        self.assertIn('"outcome":"smelted"', self.sink.lines[0])
        self.assertIn('"consumed":[{"name":"shadow iron ore","graphic":"0x19b9","hue":2406,"qty":10}]',
                      self.sink.lines[0])
        self.assertIn('"gained":[{"name":"ingots","graphic":"0x1bf2","hue":2406,"qty":5}]',
                      self.sink.lines[0])

    def test_ore_burned_away_with_no_ingot_is_a_failure(self):
        gathered = self.build()
        gathered.before_smelt()

        gathered.after_smelt({(ORE_SMALL, 0): 5}, {(ORE, 0): 10})
        gathered.settle()

        self.assertIn('"outcome":"failed"', self.sink.lines[0])
        self.assertIn('"consumed":[{"name":"ore","graphic":"0x19b9","hue":0,"qty":5}]',
                      self.sink.lines[0])
        self.assertNotIn('"gained"', self.sink.lines[0])

    def test_an_ingot_the_pack_does_not_name_is_named_by_its_art(self):
        gathered = self.build()
        gathered.before_smelt()

        gathered.after_smelt({(INGOT, 0): 5}, {(ORE, 0): 10})
        gathered.settle()

        self.assertIn('"gained":[{"name":"0x1bf2","graphic":"0x1bf2","hue":0,"qty":5}]',
                      self.sink.lines[0])

    def test_a_smelt_that_was_not_announced_writes_nothing(self):
        gathered = self.build()

        gathered.after_smelt({(INGOT, 0): 5}, {(ORE, 0): 10})
        gathered.settle()

        self.assertEqual(self.sink.lines, [])

    def test_a_smelt_at_the_cap_writes_nothing(self):
        self.api.skills["Mining"] = skill(100.0, 100.0)
        gathered = self.build()
        gathered.before_smelt()

        gathered.after_smelt({(INGOT, 0): 5}, {(ORE, 0): 10})
        gathered.settle()

        self.assertEqual(self.sink.lines, [])
