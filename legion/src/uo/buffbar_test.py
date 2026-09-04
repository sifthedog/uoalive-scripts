import unittest

from test_support.uo import install
from uo.buffbar import BuffBar


class Buff(object):
    def __init__(self, kind, title):
        self.Type = kind
        self.Title = title


class BuffBarTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.buffs = []
        self.api.ActiveBuffs = lambda: self.buffs
        self.said = []
        self.bar = BuffBar(self.said.append)

    def test_an_empty_bar_stands_nothing(self):
        self.assertFalse(self.bar.standing("ConsecrateWeapon"))

    def test_matches_on_the_buff_type(self):
        self.buffs = [Buff("ConsecrateWeapon", "")]

        self.assertTrue(self.bar.standing("ConsecrateWeapon"))

    def test_falls_back_to_the_localized_title(self):
        self.buffs = [Buff("SomethingElse", "Consecrate Weapon")]

        self.assertTrue(self.bar.standing("ConsecrateWeapon", "Consecrate Weapon"))

    def test_a_row_with_no_buff_stands_nothing(self):
        self.buffs = [Buff("ConsecrateWeapon", "Consecrate Weapon")]

        self.assertFalse(self.bar.standing(None, "Consecrate Weapon"))

    def test_dumps_the_bar_once(self):
        self.buffs = [Buff("ConsecrateWeapon", "Consecrate Weapon")]
        self.bar.standing("ConsecrateWeapon")
        self.bar.standing("ConsecrateWeapon")

        self.assertEqual(self.said, ["buff bar: ConsecrateWeapon/Consecrate Weapon"])

    def test_says_nothing_for_an_empty_bar(self):
        self.bar.standing("ConsecrateWeapon")

        self.assertEqual(self.said, [])

    def test_two_bars_do_not_share_the_dump_latch(self):
        self.buffs = [Buff("ConsecrateWeapon", "")]
        self.bar.standing("ConsecrateWeapon")

        other = []
        BuffBar(other.append).standing("ConsecrateWeapon")

        self.assertEqual(len(other), 1)
