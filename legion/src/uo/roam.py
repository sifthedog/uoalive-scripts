import API

from uo.clock import now
from uo.scan import chebyshev_to


class Roam(object):
    """Walking to the next spot, and waiting where there is nothing left but a clock."""

    def __init__(self, source, memory, saves, threat, config, log, heartbeat, stop_reason):
        self._source = source
        self._memory = memory
        self._saves = saves
        self._threat = threat
        self._config = config
        self._log = log
        self._heartbeat = heartbeat
        self._stop_reason = stop_reason
        self._walking_to = None
        self._walking_cycles = 0

    def _idle_until(self, ready_at):
        self._log(self._config["idle_message"])
        said_at = now()

        while now() < ready_at:
            if self._stop_reason() is not None:
                return

            self._threat.look()

            if now() - said_at >= self._config["idle_log_every"]:
                said_at = now()
                self._log("%dm to go" % max(1, int(round((ready_at - now()) / 60.0))))

            API.Pause(self._config["idle_poll"])

        self._heartbeat.reset()

    # One of ('target', spot), ('walked',), ('waited',), ('stop', reason)
    def approach(self):
        spot, ready_at_or_none = self._source.scan()

        if spot is None:
            if ready_at_or_none is not None:
                if not self._config["wait"]:
                    return ("stop", "%s, the soonest is back in %dm" % (
                        self._config["worked_out"],
                        max(1, int(round((ready_at_or_none - now()) / 60.0)))))

                self._idle_until(ready_at_or_none)

                return ("waited",)

            # A match with no way to walk to it is the one cause the survey below cannot show
            if self._source.skipped_unreachable() > 0:
                self._log("%d %s(s) matched but had no walkable route"
                          % (self._source.skipped_unreachable(), self._config["noun"]))

            self._log("nothing within %dz of %d matched, here is what is around"
                      % (self._config["z_range"], API.Player.Z))
            self._source.survey(self._config["scan_radius"], self._config["survey_arts"])

            return ("stop", self._config["none_left"])

        if spot["distance"] <= self._config["range"]:
            self._walking_to = None
            self._walking_cycles = 0

            return ("target", spot)

        key = "%d,%d" % (spot["x"], spot["y"])

        if self._walking_to != key:
            self._walking_to = key
            self._walking_cycles = 0

        self._walking_cycles += 1

        if self._walking_cycles > self._config["max_walks"]:
            self._memory.mark_unreachable(spot)
            self._walking_to = None
            self._walking_cycles = 0

            return ("walked",)

        before = spot["distance"]
        API.Pathfind(spot["x"], spot["y"], spot["z"], self._config["range"], True,
                     self._config["pathfind_timeout"])
        API.CancelPathfinding()

        # A step that does not move during a save is not a wall
        if chebyshev_to(spot) >= before and not self._saves.is_saving():
            self._memory.mark_unreachable(spot)
            self._walking_to = None
            self._walking_cycles = 0

        return ("walked",)
