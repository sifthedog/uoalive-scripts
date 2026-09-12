import API

from uo.retry import settled


# The serial one cursor answered, or None for ESC or a timeout. Clears a cursor left open from
# before, and the one just answered too, so a target flag never survives past it.
def request_one(timeout):
    if API.HasTarget():
        API.CancelTarget()

    serial = API.RequestTarget(timeout)

    if API.HasTarget():
        API.CancelTarget()

    return serial or None


class SelfTarget(object):
    """The fallback for a cursor the pre-target did not take."""

    def __init__(self, answers, timeout, poll, log):
        self._answers = answers
        self._timeout = timeout
        self._poll = poll
        self._log = log
        self._learned = None

    # Target(player) is the one that worked on the probe run and is first for that reason; each is
    # guarded on its own, because Target is an overloaded C# method and the wrong shape throws
    def answer(self):
        for how in [self._learned] if self._learned else self._answers:
            try:
                if how == "Target(player)":
                    API.Target(API.Player)
                elif how == "TargetSelf":
                    API.TargetSelf()
                else:
                    API.Target(API.Player.Serial)
            except Exception as error:
                self._log("%s threw - %s" % (how, error))
                continue

            if settled(self._timeout, self._poll, lambda: not API.HasTarget()):
                if self._learned is None:
                    self._learned = how
                    self._log("the cursor answers to %s" % how)

                return True

        self._log("the cursor would not take a self target")

        return False
