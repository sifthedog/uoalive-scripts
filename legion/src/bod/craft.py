import API

from uo.journal import matched_bucket
from uo.notes import Reporter

STOPPERS = ("noMaterial", "noMana", "noAnvil", "keg", "packFull", "skillTooLow", "toolWorn",
           "throttled", "saving")


class DeedCrafter(object):
    """MAKE NUMBER batches off the RECIPES row, pressed as written."""

    def __init__(self, tool, menu, items, picker, buckets, config, log, stamp=None,
                 notes=None):
        self._tool = tool
        self._menu = menu
        self._items = items
        self._picker = picker
        self._buckets = buckets
        self._config = config
        self._log = log
        self._report = Reporter(menu.lines, config, log, notes, stamp)

    def _notice_bucket(self, gump):
        if not gump:
            return None

        for name, phrases in self._buckets:
            for phrase in phrases:
                if API.GumpContains(phrase, gump):
                    return name

        return None

    def _report_outcome(self, why, gump):
        self._report.say(why, gump)

    def _choose_button(self, product, gump):
        known = self._config["recipes"].get(product)

        if known is None:
            return None, "noRow"

        if not self._menu.press(known[0], gump, self._config["gump_timeout"]):
            return None, "noGump"

        return known[1], None

    def _ready(self, material):
        if self._tool.serial() is None:
            return None, "noTool"

        gump = self._menu.open()

        if gump is None:
            return None, "noGump"

        if self._picker.needs(material):
            gump, why = self._picker.select(material, gump)

            if why is not None:
                return None, why

        return gump, None

    def _cancel(self):
        self._menu.reply(self._config["cancel_button"], self._menu.current_id())

    # The auto craft says nothing when it ends: the pack and the journal are counted up to the
    # amount, and a stretch with no change is taken as the end. One failure line per poll is
    # enough, since a craft takes longer than a poll.
    def _watch_batch(self, amount, before):
        failed = 0
        last = 0
        idle = 0.0
        waited = 0.0
        budget = amount * self._config["craft_interval"] + self._config["craft_timeout"]

        while not API.StopRequested:
            made = len(self._items.new_since(before))
            stopper = None
            hit = matched_bucket(self._buckets)

            while hit is not None:
                if hit == "failed":
                    failed += 1
                elif hit in STOPPERS:
                    stopper = hit

                hit = matched_bucket(self._buckets)

            if stopper is None:
                notice = self._notice_bucket(self._menu.current_id())

                if notice in STOPPERS:
                    stopper = notice

            progress = made + failed

            if progress >= amount:
                return "made", made, failed

            if stopper is not None:
                self._cancel()

                return stopper, made, failed

            if progress == last:
                idle += self._config["craft_poll"]
            else:
                idle = 0.0
                last = progress
                self._log("batch: %d made, %d failed of %d" % (made, failed, amount))

            if idle >= self._config["batch_idle"] or waited >= budget:
                if progress > 0:
                    self._log("the batch went quiet at %d of %d - a failure the journal did not "
                              "carry, or the shard stopped early" % (progress, amount))

                return ("made" if progress > 0 else None), made, failed

            API.Pause(self._config["craft_poll"])
            waited += self._config["craft_poll"]

        return None, len(self._items.new_since(before)), failed

    # Details button is the row's button plus one: type 2 against the row's type 1
    def craft_batch(self, product, material, amount):
        gump, why = self._ready(material)

        if why is not None:
            return why, 0, 0

        button, why = self._choose_button(product, gump)

        if why is not None:
            return why, 0, 0

        gump = self._menu.current_id() or gump
        details = self._menu.press_page(button + 1, gump, self._config["gump_timeout"])

        if not details:
            return "noGump", 0, 0

        before = self._items.serials()
        API.ClearJournal()

        if not self._menu.reply_page(self._config["make_number_button"], details):
            return "noGump", 0, 0

        API.Pause(self._config["prompt_delay"])
        API.PromptResponse(str(amount))

        outcome, made, failed = self._watch_batch(amount, before)

        if outcome is None:
            self._report_outcome("the batch of %d made nothing" % amount, self._menu.current_id())
        elif outcome == "noMaterial":
            self._report_outcome("refused for materials", self._menu.current_id())

        return outcome, made, failed
