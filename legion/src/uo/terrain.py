import API


class Terrain(object):
    """Land and statics do not change during a session, so a coordinate costs one pair of calls."""

    def __init__(self):
        self._cache = {}

    def at(self, x, y):
        cached = self._cache.get((x, y))

        if cached is not None:
            return cached

        tiles = []
        land = API.GetTile(x, y)

        if land is not None:
            tiles.append({"x": x, "y": y, "z": land.Z, "graphic": land.Graphic,
                          "is_land": True, "name": ""})

        for static in API.GetStaticsAt(x, y) or []:
            tiles.append({"x": x, "y": y, "z": static.Z, "graphic": static.Graphic,
                          "is_land": False, "name": static.Name or ""})

        self._cache[(x, y)] = tiles

        return tiles

    def box(self, radius):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                for tile in self.at(API.Player.X + dx, API.Player.Y + dy):
                    yield tile
