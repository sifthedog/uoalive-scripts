import unittest

from test_support.uo import install, item
from uo.tool import Tool


class ToolTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.tool = Tool("pickaxe", ["pickaxe"], [], ["onehanded"], None, 3, 1.0, 0.25, self.said.append)

    def _hold(self, held):
        self.api.layers["onehanded"] = held
        self.api.items[held.Serial] = held

    def test_matches_by_name(self):
        self.assertTrue(self.tool.is_tool(item(name="a sturdy pickaxe")))

    def test_does_not_match_something_else(self):
        self.assertFalse(self.tool.is_tool(item(name="a hatchet")))

    def test_matches_by_the_graphic_it_learned(self):
        self.tool.learn(item(graphic=0x0E86, name="a pickaxe"))

        self.assertTrue(self.tool.is_tool(item(graphic=0x0E86, name="")))

    def test_learns_the_graphic_once(self):
        self.tool.learn(item(graphic=0x0E86))
        self.tool.learn(item(graphic=0x1234))

        self.assertFalse(self.tool.is_tool(item(graphic=0x1234, name="")))
        self.assertEqual(len(self.said), 1)

    def test_finds_one_in_the_pack(self):
        self.api.hold(item(serial=7, name="a pickaxe"))

        self.assertEqual(self.tool.find().Serial, 7)

    def test_says_what_the_pack_holds_when_there_is_none(self):
        self.api.hold(item(serial=7, graphic=0x1BDD, name="a log"))

        self.assertIsNone(self.tool.find())
        self.assertEqual(self.said,
                         ["no pickaxe found - nothing named pickaxe in the pack. "
                          "It holds: 0x1bdd"])

    def test_says_so_once_per_dry_stretch(self):
        self.tool.find()
        self.tool.find()

        self.assertEqual(len(self.said), 1)

    def test_opens_a_bag_the_client_has_not_looked_into(self):
        bag = item(serial=5, graphic=0x0E76, name="a bag", is_container=True)
        self.api.hold(bag)
        real = self.api.UseObject

        def use(serial):
            real(serial)
            self.api.hold(item(serial=9, name="a pickaxe"))

        self.api.UseObject = use

        self.assertEqual(self.tool.find().Serial, 9)
        self.assertEqual(self.api.used, [5])
        self.assertEqual(self.said[0], "opening 1 bag(s) to look inside for a pickaxe")

    def test_opens_a_bag_once_and_leaves_an_opened_one_alone(self):
        self.api.hold(item(serial=5, name="a bag", is_container=True),
                      item(serial=6, name="a pouch", is_container=True, opened=True))

        self.tool.find()
        self.tool.find()

        self.assertEqual(self.api.used, [5])

    def test_reaches_into_the_spare_bag(self):
        spare = Tool("pickaxe", ["pickaxe"], [], ["onehanded"], 0x50000000, 3, 1.0, 0.25, self.said.append)
        self.api.containers[0x50000000] = [item(serial=9, name="a pickaxe")]

        self.assertEqual(spare.find().Serial, 9)

    def test_a_broken_tool_still_on_the_layer_is_not_held(self):
        broken = item(serial=7, name="a pickaxe")
        self.api.layers["onehanded"] = broken

        self.assertFalse(self.tool.still_holding())

    def test_one_in_hand_and_in_the_world_is_held(self):
        self._hold(item(serial=7, name="a pickaxe"))

        self.assertTrue(self.tool.still_holding())

    def test_equipping_what_is_already_held_costs_nothing(self):
        self._hold(item(serial=7, name="a pickaxe"))

        self.assertTrue(self.tool.equip())
        self.assertEqual(self.api.equipped, [])

    def test_equips_from_the_pack(self):
        spare = item(serial=7, name="a pickaxe")
        self.api.hold(spare)

        def equip(serial):
            self.api.equipped.append(serial)
            self.api.layers["onehanded"] = spare

        self.api.EquipItem = equip

        self.assertTrue(self.tool.equip())

    def test_gives_up_after_the_attempts(self):
        self.api.hold(item(serial=7, name="a pickaxe"))

        self.assertFalse(self.tool.equip())
        self.assertEqual(len(self.api.equipped), 3)
        self.assertEqual(self.said[-1], "could not get the pickaxe 0x7 onto the hand")

    def test_reads_either_hand_when_told_to(self):
        axe = item(serial=7, name="an axe")
        self.api.layers["twohanded"] = axe
        both = Tool("axe", ["axe"], ["pickaxe"], ["twohanded", "onehanded"], None, 3, 1.0, 0.25,
                    self.said.append)

        self.assertIs(both.held(), axe)

    def test_two_tools_do_not_share_the_learned_graphic(self):
        self.tool.learn(item(graphic=0x0E86))
        other = Tool("pickaxe", ["pickaxe"], [], ["onehanded"], None, 3, 1.0, 0.25, self.said.append)

        self.assertFalse(other.is_tool(item(graphic=0x0E86, name="")))
