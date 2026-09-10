import API

from uo.clock import now


def chebyshev_to(tile):
    return max(abs(tile["x"] - API.Player.X), abs(tile["y"] - API.Player.Y))


# Moves, not points: the route the client returns starts with the tile you stand on
def steps_to(tile, within):
    path = API.GetPath(tile["x"], tile["y"], tile["z"], within)

    return len(path) - 1 if path else None


# A route that steps outside the box around the player goes round something - a wall, a cliff, a
# ramp elsewhere - so its end is not on the ground the player stands on
def route_leaves(path, radius):
    x1 = API.Player.X - radius
    y1 = API.Player.Y - radius
    x2 = API.Player.X + radius
    y2 = API.Player.Y + radius

    for point in path:
        if point.X < x1 or point.X > x2 or point.Y < y1 or point.Y > y2:
            return True

    return False


# GetPath costs a call per candidate, where the web client's flood fill answered every tile at once,
# so only the nearest `probes` matches are asked for a route
def pick_nearest(candidates, memory, probes, within, in_reach_is_free=False, stats=None):
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
        # Sorted by crow flight, so once the best is at most this far nothing later can beat it
        if best_steps is not None and best_steps <= max(0, chebyshev_to(tile) - within):
            break

        # Already in reach, so there is nothing to route and no probe worth paying for
        if in_reach_is_free and chebyshev_to(tile) <= within:
            steps = 0
        else:
            steps = steps_to(tile, within)

            if stats is not None:
                stats["probes"] = stats.get("probes", 0) + 1

        # A refused route is a full A* on the client, so it is not asked for again for a while
        if steps is None:
            memory.mark_unreachable(tile)
            walled += 1
            continue

        if best_steps is None or steps < best_steps:
            best = tile
            best_steps = steps

    if best is not None:
        best = dict(best)
        best["distance"] = chebyshev_to(best)

    return best, cooling, walled
