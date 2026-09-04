import unittest

import uo.clock
from buffs.schedule import due, make_table, retire, set_aside, settled, spent

KEEP = [{"spell": "Consecrate Weapon"}, {"spell": "Divine Fury"}]


class Frozen(object):
    def __init__(self, at):
        self.at = at

    def time(self):
        return self.at


class ScheduleTest(unittest.TestCase):
    def setUp(self):
        self.clock = Frozen(1000.0)
        self.saved = uo.clock.time
        uo.clock.time = self.clock
        self.table = make_table(KEEP)

    def tearDown(self):
        uo.clock.time = self.saved

    def test_a_fresh_entry_is_due(self):
        self.assertTrue(all(due(item) for item in self.table))

    def test_setting_aside_holds_it_off(self):
        set_aside(self.table[0], 60.0)

        self.assertFalse(due(self.table[0]))

    def test_it_comes_back_once_the_hold_expires(self):
        set_aside(self.table[0], 60.0)
        self.clock.at += 60.0

        self.assertTrue(due(self.table[0]))

    def test_setting_aside_forgives_the_misses(self):
        self.table[0]["misses"] = 4
        set_aside(self.table[0], 60.0)

        self.assertEqual(self.table[0]["misses"], 0)

    def test_a_retired_entry_is_never_due(self):
        retire(self.table[0], "out of tithing points")

        self.assertFalse(due(self.table[0]))

    def test_spent_needs_every_entry_retired(self):
        retire(self.table[0], "why")

        self.assertFalse(spent(self.table))

        retire(self.table[1], "why")

        self.assertTrue(spent(self.table))

    def test_settled_counts_a_retired_entry_as_settled(self):
        retire(self.table[0], "why")

        self.assertTrue(settled(self.table, lambda entry: entry is self.table[1]["entry"]))

    def test_settled_is_false_while_one_is_down(self):
        self.assertFalse(settled(self.table, lambda entry: False))

    def test_two_tables_do_not_share_an_entry(self):
        set_aside(self.table[0], 60.0)

        self.assertTrue(due(make_table(KEEP)[0]))
