import API

from uo.clock import now
from uo.entity import hex_of
from uo.scan import chebyshev_to, route_leaves
from uo.tiles import art_key

SPOT_MARKS = "123456789abcdefghijklmnopqrstuvwxyz"


def footprint(x, y, reach):
    return [(x + dx, y + dy) for dy in range(-reach, reach + 1) for dx in range(-reach, reach + 1)]


def _chebyshev(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _soonest(a, b):
    if b is None or b == float("inf"):
        return a

    if a is None or b < a:
        return b

    return a


def cover(ore, candidates, reach, min_ore, start):
    near = set()

    for x, y in ore:
        near.update(footprint(x, y, reach))

    pool = {}

    for xy in candidates:
        if xy in near:
            pool[xy] = set(footprint(xy[0], xy[1], reach))

    uncovered = set(ore)
    picked = []

    while pool and uncovered:
        best = None
        best_rank = None

        for xy, foot in pool.items():
            count = len(uncovered & foot)

            if count < max(1, min_ore):
                continue

            rank = (-count, _chebyshev(xy, start), xy[1], xy[0])

            if best_rank is None or rank < best_rank:
                best = xy
                best_rank = rank

        if best is None:
            break

        picked.append(best)
        uncovered -= pool.pop(best)

    return picked


def route(spots, start):
    left = list(spots)
    at = start
    ordered = []

    while left:
        best = min(left, key=lambda xy: _chebyshev(xy, at))
        ordered.append(best)
        left.remove(best)
        at = best

    return ordered


def ascii_map(bounds, ore, spots, player):
    x1, y1, x2, y2 = bounds
    marks = {}

    for xy in ore:
        marks[xy] = "#"

    for index, xy in enumerate(spots):
        marks[xy] = SPOT_MARKS[index] if index < len(SPOT_MARKS) else "+"

    marks[player] = "@"

    return ["".join(marks.get((x, y), ".") for x in range(x1, x2 + 1)) for y in range(y1, y2 + 1)]


class Planner(object):
    """Spots and ore keep separate memories: a spot on a cave floor is keyed as the ore under it,
    and Roam writing the spot off would otherwise park the ore."""

    def __init__(self, veins, terrain, memory, spots, config, log):
        self._veins = veins
        self._terrain = terrain
        self._memory = memory
        self._spots = spots
        self._config = config
        self._log = log
        self._queue = []
        self._current = None
        self._skipped_unreachable = 0
        self._unstandable = set()
        self.stats = {}

    def skipped_unreachable(self):
        return self._skipped_unreachable

    def survey(self, radius, limit):
        self._veins.survey(radius, limit)

    def _is_ore(self, tile):
        return self._veins.matches(tile) and self._veins.within_z(tile["z"])

    def _live_ore_at(self, x, y):
        return [tile for tile in self._terrain.at(x, y)
                if self._is_ore(tile) and not self._memory.is_blocked(tile)]

    def _live_ore_in(self, x, y):
        tiles = []

        for cx, cy in footprint(x, y, self._config["reach"]):
            tiles.extend(self._live_ore_at(cx, cy))

        return tiles

    # A matching static is a cave floor, which is both the ore and what you stand on
    def _stand_tile(self, x, y):
        land = None

        for tile in self._terrain.at(x, y):
            if not self._veins.within_z(tile["z"]):
                continue

            if not tile["is_land"]:
                if self._veins.matches(tile):
                    return tile
            else:
                land = tile

        return land

    def _bare_land(self, x, y):
        tiles = self._terrain.at(x, y)

        return len(tiles) == 1 and tiles[0]["is_land"]

    def _with_distance(self, spot):
        found = dict(spot)
        found["distance"] = chebyshev_to(spot)

        return found

    def _count_probe(self):
        self.stats["probes"] = self.stats.get("probes", 0) + 1

    # Impassability is a property of the land art, so one refusal on bare land rules the art out
    # for the run; a static could be the obstacle instead, so those only rule out the one spot
    def _probe(self, spot):
        self._count_probe()
        path = API.GetPath(spot["x"], spot["y"], spot["z"], 0)

        if path and self._config["connected"] and route_leaves(path, self._config["scan_radius"]):
            self._skipped_unreachable += 1
            self.stats["off_ground"] = self.stats.get("off_ground", 0) + 1
            self._spots.mark_unreachable(spot)
            self._log("the spot at %d,%d is off your ground, the route to it leaves the box"
                      % (spot["x"], spot["y"]))

            return False

        if path:
            return True

        self._skipped_unreachable += 1
        self.stats["walled"] = self.stats.get("walled", 0) + 1

        if spot["is_land"] and self._bare_land(spot["x"], spot["y"]):
            self._count_probe()

            if API.GetPath(spot["x"], spot["y"], spot["z"], 1):
                self._unstandable.add(art_key(spot["graphic"], True))
                self._log("land %s cannot be stood on, planning beside it from here on"
                          % hex_of(spot["graphic"]))

                return False

        self._spots.mark_unreachable(spot)

        return False

    def _replan(self):
        radius = self._config["scan_radius"]
        reach = self._config["reach"]
        me = (API.Player.X, API.Player.Y)
        ore = {}
        parked = 0
        cooling = None

        for tile in self._terrain.box(radius):
            if not self._is_ore(tile):
                continue

            until = self._memory.blocked_until(tile)

            if until is not None and now() < until:
                parked += 1
                cooling = _soonest(cooling, until)
                continue

            ore[(tile["x"], tile["y"])] = tile

        candidates = {}
        inner = radius - reach

        for x in range(me[0] - inner, me[0] + inner + 1):
            for y in range(me[1] - inner, me[1] + inner + 1):
                tile = self._stand_tile(x, y)

                if tile is None or art_key(tile["graphic"], tile["is_land"]) in self._unstandable:
                    continue

                until = self._spots.blocked_until(tile)

                if until is not None and now() < until:
                    cooling = _soonest(cooling, until)
                    continue

                candidates[(x, y)] = tile

        order = route(cover(set(ore), sorted(candidates), reach, self._config["min_ore"], me), me)
        self._queue = [dict(candidates[xy]) for xy in order]
        self.stats["spots"] = len(order)
        self._log("plan: %d spot(s) over %d ore tile(s) within %d, %d parked"
                  % (len(order), len(ore), radius, parked))

        if ore and not order:
            self._log("%d ore tile(s) with no spot to stand on" % len(ore))

        if self._config["map"] and (ore or parked):
            bounds = (me[0] - radius, me[1] - radius, me[0] + radius, me[1] + radius)
            self._log("map: # ore, @ you, spots numbered in walking order, one row per line")

            for row in ascii_map(bounds, ore, order, me):
                self._log(row)

        return cooling

    def scan(self):
        started = now()
        reads = self._terrain.reads
        self.stats = {}
        self._skipped_unreachable = 0

        try:
            return self._scan()
        finally:
            self.stats["seconds"] = now() - started
            self.stats["reads"] = self._terrain.reads - reads

    def _scan(self):
        min_ore = max(1, self._config["min_ore"])

        if self._current is not None:
            current = self._current

            if self._spots.is_blocked(current) or len(self._live_ore_in(current["x"], current["y"])) < min_ore:
                self._current = None
            else:
                return self._with_distance(current), None

        budget = self._config["probes"]
        cooling = None

        # Bounded on the stop button: once it is pressed every client call answers with nothing, and
        # a refused route would otherwise replan forever
        while not API.StopRequested:
            if not self._queue:
                cooling = _soonest(cooling, self._replan())

                if not self._queue:
                    return None, cooling

            spot = self._queue.pop(0)
            until = self._spots.blocked_until(spot)

            if until is not None and now() < until:
                cooling = _soonest(cooling, until)
                continue

            if art_key(spot["graphic"], spot["is_land"]) in self._unstandable:
                continue

            if len(self._live_ore_in(spot["x"], spot["y"])) < min_ore:
                continue

            # Past the budget a spot goes out unprobed and Roam's no-movement check writes it off,
            # unless the ground rule is on, whose whole point is that nothing unprobed is walked to
            if chebyshev_to(spot) > 0 and (budget > 0 or self._config["connected"]):
                budget -= 1

                if not self._probe(spot):
                    continue

            self._current = spot

            return self._with_distance(spot), None

        return None, cooling

    def lone_ore_art(self):
        tiles = self._live_ore_in(API.Player.X, API.Player.Y)
        keys = set(art_key(tile["graphic"], tile["is_land"]) for tile in tiles)

        return tiles[0] if len(keys) == 1 else None

    # Around the player rather than the planned spot: a walk that stopped short still parks what
    # the shard answered about
    def exhausted(self):
        reach = self._config["reach"]
        parked = 0

        for tile in self._live_ore_in(API.Player.X, API.Player.Y):
            self._memory.mark_depleted(tile)
            parked += 1

        self._current = None
        side = 2 * reach + 1
        self._log("worked out at %d,%d, parking %d ore tile(s) in the %dx%d for %dm, %d spot(s) left"
                  % (API.Player.X, API.Player.Y, parked, side, side,
                     max(1, int(round(self._config["respawn_delay"] / 60.0))), len(self._queue)))

        return parked
