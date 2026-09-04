class Pace(object):
    """The shard's own skill timer, learned from its refusals rather than configured."""

    def __init__(self, floor, step, cap, ease_after):
        self._floor = floor
        self._step = step
        self._max = cap
        self._ease_after = ease_after
        self._delay = floor
        self._landed = 0

    def delay(self):
        return self._delay

    def refused(self):
        self._landed = 0
        self._delay = min(self._delay + self._step, self._max)

        return self._delay

    # Easing after a single success oscillates between an attempt and a refusal
    def landed(self):
        self._landed += 1

        if self._landed < self._ease_after:
            return self._delay

        self._landed = 0
        self._delay = max(self._floor, self._delay - self._step)

        return self._delay
