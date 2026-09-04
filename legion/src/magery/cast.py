import API

from uo.journal import matched_bucket


class Caster(object):
    def __init__(self, buckets, standing, self_target, skip_when_buffed, fallback_timeout,
                 fallback_delay, wait_slice, proof_grace, log):
        self._buckets = buckets
        self._standing = standing
        self._self_target = self_target
        self._skip_when_buffed = skip_when_buffed
        self._fallback_timeout = fallback_timeout
        self._fallback_delay = fallback_delay
        self._wait_slice = wait_slice
        self._proof_grace = proof_grace
        self._log = log

    # The wording wins over the two silent proofs, so it is read first on every slice: a fizzle that
    # somehow spent mana still reads as a fizzle. Giving up early once IsCasting has gone up and come
    # back down saves the rest of the budget; a shard that publishes no flag spends all of it.
    def _read_outcome(self, stage, up_before, mana_before):
        budget = stage.get("cast_timeout", self._fallback_timeout)
        wants_self = stage.get("target") == "self"
        waited = 0.0
        started = False
        ended = None
        answered = False

        while True:
            hit = matched_bucket(self._buckets)

            if hit is not None:
                return hit

            # Answered here rather than in a blocking wait before the poll: the pre-target usually
            # takes the cursor before the script sees one at all, and that wait was spent on every
            # cast
            if wants_self and not answered and API.HasTarget():
                answered = self._self_target.answer()

            # A transition, not a state: a buff already standing proves nothing, which is why
            # up_before is read before the cast
            if not up_before and self._standing(stage):
                return "cast"

            if API.Player.Mana < mana_before:
                return "cast"

            if API.Player.IsCasting:
                started = True

            elif started:
                if ended is None:
                    ended = waited

                # Not while a self row still has a cursor to answer: the shard raises it as the
                # incantation ends, so leaving on the flag falling walks out just before it appears
                elif waited - ended >= self._proof_grace and (answered or not wants_self):
                    return None

            if waited >= budget:
                return None

            API.Pause(self._wait_slice)
            waited += self._wait_slice

    def cast_once(self, stage):
        up_before = self._standing(stage)

        if self._skip_when_buffed and up_before:
            return "alreadyUp"

        mana_before = API.Player.Mana

        # Cancelled only when there is one to cancel: an unconditional cancel just before an action
        # left the next cursor unusable in the run this was copied from
        if API.HasTarget():
            API.CancelTarget()

        API.ClearJournal()

        wants_self = stage.get("target") == "self"

        # Queued before the cast, the order the client's own CastSpell example uses. The type has to
        # be the one the shard raises: these cursors report as beneficial, and a pre-target set to
        # neutral does not fire at all - it leaves the cursor standing and the cast unspent.
        if wants_self:
            try:
                API.PreTarget(API.Player.Serial, "beneficial")
            except Exception as error:
                self._log("PreTarget threw - %s" % error)

        API.CastSpell(stage["spell"])

        outcome = self._read_outcome(stage, up_before, mana_before)

        # Or a queued target the cast never used is still armed for whatever the next one raises
        if wants_self:
            API.CancelPreTarget()

        return outcome

    # The row's floor and nothing else. Waiting out IsRecovering as well made a Bless cycle several
    # seconds of standing still, and it buys nothing the shard does not already say: a cast issued
    # too early is refused in words, and that refusal costs one flat CASTING_WAIT.
    def pace(self, stage):
        API.Pause(stage.get("cast_delay", self._fallback_delay))
