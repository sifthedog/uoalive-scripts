import API

from uo.survey import survey
from uo.text import any_in


class Veins(object):
    def __init__(self, terrain, memory, config, log):
        self._terrain = terrain
        self._memory = memory
        self._config = config
        self._log = log

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

    def survey(self, radius, limit):
        survey(self._terrain.box(radius), radius, limit, self.matches, self._log)
