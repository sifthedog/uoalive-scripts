from uo.clock import now
from uo.entity import hex_of


# Land and static tiledata are numbered in separate tables, so 1339 is a mountain band as land and a
# cave floor as a static. Everything keyed on an art keys on the kind too.
def art_key(graphic, is_land):
    return "%s:%d" % ("land" if is_land else "static", graphic)


def tile_key(tile):
    return "%d,%d,%d,%s" % (tile["x"], tile["y"], tile["z"],
                            art_key(tile["graphic"], tile["is_land"]))


class TileMemory(object):
    """What is worked out, what could not be reached, and which art is not the resource at all."""

    def __init__(self, respawn_delay, unreachable_delay, noun, verb, log):
        self._respawn_delay = respawn_delay
        self._unreachable_delay = unreachable_delay
        self._noun = noun
        self._verb = verb
        self._log = log
        self._blocked = {}
        self._banned_arts = set()

    def blocked_until(self, tile):
        return self._blocked.get(tile_key(tile))

    def is_blocked(self, tile):
        until = self.blocked_until(tile)

        return until is not None and now() < until

    def block(self, tile, until):
        self._blocked[tile_key(tile)] = until

    def mark_depleted(self, tile):
        self.block(tile, now() + self._respawn_delay)

    def mark_unreachable(self, tile):
        self.block(tile, now() + self._unreachable_delay)

    def mark_unusable(self, tile, why):
        self.block(tile, float("inf"))
        self._log("the %s at %d,%d %s" % (self._noun, tile["x"], tile["y"], why))

    def art_banned(self, graphic, is_land):
        return art_key(graphic, is_land) in self._banned_arts

    # About the art, not the tile: a wrong entry in the table is a whole band of the mountain
    def ban_art(self, tile):
        key = art_key(tile["graphic"], tile["is_land"])

        if key in self._banned_arts:
            return

        self._banned_arts.add(key)
        self._log("%s cannot be %s, skipping that art from here on"
                  % (hex_of(tile["graphic"]), self._verb))
