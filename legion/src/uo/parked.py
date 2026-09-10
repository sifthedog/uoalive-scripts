import API

from uo.clock import now


class Parked(object):
    """Timed parkings kept between runs. Permanent write-offs are not: a restart is how those are
    cleared."""

    def __init__(self, store, log):
        self._store = store
        self._log = log

    # Rewritten pruned, so the file holds only what is still parked
    def load(self, memory):
        if not self._store.on():
            return 0

        here = int(API.GetMap())
        kept = {}

        for row in self._store.load():
            key = row.get("t")
            until = row.get("u")
            where = row.get("m")

            if not isinstance(key, str) or not isinstance(until, (int, float)):
                continue

            if now() >= until:
                continue

            kept[(where, key)] = {"m": where, "t": key, "u": until}

        restored = 0

        for (where, key), row in sorted(kept.items(), key=lambda item: item[1]["u"]):
            if where == here:
                memory.restore(key, row["u"])
                restored += 1

        self._store.rewrite(list(kept.values()))
        self._log("%d tile(s) still parked from the last run" % restored)

        return restored

    def save(self, key, until):
        if until == float("inf"):
            return

        self._store.append([{"m": int(API.GetMap()), "t": str(key), "u": float(until)}])
