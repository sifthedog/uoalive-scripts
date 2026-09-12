import unittest

from test_support.uo import install, item, skill
from uo.gathered import Gathered
from uo.guards import skill_capped
from uo.record import AttemptLog
from uo.skill import SkillReader

ORE = 0x19B9
ORE_SMALL = 0x19B7
INGOT = 0x1BF2
LOGS = 0x1BDD
BOARDS = 0x1BD7


class Sink(object):
    def __init__(self):
        self.lines = []

    def append(self, path, line):
        self.lines.append(line)


class GatheredTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.skills["Mining"] = skill(61.3, 100.0)
        self.sink = Sink()
        self.said = []

    def build(self, path="attempts.jsonl", metals=None, skill_name="Mining", config=None):
        table = metals or {}
        graphics = set([ORE, ORE_SMALL])
        recorder = AttemptLog(path, "Kaldor", 0x40012345, skill_name, self.said.append,
                              append=self.sink.append)
        settings = {
            "is_resource": lambda held: held.Graphic in graphics,
            "name_of": lambda held: "%s ore" % table[held.Serial] if held.Serial in table else None,
            "resource_graphics": graphics,
            "noun": "ore",
            "tool": "pickaxe",
            "converter_tool": "fire beetle",
            "made": "smelted",
        }
        settings.update(config or {})

        return Gathered(recorder, SkillReader(skill_name), skill_capped(skill_name), settings,
                        self.said.append)


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
        gathered = self.build(metals={1: "shadow iron"})
        self.api.hold(item(serial=1, graphic=ORE, hue=2406, amount=10))
        before = gathered.before_swing()

        self.api.hold(item(serial=1, graphic=ORE, hue=2406, amount=12),
                      item(serial=2, graphic=ORE_SMALL, hue=0, amount=1))
        gathered.after_swing(61.3, "dug", before)
        gathered.close()

        self.assertIn('"used":"pickaxe"', self.sink.lines[0])
        self.assertIn('"outcome":"dug"', self.sink.lines[0])
        self.assertIn('"gained":[{"name":"ore","graphic":"0x19b7","hue":0,"qty":1},'
                      '{"name":"shadow iron ore","graphic":"0x19b9","hue":2406,"qty":2}]',
                      self.sink.lines[0])

    def test_a_pile_the_caller_cannot_name_takes_its_own_name(self):
        self.api.skills["Lumberjacking"] = skill(40.0, 100.0)
        logs = set([LOGS])
        gathered = self.build(skill_name="Lumberjacking", config={
            "is_resource": lambda held: held.Graphic in logs,
            "name_of": lambda held: None,
            "resource_graphics": logs,
            "noun": "logs",
            "tool": "axe",
        })
        before = gathered.before_swing()

        self.api.hold(item(serial=1, graphic=LOGS, hue=0x0483, amount=10, name="Oak Logs"))
        gathered.after_swing(40.0, "chopped", before)
        gathered.close()

        self.assertIn('"used":"axe"', self.sink.lines[0])
        self.assertIn('"gained":[{"name":"Oak Logs","graphic":"0x1bdd","hue":1155,"qty":10}]',
                      self.sink.lines[0])

    def test_a_merge_that_changes_the_art_is_not_a_gain(self):
        gathered = self.build()
        self.api.hold(item(serial=1, graphic=ORE_SMALL, hue=0, amount=1),
                      item(serial=2, graphic=ORE_SMALL, hue=0, amount=1))
        before = gathered.before_swing()

        self.api.hold(item(serial=1, graphic=ORE, hue=0, amount=2))
        gathered.after_swing(61.3, "dug", before)
        gathered.close()

        self.assertNotIn('"gained"', self.sink.lines[0])

    def test_a_failed_swing_is_a_row_with_nothing_gained(self):
        gathered = self.build()
        before = gathered.before_swing()

        gathered.after_swing(61.3, "failed", before)
        gathered.close()

        self.assertIn('"outcome":"failed"', self.sink.lines[0])
        self.assertNotIn('"gained"', self.sink.lines[0])

    def test_the_row_ends_where_the_next_swing_starts(self):
        gathered = self.build()
        before = gathered.before_swing()

        gathered.after_swing(61.3, "failed", before)
        self.api.skills["Mining"] = skill(61.4, 100.0)
        self.assertEqual(gathered.read(), 61.4)
        self.assertEqual(self.sink.lines, [])

        gathered.after_swing(61.4, "dug", gathered.before_swing())

        self.assertIn('"from":61.3,"to":61.4', self.sink.lines[0])

    def test_close_writes_the_row_still_in_the_air(self):
        gathered = self.build()
        before = gathered.before_swing()

        gathered.after_swing(61.3, "failed", before)
        self.api.skills["Mining"] = skill(61.4, 100.0)
        gathered.close()

        self.assertIn('"from":61.3,"to":61.4', self.sink.lines[0])


