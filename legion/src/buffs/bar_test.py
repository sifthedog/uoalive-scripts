import unittest

from buffs.bar import BuffBar, armed
from test_support.uo import install

ENTRY = {"buff": "ConsecrateWeapon", "title": "Consecrate Weapon"}


class Buff(object):
    def __init__(self, kind, title):
        self.Type = kind
        self.Title = title


class BuffBarTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.api.ActiveBuffs = lambda: self.buffs
        self.buffs = []
        self.bar = BuffBar(self.said.append)

    def test_an_empty_bar_stands_nothing(self):
        self.assertFalse(self.bar.standing(ENTRY))

    def test_matches_on_the_buff_type(self):
        self.buffs = [Buff("ConsecrateWeapon", "")]

        self.assertTrue(self.bar.standing(ENTRY))

    def test_falls_back_to_the_localized_title(self):
        self.buffs = [Buff("SomethingElse", "Consecrate Weapon")]

        self.assertTrue(self.bar.standing(ENTRY))

    def test_dumps_the_bar_once(self):
        self.buffs = [Buff("ConsecrateWeapon", "Consecrate Weapon")]
        self.bar.standing(ENTRY)
        self.bar.standing(ENTRY)

        self.assertEqual(self.said, ["buff bar: ConsecrateWeapon/Consecrate Weapon"])

    def test_says_nothing_for_an_empty_bar(self):
        self.bar.standing(ENTRY)

        self.assertEqual(self.said, [])

    def test_two_bars_do_not_share_the_dump_latch(self):
        self.buffs = [Buff("ConsecrateWeapon", "")]
        self.bar.standing(ENTRY)

        other = []
        BuffBar(other.append).standing(ENTRY)

        self.assertEqual(len(other), 1)


class ArmedTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.layers = {}
        self.api.FindLayer = lambda layer, serial=None: self.layers.get(layer)

    def test_bare_hands_are_not_armed(self):
        self.assertFalse(armed())

    def test_a_one_handed_weapon_counts(self):
        self.layers["onehanded"] = object()

        self.assertTrue(armed())

    def test_a_two_handed_weapon_counts(self):
        self.layers["twohanded"] = object()

        self.assertTrue(armed())
