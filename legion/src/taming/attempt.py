import API

from taming.quarry import is_pet
from uo.journal import read_outcome


class Tamer(object):
    def __init__(self, skill, buckets, resolution, start_timeout, resolve_timeout, wait_slice):
        self._skill = skill
        self._buckets = buckets
        self._resolution = resolution
        self._start_timeout = start_timeout
        self._resolve_timeout = resolve_timeout
        self._wait_slice = wait_slice

    def _settle(self, serial, was_pet, between):
        first = read_outcome(self._buckets, self._start_timeout, self._wait_slice, between)

        if first is not None and first != "starting":
            return first

        resolved = read_outcome(self._resolution, self._resolve_timeout, self._wait_slice, between)

        if resolved is not None:
            return resolved

        # Silence is what a shard with other wordings looks like, so the flag is the proof that does
        # not go through the journal - false to true, since one already renamable proves nothing
        if not was_pet and is_pet(serial):
            return "tamed"

        return "pending" if first == "starting" else "unknown"

    def tame_once(self, serial, between):
        if API.HasTarget():
            API.CancelTarget()

        was_pet = is_pet(serial)

        API.ClearJournal()

        # Pre-targeted rather than answered through a cursor of our own: a cursor left unanswered is
        # what leaves the next cycle asking while the shard is still resolving this attempt
        API.PreTarget(serial, "neutral")
        API.UseSkill(self._skill)

        try:
            return self._settle(serial, was_pet, between)
        finally:
            # Or an attempt the shard never answered leaves the pre-target armed for the next cycle
            API.CancelPreTarget()
