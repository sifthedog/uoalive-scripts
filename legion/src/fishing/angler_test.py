import unittest

from fishing.angler import Angler, caught_name
from test_support.uo import install, tile
from uo.phrases import SAVING_TEXT, THROTTLED_TEXT

CAUGHT_TEXT = ["You pull out an item"]

BUCKETS = [
    ("caught", CAUGHT_TEXT),
    ("failed", ["fail to catch anything"]),
    ("empty", ["don't seem to be biting"]),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]

CONFIG = {
    "cursor_timeout": 1.0,
    "cursor_poll": 0.1,
    "prompt_text": ["Where do you want to fish"],
    "no_cursor_read": 0.5,
    "cast_timeout": 2.0,
    "cast_poll": 0.2,
    "caught_text": CAUGHT_TEXT,
    "tail_seconds": 20.0,
    "tail_lines": 10,
}

POLE = 0x40000123
WATER = tile(101, 98, -5, 0x00A8)


class CaughtNameTest(unittest.TestCase):
    def test_the_name_is_what_follows_the_colon(self):
        lines = ["You fish a while", "You pull out an item: a big fish"]

        self.assertEqual(caught_name(lines, ["you pull out an item"]), "a big fish")

    def test_the_latest_catch_wins(self):
        lines = ["You pull out an item: a fish", "You pull out an item: a boot"]

        self.assertEqual(caught_name(lines, ["you pull out an item"]), "a boot")

    def test_no_catch_is_none_rather_than_empty(self):
        self.assertIsNone(caught_name(["You fish a while"], ["you pull out an item"]))


class CastOnceTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.angler = Angler(BUCKETS, CONFIG, self.said.append)

    # The cursor and the answer both follow the use, the way the shard does it
    def on_use(self, lines, cursor=True):
        def use(serial):
            self.api.used.append(serial)
            self.api.has_target = cursor
            self.api.hear(*lines)

        self.api.UseObject = use

    def cast(self):
        return self.angler.cast_once(POLE, WATER)

    def test_the_pole_is_used_and_the_water_tile_is_named_with_its_art(self):
        self.on_use(["You fish a while, but fail to catch anything."])

        self.cast()

        self.assertEqual(self.api.used, [POLE])
        self.assertEqual(self.api.targeted, [(101, 98, -5, 0x00A8)])

    def test_a_catch_carries_the_name_of_what_came_out(self):
        self.on_use(["You pull out an item: a fish"])

        self.assertEqual(self.cast(), ("caught", "a fish"))

    def test_a_miss_is_failed(self):
        self.on_use(["You fish a while, but fail to catch anything."])

        self.assertEqual(self.cast(), ("failed", ""))

    def test_a_dry_spot_is_read_before_the_throttle(self):
        self.on_use(["The fish don't seem to be biting here.", "You must wait a moment."])

        self.assertEqual(self.cast(), ("empty", ""))

    def test_silence_is_unknown(self):
        self.on_use([])

        self.assertEqual(self.cast(), ("unknown", ""))

    def test_a_catch_from_an_earlier_run_is_forgotten_before_the_cast(self):
        self.api.hear("You pull out an item: a boot")
        self.on_use([])

        self.assertEqual(self.cast(), ("unknown", ""))
        self.assertIn("You pull out an item", self.api.forgotten)

    def test_the_prompt_in_the_journal_counts_as_a_cursor(self):
        self.on_use(["Where do you want to fish?", "You pull out an item: a fish"], cursor=False)

        self.assertEqual(self.cast(), ("caught", "a fish"))

    def test_no_cursor_and_no_refusal_is_no_cursor(self):
        self.on_use([], cursor=False)

        self.assertEqual(self.cast(), ("noCursor", ""))
        self.assertEqual(self.api.targeted, [])
        self.assertEqual(len(self.said), 1)

    def test_a_refusal_without_a_cursor_is_read_as_itself(self):
        self.on_use(["You must wait to perform another action."], cursor=False)

        self.assertEqual(self.cast(), ("throttled", ""))
        self.assertEqual(self.api.targeted, [])

    def test_a_cursor_left_standing_is_cancelled_first(self):
        self.api.has_target = True
        self.on_use([])

        self.cast()

        self.assertEqual(self.api.cancelled_targets, 1)
