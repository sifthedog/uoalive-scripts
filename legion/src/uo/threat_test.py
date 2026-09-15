import unittest

from test_support.uo import install, mobile
from uo.threat import ThreatWatch

ALARM = ["afplay", "/tmp/alarm.mp3"]
NOTICE = ["osascript", "-e", 'display notification "hi"']

CONFIG = {
    "watch": True,
    "range": 12,
    "ambush_text": ["been ambushed"],
    "ambush_warning": "AMBUSHED!",
    "ambush_hue": 33,
    "ambush_alarm": ALARM,
    "ambush_notices": [NOTICE],
    "ambush_repeats": 3,
}


class Holding(object):
    def __init__(self, api, slices):
        self._api = api
        self._slices = slices
        self.waits = 0
        self.speaks = None

    def wait(self, each):
        self.waits += 1

        for _ in range(self._slices):
            each()
            self._api.processes[-1].HasExited = True

        if self.speaks is not None:
            self.speaks()


class WatchCase(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []

    def build(self, hold=None, companion=lambda: None, label=lambda friend: "pet", **overrides):
        return ThreatWatch(dict(CONFIG, **overrides), self.said.append, companion, label, hold)

    def pet(self):
        return mobile(serial=0x00030000, name="a beetle", hits=40, hits_max=50)

    def ambush(self):
        self.api.hear("Doggess Sif: You have been ambushed!")

    def hostile(self):
        self.api.see(mobile(serial=0x00020000, name="an orc", graphic=0x11, distance=3,
                            notoriety=self.api.Notoriety.Gray))

    def alarm_ends(self):
        self.api.processes[-1].HasExited = True


class ThreatWatchTest(WatchCase):
    def setUp(self):
        WatchCase.setUp(self)
        self.watch = self.build()

    def test_an_ambush_line_warns_notifies_and_starts_the_alarm(self):
        self.ambush()
        self.watch.look()

        self.assertEqual(self.api.head_messages, [("AMBUSHED!", self.api.Player.Serial, 33)])
        self.assertEqual(self.api.launched, [NOTICE, ALARM])
        self.assertEqual(self.said, ["ambushed - nothing in sight, you 100/100"])
        self.assertEqual(self.api.said_aloud, [])

    def test_the_line_is_consumed_and_the_alarm_restarts_while_the_fight_lasts(self):
        self.ambush()
        self.watch.look()
        self.hostile()
        self.watch.look()
        self.alarm_ends()
        self.watch.look()

        self.assertEqual(self.api.journal, [])
        self.assertEqual(self.api.launched, [NOTICE, ALARM, ALARM])
        self.assertEqual(len(self.api.head_messages), 1)
        self.assertEqual(len(self.said), 1)

    def test_the_alarm_outlives_a_scan_the_monsters_have_not_reached_yet(self):
        self.ambush()
        self.watch.look()
        self.alarm_ends()
        self.watch.look()

        self.assertEqual(self.api.launched, [NOTICE, ALARM, ALARM])
        self.assertEqual(self.said, ["ambushed - nothing in sight, you 100/100"])

    def test_the_restarts_are_capped_and_then_clear(self):
        self.ambush()

        for _ in range(5):
            self.watch.look()
            self.alarm_ends()

        self.assertEqual(self.api.launched, [NOTICE] + [ALARM] * 3)
        self.assertEqual(self.said[-1], "clear")

    def test_the_fight_ending_stops_the_alarm_early(self):
        self.ambush()
        self.hostile()
        self.watch.look()
        self.api.mobiles = {}
        self.watch.look()
        self.watch.look()

        self.assertEqual(self.api.launched, [NOTICE, ALARM])
        self.assertTrue(self.api.processes[-1].killed)
        self.assertEqual(self.said, ["ambushed - 'an orc' 0x11 3 tiles off, you 100/100", "clear"])

    def test_no_alarm_command_means_the_notices_alone_and_a_prompt_clear(self):
        self.watch = self.build(ambush_alarm=[])
        self.ambush()
        self.watch.look()
        self.watch.look()

        self.assertEqual(self.api.launched, [NOTICE])
        self.assertEqual(self.said, ["ambushed - nothing in sight, you 100/100", "clear"])

    def test_no_wording_means_no_alarm(self):
        self.watch = self.build(ambush_text=[])
        self.ambush()
        self.hostile()
        self.watch.look()

        self.assertEqual(self.api.launched, [])
        self.assertEqual(self.api.head_messages, [])
        self.assertEqual(self.said, ["trouble - 'an orc' 0x11 3 tiles off, you 100/100"])

    def test_plain_trouble_is_logged_and_nothing_else(self):
        self.hostile()
        self.watch.look()
        self.api.mobiles = {}
        self.watch.look()

        self.assertEqual(self.said, ["trouble - 'an orc' 0x11 3 tiles off, you 100/100", "clear"])
        self.assertEqual(self.api.launched, [])
        self.assertEqual(self.api.said_aloud, [])

    def test_a_drop_in_hits_is_trouble(self):
        self.watch.look()
        self.api.Player.Hits = 60
        self.watch.look()

        self.assertEqual(self.said, ["trouble - nothing in sight, you 60/100"])

    def test_watch_off_reads_nothing(self):
        self.watch = self.build(watch=False)
        self.ambush()
        self.watch.look()

        self.assertEqual(self.api.launched, [])
        self.assertEqual(self.api.journal, ["Doggess Sif: You have been ambushed!"])

    def test_an_ambush_with_the_companion_in_sight_names_it_by_the_label(self):
        self.watch = self.build(companion=self.pet)
        self.ambush()
        self.watch.look()

        self.assertEqual(self.said, ["ambushed - nothing in sight, you 100/100, pet 40/50"])
        self.assertEqual(self.api.launched, [NOTICE, ALARM])

    # What mining once passed: the label is called, so a bare string ends the run on the first
    # ambush the companion is in sight for
    def test_a_label_that_is_not_callable_throws_on_an_ambush(self):
        self.watch = self.build(companion=self.pet, label="beetle")
        self.ambush()

        self.assertRaises(TypeError, self.watch.look)


class ThreatWatchHoldTest(WatchCase):
    def setUp(self):
        WatchCase.setUp(self)
        self.hold = Holding(self.api, 5)
        self.watch = self.build(self.hold)

    def test_an_ambush_holds_after_the_notices_and_the_alarm_restarts_while_it_waits(self):
        self.ambush()
        self.watch.look()

        self.assertEqual(self.hold.waits, 1)
        self.assertEqual(self.api.launched, [NOTICE] + [ALARM] * 3)
        self.assertEqual(self.said, ["ambushed - nothing in sight, you 100/100"])

    def test_the_hold_ending_silences_the_alarm_and_clears_the_episode(self):
        self.ambush()
        self.watch.look()
        self.watch.look()

        self.assertTrue(self.api.processes[-1].HasExited)
        self.assertEqual(self.said, ["ambushed - nothing in sight, you 100/100"])

    # The shard keeps talking while the gump is up, and the client files the hold's own
    # "holding - You have been ambushed..." SysMsg in the journal beside it
    def test_an_ambush_line_from_during_the_hold_does_not_hold_again(self):
        self.hold.speaks = self.ambush
        self.ambush()
        self.watch.look()
        self.watch.look()

        self.assertEqual(self.hold.waits, 1)
        self.assertEqual(self.said, ["ambushed - nothing in sight, you 100/100"])
        self.assertTrue(self.api.processes[-1].HasExited)

    def test_a_hostile_still_there_after_the_hold_is_plain_trouble(self):
        self.ambush()
        self.hostile()
        self.watch.look()
        self.watch.look()

        self.assertEqual(self.said[-1], "trouble - 'an orc' 0x11 3 tiles off, you 100/100")
        self.assertEqual(len(self.api.launched), 4)

    def test_plain_trouble_never_holds(self):
        self.hostile()
        self.watch.look()

        self.assertEqual(self.hold.waits, 0)
