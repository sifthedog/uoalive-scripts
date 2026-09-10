import unittest

from test_support.uo import install
from uo.hold import Hold

CONFIG = {"text": "ambushed, press when safe", "button": "Resume", "hue": 33, "poll": 0.5}


class Silent(object):
    def __init__(self):
        self.resets = 0

    def reset(self):
        self.resets += 1


class HoldTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.heartbeat = Silent()
        self.stop = [None]
        self.slices = [0]
        self.hold = Hold(CONFIG, self.said.append, lambda: self.stop[0], self.heartbeat)

    def each(self):
        self.slices[0] += 1

    def after_pauses(self, count, action):
        pauses = [0]

        def pause(seconds):
            pauses[0] += 1

            if pauses[0] == count:
                action()

        self.api.Pause = pause

    def test_the_button_ends_the_wait(self):
        self.after_pauses(3, lambda: self.api.press("Resume"))

        self.assertTrue(self.hold.wait(self.each))
        self.assertEqual(self.slices, [4])
        self.assertEqual(self.said, ["holding - ambushed, press when safe",
                                     "the button was pressed, carrying on"])

    def test_closing_the_gump_ends_the_wait(self):
        self.after_pauses(2, self.api.close_drawn)

        self.assertTrue(self.hold.wait(self.each))
        self.assertEqual(self.said[-1], "the gump was closed, carrying on")

    def test_a_reason_to_stop_ends_the_wait(self):
        self.after_pauses(2, lambda: self.stop.__setitem__(0, "dead"))

        self.assertFalse(self.hold.wait(self.each))
        self.assertEqual(self.said[-1], "the run has a reason to stop, carrying on")

    def test_a_stop_request_ends_the_wait_before_another_alarm_slice(self):
        self.after_pauses(2, lambda: setattr(self.api, "StopRequested", True))

        self.assertFalse(self.hold.wait(self.each))
        self.assertEqual(self.slices, [2])
        self.assertEqual(self.said[-1], "the run is being stopped, carrying on")

    def test_the_walk_and_the_cursor_are_cancelled_before_the_gump_goes_up(self):
        self.api.pathfinding = True
        self.api.has_target = True
        self.after_pauses(1, lambda: self.api.press("Resume"))
        self.hold.wait(self.each)

        self.assertEqual(self.api.cancelled_pathfinding, 1)
        self.assertEqual(self.api.cancelled_targets, 1)

    def test_nothing_is_cancelled_when_nothing_is_running(self):
        self.after_pauses(1, lambda: self.api.press("Resume"))
        self.hold.wait(self.each)

        self.assertEqual(self.api.cancelled_pathfinding, 0)
        self.assertEqual(self.api.cancelled_targets, 0)

    def test_the_gump_is_drawn_centred_with_the_text_and_the_button(self):
        self.after_pauses(1, lambda: self.api.press("Resume"))
        self.hold.wait(self.each)

        gump = self.api.drawn[0]
        kinds = [child.kind for child in gump.children]
        texts = [child.text for child in gump.children]

        self.assertEqual(gump.centered, 2)
        self.assertEqual(kinds, ["box", "label", "button"])
        self.assertEqual(texts[1:], ["ambushed, press when safe", "Resume"])

    def test_the_gump_comes_down_and_the_heartbeat_restarts(self):
        self.after_pauses(1, lambda: self.api.press("Resume"))
        self.hold.wait(self.each)

        self.assertTrue(self.api.drawn[0].IsDisposed)
        self.assertEqual(self.heartbeat.resets, 1)
