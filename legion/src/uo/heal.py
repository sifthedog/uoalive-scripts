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
