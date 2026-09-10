import os
import tempfile
import unittest

from uo.store import Store


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.path = os.path.join(self.folder, "rows.jsonl")
        self.said = []
        self.store = Store(self.path, self.said.append)

    def tearDown(self):
        for name in os.listdir(self.folder):
            os.remove(os.path.join(self.folder, name))

        os.rmdir(self.folder)

    def test_a_missing_file_is_nothing_and_says_nothing(self):
        self.assertEqual(self.store.load(), [])
        self.assertEqual(self.said, [])

    def test_appends_come_back_in_order(self):
        self.store.append([{"a": 1}])
        self.store.append([{"b": 2}, {"c": 3}])

        self.assertEqual(self.store.load(), [{"a": 1}, {"b": 2}, {"c": 3}])

    def test_a_rewrite_replaces_the_file(self):
        self.store.append([{"a": 1}])
        self.store.rewrite([{"b": 2}])

        self.assertEqual(self.store.load(), [{"b": 2}])

    def test_a_broken_line_is_skipped_and_counted(self):
        handle = open(self.path, "w")
        handle.write('{"a": 1}\nnot json\n\n[1, 2]\n{"b": 2}\n')
        handle.close()

        self.assertEqual(self.store.load(), [{"a": 1}, {"b": 2}])
        self.assertEqual(self.said, ["2 unreadable line(s) in %s skipped" % self.path])

    def test_an_empty_path_is_off(self):
        store = Store("", self.said.append)
        store.append([{"a": 1}])

        self.assertFalse(store.on())
        self.assertEqual(store.load(), [])

    def test_an_unwritable_path_is_said_once(self):
        store = Store(os.path.join(self.folder, "missing", "rows.jsonl"), self.said.append)

        store.append([{"a": 1}])
        store.append([{"a": 2}])

        self.assertEqual(len(self.said), 1)
        self.assertTrue(self.said[0].startswith("could not write"))

    def test_a_row_the_encoder_refuses_is_said_once_and_not_raised(self):
        self.store.append([{"a": set([1])}])
        self.store.append([{"a": set([2])}])

        self.assertEqual(len(self.said), 1)
        self.assertTrue(self.said[0].startswith("could not write"))
