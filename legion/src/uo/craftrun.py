"""The bookkeeping bowcraft, carpentry, tinkering and inscription all repeat: ending a cycle
through the stall watch, running a sell or unload trip, recording a craft's materials, and freeing
pack weight by selling or unloading when a restock is refused for it."""


def end_cycle(stall, phase, cycle, tally, stop):
    """Ends the cycle through the stall watch, keeping whichever stop reason came first: the
    caller's own, or the stall's if the caller had none yet."""
    stall.end_cycle(phase, cycle, tally)

    return stop if stop is not None else stall.reason()


class Unloader(object):
    """One dump, and how many trips in a row moved nothing."""

    def __init__(self, dump):
        self._dump = dump
        self.misses = 0

    def run(self):
        if self._dump.run() > 0:
            self.misses = 0

            return True

        self.misses += 1

        return False


class Seller(object):
    """One vendor, backed off and paused for a while once it buys nothing max_misses trips
    running - or the crafting would never get a turn."""

    def __init__(self, vendor, max_misses, retry_after, log):
        self._vendor = vendor
        self._max_misses = max_misses
        self._retry_after = retry_after
        self._log = log
        self.misses = 0
        self.paused_until = 0

    def forget(self):
        self.misses = 0
        self.paused_until = 0

    def due(self, cycle):
        return cycle >= self.paused_until

    def sell(self, titles, noun, cycle):
        if self._vendor.sell_trip(titles, noun):
            self.misses = 0

            return True

        self.misses += 1

        # Retried, but not every cycle: otherwise the crafting never gets a turn
        if self.misses >= self._max_misses:
            self.misses = 0
            self.paused_until = cycle + self._retry_after
            self._log("%d sell trips bought nothing - crafting on, and asking again in %d cycles"
                      % (self._max_misses, self._retry_after))

        return False


class CraftRecorder(object):
    """Measured either side of the craft rather than read off the recipe: a failure refunds part
    of it."""

    def __init__(self, recorder, materials, refund_settle, refund_poll):
        self._recorder = recorder
        self._materials = materials
        self._refund_settle = refund_settle
        self._refund_poll = refund_poll

    def record(self, outcome, skill_from, before, product):
        if not self._recorder.recording():
            return

        after = self._materials.settled_snapshot(self._refund_settle, self._refund_poll)
        self._recorder.record(skill_from, outcome, product, self._materials.spent(before, after))


# A pack the shard will not load for weight is emptied first, the way the band's products leave.
# sell and unload are each None, or (applies, held, run): zero-arg callables answering whether the
# trip is on for this band right now, how much is held, and whether running it moved anything.
# Tried in order, first one that applies and still holds something wins.
def make_room(restock, log, noun, sell=None, unload=None):
    if not restock.refused_for_weight():
        return None

    for phase, path in (("selling", sell), ("unloading", unload)):
        if path is None:
            continue

        applies, held_of, run = path

        if not applies():
            continue

        held = held_of()

        if held == 0:
            continue

        log("%s %d before loading more%s" % (phase, held, " " + noun if noun else ""))

        return phase if run() else None

    return None
