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

    def test_a_preferred_art_wins_over_the_first_found(self):
        tool = CraftTool("smith's tool", set([HAMMER, 0x0FBB]), [], self.said.append,
                         prefer=set([0x0FBB]))
        self.api.hold(item(serial=5, graphic=HAMMER), item(serial=6, graphic=0x0FBB))

        self.assertEqual(tool.serial(), 6)

    def test_every_tool_is_listed(self):
        self.api.hold(item(serial=5, graphic=HAMMER), item(serial=6, graphic=HAMMER),
                      item(serial=8, graphic=0x1439, name="war hammer"))

        self.assertEqual(self.tool.serials(), [5, 6])

    def test_a_war_hammer_is_not_a_tool(self):
        self.api.hold(item(serial=8, graphic=0x1439, name="war hammer"))

        self.assertIsNone(self.tool.serial())

    def test_find_opens_the_bags_in_the_pack_before_giving_up(self):
        bag = item(serial=9, graphic=0x0E76, name="a bag", is_container=True)
        self.api.hold(bag)

        def use(serial):
            self.api.used.append(serial)
            self.api.hold(bag, item(serial=5, graphic=HAMMER))

        self.api.UseObject = use

        self.assertEqual(self.tool.find(0.5, 0.1), 5)
        self.assertEqual(self.api.used, [9])
        self.assertIn("opening 1 bag(s)", self.said[-1])

    def test_find_opens_each_bag_once_and_skips_books(self):
        self.api.hold(item(serial=9, graphic=0x0E76, name="a bag", is_container=True),
                      item(serial=10, graphic=0x0EFA, name="spellbook", is_container=True))

        self.assertIsNone(self.tool.find(0.2, 0.1))
        self.assertIsNone(self.tool.find(0.2, 0.1))
        self.assertEqual(self.api.used, [9])
