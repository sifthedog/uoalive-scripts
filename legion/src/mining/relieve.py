import API

from uo.weight import too_heavy


class Relief(object):
    """Making room by turning the ore into ingots, and knowing when that has stopped working."""

    def __init__(self, ore, combiner, smelter, saves, reach, advice, log):
        self._ore = ore
        self._combiner = combiner
        self._smelter = smelter
        self._saves = saves
        self._reach = reach
        self._advice = advice
        self._log = log

    def smelt(self):
        return self._smelter.smelt_against(self._reach)

    def group_and_smelt(self):
        self._combiner.group()
        self.smelt()

    def smelt_for_room(self):
        if not too_heavy():
            return None

        before = self._ore.total()

        # Unconditional, because the decision has already been taken: a helper that asked too_heavy
        # a second time could disagree, and the run stopped for weight without ever having tried
        self.group_and_smelt()

        # Ore leaving the pack is the proof, not the weight going down: the client can still report
        # its pre-smelt figure over a conversion the pack diff has confirmed
        if self._ore.total() < before:
            return "smelting"

        # Before the retry rather than after it: a frozen shard converts nothing, and a retry spent
        # here is the run's only one gone
        if self._saves.is_saving():
            self._saves.wait_out()

            return "smelting"

        if self._smelter.retry_written_off():
            return "smelting"

        # The retry above has just reopened the hues written off, so this pass is the one that acts
        self.group_and_smelt()

        if self._ore.total() < before:
            return "smelting"

        if self._saves.is_saving():
            self._saves.wait_out()

            return "smelting"

        return {
            "stop": "overweight (%d/%d) with %d ore left, and smelting freed nothing%s"
            % (API.Player.Weight, API.Player.WeightMax, self._ore.total(), self._advice)
        }
