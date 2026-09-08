import unittest

from skilldb.convert import (Skipped, gain_of, merge, parse_line, read_lines, stamp, tables)


def line(**fields):
    row = {"v": 1, "id": "0x1/1000/1", "t": 1757030042.5, "char": "Kaldor", "serial": "0x1",
           "skill": "Magery", "used": "Bless", "from": 74.6, "to": 74.7, "outcome": "cast"}
    row.update(fields)

    parts = []

    for name in ("v", "id", "t", "char", "serial", "skill", "used", "from", "to", "outcome"):
        value = row[name]

        if isinstance(value, str):
            parts.append('"%s":"%s"' % (name, value))
        elif isinstance(value, bool):
            parts.append('"%s":%s' % (name, "true" if value else "false"))
        elif value is None:
            parts.append('"%s":null' % name)
        else:
            parts.append('"%s":%s' % (name, value))

    if "consumed" in fields:
        parts.append('"consumed":%s' % fields["consumed"])

    return "{%s}" % ",".join(parts)


class ParseLineTest(unittest.TestCase):
    def test_reads_a_row_the_macro_wrote(self):
        row = parse_line(line())

        self.assertEqual(row["skill"], "Magery")
        self.assertEqual(row["from"], 74.6)

    def test_a_half_written_line_is_skipped_rather_than_fatal(self):
        self.assertRaises(Skipped, parse_line, '{"v":1,"id":"0x1/1000/1","t":175')

    def test_a_row_missing_what_a_table_needs_is_skipped(self):
        self.assertRaises(Skipped, parse_line, '{"v":1,"id":"a","t":1.0}')

    def test_a_version_this_does_not_read_is_skipped_rather_than_guessed_at(self):
        self.assertRaises(Skipped, parse_line, line().replace('"v":1', '"v":2'))


class ReadLinesTest(unittest.TestCase):
    def test_blank_lines_are_not_problems(self):
        rows, problems = read_lines([line(), "", "  ", ""], "log.jsonl")

        self.assertEqual(len(rows), 1)
        self.assertEqual(problems, [])

    def test_a_bad_line_costs_itself_and_nothing_else(self):
        rows, problems = read_lines([line(), "{oops", line(id="0x1/1000/2")], "log.jsonl")

        self.assertEqual(len(rows), 2)
        self.assertEqual(len(problems), 1)
        self.assertIn("log.jsonl:2", problems[0])


class MergeTest(unittest.TestCase):
    def test_a_log_converted_twice_yields_one_row_of_each(self):
        rows, _ = read_lines([line(), line(id="0x1/1000/2")], "a")
        merged, problems = merge([rows, list(rows)])

        self.assertEqual(len(merged), 2)
        self.assertEqual(problems, [])

    def test_rows_come_out_in_the_order_they_happened(self):
        first, _ = read_lines([line(id="b", t=200.0)], "a")
        second, _ = read_lines([line(id="a", t=100.0)], "b")
        merged, _ = merge([first, second])

        self.assertEqual([row["id"] for row in merged], ["a", "b"])

    # Dropping the second silently would lose data the file plainly has
    def test_two_different_attempts_sharing_an_id_are_reported(self):
        first, _ = read_lines([line(id="a", skill="Magery")], "x")
        second, _ = read_lines([line(id="a", skill="Bowcraft")], "y")
        merged, problems = merge([first, second])

        self.assertEqual(len(merged), 1)
        self.assertEqual(len(problems), 1)
        self.assertIn("id a", problems[0])


class GainTest(unittest.TestCase):
    def test_a_tenth_reads_as_a_tenth_rather_than_as_binary_floating_point(self):
        self.assertEqual(gain_of({"from": 74.6, "to": 74.7}), 0.1)

    # A scroll of alacrity moves the skill several tenths at once, which is the whole reason a row
    # carries both values instead of assuming a band
    def test_an_alacrity_jump_reads_as_the_whole_jump(self):
        self.assertEqual(gain_of({"from": 74.6, "to": 74.9}), 0.3)

    def test_an_attempt_that_gained_nothing_reads_as_zero(self):
        self.assertEqual(gain_of({"from": 74.6, "to": 74.6}), 0.0)

    def test_an_unread_skill_has_no_gain_rather_than_a_gain_of_zero(self):
        self.assertIsNone(gain_of({"from": 74.6, "to": None}))


class StampTest(unittest.TestCase):
    def test_reads_as_utc(self):
        self.assertEqual(stamp(1757030042.5), "2025-09-04T23:54:02Z")


class TablesTest(unittest.TestCase):
    def test_an_attempt_becomes_one_row_with_both_values_and_the_gain(self):
        rows, _ = read_lines([line()], "a")
        attempts, consumed = tables(rows)

        self.assertEqual(len(attempts), 1)
        self.assertEqual(consumed, [])
        self.assertEqual(attempts[0]["character"], "Kaldor")
        self.assertEqual(attempts[0]["used"], "Bless")
        self.assertEqual(attempts[0]["skill_from"], "74.6")
        self.assertEqual(attempts[0]["skill_to"], "74.7")
        self.assertEqual(attempts[0]["gain"], "0.1")

    def test_a_row_written_before_used_existed_still_converts(self):
        rows, problems = read_lines([line().replace('"used":"Bless",', '')], "a")
        attempts, _ = tables(rows)

        self.assertEqual(problems, [])
        self.assertEqual(attempts[0]["used"], "")

    def test_a_failure_reads_as_one(self):
        rows, _ = read_lines([line(outcome="fizzled")], "a")
        attempts, _ = tables(rows)

        self.assertEqual(attempts[0]["outcome"], "fizzled")

    def test_an_unsettled_row_keeps_its_attempt_and_leaves_the_gain_empty(self):
        rows, _ = read_lines([line(to=None)], "a")
        attempts, _ = tables(rows)

        self.assertEqual(attempts[0]["skill_to"], "")
        self.assertEqual(attempts[0]["gain"], "")
        self.assertEqual(attempts[0]["skill_from"], "74.6")

    def test_every_material_becomes_its_own_row_against_the_attempt(self):
        rows, _ = read_lines([line(consumed='[{"name":"boards","graphic":"0x1bd7","hue":0,"qty":6},'
                                            '{"name":"feathers","graphic":"0x1bd1","hue":0,'
                                            '"qty":10}]')], "a")
        attempts, consumed = tables(rows)

        self.assertEqual(len(attempts), 1)
        self.assertEqual(len(consumed), 2)
        self.assertEqual([spent["id"] for spent in consumed], [attempts[0]["id"]] * 2)
        self.assertEqual(consumed[0], {"id": "0x1/1000/1", "name": "boards", "graphic": "0x1bd7",
                                       "hue": 0, "quantity": 6})
