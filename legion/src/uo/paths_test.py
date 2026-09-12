import unittest

from test_support.uo import install
from uo.paths import beside_script


class BesideScriptTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_a_bare_name_lands_beside_the_running_script(self):
        self.api.ScriptPath = "/Users/me/TazUO/LegionScripts/bowcraft.py"

        self.assertEqual(beside_script("skill-attempts.jsonl"),
                         "/Users/me/TazUO/LegionScripts/skill-attempts.jsonl")

    def test_a_windows_path_is_cut_the_same_way(self):
        self.api.ScriptPath = "C:\\TazUO\\LegionScripts\\bowcraft.py"

        self.assertEqual(beside_script("skill-attempts.jsonl"),
                         "C:\\TazUO\\LegionScripts\\skill-attempts.jsonl")

    def test_a_path_with_a_folder_is_left_as_written(self):
        self.api.ScriptPath = "/Users/me/TazUO/LegionScripts/bowcraft.py"

        self.assertEqual(beside_script("/tmp/attempts.jsonl"), "/tmp/attempts.jsonl")
        self.assertEqual(beside_script("data/attempts.jsonl"), "data/attempts.jsonl")

    def test_without_a_script_path_the_name_stands(self):
        self.assertEqual(beside_script("skill-attempts.jsonl"), "skill-attempts.jsonl")
        self.assertEqual(beside_script(""), "")
