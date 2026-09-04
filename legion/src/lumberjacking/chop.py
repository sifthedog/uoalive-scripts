import API

from uo.entity import hex_of
from uo.journal import read_outcome, said


class Chopper(object):
    def __init__(self, wood, tool, buckets, config, log):
        self._wood = wood
        self._tool = tool
        self._buckets = buckets
        self._config = config
        self._log = log

    def _silent_outcome(self, serial, logs_before):
        if serial is not None and API.FindItem(serial) is None:
            return "wornOut"

        if self._wood.log_total() > logs_before:
            return "chopped"

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
    def _refused_outcome(self, serial, logs_before):
        matched = read_outcome(self._buckets, self._config["no_cursor_read"],
                               self._config["cursor_poll"])

        if matched is not None:
            return matched

        silent = self._silent_outcome(serial, logs_before)

        if silent != "unknown":
            return silent

        held = self._tool.held()
        self._log("no target cursor - hand %s, the shard never asked where to chop"
                  % ((held.Name or hex_of(held.Graphic)) if held is not None else "empty"))

        return "noCursor"

    def chop_once(self, serial, tree):
        # A pathfind still running would walk the character away mid-swing
        if API.Pathfinding():
            API.CancelPathfinding()

        # Cancelled only when there is one to cancel: an unconditional cancel a few hundred
        # milliseconds before the swing left the next cursor unusable in the run this was copied
        # from
        if API.HasTarget():
            API.CancelTarget()

        logs_before = self._wood.log_total()
        API.ClearJournal()

        API.UseObject(serial)

        if not self._cursor_opened():
            return self._refused_outcome(serial, logs_before)

        if self._config["aim_at_self"]:
            # This shard takes a self-target as 'harvest what is in reach' and picks the tree
            # itself, so nothing has to name a static. The scan still earns its place: it is what
            # decides where to stand, and 'in reach' is only ever the trunk you walked to.
            API.TargetSelf()
        else:
            # The four-argument overload, and the graphic is never left off: target.terrain with no
            # art hits the land tile, which the shard answers as mining rather than as chopping. A
            # static carries no serial, so naming the tile and its art is the only other way in.
            API.Target(tree["x"], tree["y"], tree["z"], tree["graphic"])

        matched = read_outcome(self._buckets, self._config["chop_timeout"],
                               self._config["cursor_poll"])

        return matched if matched is not None else self._silent_outcome(serial, logs_before)
