import API

from uo.journal import read_outcome
from uo.retry import settled


class Meditation(object):
    def __init__(self, skill, buckets, mana, meditating, log, saves, attempts, timeout,
                 start_timeout, wait_slice, regen_timeout):
        self._skill = skill
        self._buckets = buckets
        self._mana = mana
        self._meditating = meditating
        self._log = log
        self._saves = saves
        self._attempts = attempts
        self._timeout = timeout
        self._start_timeout = start_timeout
        self._wait_slice = wait_slice
        self._regen_timeout = regen_timeout
        self._refused = None

    def refused(self):
        return self._refused

    def _start_outcome(self):
        hit = read_outcome(self._buckets, self._start_timeout, self._wait_slice)

        if hit is not None:
            return hit

        # Silence is what every use looks like on a shard whose wordings this table has wrong, so
        # the buff is the proof that does not go through the journal at all
        if self._meditating() or settled(self._start_timeout, self._wait_slice, self._meditating):
            return "trance"

        return "unknown"

    def _for(self, need):
        for attempt in range(1, self._attempts + 1):
            # Using the skill again mid-trance is at best a wasted action and at worst the shard
            # ending the very trance this attempt is waiting on
            if not self._meditating():
                API.ClearJournal()
                API.UseSkill(self._skill)

                outcome = self._start_outcome()

                # Nothing here undresses the character, so a refusal is final for the run
                if outcome == "blocked" or outcome == "unskilled":
                    self._refused = "the shard refuses meditation (%s)" % outcome
                    self._log("%s - empty your hands; falling back on natural regeneration"
                              % self._refused)

                    return self._mana.watch(need, self._regen_timeout)

                # The shard knows the pool is full better than a stat read does
                if outcome == "full":
                    return True

                # A pause and not a refusal: nothing about meditation is learned from it
                if outcome == "saving":
                    self._saves.wait_out()

            if self._mana.watch(need, self._timeout):
                return True

            # Not 'gave up': a failed concentration roll, a trance broken by a hit and a use the
            # shard threw away all look like this, and all are answered by using the skill again
            self._log("meditation attempt %d did not fill the pool, using the skill again" % attempt)

        return False

    def regain(self, need, allowed):
        if self._mana.enough(need):
            return True

        self._log("%d mana, waiting for %d" % (API.Player.Mana, self._mana.target(need)))

        if allowed and self._refused is None:
            return self._for(need)

        return self._mana.watch(need, self._regen_timeout)
