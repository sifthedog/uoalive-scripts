import unittest

from test_support.uo import install
from uo.save import SaveWatch

SAVING = ["world is saving"]
DONE = ["world save complete"]


class Silent(object):
    def __init__(self):
        self.resets = 0

    def beat(self, phase, cycle, tally):
        pass

    def reset(self):
        self.resets += 1


class SaveWatchTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.heartbeat = Silent()
        self.stop = [None]
        self.watch = SaveWatch(SAVING, DONE, 10.0, 1.0, self.said.append, self.heartbeat,
                               lambda: self.stop[0])

    def test_is_not_saving_on_a_quiet_journal(self):
        self.assertFalse(self.watch.is_saving())

    def test_notices_the_save(self):
        self.api.hear("The world is saving, please wait")

        self.assertTrue(self.watch.is_saving())

    def test_reads_the_completion_before_clearing_the_journal(self):
        self.api.hear("world save complete")
        self.watch.wait_out()

        self.assertIn("the shard had already finished, carrying on", self.said)
        self.assertEqual(self.api.paused, 0.0)

    def test_waits_until_the_shard_says_it_is_done(self):
        pauses = [0]

        def pause(seconds):
            pauses[0] += 1

            if pauses[0] == 3:
                self.api.journal.append("world save complete")

        self.api.Pause = pause
        self.watch.wait_out()

        self.assertIn("the shard says it is done, carrying on", self.said)

    def test_gives_up_after_the_wait(self):
        self.watch.wait_out()

        self.assertIn("nothing said in 10s, carrying on", self.said)
        self.assertAlmostEqual(self.api.paused, 10.0)

    def test_a_reason_to_stop_ends_the_wait(self):
        self.stop[0] = "you are dead"
        self.watch.wait_out()

        self.assertIn("the run has a reason to stop, carrying on", self.said)
        self.assertAlmostEqual(self.api.paused, 1.0)

    def test_resets_the_heartbeat_so_it_does_not_fire_on_top_of_the_wait(self):
        self.watch.wait_out()

        self.assertEqual(self.heartbeat.resets, 1)
