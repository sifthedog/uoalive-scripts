import unittest

from test_support.uo import install, item
from uo.heal import Bandager, Healer

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


SPELL = {"spell": "Greater Heal", "mana": 11, "target": "self", "target_kind": "beneficial"}


class FakeCaster(object):
    def __init__(self, api, heals=0, outcome="cast"):
        self._api = api
        self._heals = heals
        self._outcome = outcome
        self.cast = []
        self.paced = 0

    def cast_once(self, stage):
        self.cast.append(stage["spell"])
        self._api.Player.Hits = min(self._api.Player.HitsMax, self._api.Player.Hits + self._heals)

        return self._outcome

    def pace(self, stage):
        self.paced += 1


class HealerTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.gathered = 0

    def _healer(self, caster, mana=True, attempts=6):
        def gather():
            self.gathered += 1

            return mana

        return Healer(caster, SPELL, gather, lambda: self.api.Player.Hits < 40,
                      lambda: self.api.Player.Hits >= self.api.Player.HitsMax, attempts,
                      self.said.append)

    def test_casts_nothing_while_the_hits_are_above_the_floor(self):
        caster = FakeCaster(self.api)
        self.api.Player.Hits = 55

        self.assertTrue(self._healer(caster).mend())
        self.assertEqual(caster.cast, [])
        self.assertEqual(self.said, [])

    def test_heals_to_full_rather_than_stopping_at_the_floor(self):
        caster = FakeCaster(self.api, heals=25)
        self.api.Player.Hits = 30

        self.assertTrue(self._healer(caster).mend())
        self.assertEqual(caster.cast, ["Greater Heal"] * 3)
        self.assertEqual(self.said, ["30/100 hits, healing", "healed to 100/100"])

    def test_gathers_mana_before_every_cast(self):
        caster = FakeCaster(self.api, heals=25)
        self.api.Player.Hits = 30

        self._healer(caster).mend()

        self.assertEqual(self.gathered, 3)

    # Only a refusal nothing can answer retires the healing; a dry pool is another cycle's problem
    def test_mana_that_never_comes_back_ends_the_mend_without_retiring_it(self):
        caster = FakeCaster(self.api)
        self.api.Player.Hits = 30
        healer = self._healer(caster, mana=False)

        self.assertFalse(healer.mend())
        self.assertEqual(caster.cast, [])
        self.assertIsNone(healer.retired())
        self.assertEqual(self.said[-1], "the mana for Greater Heal did not come back")

    def test_a_retired_healer_says_so_once_and_stops_trying(self):
        caster = FakeCaster(self.api, outcome="noReagents")
        self.api.Player.Hits = 30
        healer = self._healer(caster)

        self.assertFalse(healer.mend())
        self.assertFalse(healer.mend())
        self.assertEqual(caster.cast, ["Greater Heal"])
        self.assertEqual(self.said, ["30/100 hits, healing", "out of reagents for Greater Heal"])

    def test_a_shard_that_refuses_the_spell_retires_it_too(self):
        caster = FakeCaster(self.api, outcome="unskilled")
        self.api.Player.Hits = 30
        healer = self._healer(caster)

        healer.mend()

        self.assertEqual(healer.retired(),
                         "the shard refuses Greater Heal from this character")

    def test_gives_up_on_the_attempt_backstop_without_retiring(self):
        caster = FakeCaster(self.api, heals=1)
        self.api.Player.Hits = 30
        healer = self._healer(caster, attempts=2)

        self.assertFalse(healer.mend())
        self.assertEqual(caster.cast, ["Greater Heal"] * 2)
        self.assertIsNone(healer.retired())

    def test_dying_mid_mend_ends_it(self):
        caster = FakeCaster(self.api)
        self.api.Player.Hits = 30
        self.api.Player.IsDead = True

        self._healer(caster).mend()

        self.assertEqual(caster.cast, ["Greater Heal"])

    # The stop reason stands its health floor down on this, or the trance a mend needs would end on
    # the floor that asked for the mend
    def test_reports_a_mend_in_flight_only_while_one_is_running(self):
        caster = FakeCaster(self.api, heals=100)
        self.api.Player.Hits = 30
        healer = self._healer(caster)
        seen = []
        original = caster.cast_once

        def watched(stage):
            seen.append(healer.mending())

            return original(stage)

        caster.cast_once = watched

        self.assertFalse(healer.mending())

        healer.mend()

        self.assertEqual(seen, [True])
        self.assertFalse(healer.mending())
