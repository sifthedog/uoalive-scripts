import unittest

from test_support.uo import install
from uo.journal import journal_tail


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

    def test_a_client_that_throws_reads_as_nothing(self):
        def throw(seconds=None):
            raise Exception("no journal here")

        self.api.GetJournalEntries = throw

        self.assertEqual(journal_tail(20.0, 4), [])
