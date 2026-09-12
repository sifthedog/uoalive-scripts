import API

# API.Player.Direction is a string, not a bitmask - confirmed live, after an earlier version of
# this tried "& 0x07" on it and threw. These are ClassicUO's own Direction enum names, matched
# case-insensitively; a running character may report an extra word (e.g. "North, Running"), so the
# match looks at each word rather than the whole string. Falls back to North if nothing matches.
NAMES = ["North", "Right", "East", "Down", "South", "Left", "West", "Up"]

# Index order matches NAMES: N, NE, E, SE, S, SW, W, NW
DELTAS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]


def facing():
    text = (API.Player.Direction or "").replace(",", " ")

    for word in text.split():
        for index, name in enumerate(NAMES):
            if word.lower() == name.lower():
                return index

    return 0


# A shoreline's water is commonly a static laid over plain grass, not a change to the land tile
# underneath - an earlier version read only the land tile there, named the grass, and the shard
# silently ignored every cast. A static match wins over the land tile it sits on; failing that, the
# plain land tile is used as given - that is what open ocean off a boat looks like, with no static
# to name at all - and fallback_graphic only covers a coordinate the client has no land data for.
# "source" is not read by the cast itself; it is there so a run can log which path a tile came from
def tile_ahead(tiles_ahead, land_graphics, static_graphics, fallback_graphic):
    dx, dy = DELTAS[facing()]
    x = API.Player.X + dx * tiles_ahead
    y = API.Player.Y + dy * tiles_ahead

    for static in API.GetStaticsAt(x, y) or []:
        if static.Graphic in static_graphics:
            return {"x": x, "y": y, "z": static.Z, "graphic": static.Graphic, "source": "static"}

    land = API.GetTile(x, y)

    if land is not None:
        source = "land" if land.Graphic in land_graphics else "land (unrecognized)"

        return {"x": x, "y": y, "z": land.Z, "graphic": land.Graphic, "source": source}

    return {"x": x, "y": y, "z": API.Player.Z, "graphic": fallback_graphic, "source": "fallback"}


def _is_water(x, y, land_graphics, static_graphics):
    for static in API.GetStaticsAt(x, y) or []:
        if static.Graphic in static_graphics:
            return True

    land = API.GetTile(x, y)

    return land is not None and land.Graphic in land_graphics


# The DELTAS/NAMES index of the nearest direction whose tile at tiles_ahead is recognized water -
# current facing checked first, so an already-good facing is never turned away from. None when none
# of the eight match; the water tables are a hypothesis, same as tile_ahead's own fallback
def water_direction(tiles_ahead, land_graphics, static_graphics):
    current = facing()
    order = [current] + [index for index in range(len(DELTAS)) if index != current]

    for index in order:
        dx, dy = DELTAS[index]
        x = API.Player.X + dx * tiles_ahead
        y = API.Player.Y + dy * tiles_ahead

        if _is_water(x, y, land_graphics, static_graphics):
            return index

    return None


# API.Turn only turns, the way a single directional key press does when you are not already facing
# that way - it never steps forward. Does nothing when already facing water, or when none of the
# eight directions match anything in the water tables
def turn_toward_water(tiles_ahead, land_graphics, static_graphics, turn_delay):
    current = facing()
    direction = water_direction(tiles_ahead, land_graphics, static_graphics)

    if direction is not None and direction != current:
        API.Turn(NAMES[direction].lower())
        API.Pause(turn_delay)

    return direction
