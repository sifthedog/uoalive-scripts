import unittest

from test_support.uo import install
from uo.gainpath import COMMAND, read_gain_path


class ReadGainPathTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []

    def test_sends_the_command(self):
        read_gain_path(1.0, 0.5, self.said.append)

        self.assertEqual(self.api.said_aloud, [COMMAND])

    def test_names_the_path_the_client_reports(self):
        self.api.hear("Your skill gain path is Modern. This character's gains are unaffected.")

        self.assertEqual(read_gain_path(1.0, 0.5, self.said.append), "Modern")
        self.assertEqual(self.api.paused, 0.0)

    def test_reads_legacy(self):
        self.api.hear("Your skill gain path is Legacy.")

        self.assertEqual(read_gain_path(1.0, 0.5, self.said.append), "Legacy")

    def test_reads_perilous(self):
        self.api.hear("Your skill gain path is Perilous.")

        self.assertEqual(read_gain_path(1.0, 0.5, self.said.append), "Perilous")

    def test_ignores_unrelated_journal_lines(self):
        self.api.hear("You dig some iron ore")

        self.assertIsNone(read_gain_path(1.0, 0.5, self.said.append))

    def test_times_out_to_none_and_says_so_once(self):
        result = read_gain_path(1.0, 0.5, self.said.append)

        self.assertIsNone(result)
        self.assertEqual(self.said, ["no skill gain path reported - recording without one"])
        self.assertAlmostEqual(self.api.paused, 1.0)
