import unittest

from test_support.uo import FakeButton, FakeHtml, install
from uo.gump import (await_changed, await_gump, await_recognised, button_ids, controls, gump_says,
                     is_open, open_ids)


class AwaitChangedTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_a_stale_gump_does_not_count(self):
        self.api.gump = 77

        self.assertEqual(await_changed(77, 1.0, 0.25), 0)

    def test_returns_the_new_gump(self):
        self.api.gump = 78

        self.assertEqual(await_changed(77, 1.0, 0.25), 78)

    def test_reads_a_gump_that_arrives_late(self):
        pauses = [0]

        def pause(seconds):
            pauses[0] += 1

            if pauses[0] == 2:
                self.api.gump = 78

        self.api.Pause = pause

        self.assertEqual(await_changed(0, 1.0, 0.25), 78)

    def test_gives_up_after_the_timeout(self):
        self.assertEqual(await_changed(0, 1.0, 0.25), 0)
        self.assertAlmostEqual(self.api.paused, 1.0)


class GumpSaysTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_is_false_for_an_empty_gump(self):
        self.assertFalse(gump_says(1, ["release this creature"]))

    def test_matches_any_of_the_wordings(self):
        self.api.gump_text = ["Are you sure you wish to release this creature?"]

        self.assertTrue(gump_says(1, ["nothing like it", "release this creature"]))


class OpenIdsTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_nothing_open(self):
        self.assertEqual(open_ids(), [])

    def test_the_last_gump_comes_first_and_the_rest_follow_once(self):
        self.api.gump = 77
        self.api.open_gumps = set([77, 78])

        self.assertEqual(open_ids(), [77, 78])

    def test_without_the_listing_call_the_last_gump_is_all_there_is(self):
        self.api.gump = 77

        def missing():
            raise AttributeError("GetAllGumps")

        self.api.GetAllGumps = missing

        self.assertEqual(open_ids(), [77])


class IsOpenTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.gump = 77
        self.api.open_gumps = set([78])

    def test_answers_by_id_not_by_which_was_last(self):
        self.assertTrue(is_open(78))
        self.assertTrue(is_open(77))
        self.assertFalse(is_open(79))
        self.assertFalse(is_open(0))

    def test_await_gump_answers_the_id_or_nothing(self):
        self.assertEqual(await_gump(78, 1.0), 78)
        self.assertEqual(await_gump(79, 1.0), 0)
        self.assertEqual(await_gump(0, 1.0), 0)


class ButtonIdsTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_unreadable_is_none_not_empty(self):
        self.assertIsNone(button_ids(77))
        self.assertIsNone(button_ids(0))

    def test_reads_the_buttons_off_the_gump(self):
        self.api.gump_buttons[77] = set([0, 1, 21, 41])

        self.assertEqual(button_ids(77), set([0, 1, 21, 41]))

    def test_a_throwing_client_reads_as_unknown(self):
        def boom(ident=None):
            raise RuntimeError("off the main thread")

        self.api.GetGump = boom

        self.assertIsNone(button_ids(77))

    def test_controls_come_back_in_order_with_their_button_or_text(self):
        self.api.gump_controls[77] = [FakeButton(2), FakeHtml("bow"), FakeButton(3), FakeHtml("")]

        self.assertEqual(controls(77), [(2, None), (None, "bow"), (3, None), (None, None)])
        self.assertEqual(button_ids(77), set([2, 3]))

    def test_a_getter_that_throws_is_that_field_alone(self):
        class Sulky(object):
            ButtonID = 5

            @property
            def Text(self):
                raise ValueError("no text here")

        self.api.gump_controls[77] = [Sulky()]

        self.assertEqual(controls(77), [(5, None)])


class AwaitRecognisedTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.gump_contents[88] = "BOWCRAFT"
        self.known = lambda ident: "BOWCRAFT" in self.api.gump_contents.get(ident, "")

    def test_a_recognised_gump_wins_even_when_it_is_not_last(self):
        self.api.gump = 77
        self.api.open_gumps = set([88])

        self.assertEqual(await_recognised(self.known, [77], 1.0, 0.25), (88, True))

    def test_a_gump_that_was_up_before_is_not_a_newcomer(self):
        self.api.gump = 77

        self.assertEqual(await_recognised(self.known, [77], 1.0, 0.25), (0, False))

    def test_a_newcomer_no_text_names_is_taken_and_flagged(self):
        self.api.gump = 78

        self.assertEqual(await_recognised(self.known, [77], 1.0, 0.25), (78, False))

    def test_waits_for_one_that_arrives_late(self):
        pauses = [0]

        def pause(seconds):
            pauses[0] += 1

            if pauses[0] == 2:
                self.api.gump = 88

        self.api.Pause = pause

        self.assertEqual(await_recognised(self.known, [], 1.0, 0.25), (88, True))
