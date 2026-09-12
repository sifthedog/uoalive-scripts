import unittest

from fishing.prompt import StartPrompt
from test_support.uo import install

CONFIG = {
    "tiles_text": "How many tiles ahead?",
    "tiles_default": 4,
    "tiles_hue": 996,
    "catch_text": "What happens to junk catches?",
    "catch_options": [("container", "Container"), ("keep", "Keep"), ("discard", "Discard")],
    "catch_default": "discard",
    "catch_hue": 996,
    "poll": 0.5,
}


class StartPromptTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.stop = [None]
        self.prompt = StartPrompt(CONFIG, self.said.append, lambda: self.stop[0])

    def schedule(self, plan):
        pauses = [0]

        def pause(seconds):
            pauses[0] += 1

            if pauses[0] in plan:
                plan[pauses[0]]()

        self.api.Pause = pause

    def test_bare_ok_takes_the_prefilled_default_and_the_discard_radio(self):
        self.schedule({1: lambda: self.api.press("OK")})

        self.assertEqual(self.prompt.ask(),
                        {"tiles_ahead": 4, "catch_mode": "discard", "debug_logs": True})
        self.assertEqual(self.api.text_boxes()[0].Text, "4")

    def test_a_typed_number_wins(self):
        def type_and_press():
            self.api.type_into(0, "9")
            self.api.press("OK")

        self.schedule({1: type_and_press})

        self.assertEqual(self.prompt.ask(),
                        {"tiles_ahead": 9, "catch_mode": "discard", "debug_logs": True})

    def test_blank_zero_negative_and_non_numeric_all_fall_back_to_the_default(self):
        for typed in ("", "0", "-3", "abc"):
            self.api = install()
            self.prompt = StartPrompt(CONFIG, self.said.append, lambda: self.stop[0])

            def type_and_press(typed=typed):
                self.api.type_into(0, typed)
                self.api.press("OK")

            self.schedule({1: type_and_press})

            self.assertEqual(self.prompt.ask()["tiles_ahead"], 4)

    def test_checking_container_wins_over_the_prefilled_discard(self):
        def check_and_press():
            self.api.check("Container")
            self.api.press("OK")

        self.schedule({1: check_and_press})

        self.assertEqual(self.prompt.ask(),
                        {"tiles_ahead": 4, "catch_mode": "container", "debug_logs": True})

    def test_checking_keep_wins_over_the_prefilled_discard(self):
        def check_and_press():
            self.api.check("Keep")
            self.api.press("OK")

        self.schedule({1: check_and_press})

        self.assertEqual(self.prompt.ask(),
                        {"tiles_ahead": 4, "catch_mode": "keep", "debug_logs": True})

    def test_unchecking_debug_logs_is_read_back(self):
        def uncheck_and_press():
            self.api.uncheck("Debug logs")
            self.api.press("OK")

        self.schedule({1: uncheck_and_press})

        self.assertEqual(self.prompt.ask()["debug_logs"], False)

    # On the real client, a radio's isChecked-at-creation is not always something GetIsChecked
    # reflects until an actual click has landed on one - pressing OK straight away must not silently
    # read back as the first option in the list just because nothing reports checked
    def test_pressing_ok_with_no_radio_reporting_checked_still_uses_the_configured_default(self):
        def uncheck_all_and_press():
            for control in self.api.drawn_controls():
                if control.kind == "radio":
                    control.SetIsChecked(False)

            self.api.press("OK")

        self.schedule({1: uncheck_all_and_press})

        self.assertEqual(self.prompt.ask(),
                        {"tiles_ahead": 4, "catch_mode": "discard", "debug_logs": True})

    def test_cancel_takes_both_defaults_even_over_a_typed_number_and_a_checked_radio(self):
        def type_check_and_cancel():
            self.api.type_into(0, "9")
            self.api.check("Container")
            self.api.press("Cancel")

        self.schedule({1: type_check_and_cancel})

        self.assertEqual(self.prompt.ask(),
                        {"tiles_ahead": 4, "catch_mode": "discard", "debug_logs": True})

    def test_closing_the_gump_takes_both_defaults(self):
        self.schedule({1: self.api.close_drawn})

        self.assertEqual(self.prompt.ask(),
                        {"tiles_ahead": 4, "catch_mode": "discard", "debug_logs": True})

    def test_a_reason_to_stop_takes_both_defaults(self):
        self.schedule({1: lambda: self.stop.__setitem__(0, "dead")})

        self.assertEqual(self.prompt.ask(),
                        {"tiles_ahead": 4, "catch_mode": "discard", "debug_logs": True})

    def test_a_run_already_being_stopped_draws_nothing(self):
        self.api.StopRequested = True

        self.assertEqual(self.prompt.ask(),
                        {"tiles_ahead": 4, "catch_mode": "discard", "debug_logs": True})
        self.assertEqual(self.api.drawn, [])

    def test_the_gump_is_drawn_centred_with_the_label_radios_box_and_buttons(self):
        self.schedule({1: lambda: self.api.press("OK")})
        self.prompt.ask()

        gump = self.api.drawn[0]
        kinds = [child.kind for child in gump.children]

        self.assertEqual(gump.centered, 2)
        self.assertEqual(kinds, ["box", "label", "radio", "radio", "radio", "label", "textbox",
                                 "checkbox", "button", "button"])
        self.assertTrue(gump.IsDisposed)
