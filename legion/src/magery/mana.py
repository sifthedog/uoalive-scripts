import API


class ManaWatch(object):
    def __init__(self, to_full, poll, log_every, log, stop_reason, meditating):
        self._to_full = to_full
        self._poll = poll
        self._log_every = log_every
        self._log = log
        self._stop_reason = stop_reason
        self._meditating = meditating

    # Worked out on every read rather than once: ManaMax is 0 while the client refreshes stats, and
    # a ceiling taken in that window would either end the wait as it started or never end it at all
    def target(self, need):
        ceiling = API.Player.ManaMax

        if not self._to_full or ceiling <= 0:
            return need

        return max(need, ceiling)

    # >= and never !=: a regenerating pool passes a figure as often as it lands on it
    def enough(self, need):
        return API.Player.Mana >= self.target(need)

    # Sliced rather than slept through, so the guards get a look in and the pool is reported on
    def watch(self, need, budget):
        waited = 0.0
        since = 0.0

        while waited < budget:
            if self.enough(need):
                return True

            if self._stop_reason() is not None:
                return False

            API.Pause(self._poll)
            waited += self._poll
            since += self._poll

            if since >= self._log_every:
                since = 0.0
                self._log(
                    "%d/%d mana%s"
                    % (
                        API.Player.Mana,
                        self.target(need),
                        ", meditating" if self._meditating() else "",
                    )
                )

        return self.enough(need)
