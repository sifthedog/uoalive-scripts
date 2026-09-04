import API

from uo.entity import distance_of, find_mobile


def chase(serial, within, timeout):
    """'gained' is ground made up on something still walking away, and is worth another cycle."""
    before = distance_of(serial)

    if API.PathfindEntity(serial, within, True, timeout, True):
        return "closed"

    after = distance_of(serial)

    if before is not None and after is not None and after < before:
        return "gained"

    return "stuck"


# Called between the slices of a wait, so a mobile is followed while an attempt resolves
def keep_up(serial, within, timeout):
    found = find_mobile(serial)

    if found is not None and found.Distance > within and not API.Pathfinding():
        API.PathfindEntity(serial, within, False, timeout, True)
