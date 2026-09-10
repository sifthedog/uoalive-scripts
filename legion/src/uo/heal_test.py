import unittest

from test_support.uo import install, item
from uo.heal import Bandager

TEXT = [
    ("healed", ["You finish applying the bandages"]),
    ("noBandages", ["You do not have any bandages"]),
    ("saving", ["The world is saving"]),
]


class Saves(object):
    def __init__(self):
        self.waited = 0

    def wait_out(self):
        self.waited += 1


class BandagerTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.saves = Saves()
        self.bandager = Bandager(0x0E21, TEXT, 1.0, 0.5, 0.5, 3,
                                 lambda: self.api.Player.Hits >= 50, self.saves, self.said.append)

    # A use raises the cursor and the shard answers after it, which a static fake cannot play out
    def _hurt(self, *shard_says):
        self.api.Player.Hits = 20
        self.api.hold(item(serial=0x40000777, graphic=0x0E21, name="clean bandage"))

        def use(serial):
            self.api.used.append(serial)
            self.api.has_target = True
            self.api.hear(*shard_says)

        self.api.UseObject = use

    def test_is_a_no_op_when_the_character_is_fine(self):
        self.assertTrue(self.bandager.mend())
        self.assertEqual(self.api.used, [])
        self.assertEqual(self.said, [])

    def test_runs_out_on_an_empty_pack_and_says_so_once(self):
        self.api.Player.Hits = 20

        self.assertFalse(self.bandager.mend())
        self.assertFalse(self.bandager.mend())
        self.assertEqual(self.bandager.empty(), "no bandages left in the pack")
        self.assertEqual(self.said, ["20/100 hits, bandaging", "no bandages left in the pack"])
        self.assertEqual(self.api.used, [])

    def test_uses_the_bandage_on_itself(self):
        self._hurt("You finish applying the bandages")

        self.bandager.mend()

        self.assertEqual(self.api.used, [0x40000777, 0x40000777, 0x40000777])
        self.assertEqual(self.api.targeted[0], ("self",))

    def test_the_hits_rising_is_what_ends_the_bandaging(self):
        self._hurt("You finish applying the bandages")

        original = self.api.TargetSelf

        def heal():
            original()
            self.api.Player.Hits = 80

        self.api.TargetSelf = heal

        self.assertTrue(self.bandager.mend())
        self.assertEqual(self.api.used, [0x40000777])
        self.assertEqual(self.said[-1], "healed to 80/100")

    def test_the_shard_saying_there_are_none_retires_it(self):
        self._hurt("You do not have any bandages")

        self.assertFalse(self.bandager.mend())
        self.assertEqual(self.api.used, [0x40000777])
        self.assertEqual(self.bandager.empty(), "the shard says there are no bandages")

    def test_waits_out_a_save(self):
        self._hurt("The world is saving")

        self.bandager.mend()

        self.assertEqual(self.saves.waited, 3)

    def test_says_when_no_cursor_comes(self):
        self._hurt()
        self.api.WaitForTarget = lambda kind="any", timeout=None: False

        self.bandager.mend()

        self.assertIn("no cursor for the bandage", self.said)
        self.assertEqual(self.api.targeted, [])

    def test_stops_trying_on_a_corpse(self):
        self._hurt()
        self.api.Player.IsDead = True

        self.assertFalse(self.bandager.mend())
        self.assertEqual(self.api.used, [0x40000777])
