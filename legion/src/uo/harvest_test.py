import unittest

from test_support.uo import install, item
from uo.harvest import Harvester

CONFIG = {
    "prompt_text": ["Where do you wish to dig"],
    "cursor_timeout": 1.0,
    "cursor_poll": 0.1,
    "no_cursor_read": 0.2,
    "swing_timeout": 1.0,
}

BUCKETS = [("failed", ["You loosen some rocks"]), ("empty", ["nothing nearby to mine"])]

TOOL_SERIAL = 5


class FakeTool(object):
    def __init__(self, held):
        self._held = held

    def held(self):
        return self._held


class HarvesterTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.hold(item(serial=TOOL_SERIAL))
        self.total = 0
        self.said = []

    def resource_total(self):
        return self.total

    def make(self, tool=None, cancel_pathfinding=True):
        return Harvester(self.resource_total, BUCKETS, CONFIG, self.said.append, "dig", "dug",
                         "swing_timeout", tool=tool, cancel_pathfinding=cancel_pathfinding)

    # The shard raises the cursor as a side effect of UseObject; forget() at the top of
    # swing_once would erase anything heard before it, so this stands in for that response
    def open_cursor_on_use(self):
        real_use_object = self.api.UseObject

        def use_object(serial):
            real_use_object(serial)
            self.api.hear(*CONFIG["prompt_text"])

        self.api.UseObject = use_object

    def test_a_journal_match_wins(self):
        self.open_cursor_on_use()
        harvester = self.make()

        def aim():
            self.api.hear("You loosen some rocks but fail to find any useable ore")

        self.assertEqual(harvester.swing_once(TOOL_SERIAL, aim), "failed")

    def test_silence_with_more_resource_reads_as_made(self):
        self.open_cursor_on_use()
        harvester = self.make()

        def aim():
            self.total += 1

        self.assertEqual(harvester.swing_once(TOOL_SERIAL, aim), "dug")

    def test_silence_with_no_more_resource_is_unknown(self):
        self.open_cursor_on_use()
        harvester = self.make()

        self.assertEqual(harvester.swing_once(TOOL_SERIAL, lambda: None), "unknown")

    def test_the_tool_gone_is_worn_out(self):
        self.open_cursor_on_use()
        harvester = self.make()
        del self.api.items[TOOL_SERIAL]

        self.assertEqual(harvester.swing_once(TOOL_SERIAL, lambda: None), "wornOut")

    def test_no_cursor_at_all_without_a_tool(self):
        harvester = self.make()

        self.assertEqual(harvester.swing_once(TOOL_SERIAL, lambda: None), "noCursor")
        self.assertEqual(self.said, ["no target cursor - the shard never asked where to dig"])

    def test_no_cursor_names_the_tool_in_hand(self):
        harvester = self.make(tool=FakeTool(item(graphic=0xF39, name="a pickaxe")))

        self.assertEqual(harvester.swing_once(TOOL_SERIAL, lambda: None), "noCursor")
        self.assertEqual(self.said,
                          ["no target cursor - hand a pickaxe, the shard never asked where to dig"])

    def test_no_cursor_with_an_empty_hand(self):
        harvester = self.make(tool=FakeTool(None))

        self.assertEqual(harvester.swing_once(TOOL_SERIAL, lambda: None), "noCursor")
        self.assertEqual(self.said,
                          ["no target cursor - hand empty, the shard never asked where to dig"])

    def test_a_running_pathfind_is_cancelled_before_the_swing(self):
        self.open_cursor_on_use()
        self.api.pathfinding = True
        harvester = self.make()

        harvester.swing_once(TOOL_SERIAL, lambda: None)

        self.assertEqual(self.api.cancelled_pathfinding, 1)

    def test_cancel_pathfinding_false_leaves_it_running(self):
        self.open_cursor_on_use()
        self.api.pathfinding = True
        harvester = self.make(cancel_pathfinding=False)

        harvester.swing_once(TOOL_SERIAL, lambda: None)

        self.assertEqual(self.api.cancelled_pathfinding, 0)
        self.assertTrue(self.api.pathfinding)

    def test_a_stale_cursor_is_cancelled_before_the_swing(self):
        self.open_cursor_on_use()
        self.api.has_target = True
        harvester = self.make()

        harvester.swing_once(TOOL_SERIAL, lambda: None)

        self.assertEqual(self.api.cancelled_targets, 1)

    def test_the_aim_callback_is_invoked_once_the_cursor_opens(self):
        self.open_cursor_on_use()
        harvester = self.make()
        calls = []

        harvester.swing_once(TOOL_SERIAL, lambda: calls.append(1))

        self.assertEqual(calls, [1])


if __name__ == "__main__":
    unittest.main()
