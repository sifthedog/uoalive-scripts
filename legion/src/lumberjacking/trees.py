import API

from uo.clock import now
from uo.entity import hex_of
from uo.scan import chebyshev_to, pick_nearest
from uo.survey import survey
from uo.text import any_in


def as_tile(static):
    return {
        "x": static.X,
        "y": static.Y,
        "z": static.Z,
        "graphic": static.Graphic,
        "is_land": False,
        "name": static.Name or "",
        "flagged": bool(getattr(static, "IsTree", False)),
        "vegetation": bool(getattr(static, "IsVegetation", False)),
    }


def tree_marks(tile):
    marks = []

    if tile.get("flagged"):
        marks.append("IsTree")

    if tile.get("vegetation"):
        marks.append("IsVegetation")

    return marks


class Trees(object):
    def __init__(self, memory, config, log):
        self._memory = memory
        self._config = config
        self._log = log
        self._current = None
        self._skipped_unreachable = 0

    def skipped_unreachable(self):
        return self._skipped_unreachable

    # Overrides first, which is the opposite order to mining's is_ore and deliberate: that one asks
    # the refusals first because its land table ships full and would outrank a ban learned on the
    # shard. Both sets here ship empty, so the override gets asked first.
    def is_tree(self, graphic, name, flagged):
        if graphic in self._config["graphics"]:
            return True

        if graphic in self._config["not_graphics"]:
            return False

        if self._memory.art_banned(graphic, False):
            return False

        if flagged:
            return True

        return any_in(name, self._config["names"])

    def matches(self, tile):
        return self.is_tree(tile["graphic"], tile.get("name", ""), tile.get("flagged", False))

    def within_z(self, z):
        return abs(z - API.Player.Z) <= self._config["z_range"]

    # One call for the whole box, where mining pays a pair of reads per coordinate. There is no
    # terrain cache behind it for the same reason: a sweep is one call, and a felled tree that
    # changes art would go stale in one.
    def _statics_in(self, radius):
        x = API.Player.X
        y = API.Player.Y

        return API.GetStaticsInArea(x - radius, y - radius, x + radius, y + radius) or []

    def _candidates(self, radius):
        for static in self._statics_in(radius):
            tile = as_tile(static)

            if self.matches(tile) and self.within_z(tile["z"]):
                yield tile

    def scan_box(self, radius):
        best, cooling, walled = pick_nearest(self._candidates(radius), self._memory,
                                             self._config["probes"], self._config["range"], True)
        self._skipped_unreachable = walled

        return best, cooling

    # The z and the art have to match as well as the coordinates: a tile carries several statics,
    # and only one of them is the trunk that was picked
    def _still_tree(self, tree):
        if self._memory.is_blocked(tree) or not self.within_z(tree["z"]):
            return None

        for static in API.GetStaticsAt(tree["x"], tree["y"]) or []:
            if static.Z == tree["z"] and static.Graphic == tree["graphic"]:
                if not self.matches(as_tile(static)):
                    return None

                found = dict(tree)
                found["distance"] = chebyshev_to(tree)

                return found

        return None

    # Widened rather than swept twice: the roam radius is 49 tiles a side, and walking that many
    # statics through interop is only worth paying for on the cycle that would otherwise stand still
    def scan(self):
        if self._current is not None:
            self._current = self._still_tree(self._current)

            if self._current is not None:
                return self._current, None

        near, near_cooling = self.scan_box(self._config["scan_radius"])

        if near is not None:
            self._current = near

            return near, None

        found, cooling = self.scan_box(self._config["roam_radius"])
        self._current = found

        return found, cooling if cooling is not None else near_cooling

    def forget_current(self):
        self._current = None

    # For the shard answering about what it can reach rather than about a tile, which is what a
    # self-target asks it. Parking only the trunk the scan picked left mining swinging at the
    # neighbour the shard had just written off, for the same sentence.
    def mark_area_depleted(self, reach):
        until = now() + self._config["regrow_delay"]
        parked = 0

        for tile in self._candidates(reach):
            self._memory.block(tile, until)
            parked += 1

        self._log("nothing to chop at %d,%d, parking %d tree(s) within %d for %dm"
                  % (API.Player.X, API.Player.Y, parked, reach,
                     max(1, int(round(self._config["regrow_delay"] / 60.0)))))

        return parked

    def survey(self, radius, limit):
        survey([as_tile(static) for static in self._statics_in(radius)], radius, limit,
               self.matches, self._log, tree_marks)
