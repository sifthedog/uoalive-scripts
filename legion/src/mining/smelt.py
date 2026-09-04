import API

from uo.entity import hex_of
from uo.journal import said
from uo.pack import counts_by_graphic, diff_counts, hue_of, pack_contents


class Smelter(object):
    def __init__(self, ore, beetle, combiner, saves, config, log):
        self._ore = ore
        self._beetle = beetle
        self._combiner = combiner
        self._saves = saves
        self._config = config
        self._log = log

        self._written_off = set()
        self._misses = {}
        # Whether anything has converted since the last retry. Without it a retry granted
        # unconditionally answers true again next cycle and the caller loops until the watchdog ends
        self._progressed = True
        self._forge = None
        self._reported_no_beetle = False

    def written_off(self):
        return self._written_off

    def _counts(self):
        return counts_by_graphic(pack_contents())

    # Every failing path comes through here: one that returns without counting leaves the candidate
    # set unchanged, so the next pass picks the same stack and the loop runs to its backstop
    def _missed(self, hue):
        count = self._misses.get(hue, 0) + 1
        self._misses[hue] = count

        if count >= self._config["attempts"]:
            self._written_off.add(hue)
            self._log("hue %d failed %d times, leaving it as ore" % (hue, count))

    def _learn_ingot(self, gained):
        for graphic, _hue in gained:
            if graphic in self._config["ore_graphics"]:
                continue

            if graphic in self._config["ingot_graphics"]:
                continue

            self._config["ingot_graphics"].add(graphic)
            self._log("ingot graphic is %s" % hex_of(graphic))

    # The action throttle can hold a conversion well past any pause worth taking, and reading too
    # early is indistinguishable from a resource that cannot be worked
    def _wait_for_change(self, before):
        waited = 0.0

        while waited < self._config["timeout"]:
            API.Pause(self._config["poll"])
            waited += self._config["poll"]

            gained, lost = diff_counts(before, self._counts())

            if gained or lost:
                return gained

        return None

    # The journal is cleared to perform the smelt, so a save that starts mid-attempt is past the
    # check at the top of the pass: one cost three hues and ended a live run overweight beside a
    # working beetle
    def _saving(self, hue):
        if not self._saves.is_saving():
            return False

        self._log("the world is saving, not counting it against hue %d" % hue)

        return True

    # A smelt aimed at a beetle that has drifted out of range fails exactly the way ore that cannot
    # be worked does: silently. Three of those wrote off 86 ore of one colour on a live run.
    def _forge_gone(self):
        if self._forge is None:
            return "no beetle to smelt against"

        here = API.FindMobile(self._forge.Serial)

        if here is None:
            return "the beetle %s is out of sight" % hex_of(self._forge.Serial)

        if here.Distance > self._config["range"]:
            return "the beetle has wandered %d tiles off" % here.Distance

        return None

    # The inverse of making boards: the ore is double-clicked and the beetle is the target. The
    # beetle is never double-clicked itself - it is rideable, so that mounts you.
    def _perform(self, stack):
        if self._forge is None:
            return False

        # Cancelled only when there is one to cancel: a cursor cancelled shortly before an action
        # has been measured costing that action its own
        if API.HasTarget():
            API.CancelTarget()

        API.ClearJournal()
        API.UseObject(stack.Serial)

        if not API.WaitForTarget("any", self._config["target_timeout"]):
            API.CancelTarget()
            self._log("no target cursor for the beetle")

            return False

        API.Target(self._forge.Serial)

        return True

    def _convert_one(self, stack):
        hue = hue_of(stack)
        before = self._counts()

        if not self._perform(stack):
            if self._saving(hue):
                return

            # Counted like any other failure: without this an empty hand spends every pass waiting
            # on a cursor that is never going to come
            self._missed(hue)

            return

        gained = self._wait_for_change(before)

        if gained is not None:
            self._misses.pop(hue, None)
            self._progressed = True
            self._learn_ingot(gained)

            return

        # Asked before either wording, because a frozen shard's verdict on the material is worthless
        if self._saving(hue):
            return

        # Nothing was attempted, so this is not a verdict on the material
        if said(self._config["throttled_text"]):
            self._log("the shard says wait, not counting it against hue %d" % hue)

            return

        if said(self._config["unskilled_text"]):
            self._written_off.add(hue)
            self._log("not skilled enough for hue %d, leaving it as ore" % hue)

            return

        # Otherwise it was silent, which is also what a throttled or stale attempt looks like
        self._missed(hue)

    def _run(self):
        for _pass in range(self._config["passes"]):
            # A frozen shard answers a conversion the same way an unworkable material does, so
            # without this a world save costs the attempts and writes the hue off for the run
            if self._saves.is_saving():
                self._log("the world is saving, leaving it for now")

                return False

            stack = self._ore.next_ore(self._written_off)

            if stack is None:
                piles = self._ore.piles()

                if len(piles) > 0:
                    described = [self._ore.describe_skipped(pile, self._written_off)
                                 for pile in piles]
                    self._log("nothing to smelt in %d pile(s) - %s"
                              % (len(piles), ", ".join(described)))

                return True

            # Asked only once there is something that needs it, which is what makes smelting on
            # every dry vein affordable
            blocked = self._forge_gone()

            if blocked is not None:
                self._log("%s, leaving it for now" % blocked)

                return False

            self._convert_one(stack)
            API.Pause(self._config["delay"])

        self._log("hit the %d smelt pass backstop" % self._config["passes"])

        return False

    def retry_written_off(self, force=False):
        if len(self._written_off) == 0 or (not self._progressed and not force):
            return False

        self._progressed = False
        self._log("giving %d hue(s) written off earlier another go" % len(self._written_off))
        self._written_off.clear()
        self._misses.clear()

        return True

    def smelt_against(self, reach):
        # Asked before the beetle is looked for, so a pack with nothing eligible costs neither a
        # search nor a walk
        if self._ore.next_ore(self._written_off) is None:
            return self._run()

        found = self._beetle.find()

        if found is None:
            # Said once rather than every pass: a missing beetle is not fatal, the ore travels on
            if not self._reported_no_beetle:
                self._reported_no_beetle = True
                self._log("no fire beetle nearby, keeping the ore as it is")

            return False

        self._reported_no_beetle = False
        self._forge = reach(found.Serial)

        if self._forge is None:
            return False

        return self._run()
