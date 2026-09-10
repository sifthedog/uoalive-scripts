import API


# Plain Python types, not the client's sbyte and ushort: json cannot write those, and a .NET string
# is only a str by courtesy
def land_tile(x, y, land):
    return {"x": int(x), "y": int(y), "z": int(land.Z), "graphic": int(land.Graphic),
            "is_land": True, "name": ""}


def static_tile(x, y, static):
    return {"x": int(x), "y": int(y), "z": int(static.Z), "graphic": int(static.Graphic),
            "is_land": False, "name": str(static.Name or "")}


class Terrain(object):
    """Land and statics do not change during a session, so a coordinate is read once. Every read is
    a client frame, which is why the statics of a box come in one call and the land only on demand."""

    def __init__(self):
        self._land = {}
        self._statics = {}
        self._fresh = set()
        self.reads = 0

    def _land_at(self, x, y):
        cached = self._land.get((x, y))

        if cached is None:
            self.reads += 1
            land = API.GetTile(x, y)
            cached = [land_tile(x, y, land)] if land is not None else []
            self._land[(x, y)] = cached
            self._fresh.add((x, y))

        return cached

    def _statics_at(self, x, y):
        cached = self._statics.get((x, y))

        if cached is None:
            self.reads += 1
            cached = [static_tile(x, y, static) for static in API.GetStaticsAt(x, y) or []]
            self._statics[(x, y)] = cached
            self._fresh.add((x, y))

        return cached

    def _fill_statics(self, x1, y1, x2, y2):
        missing = [(x, y) for x in range(x1, x2 + 1) for y in range(y1, y2 + 1)
                   if (x, y) not in self._statics]

        if not missing:
            return

        self.reads += 1
        by_coord = {}

        for static in API.GetStaticsInArea(x1, y1, x2, y2) or []:
            by_coord.setdefault((static.X, static.Y), []).append(static)

        for x, y in missing:
            self._statics[(x, y)] = [static_tile(x, y, static)
                                     for static in by_coord.get((x, y), [])]
            self._fresh.add((x, y))

    def remember(self, x, y, land, statics):
        self._land[(x, y)] = land
        self._statics[(x, y)] = statics

    # Coordinates read this session with both halves in, handed out once
    def fresh(self):
        done = [xy for xy in self._fresh if xy in self._land and xy in self._statics]
        self._fresh.difference_update(done)

        return [(xy, self._land[xy], self._statics[xy]) for xy in sorted(done)]

    def at(self, x, y):
        return self._land_at(x, y) + self._statics_at(x, y)

    def _bounds(self, radius):
        return (API.Player.X - radius, API.Player.Y - radius,
                API.Player.X + radius, API.Player.Y + radius)

    def statics_box(self, radius):
        x1, y1, x2, y2 = self._bounds(radius)
        self._fill_statics(x1, y1, x2, y2)

        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                for tile in self._statics[(x, y)]:
                    yield tile

    def box(self, radius):
        x1, y1, x2, y2 = self._bounds(radius)
        self._fill_statics(x1, y1, x2, y2)

        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                for tile in self._land_at(x, y):
                    yield tile

                for tile in self._statics[(x, y)]:
                    yield tile
