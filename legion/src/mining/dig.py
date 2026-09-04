import API

from uo.journal import read_outcome, said


class Digger(object):
    def __init__(self, ore, buckets, config, log, cancel_pathfinding):
        self._ore = ore
        self._buckets = buckets
        self._config = config
        self._log = log
        self._cancel_pathfinding = cancel_pathfinding

    def _silent_outcome(self, serial, ore_before):
        if serial is not None and API.FindItem(serial) is None:
            return "wornOut"

        if self._ore.total() > ore_before:
            return "dug"

        return "unknown"

    # HasTarget alone was not enough on the web client: a measured swing had the shard's prompt in
    # the journal at 164ms and the cursor flag false for the whole six seconds after it
    def _cursor_opened(self):
        waited = 0.0

        while waited < self._config["cursor_timeout"]:
            if API.HasTarget() or said(self._config["prompt_text"]):
                return True

            API.Pause(self._config["cursor_poll"])
            waited += self._config["cursor_poll"]

        return False

    # No cursor is not the same as nothing having happened: the commonest reason a shard declines a
    # swing is that it refused the action outright and said so
    def _refused_outcome(self, serial, ore_before):
        matched = read_outcome(self._buckets, self._config["no_cursor_read"],
                               self._config["cursor_poll"])

        if matched is not None:
            return matched

        silent = self._silent_outcome(serial, ore_before)

        if silent != "unknown":
            return silent

        self._log("no target cursor - the shard never asked where to dig")

        return "noCursor"

    def dig_once(self, serial):
        # A pathfind still running would walk the character away mid-swing
        if self._cancel_pathfinding and API.Pathfinding():
            API.CancelPathfinding()

        # Cancelled only when there is one to cancel: an unconditional cancel a few hundred
        # milliseconds before the swing left the next cursor unusable in the run this was copied
        # from
        if API.HasTarget():
            API.CancelTarget()

        ore_before = self._ore.total()
        API.ClearJournal()

        API.UseObject(serial)

        if not self._cursor_opened():
            return self._refused_outcome(serial, ore_before)

        # Answered with yourself rather than with the vein's coordinates: the shard takes that as
        # 'mine where I am' and picks the ore itself, so nothing has to guess land versus static
        API.TargetSelf()

        matched = read_outcome(self._buckets, self._config["dig_timeout"],
                               self._config["cursor_poll"])

        return matched if matched is not None else self._silent_outcome(serial, ore_before)
