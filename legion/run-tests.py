#!/usr/bin/env python3
"""Runs the suite. Registers the fake API before discovery, the way vitest setupFiles does for src/."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")

sys.path.insert(0, SRC)

# A module under test binds API while it is being imported, so the fake has to be in place first
import test_support


def main():
    loader = unittest.defaultTestLoader
    suite = loader.discover(SRC, pattern="*_test.py", top_level_dir=SRC)

    if loader.errors:
        for error in loader.errors:
            print(error)

        return 1

    result = unittest.TextTestRunner(verbosity=1).run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
