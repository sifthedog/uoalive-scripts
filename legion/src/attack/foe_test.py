import unittest

from attack.foe import nearest_foe
from test_support.uo import FakeMobile, install, mobile

WORDS = ["(tame)", "(summoned)"]


class Unasked(FakeMobile):
    def NameAndProps(self, force=False, timeout=None):
        raise AssertionError("tooltip asked of %s" % self.Name)


class NearestFoeTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def see(self, **fields):
        fields.setdefault("notoriety", self.api.Notoriety.Gray)
        self.api.see(mobile(**fields))

    def foe(self):
        found = nearest_foe(10, WORDS, 1.0)

        return None if found is None else found.Name

    def test_the_closest_gray_mobile_wins_over_a_farther_one_seen_first(self):
        self.see(serial=0x20, name="far orc", distance=8)
        self.see(serial=0x21, name="near orc", distance=2)

        self.assertEqual(self.foe(), "near orc")

    def test_a_blue_mobile_is_never_a_foe(self):
        self.see(serial=0x20, name="a healer", distance=1, notoriety=self.api.Notoriety.Innocent)

        self.assertIsNone(self.foe())

    def test_your_own_pet_a_dead_mobile_and_yourself_are_passed_over(self):
        self.see(serial=self.api.Player.Serial, name="me", distance=0)
        self.see(serial=0x20, name="my horse", distance=1, is_renamable=True)
        self.see(serial=0x21, name="a corpse", distance=2, is_dead=True)
        self.see(serial=0x22, name="an ettin", distance=3)

        self.assertEqual(self.foe(), "an ettin")

    def test_a_tooltip_naming_an_owner_is_skipped_for_the_next_one_out(self):
        self.see(serial=0x20, name="a drake", distance=1, props="a drake\n(tame)")
        self.see(serial=0x21, name="an energy vortex", distance=2, props="An Energy Vortex\n(SUMMONED)")
        self.see(serial=0x22, name="a lich", distance=3, props="a lich")

        self.assertEqual(self.foe(), "a lich")

    def test_the_tooltip_is_asked_only_of_the_ones_in_line(self):
        self.api.see(Unasked(serial=0x20, name="a healer", distance=1,
                             notoriety=self.api.Notoriety.Innocent))
        self.api.see(Unasked(serial=0x21, name="a corpse", distance=2, is_dead=True,
                             notoriety=self.api.Notoriety.Gray))
        self.see(serial=0x22, name="a lich", distance=3)
        self.api.see(Unasked(serial=0x23, name="a dragon", distance=4,
                             notoriety=self.api.Notoriety.Gray))

        self.assertEqual(self.foe(), "a lich")

    def test_out_of_range_is_out(self):
        self.see(serial=0x20, name="an orc", distance=11)

        self.assertIsNone(self.foe())

    def test_an_empty_scan_returns_none(self):
        self.assertIsNone(self.foe())