class ConvertTest(GatheredTest):
    def test_a_smelt_row_carries_the_ore_spent_and_the_ingots_made(self):
        gathered = self.build(metals={1: "shadow iron"})
        self.api.hold(item(serial=1, graphic=ORE, hue=2406, amount=10))
        gathered.before_swing()

        gathered.before_convert()
        self.api.hold(item(serial=3, graphic=INGOT, hue=2406, amount=5, name="ingots"))
        gathered.after_convert({(INGOT, 2406): 5}, {(ORE, 2406): 10})
        gathered.close()

        self.assertIn('"used":"fire beetle"', self.sink.lines[0])
        self.assertIn('"outcome":"smelted"', self.sink.lines[0])
        self.assertIn('"consumed":[{"name":"shadow iron ore","graphic":"0x19b9","hue":2406,"qty":10}]',
                      self.sink.lines[0])
        self.assertIn('"gained":[{"name":"ingots","graphic":"0x1bf2","hue":2406,"qty":5}]',
                      self.sink.lines[0])

    def test_boards_made_from_logs_read_as_converted(self):
        self.api.skills["Lumberjacking"] = skill(40.0, 100.0)
        logs = set([LOGS])
        gathered = self.build(skill_name="Lumberjacking", config={
            "is_resource": lambda held: held.Graphic in logs,
            "name_of": lambda held: None,
            "resource_graphics": logs,
            "noun": "logs",
            "converter_tool": "axe",
            "made": "converted",
        })
        gathered.before_convert()

        self.api.hold(item(serial=3, graphic=BOARDS, hue=0, amount=10, name="boards"))
        gathered.after_convert({(BOARDS, 0): 10}, {(LOGS, 0): 10})
        gathered.close()

        self.assertIn('"used":"axe"', self.sink.lines[0])
        self.assertIn('"outcome":"converted"', self.sink.lines[0])
        self.assertIn('"consumed":[{"name":"logs","graphic":"0x1bdd","hue":0,"qty":10}]',
                      self.sink.lines[0])
        self.assertIn('"gained":[{"name":"boards","graphic":"0x1bd7","hue":0,"qty":10}]',
                      self.sink.lines[0])

    def test_ore_burned_away_with_no_ingot_is_a_failure(self):
        gathered = self.build()
        gathered.before_convert()

        gathered.after_convert({(ORE_SMALL, 0): 5}, {(ORE, 0): 10})
        gathered.close()

        self.assertIn('"outcome":"failed"', self.sink.lines[0])
        self.assertIn('"consumed":[{"name":"ore","graphic":"0x19b9","hue":0,"qty":5}]',
                      self.sink.lines[0])
        self.assertNotIn('"gained"', self.sink.lines[0])

    def test_a_product_the_pack_does_not_name_is_named_by_its_art(self):
        gathered = self.build()
        gathered.before_convert()

        gathered.after_convert({(INGOT, 0): 5}, {(ORE, 0): 10})
        gathered.close()

        self.assertIn('"gained":[{"name":"0x1bf2","graphic":"0x1bf2","hue":0,"qty":5}]',
                      self.sink.lines[0])

    def test_a_conversion_that_was_not_announced_writes_nothing(self):
        gathered = self.build()

        gathered.after_convert({(INGOT, 0): 5}, {(ORE, 0): 10})
        gathered.close()

        self.assertEqual(self.sink.lines, [])

    def test_a_conversion_at_the_cap_writes_nothing(self):
        self.api.skills["Mining"] = skill(100.0, 100.0)
        gathered = self.build()
        gathered.before_convert()

        gathered.after_convert({(INGOT, 0): 5}, {(ORE, 0): 10})
        gathered.close()

        self.assertEqual(self.sink.lines, [])
