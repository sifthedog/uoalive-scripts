import unittest

from test_support.uo import install, item
from uo.convert import Converter


class Saves(object):
    def is_saving(self):
        return False

    def wait_out(self):
        pass


# is_saving answers False the first call (the pass-level check in run()) and True from then on,
# so a test can put a save in the middle of one attempt without ending the pass before it starts
class TogglingSaves(object):
    def __init__(self, saving_from_call=2):
        self.calls = 0
        self.waited_out = 0
        self._saving_from_call = saving_from_call

    def is_saving(self):
        self.calls += 1

        return self.calls >= self._saving_from_call

    def wait_out(self):
        self.waited_out += 1


class ConverterTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.converted = []
        self.after = None
        self.blocked_calls = []
        self.nothing_to_do_calls = []

    def perform(self, stack):
        if self.after is not None:
            self.api.hold(*self.after)

        return True

    def build(self, saves=None, **overrides):
        stacks = [item(serial=1, graphic=0x19B9, hue=0, amount=10)]

        config = {
            "noun": "ore",
            "attempts": 3,
            "passes": 1,
            "delay": 0.0,
            "timeout": 1.0,
            "poll": 0.5,
            "throttled_text": ["wait"],
            "unskilled_text": ["no idea"],
            "wait_on_save": False,
            "saving_message": "saving",
            "next_source": lambda skip: stacks[0],
            "perform": self.perform,
            "blocked": lambda: self.blocked_calls.append(1) or None,
            "learn_product": lambda gained: None,
            "converted": lambda gained, lost: self.converted.append((gained, lost)),
            "nothing_to_do": lambda skip: self.nothing_to_do_calls.append(1),
            "about_to_convert": lambda: None,
        }
        config.update(overrides)

        return Converter(config, self.said.append, saves or Saves())

    def test_the_converted_hook_sees_what_the_pack_gained_and_lost(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))
        self.after = [item(serial=2, graphic=0x1BF2, hue=0, amount=5)]

        self.build().run()

        self.assertEqual(self.converted, [({(0x1BF2, 0): 5}, {(0x19B9, 0): 10})])

    def test_a_pack_that_held_still_is_not_a_conversion(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))

        self.build().run()

        self.assertEqual(self.converted, [])

    def test_repeated_misses_write_the_hue_off(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))
        converter = self.build(perform=lambda stack: False, attempts=2, passes=2)

        converter.run()

        self.assertEqual(converter.written_off(), set([0]))
        self.assertIn("hue 0 failed 2 times, leaving it as ore", self.said)

    def test_a_save_starting_mid_attempt_is_not_counted_as_a_miss(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))
        saves = TogglingSaves(saving_from_call=2)
        converter = self.build(saves=saves, wait_on_save=True, timeout=0.1, poll=0.1)

        self.assertFalse(converter.run())
        self.assertEqual(saves.waited_out, 1)
        self.assertIn("the world is saving, not counting it against hue 0", self.said)
        self.assertEqual(converter.written_off(), set())

    def test_throttled_text_is_not_counted_as_a_miss(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))
        self.api.hear("You must wait a while before trying that again")
        converter = self.build(timeout=0.1, poll=0.1)

        converter.run()

        self.assertIn("the shard says wait, not counting it against hue 0", self.said)
        self.assertEqual(converter.written_off(), set())

    def test_unskilled_text_writes_the_hue_off(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))
        self.api.hear("You have no idea how to work that")
        converter = self.build(timeout=0.1, poll=0.1)

        converter.run()

        self.assertEqual(converter.written_off(), set([0]))
        self.assertIn("not skilled enough for hue 0, leaving it as ore", self.said)

    def test_blocked_ends_the_pass_before_converting(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))
        performed = []
        converter = self.build(perform=lambda stack: performed.append(1),
                               blocked=lambda: "short of mana")

        self.assertFalse(converter.run())
        self.assertEqual(performed, [])
        self.assertIn("short of mana, leaving it for now", self.said)

    def test_nothing_to_do_ends_the_pass_successfully(self):
        converter = self.build(next_source=lambda skip: None)

        self.assertTrue(converter.run())
        self.assertEqual(self.nothing_to_do_calls, [1])

    def test_the_pass_backstop_is_reported(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))
        converter = self.build(passes=2)

        self.assertFalse(converter.run())
        self.assertIn("hit the 2 conversion pass backstop", self.said)

    def test_retry_written_off_clears_the_write_offs_once(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))
        converter = self.build(perform=lambda stack: False, attempts=1, passes=1)
        converter.run()

        self.assertEqual(converter.written_off(), set([0]))
        self.assertTrue(converter.retry_written_off())
        self.assertEqual(converter.written_off(), set())

        # No progress happened since the retry, so a second one without force is refused
        self.assertFalse(converter.retry_written_off())

    def test_force_retries_even_without_progress(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))
        converter = self.build(perform=lambda stack: False, attempts=1, passes=1)
        converter.run()
        converter.retry_written_off()
        converter.run()  # written off again, with nothing having progressed since the retry

        self.assertFalse(converter.retry_written_off())
        self.assertTrue(converter.retry_written_off(force=True))

    def test_retry_written_off_does_nothing_when_nothing_is_written_off(self):
        self.assertFalse(self.build().retry_written_off())
