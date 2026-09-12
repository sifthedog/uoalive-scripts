import unittest

import uo.record
from test_support.uo import FakePlayer, install
from uo.record import AttemptLog, attempt_log, json_object, json_value, quoted, skill_json


class Sink(object):
    """Stands in for the file, so the suite never touches the disk."""

    def __init__(self, throws=False):
        self.lines = []
        self.throws = throws

    def append(self, path, line):
        if self.throws:
            raise IOError("read-only")

        self.lines.append((path, line))


class QuotedTest(unittest.TestCase):
    def test_wraps_plain_text_in_quotes(self):
        self.assertEqual(quoted("Magery"), '"Magery"')

    def test_escapes_a_quote_and_a_backslash(self):
        self.assertEqual(quoted('a"b\\c'), '"a\\"b\\\\c"')

    def test_escapes_the_line_breaks_a_row_cannot_carry(self):
        self.assertEqual(quoted("a\nb\tc"), '"a\\nb\\tc"')

    def test_escapes_an_accent_rather_than_writing_it_through(self):
        self.assertEqual(quoted("João"), '"Jo\\u00e3o"')


class SkillJsonTest(unittest.TestCase):
    def test_writes_one_decimal(self):
        self.assertEqual(skill_json(74.65), "74.7")

    def test_an_unread_skill_is_null_rather_than_zero(self):
        self.assertEqual(skill_json(None), "null")


class JsonValueTest(unittest.TestCase):
    def test_a_bool_is_a_bool_before_it_is_an_int(self):
        self.assertEqual(json_value(True), "true")
        self.assertEqual(json_value(False), "false")
        self.assertEqual(json_value(1), "1")

    def test_none_is_null(self):
        self.assertEqual(json_value(None), "null")

    def test_a_float_keeps_its_point(self):
        self.assertEqual(json_value(2.5), "2.5")
        self.assertEqual(json_value(-10), "-10")

    def test_text_is_quoted_like_a_row(self):
        self.assertEqual(json_value('Jo\u00e3o "x"'), '"Jo\\u00e3o \\"x\\""')

    def test_a_list_nests(self):
        self.assertEqual(json_value([13, [15, None], "a"]), '[13,[15,null],"a"]')

    def test_a_dict_is_written_with_its_keys_sorted(self):
        self.assertEqual(json_value({"luck": 5, "antique": True}), '{"antique":true,"luck":5}')

    def test_pairs_keep_their_order(self):
        self.assertEqual(json_object([("v", 1), ("a", "b")]), '{"v":1,"a":"b"}')

    def test_empty_containers(self):
        self.assertEqual(json_value([]), "[]")
        self.assertEqual(json_value({}), "{}")
        self.assertEqual(json_object([]), "{}")


class RecordingTest(unittest.TestCase):
    def setUp(self):
        self.clock = [1000.0]
        self.saved = uo.record.now
        uo.record.now = lambda: self.clock[0]
        self.sink = Sink()
        self.said = []

    def tearDown(self):
        uo.record.now = self.saved

    def make(self, path="attempts.jsonl"):
        return AttemptLog(path, "Kaldor", 0x40012345, "Magery", self.said.append,
                          append=self.sink.append)

    def test_a_recorded_attempt_is_not_written_until_the_next_one_or_the_close(self):
        log = self.make()
        log.record(74.6, "cast", "Bless")

        self.assertEqual(self.sink.lines, [])

        log.close(74.7)

        self.assertEqual(len(self.sink.lines), 1)

    def test_a_row_ends_where_the_next_attempt_starts(self):
        log = self.make()
        log.record(74.6, "cast", "Bless")
        log.record(74.8, "cast", "Bless")

        self.assertEqual(len(self.sink.lines), 1)
        self.assertIn('"from":74.6,"to":74.8', self.sink.lines[0][1])

    def test_closing_twice_writes_the_row_once(self):
        log = self.make()
        log.record(74.6, "cast", "Bless")
        log.close(74.7)
        log.close(74.7)

        self.assertEqual(len(self.sink.lines), 1)

    def test_the_row_carries_both_skill_values_and_the_character(self):
        log = self.make()
        log.record(74.6, "cast", "Bless")
        log.close(74.7)

        path, line = self.sink.lines[0]

        self.assertEqual(path, "attempts.jsonl")
        self.assertIn('"char":"Kaldor"', line)
        self.assertIn('"serial":"0x40012345"', line)
        self.assertIn('"skill":"Magery"', line)
        self.assertIn('"used":"Bless"', line)
        self.assertIn('"from":74.6', line)
        self.assertIn('"to":74.7', line)
        self.assertIn('"outcome":"cast"', line)

    def test_what_was_used_is_escaped_like_any_other_text(self):
        log = self.make()
        log.record(74.6, "tamed", 'a "wild" João')
        log.close(74.7)

        self.assertIn('"used":"a \\"wild\\" Jo\\u00e3o"', self.sink.lines[0][1])

    def test_ids_run_in_sequence_within_a_run(self):
        log = self.make()
        log.record(74.6, "cast", "Bless")
        log.close(74.6)
        log.record(74.6, "cast", "Bless")
        log.close(74.7)

        self.assertIn('"id":"0x40012345/1000000/1"', self.sink.lines[0][1])
        self.assertIn('"id":"0x40012345/1000000/2"', self.sink.lines[1][1])

    # Two runs inside the same second would otherwise mint the same ids, and the converter reads a
    # repeated id as the same row arriving twice
    def test_two_runs_started_a_millisecond_apart_do_not_share_ids(self):
        first = self.make()
        self.clock[0] += 0.001
        second = self.make()

        first.record(74.6, "cast", "Bless")
        first.close(74.6)
        second.record(74.6, "cast", "Bless")
        second.close(74.6)

        self.assertNotEqual(self.sink.lines[0][1], self.sink.lines[1][1])

    def test_closing_with_nothing_recorded_writes_nothing(self):
        log = self.make()
        log.close(74.7)

        self.assertEqual(self.sink.lines, [])

    def test_a_close_with_no_reading_writes_the_row_with_its_end_unknown(self):
        log = self.make()
        log.record(74.6, "cast", "Bless")
        log.close(None)

        self.assertIn('"to":null', self.sink.lines[0][1])

    def test_an_attempt_with_no_skill_reading_is_not_recorded(self):
        log = self.make()
        log.record(None, "cast", "Bless")
        log.close(74.7)

        self.assertEqual(self.sink.lines, [])

    def test_an_empty_path_records_nothing(self):
        log = self.make("")
        log.record(74.6, "cast", "Bless")
        log.close(74.7)

        self.assertEqual(self.sink.lines, [])


