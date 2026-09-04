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

    def _candidates(self, radius):
        for tile in self._terrain.box(radius):
            if self.matches(tile) and self.within_z(tile["z"]):
                yield tile

    def scan_box(self, radius):
        best, cooling, walled = pick_nearest(self._candidates(radius), self._memory,
                                             self._config["probes"], self._config["range"])
        self._skipped_unreachable = walled

        return best, cooling

    # One pair of reads against the (2 * radius + 1) squared the box costs. The z and the art have
    # to match as well as the coordinates: a tile carries several, and only one of them is the vein.
    def _still_ore(self, vein):
        if self._memory.is_blocked(vein):
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

    # Widened rather than swept: a mountain face is wall-to-wall ore, so the tile that replaces a
    # worked out one is almost always within reach
    def scan(self):
        if self._current is not None:
            self._current = self._still_ore(self._current)

            if self._current is not None:
                return self._current, None

        near, _cooling = self.scan_box(self._config["range"])

        if near is not None:
            self._current = near

            return near, None

        found, cooling = self.scan_box(self._config["scan_radius"])
        self._current = found

        return found, cooling

    def forget_current(self):
        self._current = None

    # For the shard answering about where you stand rather than about a tile. Parking a single tile
    # left the character swinging at the spot the shard had just written off, for the same sentence.
    def mark_area_depleted(self, reach):
        until = now() + self._config["respawn_delay"]
        parked = 0

        for tile in self._terrain.box(reach):
            # The shard's sentence is about what it can reach, so parking a tile 60 z up would
            # record a claim it never made
            if not self.within_z(tile["z"]) or not self.matches(tile):
                continue

            self._memory.block(tile, until)
            parked += 1

        self._log("nothing harvestable at %d,%d, parking %d tile(s) within %d for %dm"
                  % (API.Player.X, API.Player.Y, parked, reach,
                     max(1, int(round(self._config["respawn_delay"] / 60.0)))))

        return parked

    def survey(self, radius, limit):
        survey(self._terrain.box(radius), radius, limit, self.matches, self._log)
