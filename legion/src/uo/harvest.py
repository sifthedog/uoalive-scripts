import API

from uo.entity import hex_of
from uo.journal import forget, forget_outcomes, read_outcome, said


class Harvester(object):
    """The swing lumberjacking's Chopper and mining's Digger share: use the tool, wait for a
    cursor, answer it, and read what the shard says three ways - the journal, silence with the
    pile larger, or the tool gone."""

    def __init__(self, resource_total, buckets, config, log, noun, made_outcome, swing_timeout_key,
                tool=None, cancel_pathfinding=True):
        self._resource_total = resource_total
        self._buckets = buckets
        self._config = config
        self._log = log
        self._noun = noun
        self._made_outcome = made_outcome
        self._swing_timeout_key = swing_timeout_key
        self._tool = tool
        self._cancel_pathfinding = cancel_pathfinding

    def _silent_outcome(self, serial, before):
        if serial is not None and API.FindItem(serial) is None:
            return "wornOut"

        if self._resource_total() > before:
            return self._made_outcome

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
    def _refused_outcome(self, serial, before):
        matched = read_outcome(self._buckets, self._config["no_cursor_read"],
                               self._config["cursor_poll"])

        if matched is not None:
            return matched

        silent = self._silent_outcome(serial, before)

        if silent != "unknown":
            return silent

        if self._tool is not None:
            held = self._tool.held()
            self._log("no target cursor - hand %s, the shard never asked where to %s"
                      % ((held.Name or hex_of(held.Graphic)) if held is not None else "empty",
                         self._noun))
        else:
            self._log("no target cursor - the shard never asked where to %s" % self._noun)

        return "noCursor"

    # aim is called with no arguments once the cursor is open, to answer it
    def swing_once(self, serial, aim):
        # A pathfind still running would walk the character away mid-swing
        if self._cancel_pathfinding and API.Pathfinding():
            API.CancelPathfinding()

        # Cancelled only when there is one to cancel: an unconditional cancel a few hundred
        # milliseconds before the swing left the next cursor unusable in the run this was copied
        # from
        if API.HasTarget():
            API.CancelTarget()

        before = self._resource_total()
        forget(self._config["prompt_text"])
        forget_outcomes(self._buckets)

        API.UseObject(serial)

        if not self._cursor_opened():
            return self._refused_outcome(serial, before)

        aim()

        matched = read_outcome(self._buckets, self._config[self._swing_timeout_key],
                               self._config["cursor_poll"])

        return matched if matched is not None else self._silent_outcome(serial, before)
