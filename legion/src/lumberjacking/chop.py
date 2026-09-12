import API

from uo.harvest import Harvester


class Chopper(object):
    def __init__(self, wood, tool, buckets, config, log):
        self._config = config
        self._harvester = Harvester(wood.log_total, buckets, config, log, "chop", "chopped",
                                    "chop_timeout", tool=tool)

    def chop_once(self, serial, tree):
        if self._config["aim_at_self"]:
            # This shard takes a self-target as 'harvest what is in reach' and picks the tree
            # itself, so nothing has to name a static. The scan still earns its place: it is what
            # decides where to stand, and 'in reach' is only ever the trunk you walked to.
            aim = API.TargetSelf
        else:
            # The four-argument overload, and the graphic is never left off: target.terrain with no
            # art hits the land tile, which the shard answers as mining rather than as chopping. A
            # static carries no serial, so naming the tile and its art is the only other way in.
            aim = lambda: API.Target(tree["x"], tree["y"], tree["z"], tree["graphic"])

        return self._harvester.swing_once(serial, aim)
