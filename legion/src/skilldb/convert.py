"""Turns the macros' raw attempt log into the two tables.

Host-side CPython, run from legion/skilldb.py. Nothing here is bundled into a dist script, so it is
the one thing under src/ that is not held to what IronPython 3.4 can parse.
"""

import datetime
import json

VERSION = 1

ATTEMPT_COLUMNS = ["id", "ts", "at_utc", "character", "serial", "skill", "skill_from", "skill_to",
                   "gain", "outcome", "success"]

CONSUMED_COLUMNS = ["id", "name", "graphic", "hue", "quantity"]

REQUIRED = ("id", "t", "skill", "from", "outcome", "ok")


class Skipped(Exception):
    """A line the converter will not guess at. Reported with its origin, never fatal."""


def parse_line(text):
    try:
        row = json.loads(text)
    except ValueError as error:
        raise Skipped("not JSON (%s)" % error)

    if not isinstance(row, dict):
        raise Skipped("not an object")

    version = row.get("v")

    # Forward-compatible on purpose: a newer macro writing a shape this converter has not been
    # taught is a reason to say so and carry on, not to refuse the whole file
    if version != VERSION:
        raise Skipped("version %r, this reads version %d" % (version, VERSION))

    missing = [name for name in REQUIRED if name not in row]

    if missing:
        raise Skipped("no %s" % ", ".join(missing))

    return row


def read_lines(lines, origin):
    """(rows, problems) - a bad line costs itself and nothing else."""
    rows = []
    problems = []

    for number, text in enumerate(lines, start=1):
        if not text.strip():
            continue

        try:
            rows.append(parse_line(text))
        except Skipped as error:
            problems.append("%s:%d: %s" % (origin, number, error))

    return rows, problems


# First seen wins, so re-copying a log that has already been converted changes nothing. Sorted by
# when the attempt happened rather than by which file it arrived in.
#
# (rows, problems): a repeated id carrying a *different* row is not a re-conversion, it is two runs
# that minted the same id, and dropping the second silently would lose data the file plainly has.
def merge(batches):
    seen = {}
    order = []
    problems = []

    for rows in batches:
        for row in rows:
            first = seen.get(row["id"])

            if first is not None:
                if first != row:
                    problems.append("id %s is used by two different attempts" % row["id"])

                continue

            seen[row["id"]] = row
            order.append(row)

    return sorted(order, key=lambda row: (row["t"], row["id"])), problems


def gain_of(row):
    before = row.get("from")
    after = row.get("to")

    if before is None or after is None:
        return None

    # Rounded because the shard deals in tenths and 74.7 - 74.6 is 0.09999999999999432 in binary
    # floating point, which would turn every band in the table into its own value
    return round(after - before, 1)


def stamp(seconds):
    when = datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc)

    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def number(value):
    return "" if value is None else "%.1f" % value


def attempt_row(row):
    return {
        "id": row["id"],
        "ts": "%.3f" % row["t"],
        "at_utc": stamp(row["t"]),
        "character": row.get("char", ""),
        "serial": row.get("serial", ""),
        "skill": row["skill"],
        "skill_from": number(row.get("from")),
        "skill_to": number(row.get("to")),
        "gain": number(gain_of(row)),
        "outcome": row["outcome"],
        "success": "true" if row["ok"] else "false",
    }


# One row per material, joined back to the attempt by id: a craft can spend several things at once
# and a column pair per material would cap how many at whatever seemed enough today
def consumed_rows(row):
    rows = []

    for spent in row.get("consumed") or []:
        rows.append({
            "id": row["id"],
            "name": spent.get("name", ""),
            "graphic": spent.get("graphic", ""),
            "hue": spent.get("hue", 0),
            "quantity": spent.get("qty", 0),
        })

    return rows


def tables(rows):
    attempts = [attempt_row(row) for row in rows]
    consumed = []

    for row in rows:
        consumed.extend(consumed_rows(row))

    return attempts, consumed
