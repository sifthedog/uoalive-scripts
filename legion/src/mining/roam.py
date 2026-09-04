import API

from uo.clock import now
from uo.scan import chebyshev_to


class Roam(object):
    """Walking to the next vein, and waiting where there is nothing left but a clock."""

    def __init__(self, veins, memory, saves, threat, config, log, heartbeat, stop_reason):
        self._veins = veins
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
        self._log("everything in reach is worked out, waiting for a vein to come back")
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

    # One of ('target', vein), ('walked',), ('waited',), ('stop', reason)
    def approach(self):
        vein, respawns_at = self._veins.scan()

        if vein is None:
            if respawns_at is not None:
                self._idle_until(respawns_at)

                return ("waited",)

            # Ore that matched everything and had no way to walk to it is the one cause the survey
            # below cannot show
            if self._veins.skipped_unreachable() > 0:
                self._log("%d vein(s) matched but had no walkable route"
                          % self._veins.skipped_unreachable())

            self._log("nothing within %dz of %d matched, here is what is around"
                      % (self._config["z_range"], API.Player.Z))
            self._veins.survey(self._config["scan_radius"], self._config["survey_arts"])

            return ("stop", "no ore in range")

        if vein["distance"] <= self._config["range"]:
            self._walking_to = None
            self._walking_cycles = 0

            return ("target", vein)

        key = "%d,%d" % (vein["x"], vein["y"])

        if self._walking_to != key:
            self._walking_to = key
            self._walking_cycles = 0

        self._walking_cycles += 1

        if self._walking_cycles > self._config["max_walks"]:
            self._memory.mark_unreachable(vein)
            self._walking_to = None
            self._walking_cycles = 0

            return ("walked",)

        before = vein["distance"]
        API.Pathfind(vein["x"], vein["y"], vein["z"], self._config["range"], True,
                     self._config["pathfind_timeout"])
        API.CancelPathfinding()

        # A step that does not move during a save is not a wall
        if chebyshev_to(vein) >= before and not self._saves.is_saving():
            self._memory.mark_unreachable(vein)
            self._walking_to = None
            self._walking_cycles = 0

        return ("walked",)
