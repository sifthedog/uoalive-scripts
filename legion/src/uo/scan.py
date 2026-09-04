import API

from uo.clock import now


def chebyshev_to(tile):
    return max(abs(tile["x"] - API.Player.X), abs(tile["y"] - API.Player.Y))


def steps_to(tile, within):
    path = API.GetPath(tile["x"], tile["y"], tile["z"], within)

    return len(path) if path else None


# GetPath costs a call per candidate, where the web client's flood fill answered every tile at once,
# so only the nearest `probes` matches are asked for a route
def pick_nearest(candidates, memory, probes, within):
    """(the shortest route in reach, when the soonest cooling tile is back, how many were walled)"""
    live = []
    cooling = None

    for tile in candidates:
        until = memory.blocked_until(tile)

        if until is not None and now() < until:
            if until != float("inf") and (cooling is None or until < cooling):
                cooling = until

            continue

        live.append(tile)

    live.sort(key=chebyshev_to)

    best = None
    best_steps = None
    walled = 0

    for tile in live[:probes]:
        steps = steps_to(tile, within)

        if steps is None:
            walled += 1
            continue

        if best_steps is None or steps < best_steps:
            best = tile
            best_steps = steps

    if best is not None:
        best = dict(best)
        best["distance"] = chebyshev_to(best)

    return best, cooling, walled
