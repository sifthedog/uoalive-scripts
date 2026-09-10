import unittest

from test_support.uo import install, item
from uo.hands import Hands, describe_item


class HandsTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.hands = Hands(["onehanded", "twohanded"], 2, 1.0, 0.5, self.said.append)
        self.sword = item(serial=0x40000123, name="a longsword")

    def _arm(self):
        self.api.layers["onehanded"] = self.sword

        return self.hands.remember()

    # The fake's layers are static, so the world answering a move is played by the move itself
    def _moves_land(self):
        def move(serial, container, amount=-1):
            self.api.moved.append((serial, container, amount))
            self.api.layers["onehanded"] = None

        def equip(serial):
            self.api.equipped.append(serial)
            self.api.layers["onehanded"] = self.sword

        self.api.MoveItem = move
        self.api.EquipItem = equip

    def test_remembers_nothing_from_empty_hands(self):
        self.assertEqual(self.hands.remember(), [])
        self.assertFalse(self.hands.remembered())

    def test_remembers_what_is_held(self):
        self.assertEqual([held.Serial for held in self._arm()], [0x40000123])
        self.assertTrue(self.hands.remembered())

    def test_stow_and_restore_are_no_ops_with_nothing_remembered(self):
        self.assertTrue(self.hands.stow())
        self.assertTrue(self.hands.restore())
        self.assertEqual(self.api.moved, [])
        self.assertEqual(self.api.equipped, [])

    def test_stows_the_weapon_into_the_pack(self):
        self._arm()
        self._moves_land()

        self.assertTrue(self.hands.stow())
        self.assertEqual(self.api.moved, [(0x40000123, self.api.Backpack, -1)])

    def test_stow_cancels_a_live_cursor_first(self):
        self._arm()
        self._moves_land()
        self.api.has_target = True

        self.hands.stow()

        self.assertEqual(self.api.cancelled_targets, 1)

    def test_stow_gives_up_after_its_attempts_and_says_so(self):
        self._arm()

        self.assertFalse(self.hands.stow())
        self.assertEqual(len(self.api.moved), 2)
        self.assertEqual(self.said, ["could not put 0x40000123 in the pack"])

    def test_stow_leaves_a_weapon_already_in_the_pack_alone(self):
        self._arm()
        self._moves_land()
        self.hands.stow()
        self.api.moved = []

        self.assertTrue(self.hands.stow())
        self.assertEqual(self.api.moved, [])

    def test_restores_by_serial(self):
        self._arm()
        self._moves_land()
        self.hands.stow()

        self.assertTrue(self.hands.restore())
        self.assertEqual(self.api.equipped, [0x40000123])

    def test_restore_gives_up_after_its_attempts_and_says_so(self):
        self._arm()
        self.api.layers["onehanded"] = None

        self.assertFalse(self.hands.restore())
        self.assertEqual(len(self.api.equipped), 2)
        self.assertEqual(self.said, ["could not draw 0x40000123 again"])

    def test_restore_is_a_no_op_while_the_weapon_is_still_held(self):
        self._arm()

        self.assertTrue(self.hands.restore())
        self.assertEqual(self.api.equipped, [])


class DescribeItemTest(unittest.TestCase):
    def test_names_the_serial_and_the_name(self):
        self.assertEqual(describe_item(item(serial=0x40000123, name="a longsword")),
                         "0x40000123 ('a longsword')")

    def test_says_unnamed_for_a_tooltip_that_has_not_arrived(self):
        self.assertEqual(describe_item(item(serial=0x40000123, name="")), "0x40000123 ('unnamed')")

    def test_says_nothing_for_none(self):
        self.assertEqual(describe_item(None), "nothing")
