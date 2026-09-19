import API

from uo.journal import read_outcome
from uo.pack import pack_contents


class Bandager(object):
    """Bandages the character it runs on; the hits rising are the proof, the wordings only explain."""

    def __init__(self, graphic, buckets, timeout, cursor_timeout, wait_slice, attempts, recovered,
                 saves, log):
        self._graphic = graphic
        self._buckets = buckets
        self._timeout = timeout
        self._cursor_timeout = cursor_timeout
        self._wait_slice = wait_slice
        self._attempts = attempts
        self._recovered = recovered
        self._saves = saves
        self._log = log
        self._ran_out = None

    def empty(self):
        return self._ran_out

    def in_pack(self):
        for item in pack_contents():
            if item.Graphic == self._graphic:
                return item

        return None

    def _apply_once(self):
        bandages = self.in_pack()

        if bandages is None:
            self._ran_out = "no bandages left in the pack"

            return False

        if API.HasTarget():
            API.CancelTarget()

        API.ClearJournal()
        API.UseObject(bandages.Serial)

        if not API.WaitForTarget("any", self._cursor_timeout):
            self._log("no cursor for the bandage")

            return False

        before = API.Player.Hits
        API.TargetSelf()

        outcome = read_outcome(self._buckets, self._timeout, self._wait_slice)

        if outcome == "noBandages":
            self._ran_out = "the shard says there are no bandages"

            return False

        if outcome == "saving":
            self._saves.wait_out()

        return API.Player.Hits > before or outcome == "healed"

    def mend(self):
        if self._recovered():
            return True

        if self._ran_out is not None:
            return False

        self._log("%d/%d hits, bandaging" % (API.Player.Hits, API.Player.HitsMax))

        for _attempt in range(self._attempts):
            if self._ran_out is not None:
                break

            self._apply_once()

            if self._recovered():
                self._log("healed to %d/%d" % (API.Player.Hits, API.Player.HitsMax))

                return True

            if API.Player.IsDead:
                break

        if self._ran_out is not None:
            self._log(self._ran_out)

        return False


class Healer(object):
    """Casts a heal at the caster until the hits are back up; the hits rising are the proof."""

    # hurt is the floor a mend starts at and recovered the mark it stops at: one predicate would
    # either heal on every chip or stop the moment the floor was cleared
    def __init__(self, caster, stage, gather_mana, hurt, recovered, attempts, log):
        self._caster = caster
        self._stage = stage
        self._gather_mana = gather_mana
        self._hurt = hurt
        self._recovered = recovered
        self._attempts = attempts
        self._log = log
        self._retired = None
        self._mending = False

    def retired(self):
        return self._retired

    # Read by the stop reason, which stands its health floor down while this is true
    def mending(self):
        return self._mending

    # A dry pool ends this mend and nothing more: the next cycle is another trance's worth of
    # regeneration away, and only a refusal nothing can answer retires the healing for good
    def _cast_once(self):
        if not self._gather_mana():
            self._log("the mana for %s did not come back" % self._stage["spell"])

            return False

        outcome = self._caster.cast_once(self._stage)

        if outcome == "noReagents":
            self._retired = "out of reagents for %s" % self._stage["spell"]
        elif outcome == "unskilled":
            self._retired = "the shard refuses %s from this character" % self._stage["spell"]

        return self._retired is None

    def mend(self):
        if self._recovered() or not self._hurt():
            return True

        if self._retired is not None:
            return False

        self._log("%d/%d hits, healing" % (API.Player.Hits, API.Player.HitsMax))
        self._mending = True

        try:
            for _attempt in range(self._attempts):
                carried = self._cast_once()

                if self._recovered():
                    self._log("healed to %d/%d" % (API.Player.Hits, API.Player.HitsMax))

                    return True

                if not carried or API.Player.IsDead:
                    break

                self._caster.pace(self._stage)
        finally:
            self._mending = False

        if self._retired is not None:
            self._log(self._retired)

        return False
