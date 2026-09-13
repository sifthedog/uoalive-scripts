import unittest

from test_support.uo import install
from uo.journal import journal_report, journal_tail
from uo.log import make_log


class JournalTailTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_an_empty_journal_reads_as_nothing(self):
        self.assertEqual(journal_tail(20.0, 4), [])

    def test_returns_the_last_few_lines(self):
        self.api.hear("one", "two", "three", "four", "five")

        self.assertEqual(journal_tail(20.0, 3), ["three", "four", "five"])

    def test_leaves_out_skill_gains(self):
        self.api.hear("You fail", "Your skill in Meditation has increased by 0.1.  It is now 30.1.",
                      "Your dexterity has changed by 1.  It is now 17.")

        self.assertEqual(journal_tail(20.0, 4), ["You fail"])

    def test_leaves_out_blank_lines(self):
        self.api.hear("one", "   ", "two")

        self.assertEqual(journal_tail(20.0, 4), ["one", "two"])

    # Or a report of an unreadable outcome quotes the last report of an unreadable outcome, and
    # every one after it quotes the one before
    def test_leaves_out_what_the_script_said_itself(self):
        log = make_log("chiv")

        log("outcome unreadable - carrying on")
        self.api.hear(*self.api.messages)
        self.api.hear("Dark Elf: Augus Luminos")

        self.assertEqual(journal_tail(20.0, 4, log.stamp), ["Dark Elf: Augus Luminos"])

    def test_a_stamp_only_filters_its_own_script(self):
        mining_log = make_log("mining")
        mining_log("dug")
        self.api.hear(*self.api.messages)
        self.api.hear("Dark Elf: Augus Luminos")

        self.assertEqual(journal_tail(20.0, 4, make_log("lumberjack").stamp),
                          ["mining: dug", "Dark Elf: Augus Luminos"])

    def test_a_client_that_throws_reads_as_nothing(self):
        def throw(seconds=None):
            raise Exception("no journal here")

        self.api.GetJournalEntries = throw

        self.assertEqual(journal_tail(20.0, 4), [])


class JournalReportTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_a_chatty_npc_does_not_evict_the_shard(self):
        self.api.hear("You create the item")
        self.api.overhear("Lurid Halo the Necromancer", "Hey buddy. Looking for work?",
                          "I want to make you an offer", "Know yourself", "a wren")

        self.assertEqual(journal_report(20.0, 4), ["You create the item"])

    def test_names_who_spoke_when_only_chatter_is_left(self):
        self.api.overhear("Lurid Halo the Necromancer", "Hey buddy. Looking for work?")

        self.assertEqual(journal_report(20.0, 4),
                         ["Lurid Halo the Necromancer: Hey buddy. Looking for work?"])

    def test_your_own_character_counts_as_the_shard(self):
        self.api.overhear("tester", "You have been ambushed!")
        self.api.overhear("Doggess Sif", "woof")

        self.assertEqual(journal_report(20.0, 4), ["You have been ambushed!"])

    def test_no_limit_writes_the_lot(self):
        self.api.hear("one", "two", "three", "four", "five")

        self.assertEqual(len(journal_report(20.0, None)), 5)

    def test_the_notes_file_keeps_every_speaker(self):
        self.api.hear("You create the item")
        self.api.overhear("Lurid Halo the Necromancer", "Hey buddy. Looking for work?")

        self.assertEqual(journal_report(20.0, None, None, False),
                         ["You create the item",
                          "Lurid Halo the Necromancer: Hey buddy. Looking for work?"])
