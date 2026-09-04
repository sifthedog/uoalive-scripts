import API

from uo.convert import Converter
from uo.entity import hex_of


class Smelter(object):
    """The ore side of the converter: a fire beetle is the forge, and the ore is what is used."""

    def __init__(self, ore, beetle, saves, config, log):
        self._ore = ore
        self._beetle = beetle
        self._config = config
        self._log = log
        self._forge = None
        self._reported_no_beetle = False

        self._converter = Converter({
            "noun": "ore",
            "attempts": config["attempts"],
            "passes": config["passes"],
            "delay": config["delay"],
            "timeout": config["timeout"],
            "poll": config["poll"],
            "throttled_text": config["throttled_text"],
            "unskilled_text": config["unskilled_text"],
            "wait_on_save": False,
            "saving_message": "the world is saving, leaving it for now",
            "next_source": ore.next_ore,
            "perform": self._perform,
            "blocked": self._forge_gone,
            "learn_product": self._learn_ingot,
            "nothing_to_do": self._say_what_is_left,
            "about_to_convert": self._nothing_to_note,
        }, log, saves)

    def written_off(self):
        return self._converter.written_off()

    def retry_written_off(self, force=False):
        return self._converter.retry_written_off(force)

    def _learn_ingot(self, gained):
        for graphic, _hue in gained:
            if graphic in self._config["ore_graphics"]:
                continue

            if graphic in self._config["ingot_graphics"]:
                continue

            self._config["ingot_graphics"].add(graphic)
            self._log("ingot graphic is %s" % hex_of(graphic))

    def _nothing_to_note(self):
        pass

    def _say_what_is_left(self, written_off):
        piles = self._ore.piles()

        if len(piles) > 0:
            described = [self._ore.describe_skipped(pile, written_off) for pile in piles]
            self._log("nothing to smelt in %d pile(s) - %s" % (len(piles), ", ".join(described)))

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

    def smelt_against(self, reach):
        # Asked before the beetle is looked for, so a pack with nothing eligible costs neither a
        # search nor a walk
        if self._ore.next_ore(self.written_off()) is None:
            return self._converter.run()

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

        return self._converter.run()
