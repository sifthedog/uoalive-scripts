import unittest

from taming.pet import Release, command_kill, rename_pet
from test_support.uo import install, mobile

RELEASE = {
    "menu_text": ["Release"],
    "buttons": [1, 2, 0],
    "confirm_text": ["release this creature"],
    "confirm_timeout": 1.0,
    "confirm_poll": 0.25,
    "attempts": 3,
    "timeout": 1.0,
    "poll": 0.25,
    "context_timeout": 2.0,
    "retry_delay": 0.5,
}

KILL = {
    "menu_text": ["Kill", "Attack"],
    "context_timeout": 2.0,
    "cursor_timeout": 2.0,
    "pick_timeout": 5.0,
    "pick_poll": 0.25,
}


class RenamePetTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.see(mobile(serial=5, name="a llama"))

    def test_renames_and_proves_it_by_the_name(self):
        def rename(serial, name):
            self.api.mobiles[serial].Name = name

        self.api.Rename = rename

        self.assertEqual(rename_pet(5, "sifinha", 3, 1.0, 0.25), "renamed")

    def test_a_name_that_never_lands_gives_up(self):
        self.assertEqual(rename_pet(5, "sifinha", 3, 1.0, 0.25), "unnamed")
        self.assertEqual(len(self.api.renamed), 3)

    def test_one_already_named_is_not_renamed_again(self):
        self.api.see(mobile(serial=5, name="Sifinha"))

        self.assertEqual(rename_pet(5, "sifinha", 3, 1.0, 0.25), "renamed")
        self.assertEqual(self.api.renamed, [])


class ReleaseTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.see(mobile(serial=5, is_renamable=True))
        self.said = []
        self.release = Release(RELEASE, self.said.append)

    def _let_go(self):
        self.api.mobiles[5].IsRenamable = False

    def test_no_menu_entry_at_all_reads_as_noentry(self):
        self.assertEqual(self.release.release(5), "noEntry")

    def test_releases_and_learns_the_button(self):
        self.api.menu_entries = set(["Release"])
        self.api.gump = 0

        def reply(button, gump=None):
            self._let_go()

        self.api.ReplyGump = reply
        self.api.Pause = lambda seconds: setattr(self.api, "gump", 88)

        self.assertEqual(self.release.release(5), "released")
        self.assertIn("the release gump answers to button 1", self.said)

    def test_says_once_when_no_gump_arrives(self):
        self.api.menu_entries = set(["Release"])
        self.release.release(5)

        self.assertEqual(self.said.count("found no gump to confirm the release with"), 1)

    def test_the_entry_going_away_after_a_press_proves_it_worked(self):
        self.api.menu_entries = set(["Release"])
        presses = [0]

        def menu(serial, text, timeout=None):
            presses[0] += 1

            return presses[0] == 1

        self.api.ContextMenu = menu

        self.assertEqual(self.release.release(5), "released")

    def test_closes_a_confirmation_nobody_answered(self):
        self.api.menu_entries = set(["Release"])
        self.api.Pause = lambda seconds: setattr(self.api, "gump", 88)

        self.assertEqual(self.release.release(5), "stillPet")
        self.assertEqual(self.api.closed_gumps, 1)

    def test_two_releases_do_not_share_the_learned_button(self):
        self.assertIsNone(Release(RELEASE, [].append)._button)


class CommandKillTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []

    def test_no_menu_entry_reads_as_noentry(self):
        self.assertEqual(command_kill(5, "sifinha", KILL, self.said.append), "noEntry")

    def test_no_cursor_reads_as_nocursor(self):
        self.api.menu_entries = set(["Kill"])

        self.assertEqual(command_kill(5, "sifinha", KILL, self.said.append), "noCursor")

    def _menu_raises_the_cursor(self):
        def menu(serial, text, timeout=None):
            self.api.has_target = True

            return text == "Kill"

        self.api.ContextMenu = menu

    def test_a_cursor_the_player_answers_reads_as_ordered(self):
        self._menu_raises_the_cursor()
        self.api.Pause = lambda seconds: setattr(self.api, "has_target", False)

        self.assertEqual(command_kill(5, "sifinha", KILL, self.said.append), "ordered")
        self.assertIn("told 'sifinha' to kill - pick its target", self.said)

    def test_a_cursor_nobody_answers_reads_as_unanswered(self):
        self._menu_raises_the_cursor()

        self.assertEqual(command_kill(5, "sifinha", KILL, self.said.append), "unanswered")
