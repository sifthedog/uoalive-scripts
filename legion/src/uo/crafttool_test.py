import unittest

from test_support.uo import install, item
from uo.crafttool import CraftTool

HAMMER = 0x13E3


class CraftToolTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.tool = CraftTool("smith's tool", set([HAMMER]), ["tongs"], self.said.append)

    def test_nothing_in_the_pack_is_none(self):
        self.assertIsNone(self.tool.serial())

    def test_found_by_graphic(self):
        self.api.hold(item(serial=5, graphic=HAMMER))

        self.assertEqual(self.tool.serial(), 5)

    def test_a_name_match_learns_the_art(self):
        self.api.hold(item(serial=6, graphic=0x0FBB, name="tongs"))

        self.assertEqual(self.tool.serial(), 6)
        self.assertTrue(self.tool.is_tool(item(serial=7, graphic=0x0FBB)))
        self.assertEqual(len(self.said), 1)

    def test_a_war_hammer_is_not_a_tool(self):
        self.api.hold(item(serial=8, graphic=0x1439, name="war hammer"))

        self.assertIsNone(self.tool.serial())
