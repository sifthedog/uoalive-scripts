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


class ThreatWatchTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.watch = self.build()

    def build(self, **overrides):
        return ThreatWatch(dict(CONFIG, **overrides), self.said.append, lambda: None,
                           lambda friend: "pet")

    def ambush(self):
        self.api.hear("Doggess Sif: You have been ambushed!")

    def hostile(self):
        self.api.see(mobile(serial=0x00020000, name="an orc", graphic=0x11, distance=3))

    def alarm_ends(self):
        self.api.processes[-1].HasExited = True

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
