import API

from uo.journal import said
from uo.pack import amount_of, hue_of, pack_contents


def serial_key(a, b):
    if a.Serial < b.Serial:
        return "s%d:%d" % (a.Serial, b.Serial)

    return "s%d:%d" % (b.Serial, a.Serial)


def hue_key(a, b):
    low, high = sorted([hue_of(a), hue_of(b)])

    return "h%d:%d" % (low, high)


# Never for hue 0, which is both iron and 'the client has not said yet'
def hue_tells_apart(a, b):
    return hue_of(a) != 0 and hue_of(b) != 0 and hue_of(a) != hue_of(b)


class Combiner(object):
    def __init__(self, ore, metals, config, log):
        self._ore = ore
        self._metals = metals
        self._config = config
        self._log = log

        # The backstop for the piles no tooltip named. Remembered by serial, which is why it cannot
        # carry a run alone: every swing delivers a pile wearing a serial nothing is known about.
        self._differing = set()

        # This call only: a silent miss is as likely to be a busy moment as a verdict, and
        # remembering it for the run would split two piles of one metal for good
        self._skipped = set()

    def _describe(self, item):
        metal = self._metals.of(item)

        return "%d %s" % (amount_of(item), metal if metal is not None else "hue %d" % hue_of(item))

    # Only ever forbids: one pile the tooltip could not name must not split its own metal
    def _metal_tells_apart(self, a, b):
        mine = self._metals.of(a)
        theirs = self._metals.of(b)

        return mine is not None and theirs is not None and mine != theirs

    def _differs(self, a, b):
        # A pile whose tooltip is still in flight is paired with nothing at all - guessing at it
        # earned a refusal every cycle, and one more swing loose costs the pack nothing
        return (
            self._metals.pending(a)
            or self._metals.pending(b)
            or self._metal_tells_apart(a, b)
            or serial_key(a, b) in self._differing
            or serial_key(a, b) in self._skipped
            or (hue_tells_apart(a, b) and hue_key(a, b) in self._differing)
        )

    def _same_metal(self, a, b):
        mine = self._metals.of(a)

        return mine is not None and mine == self._metals.of(b)

    # A merge is silent either way, so the pack is the evidence: the consumed pile gone, or the pile
    # it went into grown. The refusal cuts the wait short, or a pack holding two metals spends the
    # whole timeout on every swing.
    def _merged(self, primary, dup, before):
        waited = 0.0

        while waited < self._config["timeout"]:
            grown = None
            dup_here = False

            for item in pack_contents():
                if item.Serial == primary.Serial:
                    grown = item
                elif item.Serial == dup.Serial:
                    dup_here = True

            if not dup_here or (grown is not None and amount_of(grown) > before):
                return True

            if said(self._config["different_text"]):
                return False

            API.Pause(self._config["poll"])
            waited += self._config["poll"]

        return False

    def _combine(self, primary, dup):
        before = amount_of(primary)

        API.ClearJournal()

        # No cancel before the use: a cursor cancelled shortly before an action has been measured
        # costing that action its own cursor
        API.UseObject(dup.Serial)

        if not API.WaitForTarget("any", self._config["target_timeout"]):
            API.CancelTarget()
            self._skipped.add(serial_key(primary, dup))
            self._log("no target cursor for %s" % self._describe(dup))

            return

        API.Target(primary.Serial)

        if self._merged(primary, dup, before):
            return

        # Nothing was attempted, so nothing has been learned about the metals
        if said(self._config["throttled_text"]):
            self._log("the shard says wait, leaving the two of them paired")

            return

        if said(self._config["different_text"]):
            metal = self._metals.of(primary)

            if metal is not None and metal == self._metals.of(dup):
                self._metals.doubt(metal)

            self._differing.add(serial_key(primary, dup))

            if hue_tells_apart(primary, dup):
                self._differing.add(hue_key(primary, dup))

            return

        self._skipped.add(serial_key(primary, dup))
        self._log("%s and %s did not merge and nothing was said"
                  % (self._describe(primary), self._describe(dup)))

    # The first pile that can join one already seen. Everything ahead of it is a family of its own,
    # so returning nothing means every pile in the pack is a metal of its own.
    def _next_pair(self, piles):
        primaries = []

        for pile in piles:
            home = None

            # The tooltip's metal first, then hue: hue is right nearly always, and wrong costs a
            # refusal
            for primary in primaries:
                if self._same_metal(primary, pile) and not self._differs(primary, pile):
                    home = primary
                    break

            if home is None:
                for primary in primaries:
                    if hue_of(primary) == hue_of(pile) and not self._differs(primary, pile):
                        home = primary
                        break

            if home is None:
                for primary in primaries:
                    if not self._differs(primary, pile):
                        home = primary
                        break

            if home is not None:
                return home, pile

            primaries.append(pile)

        return None

    def group(self):
        self._skipped.clear()
        self._metals.start_pass()

        for _attempt in range(self._config["attempts"]):
            piles = self._ore.piles()
            self._metals.forget_missing(piles)

            pair = self._next_pair(piles)

            if pair is None:
                if len(self._skipped) > 0 and len(piles) > 1:
                    self._log("left %d piles - %s"
                              % (len(piles), ", ".join(map(self._describe, piles))))

                return

            self._combine(pair[0], pair[1])
            API.Pause(self._config["delay"])

        self._log("hit the %d combine attempt backstop" % self._config["attempts"])
