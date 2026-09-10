import unittest

from test_support.uo import install
from uo.alert import Launcher

ALARM = ["afplay", "/tmp/alarm.mp3"]
NOTICE = ["osascript", "-e", 'display notification "hi"']


class LauncherTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.launcher = Launcher(self.said.append)

    def test_run_starts_the_command_with_its_arguments(self):
        self.launcher.run(NOTICE)

        self.assertEqual(self.api.launched, [NOTICE])
        self.assertEqual(self.said, [])

    def test_an_empty_command_does_nothing(self):
        self.launcher.run([])

        self.assertFalse(self.launcher.play([]))
        self.assertEqual(self.api.launched, [])

    def test_play_does_not_layer_a_running_command(self):
        self.assertTrue(self.launcher.play(ALARM))
        self.assertFalse(self.launcher.play(ALARM))

        self.assertEqual(self.api.launched, [ALARM])

    def test_play_restarts_once_the_last_one_has_exited(self):
        self.launcher.play(ALARM)
        self.api.processes[0].HasExited = True

        self.assertTrue(self.launcher.play(ALARM))
        self.assertEqual(self.api.launched, [ALARM, ALARM])

    def test_stop_kills_what_is_still_playing(self):
        self.launcher.play(ALARM)
        self.launcher.stop()

        self.assertTrue(self.api.processes[0].killed)
        self.assertTrue(self.launcher.play(ALARM))

    def test_stop_with_nothing_playing_is_fine(self):
        self.launcher.stop()
        self.launcher.play(ALARM)
        self.api.processes[0].HasExited = True
        self.launcher.stop()

        self.assertFalse(self.api.processes[0].killed)

    def test_a_failure_is_logged_once_and_still_counts_as_an_attempt(self):
        self.api.launch_error = OSError("no such file")

        self.assertTrue(self.launcher.play(ALARM))
        self.assertTrue(self.launcher.play(ALARM))
        self.launcher.run(ALARM)

        self.assertEqual(self.said, ["could not run afplay - no such file"])
        self.assertEqual(self.api.launched, [])

    def test_a_failure_while_the_script_is_stopping_is_not_swallowed(self):
        self.api.launch_error = RuntimeError("interrupted")
        self.api.StopRequested = True

        self.assertRaises(RuntimeError, self.launcher.run, NOTICE)
