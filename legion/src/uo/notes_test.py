import unittest

from test_support.uo import install
from uo.log import make_log
from uo.notes import NoteLog, Reporter, note_log

CONFIG = {
    "max_reports": 2,
    "text_limit": 40,
    "tail_seconds": 20.0,
    "tail_lines": 4,
    "notes_seconds": 60.0,
}

HEADER = ("CARPENTRY MENU CATEGORIES SELECTIONS NOTICES EXIT CANCEL MAKE REPAIR ITEM MARK ITEM "
          "ENHANCE ITEM ALTER ITEM (GARGOYLE) NON QUEST ITEM MAKE LAST 0/1 COMPLETED")

# What the menu draws after the notice, which is most of it
ROWS = "WOOD (130) LAST TEN Other Furniture Containers barrel staves barrel lid easel (south)"


class Written(object):
    def __init__(self):
        self.blocks = []

    def append(self, path, block):
        self.blocks.append((path, block))


class NoteLogTest(unittest.TestCase):
    def setUp(self):
        install()
        self.said = []
        self.written = Written()

    def test_writes_one_block_per_report(self):
        notes = NoteLog("notes.log", self.said.append, self.written.append)

        notes.write("nothing readable came back", [("gump", ["You wat?"])])

        path, block = self.written.blocks[0]
        self.assertEqual(path, "notes.log")
        self.assertIn("] nothing readable came back", block)
        self.assertIn("  gump:\n    You wat?", block)

    def test_a_row_with_nothing_in_it_says_so(self):
        notes = NoteLog("notes.log", self.said.append, self.written.append)

        notes.write("refused for materials", [("journal", [])])

        self.assertIn("  journal:\n    (nothing)", self.written.blocks[0][1])

    def test_an_empty_path_writes_nothing(self):
        notes = NoteLog("", self.said.append, self.written.append)

        notes.write("nothing readable came back", [("gump", ["You wat?"])])

        self.assertFalse(notes.writing())
        self.assertEqual(self.written.blocks, [])

    def test_a_file_it_cannot_write_retires_the_sink_and_says_so_once(self):
        def throw(path, block):
            raise Exception("read-only")

        notes = NoteLog("notes.log", self.said.append, throw)

        notes.write("one", [])
        notes.write("two", [])

        self.assertFalse(notes.writing())
        self.assertEqual(self.said, ["cannot write notes.log (read-only) - not writing notes "
                                     "this run"])

    def test_a_bare_name_lands_beside_the_script(self):
        self.assertEqual(note_log("notes.log", self.said.append).where(),
                         "LegionScripts/notes.log")


class ReporterTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.written = Written()
        self.notes = NoteLog("notes.log", self.said.append, self.written.append)
        self.lines = [HEADER, "You create an exceptional quality item.", ROWS]

    def report(self, notes=None, stamp=None):
        return Reporter(lambda gump: self.lines, CONFIG, self.said.append, notes, stamp)

    def test_says_the_shard_sentence_and_neither_the_header_nor_the_rows(self):
        self.report().say("nothing readable came back", 88)

        self.assertIn("'...You create an exceptional quality item.", self.said[0])
        self.assertNotIn("CATEGORIES", self.said[0])
        self.assertNotIn("barrel staves", self.said[0])
        self.assertNotIn("CATEGORIES", self.said[0])

    def test_says_nothing_of_a_gump_that_never_opened(self):
        self.report().say("nothing readable came back", 0)

        self.assertIn("the gump says '(nothing)'", self.said[0])

    def test_the_window_quotes_the_shard_over_the_chatter(self):
        self.api.hear("You create an exceptional quality item.")
        self.api.overhear("Lurid Halo the Necromancer", "Hey buddy", "a wren")

        self.report().say("nothing readable came back", 88)

        self.assertIn("the journal says 'You create an exceptional quality item.'", self.said[1])

    def test_an_extra_is_said_as_written_and_labelled_in_the_file(self):
        self.report(self.notes).say("refused for materials", 88,
                                    [("pack", "the pack holds 165 boards")])

        self.assertIn("the pack holds 165 boards", self.said)
        self.assertIn("  pack:\n    the pack holds 165 boards", self.written.blocks[0][1])

    def test_the_file_gets_the_whole_gump_untruncated(self):
        self.report(self.notes).say("nothing readable came back", 88)

        self.assertIn(HEADER, self.written.blocks[0][1])
        self.assertIn(ROWS, self.written.blocks[0][1])

    def test_the_file_keeps_the_chatter_the_window_left_out(self):
        self.api.hear("You create an exceptional quality item.")
        self.api.overhear("Lurid Halo the Necromancer", "Hey buddy")

        self.report(self.notes).say("nothing readable came back", 88)

        self.assertNotIn("Lurid Halo", self.said[1])
        self.assertIn("Lurid Halo the Necromancer: Hey buddy", self.written.blocks[0][1])

    def test_it_leaves_out_what_the_script_said_itself(self):
        log = make_log("carpentry")
        log("unreadable outcome (1/5)")
        self.api.hear(*self.api.messages)

        Reporter(lambda gump: self.lines, CONFIG, self.said.append, self.notes,
                 log.stamp).say("nothing readable came back", 88)

        self.assertNotIn("unreadable outcome", self.written.blocks[0][1])

    def test_the_window_goes_quiet_after_max_reports_and_the_file_does_not(self):
        reporter = self.report(self.notes)

        for _each in range(4):
            reporter.say("nothing readable came back", 88)

        self.assertEqual(len(self.written.blocks), 4)
        self.assertEqual(len([line for line in self.said if line.startswith("nothing readable")]),
                         2)

    def test_a_craft_that_reads_cleanly_gives_the_window_its_voice_back(self):
        reporter = self.report(self.notes)

        for _each in range(2):
            reporter.say("nothing readable came back", 88)

        reporter.forget()
        reporter.say("nothing readable came back", 88)

        self.assertEqual(len([line for line in self.said if line.startswith("nothing readable")]),
                         3)

    def test_where_the_file_is_is_said_once(self):
        reporter = self.report(self.notes)

        reporter.say("nothing readable came back", 88)
        reporter.say("nothing readable came back", 88)

        self.assertEqual(self.said.count("the whole of it is in notes.log"), 1)

    def test_no_file_is_no_error(self):
        self.report().say("nothing readable came back", 88)

        self.assertEqual(self.written.blocks, [])
