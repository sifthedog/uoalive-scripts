import unittest

from test_support.uo import install
from uo.log import make_log


class MakeLogTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_prefixes_every_line(self):
        make_log("mining")("found a vein")

        self.assertEqual(self.api.messages, ["mining: found a vein"])

    def test_two_scripts_do_not_share_a_prefix(self):
        make_log("mining")("dug")
        make_log("lumberjack")("chopped")

        self.assertEqual(self.api.messages, ["mining: dug", "lumberjack: chopped"])

    def test_the_stamp_is_lowercase_and_its_own(self):
        first = make_log("Mining")
        second = make_log("Lumberjack")

        self.assertEqual(first.stamp, "mining: ")
        self.assertEqual(second.stamp, "lumberjack: ")
