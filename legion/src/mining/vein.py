import API

from uo.clock import now
from uo.scan import chebyshev_to, pick_nearest
from uo.survey import survey
from uo.text import any_in


class Veins(object):
    def __init__(self, terrain, memory, config, log):
        self._terrain = terrain
        self._memory = memory
        self._config = config
        self._log = log
        self._current = None
        self._skipped_unreachable = 0
        self._banks = {}
        self._bank_cooling = None
        self.stats = {}

    def skipped_unreachable(self):
        return self._skipped_unreachable

    # Refusals first, seeds second: the land table ships full, so asking it first made the ban
    # silently do nothing - it was recorded and ignored on the next scan
    def is_ore(self, graphic, is_land, name):
        if graphic in self._config["not_ore_graphics"]:
            return False

        if self._memory.art_banned(graphic, is_land):
            return False

        # No name to fall back on, so the table is the whole answer for land
        if is_land:
            return graphic in self._config["tile_graphics"]

        return any_in(name, self._config["static_names"])

    def matches(self, tile):
        return self.is_ore(tile["graphic"], tile["is_land"], tile.get("name"))

    def within_z(self, z):
        return abs(z - API.Player.Z) <= self._config["z_range"]

    def _bank_key(self, x, y):
        bank = self._config["bank"]

        return (x // bank, y // bank)

    def _bank_parked_until(self, tile):
        until = self._banks.get(self._bank_key(tile["x"], tile["y"]))

        if until is None:
            return None

        if now() >= until:
            return None

        return until

    def is_parked(self, tile):
        return self._memory.is_blocked(tile) or self._bank_parked_until(tile) is not None

    def _candidates(self, radius, statics_only):
        box = self._terrain.statics_box if statics_only else self._terrain.box

        for tile in box(radius):
            if not self.matches(tile) or not self.within_z(tile["z"]):
                continue

            until = self._bank_parked_until(tile)

            if until is not None:
                if self._bank_cooling is None or until < self._bank_cooling:
                    self._bank_cooling = until

                continue

            yield tile

    def scan_box(self, radius, statics_only=False):
        self._bank_cooling = None
        # The swing names no tile, so one already in reach needs no route
        best, cooling, walled = pick_nearest(self._candidates(radius, statics_only), self._memory,
                                             self._config["probes"], self._config["range"], True,
                                             self.stats)
        self._skipped_unreachable = walled
        self.stats["walled"] = self.stats.get("walled", 0) + walled

        if self._bank_cooling is not None and (cooling is None or self._bank_cooling < cooling):
            cooling = self._bank_cooling

        return best, cooling

    # One pair of reads against the (2 * radius + 1) squared the box costs. The z and the art have
    # to match as well as the coordinates: a tile carries several, and only one of them is the vein.
    def _still_ore(self, vein):
        if self.is_parked(vein):
            return None

        # The character has walked since this was picked, and the vein is now up a cliff
        if not self.within_z(vein["z"]):
            return None

        for tile in self._terrain.at(vein["x"], vein["y"]):
            if (
                tile["z"] == vein["z"]
                and tile["graphic"] == vein["graphic"]
                and tile["is_land"] == vein["is_land"]
            ):
                if not self.matches(tile):
                    return None

                found = dict(vein)
                found["distance"] = chebyshev_to(vein)

                return found

        return None

    def _radii(self):
        return range(self._config["range"], self._config["scan_radius"] + 1)

    # Widened a ring at a time rather than swept, statics before land in each: the next vein is
    # almost always close, a ring's statics are one read, and each land tile is a read of its own
    def scan(self):
        started = now()
        reads = self._terrain.reads
        self.stats = {}

        try:
            return self._scan()
        finally:
            self.stats["seconds"] = now() - started
            self.stats["reads"] = self._terrain.reads - reads

    def _scan(self):
        if self._current is not None:
            self._current = self._still_ore(self._current)

            if self._current is not None:
                return self._current, None

        cooling = None

        for radius in self._radii():
            for statics_only in [True, False]:
                found, cooling = self.scan_box(radius, statics_only)

                if found is not None:
                    self._current = found

                    return found, None

        self._current = None

        return None, cooling

    def forget_current(self):
        self._current = None

    # The sentence is about the bank the character stands in. The reach circle as well: a walk stops
    # short of its target, which can leave the character in the bank swinging at a tile past its edge
    def mark_area_depleted(self, reach):
        until = now() + self._config["respawn_delay"]
        bank = self._config["bank"]
        self._banks[self._bank_key(API.Player.X, API.Player.Y)] = until
        parked = 0

        for tile in self._terrain.box(reach):
            # The sentence is about what the shard can reach, so a tile 60 z up is not its claim
            if not self.within_z(tile["z"]) or not self.matches(tile):
                continue

            self._memory.block(tile, until)
            parked += 1

        self._log("nothing harvestable at %d,%d, parking the %dx%d bank and %d tile(s) within %d "
                  "for %dm"
                  % (API.Player.X, API.Player.Y, bank, bank, parked, reach,
                     max(1, int(round(self._config["respawn_delay"] / 60.0)))))

        return parked

    def survey(self, radius, limit):
        survey(self._terrain.box(radius), radius, limit, self.matches, self._log)