class ConsumedTest(unittest.TestCase):
    def setUp(self):
        self.sink = Sink()

    def make(self):
        return AttemptLog("attempts.jsonl", "Kaldor", 0x1, "Bowcraft", lambda text: None,
                          append=self.sink.append)

    def test_an_attempt_that_spent_nothing_carries_no_consumed_field(self):
        log = self.make()
        log.record(74.6, "made", "bow")
        log.close(74.7)

        self.assertNotIn("consumed", self.sink.lines[0][1])

    def test_every_material_lands_in_the_row(self):
        log = self.make()
        log.record(74.6, "made", "bow", [("board", 0x1BD7, 0, 1), ("feather", 0x1BD1, 0, 4)])
        log.close(74.7)

        self.assertIn(
            '"consumed":[{"name":"board","graphic":"0x1bd7","hue":0,"qty":1},'
            '{"name":"feather","graphic":"0x1bd1","hue":0,"qty":4}]',
            self.sink.lines[0][1])


class GainedTest(unittest.TestCase):
    def setUp(self):
        self.sink = Sink()

    def make(self):
        return AttemptLog("attempts.jsonl", "Kaldor", 0x1, "Fishing", lambda text: None,
                          append=self.sink.append)

    def test_an_attempt_that_brought_nothing_in_carries_no_gained_field(self):
        log = self.make()
        log.record(50.0, "failed", "fishing pole")
        log.close(50.1)

        self.assertNotIn("gained", self.sink.lines[0][1])

    def test_what_came_in_lands_in_the_row_with_its_name(self):
        log = self.make()
        log.record(50.0, "caught", "fishing pole", gained=[("a fish", 0x09CC, 0, 1)])
        log.close(50.1)

        self.assertIn('"gained":[{"name":"a fish","graphic":"0x9cc","hue":0,"qty":1}]',
                      self.sink.lines[0][1])


class WriteFailureTest(unittest.TestCase):
    def setUp(self):
        self.said = []
        self.sink = Sink(throws=True)
        self.log = AttemptLog("attempts.jsonl", "Kaldor", 0x1, "Magery", self.said.append,
                              append=self.sink.append)

    def test_a_failed_write_says_so_and_does_not_throw(self):
        self.log.record(74.6, "cast", "Bless")
        self.log.close(74.7)

        self.assertEqual(len(self.said), 1)
        self.assertIn("not recording", self.said[0])

    def test_it_says_so_once_and_stops_trying(self):
        for _ in range(3):
            self.log.record(74.6, "cast", "Bless")
            self.log.close(74.7)

        self.assertEqual(len(self.said), 1)


class AttemptLogFactoryTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []

    def test_it_names_the_character_the_client_reports(self):
        self.api.Player = FakePlayer(name="Kaldor", serial=0x40012345)
        sink = Sink()
        log = attempt_log("attempts.jsonl", "Magery", self.said.append)
        log._append = sink.append
        log.record(74.6, "cast", "Bless")
        log.close(74.7)

        self.assertIn('"char":"Kaldor"', sink.lines[0][1])
        self.assertIn('"serial":"0x40012345"', sink.lines[0][1])

    def test_a_client_between_world_states_says_so_and_still_records(self):
        self.api.Player = None
        log = attempt_log("attempts.jsonl", "Magery", self.said.append)

        self.assertEqual(len(self.said), 2)
        self.assertIn("not reporting the character", self.said[0])
        self.assertEqual(self.said[1], "recording to LegionScripts/attempts.jsonl")

    def test_it_stays_quiet_when_recording_is_off(self):
        self.api.Player = None
        attempt_log("", "Magery", self.said.append)

        self.assertEqual(self.said, [])
