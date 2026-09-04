import API

from uo.journal import said
from uo.pack import counts_by_graphic, diff_counts, hue_of, pack_contents


class Converter(object):
    """One resource into another, judged by the pack diff, with a per-hue write-off."""

    def __init__(self, config, log, saves):
        self._config = config
        self._log = log
        self._saves = saves
        self._written_off = set()
        self._misses = {}
        # Whether anything has converted since the last retry. Without it a retry granted
        # unconditionally answers true again next cycle and the caller loops until the watchdog ends
        self._progressed = True

    def written_off(self):
        return self._written_off

    # Every failing path comes through here: one that returns without counting leaves the candidate
    # set unchanged, so the next pass picks the same stack and the loop runs to its backstop
    def _missed(self, hue):
        count = self._misses.get(hue, 0) + 1
        self._misses[hue] = count

        if count >= self._config["attempts"]:
            self._written_off.add(hue)
            self._log("hue %d failed %d times, leaving it as %s"
                      % (hue, count, self._config["noun"]))

    # The journal is cleared to perform the conversion, so a save that starts mid-attempt is past
    # the check at the top of the pass
    def _saving(self, hue):
        if not self._saves.is_saving():
            return False

        self._log("the world is saving, not counting it against hue %d" % hue)

        if self._config["wait_on_save"]:
            self._saves.wait_out()

        return True

    # The action throttle can hold a conversion well past any pause worth taking, and reading too
    # early is indistinguishable from a resource that cannot be worked
    def _wait_for_change(self, before):
        waited = 0.0

        while waited < self._config["timeout"]:
            API.Pause(self._config["poll"])
            waited += self._config["poll"]

            gained, lost = diff_counts(before, counts_by_graphic(pack_contents()))

            if gained or lost:
                return gained

        return None

    def _convert_one(self, stack):
        hue = hue_of(stack)
        before = counts_by_graphic(pack_contents())

        if not self._config["perform"](stack):
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
            self._config["learn_product"](gained)

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
            self._log("not skilled enough for hue %d, leaving it as %s"
                      % (hue, self._config["noun"]))

            return

        # Otherwise it was silent, which is also what a throttled or stale attempt looks like
        self._missed(hue)

    def run(self):
        for _pass in range(self._config["passes"]):
            # A frozen shard answers a conversion the same way an unworkable material does, so
            # without this a world save costs the attempts and writes the hue off for the run
            if self._saves.is_saving():
                self._log(self._config["saving_message"])

                return False

            stack = self._config["next_source"](self._written_off)

            if stack is None:
                self._config["nothing_to_do"](self._written_off)

                return True

            # Asked only once there is something that needs it, which is what makes converting on
            # every dry spot affordable
            blocked = self._config["blocked"]()

            if blocked is not None:
                self._log("%s, leaving it for now" % blocked)

                return False

            self._config["about_to_convert"]()
            self._convert_one(stack)
            API.Pause(self._config["delay"])

        self._log("hit the %d conversion pass backstop" % self._config["passes"])

        return False

    def retry_written_off(self, force=False):
        if len(self._written_off) == 0 or (not self._progressed and not force):
            return False

        self._progressed = False
        self._log("giving %d hue(s) written off earlier another go" % len(self._written_off))
        self._written_off.clear()
        self._misses.clear()

        return True
