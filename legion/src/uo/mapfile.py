import API


def _land_row(land):
    return [land[0]["z"], land[0]["graphic"]] if land else None


def _statics_row(statics):
    return [[tile["z"], tile["graphic"], tile["name"]] for tile in statics]


class MapFile(object):
    """The ground a run has read, kept between runs so a known place costs no reads."""

    def __init__(self, terrain, store, log):
        self._terrain = terrain
        self._store = store
        self._log = log

    def load(self):
        if not self._store.on():
            return 0

        here = int(API.GetMap())
        count = 0

        for row in self._store.load():
            try:
                if row["m"] != here:
                    continue

                x = row["x"]
                y = row["y"]
                land = row["l"]
                land = [{"x": x, "y": y, "z": land[0], "graphic": land[1], "is_land": True,
                         "name": ""}] if land else []
                statics = [{"x": x, "y": y, "z": s[0], "graphic": s[1], "is_land": False,
                            "name": s[2]} for s in row["s"]]
            except (KeyError, IndexError, TypeError):
                continue

            self._terrain.remember(x, y, land, statics)
            count += 1

        self._log("map: %d coordinate(s) remembered from %s" % (count, self._store.path()))

        return count

    def flush(self):
        if not self._store.on():
            return 0

        fresh = self._terrain.fresh()

        if not fresh:
            return 0

        here = int(API.GetMap())
        self._store.append([{"m": here, "x": int(x), "y": int(y), "l": _land_row(land),
                             "s": _statics_row(statics)} for (x, y), land, statics in fresh])

        return len(fresh)
