import unittest

from test_support.uo import install
from uo.setup import Setup

CONFIG = {
    "title": "Bowcraft",
    "tool_noun": "fletcher's tools",
    "tool_modes": [("stop", "Stop the run"), ("fetch", "Fetch from a container")],
    "outputs": [("sell", "Sell to the bowyer"), ("unload", "Unload into a container"),
                ("keep", "Keep")],
    "unsold_hint": "for what nobody buys",
    "dump_at": 10,
    "hue": 996,
    "poll": 0.5,
    "timeout": 5.0,
}
ROWS = [("30 - 60  bow  bowyer", False), ("80 - 90  heavy crossbow  bowyer", True)]


class Actions(object):
    """What the form is handed: canned answers, and a record of what it asked for."""

    def __init__(self):
        self.source_answers = []
        self.tools_answer = (None, None)
        self.unload_answer = (None, None)
        self.tool_count = 0
        self.unloaded = False
        self.wood = True
        self.unsold = False
        self.cleared = 0

    def source(self):
        return self.source_answers.pop(0) if self.source_answers else (None, None)

    def clear(self):
        self.cleared += 1

    def as_dict(self):
        return {
            "table": lambda: ("Bowcraft 87.3 / 120.0", ROWS),
            "tools": lambda: self.tools_answer,
            "tools_ready": lambda: self.tool_count > 0,
            "source": self.source,
            "clear": self.clear,
            "unload": lambda: self.unload_answer,
            "unload_ready": lambda: self.unloaded,
            "has_wood": lambda: self.wood,
            "unsold_ahead": lambda: self.unsold,
        }


class SetupTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.stop = [None]
        self.actions = Actions()
        self.setup = Setup(CONFIG, self.said.append, lambda: self.stop[0])

    def schedule(self, plan):
        pauses = [0]

        def pause(seconds):
            pauses[0] += 1

            if pauses[0] in plan:
                plan[pauses[0]]()

        self.api.Pause = pause

    def ask(self):
        return self.setup.ask(self.actions.as_dict())

    def pick_buttons(self):
        return [button.IsVisible for button in self.api.drawn_buttons()
                if button.text in ("Pick tool container", "Pick container")]

    def test_the_table_is_drawn_with_the_current_band_marked(self):
        self.schedule({1: lambda: self.api.press("Cancel")})

        self.assertIsNone(self.ask())
        self.assertIn("Bowcraft 87.3 / 120.0", self.api.texts())
        self.assertIn("> 80 - 90  heavy crossbow  bowyer", self.api.texts())
        self.assertIn("   30 - 60  bow  bowyer", self.api.texts())

    def test_ok_with_the_defaults_and_wood_in_the_pack(self):
        self.schedule({1: lambda: self.api.press("OK")})

        self.assertEqual(self.ask(), {"tools": "stop", "output": "sell", "sources": 0,
                                      "dump_at": 10, "debug_logs": True})
        self.assertIn("OK was pressed", self.said)
        self.assertTrue(self.api.drawn[-1].IsDisposed)
        self.assertEqual(self.pick_buttons(), [False, False])

    def test_ok_is_refused_without_wood_or_a_source(self):
        self.actions.wood = False
        self.schedule({1: lambda: self.api.press("OK"), 3: lambda: self.api.press("Cancel")})

        self.assertIsNone(self.ask())
        self.assertIn("add a source of wood, or carry some", self.api.texts())

    def test_fetching_tools_shows_the_row_and_needs_a_container_with_tools(self):
        seen = []

        def pick():
            self.actions.tools_answer = ("'a wooden box' 0x40001000 - 3 fletcher's tools", None)
            self.actions.tool_count = 3
            self.api.press("Pick tool container")

        self.schedule({
            1: lambda: self.api.select(1),
            2: lambda: seen.append(self.pick_buttons()),
            3: lambda: self.api.press("OK"),
            4: lambda: seen.append(list(self.api.texts())),
            5: pick,
            6: lambda: self.api.press("OK"),
        })

        self.assertEqual(self.ask(), {"tools": "fetch", "output": "sell", "sources": 0,
                                      "dump_at": 10, "debug_logs": True})
        self.assertEqual(seen[0], [True, False])
        self.assertTrue(any(text.startswith("pick a container holding") for text in seen[1]))
        self.assertIn("'a wooden box' 0x40001000 - 3 fletcher's tools", self.api.texts())

    def test_a_container_with_no_tools_is_shown_and_refused(self):
        def pick():
            self.actions.tools_answer = ("'a wooden box' 0x40001000 - 0 fletcher's tools",
                                         "'a wooden box' holds no fletcher's tools")
            self.api.press("Pick tool container")

        self.schedule({1: lambda: self.api.select(1), 2: pick, 3: lambda: self.api.press("OK"),
                       5: lambda: self.api.press("Cancel")})

        self.assertIsNone(self.ask())
        self.assertIn("'a wooden box' 0x40001000 - 0 fletcher's tools", self.api.texts())
        self.assertTrue(any(text.startswith("pick a container holding")
                            for text in self.api.texts()))

    def test_unloading_needs_its_container(self):
        seen = []

        def pick():
            self.actions.unload_answer = ("'a trash barrel' 0x40002000", None)
            self.actions.unloaded = True
            self.api.press("Pick container")

        self.schedule({
            1: lambda: self.api.check("Unload into a container"),
            2: lambda: seen.append(self.pick_buttons()),
            3: lambda: self.api.press("OK"),
            4: lambda: seen.append(list(self.api.texts())),
            5: pick,
            6: lambda: self.api.press("OK"),
        })

        self.assertEqual(self.ask(), {"tools": "stop", "output": "unload", "sources": 0,
                                      "dump_at": 10, "debug_logs": True})
        self.assertEqual(seen[0], [False, True])
        self.assertIn("pick the container to unload into", seen[1])
        self.assertIn("'a trash barrel' 0x40002000", self.api.texts())

    def test_the_unload_count_shows_its_default_and_reads_back_what_was_typed(self):
        seen = []

        def pick():
            self.actions.unload_answer = ("'a trash barrel' 0x40002000", None)
            self.actions.unloaded = True
            self.api.press("Pick container")

        self.schedule({
            1: lambda: seen.append(self.api.visible("Unload every")),
            2: lambda: self.api.check("Unload into a container"),
            3: lambda: seen.append(self.api.visible("Unload every")),
            4: pick,
            5: lambda: self.api.type_into(0, " 25 "),
            6: lambda: self.api.press("OK"),
        })

        self.assertEqual(self.ask()["dump_at"], 25)
        self.assertEqual(self.api.text_boxes()[0].text, " 25 ")
        self.assertEqual(seen, [False, True])

    def test_the_unload_count_starts_at_the_configured_default(self):
        self.schedule({1: lambda: self.api.press("OK")})

        self.assertEqual(self.ask()["dump_at"], 10)
        self.assertEqual(self.api.text_boxes()[0].Text, "10")

    def test_a_bad_unload_count_is_refused(self):
        self.actions.unloaded = True
        self.schedule({
            1: lambda: self.api.check("Unload into a container"),
            2: lambda: self.api.type_into(0, "lots"),
            3: lambda: self.api.press("OK"),
            4: lambda: self.api.type_into(0, "0"),
            5: lambda: self.api.press("OK"),
            6: lambda: self.api.press("Cancel"),
        })

        self.assertIsNone(self.ask())
        self.assertIn("unload every: a whole number of products, 1 or more", self.api.texts())

    def test_a_hidden_unload_count_falls_back_to_the_default(self):
        self.schedule({1: lambda: self.api.type_into(0, "lots"), 2: lambda: self.api.press("OK")})

        self.assertEqual(self.ask()["dump_at"], 10)

    def test_selling_with_an_unsold_band_ahead_shows_the_hint_but_allows_ok(self):
        self.actions.unsold = True
        seen = []
        self.schedule({1: lambda: seen.append(self.pick_buttons()),
                       2: lambda: self.api.press("OK")})

        self.assertEqual(self.ask()["output"], "sell")
        self.assertEqual(seen[0], [False, True])
        self.assertIn("for what nobody buys", self.api.texts())

    def test_unchecking_debug_logs_is_read_back(self):
        self.schedule({1: lambda: self.api.uncheck("Debug logs"), 2: lambda: self.api.press("OK")})

        self.assertEqual(self.ask()["debug_logs"], False)

    def test_sources_are_listed_as_picked_and_cleared_together(self):
        self.actions.source_answers = [("'a pack horse' 0x1234, 300 boards in it", None),
                                       (None, "that is your own pack")]
        seen = []
        self.schedule({
            1: lambda: self.api.press("Add a source"),
            2: lambda: self.api.press("Add a source"),
            3: lambda: seen.append(list(self.api.texts())),
            4: lambda: self.api.press("Clear"),
            5: lambda: self.api.press("OK"),
        })

        self.assertEqual(self.ask()["sources"], 0)
        self.assertIn("'a pack horse' 0x1234, 300 boards in it", seen[0])
        self.assertIn("that is your own pack", seen[0])
        self.assertEqual(self.actions.cleared, 1)
        self.assertIn("nothing picked - the run works through the wood you carry", self.api.texts())

    def test_a_picked_source_counts_in_the_answer(self):
        self.actions.source_answers = [("'a pack horse' 0x1234, 300 boards in it", None)]
        self.schedule({1: lambda: self.api.press("Add a source"), 2: lambda: self.api.press("OK")})

        self.assertEqual(self.ask()["sources"], 1)

    def test_more_sources_than_rows_are_all_kept_and_summed_on_the_last_row(self):
        self.actions.source_answers = [("source %d" % n, None) for n in range(6)]
        seen = []
        self.schedule(dict([(n, lambda: self.api.press("Add a source")) for n in range(1, 7)]
                           + [(7, lambda: seen.append(list(self.api.texts()))),
                              (8, lambda: self.api.press("OK"))]))

        self.assertEqual(self.ask()["sources"], 6)
        self.assertIn("source 2", seen[0])
        self.assertNotIn("source 3", seen[0])
        self.assertIn("... and 3 more", seen[0])

    def test_closing_the_form_answers_nothing(self):
        self.schedule({2: self.api.close_drawn})

        self.assertIsNone(self.ask())
        self.assertIn("the form was closed", self.said)

    def test_a_reason_to_stop_ends_the_form(self):
        def die():
            self.stop[0] = "dead"

        self.schedule({2: die})

        self.assertIsNone(self.ask())
        self.assertIn("the run has a reason to stop", self.said)

    def test_nothing_pressed_in_time_answers_nothing(self):
        self.api.Pause = lambda seconds: None

        self.assertIsNone(self.ask())
        self.assertIn("nothing was pressed in 5s", self.said)

    def test_a_stop_before_the_draw_asks_nothing(self):
        self.api.StopRequested = True

        self.assertIsNone(self.ask())
        self.assertEqual(self.api.drawn, [])
