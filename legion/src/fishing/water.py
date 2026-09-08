from uo.scan import chebyshev_to


def is_water(tile, land_graphics, static_graphics):
    table = land_graphics if tile["is_land"] else static_graphics

    return tile["graphic"] in table


# Nearest by crow flight and nothing else: the run never walks, so there is no route to price
def nearest_water(terrain, radius, land_graphics, static_graphics):
    found = [tile for tile in terrain.box(radius)
             if is_water(tile, land_graphics, static_graphics)]

    if not found:
        return None

    found.sort(key=chebyshev_to)

    return found[0]
