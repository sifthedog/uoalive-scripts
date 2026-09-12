#!/usr/bin/env python3
"""Checks the two bundler gaps fixed alongside this file: `import x as y` on a hoisted module, and a
top-level tuple/list assignment colliding with another module's name. Not under src/, so run-tests.py
does not find it; run directly with `python3 legion/build_test.py`."""

import ast
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build


class ImportAliasTest(unittest.TestCase):
    def test_a_hoisted_module_cannot_be_aliased(self):
        tree = ast.parse("import API as api\n")

        with self.assertRaises(build.BuildError):
            build.imports_of("src/whatever/index.py", tree)


class DuplicateTopLevelNameTest(unittest.TestCase):
    def test_a_tuple_assignment_colliding_with_a_def_is_rejected(self):
        folder = tempfile.mkdtemp()
        entry = os.path.join(folder, "index.py")

        handle = open(entry, "w")

        try:
            handle.write("x, y = 1, 2\n\n\ndef x():\n    pass\n")
        finally:
            handle.close()

        with self.assertRaises(build.BuildError):
            build.bundle({"in": entry, "out": "test"})


if __name__ == "__main__":
    unittest.main()
