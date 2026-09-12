import API

from uo.harvest import Harvester


class Digger(object):
    def __init__(self, ore, buckets, config, log, cancel_pathfinding):
        self._harvester = Harvester(ore.total, buckets, config, log, "dig", "dug", "dig_timeout",
                                    cancel_pathfinding=cancel_pathfinding)

    def dig_once(self, serial):
        # Answered with yourself rather than with the vein's coordinates: the shard takes that as
        # 'mine where I am' and picks the ore itself, so nothing has to guess land versus static
        return self._harvester.swing_once(serial, API.TargetSelf)
