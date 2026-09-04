import API

from uo.entity import hex_of


class Beetle(object):
    """The fire beetle the ore is smelted against."""

    def __init__(self, graphics, serial, radius, smelt_range, pathfind_timeout, pick_timeout, log):
        self._graphics = graphics
        self._radius = radius
        self._smelt_range = smelt_range
        self._pathfind_timeout = pathfind_timeout
        self._pick_timeout = pick_timeout
        self._log = log

        self._serial = serial
        # A serial chosen rather than guessed - from config or from the cursor - is the law, so a
        # moment out of sight is not a reason to go looking for someone else's beetle
        self._pinned = serial is not None
        self._reported = False

    def pick(self):
        # A cursor left open by whatever ran last would swallow this query
        if API.HasTarget():
            API.CancelTarget()

        self._log("target your fire beetle, ESC to let the script find it")

        serial = API.RequestTarget(self._pick_timeout)

        if not serial:
            # A cancelled pick can still leave the cursor up, and a live one would spend the
            # double-clicks that follow as target clicks instead
            if API.HasTarget():
                API.CancelTarget()

            self._log("nothing picked, looking for one instead")

            return None

        picked = API.FindMobile(serial)

        if picked is None:
            self._log("%s is not a mobile, looking for one instead" % hex_of(serial))

            return None

        # Not a refusal: the graphics table is a guess at this shard, so a body it has never heard
        # of is worth reporting and then using
        if picked.Graphic not in self._graphics:
            self._log("%s is not a body FIRE_BEETLE_GRAPHICS knows, using it anyway"
                      % hex_of(picked.Graphic))

        self._serial = serial
        self._pinned = True
        self._reported = True
        self._log("using '%s' %s as the forge" % (picked.Name or hex_of(serial),
                                                  hex_of(picked.Graphic)))

        return picked

    def find(self):
        if self._serial is not None:
            resolved = API.FindMobile(self._serial)

            if resolved is not None:
                return resolved

            # Out of range, dead, or a hand-written serial that was never a mobile
            if self._pinned:
                return None

            self._serial = None

        found = []

        for graphic in self._graphics:
            for mobile in API.GetAllMobiles(graphic, self._radius) or []:
                found.append(mobile)

        if not found:
            return None

        # Only your own pets can be renamed, so this is what tells yours from a stranger's
        mine = [mobile for mobile in found if mobile.IsRenamable]
        candidates = mine if mine else found
        candidates.sort(key=lambda mobile: mobile.Distance)

        beetle = candidates[0]

        if not self._reported:
            self._reported = True
            self._log("using '%s' %s as the forge" % (beetle.Name or hex_of(beetle.Serial),
                                                      hex_of(beetle.Graphic)))

        self._serial = beetle.Serial

        return beetle

    # A pet's coordinates go stale within a cycle, so the serial is re-resolved rather than the
    # find result trusted
    def walk_to(self, serial):
        here = API.FindMobile(serial)

        if here is None:
            self._log("lost track of %s" % hex_of(serial))

            return None

        if here.Distance <= self._smelt_range:
            return here

        API.PathfindEntity(serial, self._smelt_range, True, self._pathfind_timeout)
        API.CancelPathfinding()

        here = API.FindMobile(serial)

        if here is None or here.Distance > self._smelt_range:
            self._log("could not get within %d of the beetle" % self._smelt_range)

            return None

        return here

    # The stationary counterpart: a beetle not already next to you is not a forge this run can use
    def in_range(self, serial):
        found = API.FindMobile(serial)

        if found is None:
            self._log("lost track of %s" % hex_of(serial))

            return None

        if found.Distance > self._smelt_range:
            self._log("the beetle is %d tiles off and this run does not walk" % found.Distance)

            return None

        return found
