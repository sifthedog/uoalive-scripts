import unittest

from test_support.uo import install
from uo.menu import context_menu


class ContextMenuTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_is_false_when_no_entry_is_on_the_menu(self):
        self.assertFalse(context_menu(1, ["Kill", "Attack"], 2.0))

    def test_tries_each_wording_until_one_takes(self):
        self.api.menu_entries = set(["Attack"])

        self.assertTrue(context_menu(1, ["Kill", "Attack"], 2.0))
        self.assertEqual(self.api.menus, [(1, "Kill"), (1, "Attack")])

    def test_stops_at_the_first_that_takes(self):
        self.api.menu_entries = set(["Kill", "Attack"])
        context_menu(1, ["Kill", "Attack"], 2.0)

        self.assertEqual(self.api.menus, [(1, "Kill")])
