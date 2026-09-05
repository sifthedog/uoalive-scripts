#!/usr/bin/env python3
"""Turns the .jsonl the Legion macros append into attempts.csv and consumed.csv.

    python3 legion/skilldb.py convert LegionScripts/skill-attempts.jsonl --out legion/data

Every file named is merged, so a log copied off each character joins one table. Rows already in the
output are recognised by their id, so converting the same log twice changes nothing.
"""

import argparse
import csv
import io
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))

from skilldb.convert import ATTEMPT_COLUMNS, CONSUMED_COLUMNS, merge, read_lines, tables


def read_file(path):
    with io.open(path, encoding="utf-8") as handle:
        return read_lines(handle.read().split("\n"), path)


def write_csv(path, columns, rows):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def convert(paths, out):
    batches = []
    problems = []

    for path in paths:
        rows, trouble = read_file(path)
        batches.append(rows)
        problems.extend(trouble)

    merged, clashes = merge(batches)
    problems.extend(clashes)

    attempts, consumed = tables(merged)

    if not os.path.isdir(out):
        os.makedirs(out)

    write_csv(os.path.join(out, "attempts.csv"), ATTEMPT_COLUMNS, attempts)
    write_csv(os.path.join(out, "consumed.csv"), CONSUMED_COLUMNS, consumed)

    for problem in problems:
        print("skipped %s" % problem)

    print("%d attempts, %d consumed row(s) -> %s"
          % (len(attempts), len(consumed), out))

    return 0


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command")

    convert_parser = commands.add_parser("convert", help="merge .jsonl logs into the two tables")
    convert_parser.add_argument("logs", nargs="+", help="the .jsonl files the macros appended to")
    convert_parser.add_argument("--out", default=os.path.join(ROOT, "data"),
                                help="where the CSVs go (default legion/data)")

    args = parser.parse_args(argv)

    if args.command != "convert":
        parser.print_help()

        return 1

    return convert(args.logs, args.out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
