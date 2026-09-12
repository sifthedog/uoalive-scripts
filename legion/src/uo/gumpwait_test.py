import unittest

from test_support.uo import install
from uo.gumpwait import wait_for_gump


class FakeGump(object):
    def __init__(self):
        self.IsDisposed = False
        self.disposed = 0

    def Dispose(self):
        self.IsDisposed = True
        self.disposed += 1


class WaitForGumpTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.gump = FakeGump()
        self.stop = [None]

    def stop_reason(self):
        return self.stop[0]

    def after_pauses(self, count, action):
        pauses = [0]

        def pause(seconds):
            pauses[0] += 1

            if pauses[0] == count:
                action()

        self.api.Pause = pause

    def test_resolve_winning_disposes_the_gump_and_returns_why(self):
        resolved = [False]

        def resolve():
            resolved[0] = True

            return "'Unload' was pressed"

        why = wait_for_gump(self.gump, self.stop_reason, 0.5, resolve)

        self.assertEqual(why, "'Unload' was pressed")
        self.assertTrue(self.gump.IsDisposed)

    def test_keeps_polling_until_resolve_answers(self):
        calls = [0]

        def resolve():
            calls[0] += 1

            return "done" if calls[0] >= 3 else None

        why = wait_for_gump(self.gump, self.stop_reason, 0.1, resolve)

        self.assertEqual(why, "done")
        self.assertEqual(calls[0], 3)

    def test_the_gump_closing_wins_when_resolve_has_nothing(self):
        self.after_pauses(1, lambda: setattr(self.gump, "IsDisposed", True))

        why = wait_for_gump(self.gump, self.stop_reason, 0.1, lambda: None)

        self.assertEqual(why, "the gump was closed")

    def test_a_custom_closed_message_is_used_instead(self):
        self.after_pauses(1, lambda: setattr(self.gump, "IsDisposed", True))

        why = wait_for_gump(self.gump, self.stop_reason, 0.1, lambda: None,
                            closed_message="the form was closed")

        self.assertEqual(why, "the form was closed")

    def test_a_reason_to_stop_wins_over_the_timeout(self):
        self.after_pauses(1, lambda: self.stop.__setitem__(0, "dead"))

        why = wait_for_gump(self.gump, self.stop_reason, 0.1, lambda: None, timeout=100.0)

        self.assertEqual(why, "the run has a reason to stop")

    def test_the_timeout_ends_the_wait(self):
        self.api.Pause = lambda seconds: None

        why = wait_for_gump(self.gump, self.stop_reason, 1.0, lambda: None, timeout=5.0)

        self.assertEqual(why, "nothing was pressed in 5s")

    def test_no_timeout_means_no_ceiling(self):
        self.after_pauses(50, lambda: setattr(self.gump, "IsDisposed", True))

        why = wait_for_gump(self.gump, self.stop_reason, 0.01, lambda: None)

        self.assertEqual(why, "the gump was closed")

    def test_a_stop_request_wins_immediately(self):
        calls = [0]

        def resolve():
            calls[0] += 1

            return None

        self.api.StopRequested = True

        why = wait_for_gump(self.gump, self.stop_reason, 0.1, resolve)

        self.assertEqual(why, "the run is being stopped")
        self.assertEqual(calls[0], 0)

    def test_each_runs_once_a_slice_before_resolve(self):
        order = []

        def each():
            order.append("each")

        def resolve():
            order.append("resolve")

            return "done" if len(order) >= 4 else None

        wait_for_gump(self.gump, self.stop_reason, 0.1, resolve, each=each)

        self.assertEqual(order, ["each", "resolve", "each", "resolve"])

    def test_a_disposed_gump_is_not_disposed_again(self):
        wait_for_gump(self.gump, self.stop_reason, 0.1, lambda: "done")

        self.assertEqual(self.gump.disposed, 1)


if __name__ == "__main__":
    unittest.main()
