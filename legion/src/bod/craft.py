import API

from uo.journal import journal_tail, matched_bucket
from uo.retry import settled
from uo.text import clipped

STOPPERS = ("noMaterial", "noAnvil", "skillTooLow", "toolWorn", "throttled", "saving")


class DeedCrafter(object):
    """One proving craft off the row, then MAKE NUMBER batches of it."""

    def __init__(self, tool, menu, items, picker, buckets, config, log):
        self._tool = tool
        self._menu = menu
        self._items = items
        self._picker = picker
        self._buckets = buckets
        self._config = config
        self._log = log
        self._item_buttons = {}
        self._said_unreadable = 0
        self._said_unjudged = False

    def forget_row(self, product):
        if product in self._item_buttons:
            del self._item_buttons[product]

    def proven(self, product):
        return product in self._item_buttons

    def _notice_bucket(self, gump):
        if not gump:
            return None

        for name, phrases in self._buckets:
            for phrase in phrases:
                if API.GumpContains(phrase, gump):
                    return name

        return None

    # Pack first: a success this table has no wording for would otherwise wait out the timeout.
    # The gump's NOTICES panel is read too because the shard writes refusals there, not the journal.
    def _read_outcome(self, opened, landed):
        waited = 0.0

        while not API.StopRequested:
            if landed():
                return "made"

            hit = matched_bucket(self._buckets)

            if hit is None:
                hit = self._notice_bucket(opened)

            if hit is not None:
                return hit

            if waited >= self._config["craft_timeout"]:
                return None

            API.Pause(self._config["craft_poll"])
            waited += self._config["craft_poll"]

    def _report_outcome(self, why, gump):
        if self._said_unreadable >= self._config["max_reports"]:
            return

        self._said_unreadable += 1

        text = (clipped(" ".join(self._menu.lines(gump)), self._config["text_limit"])
                if gump else "")
        lines = journal_tail(self._config["tail_seconds"], self._config["tail_lines"])

        self._log("%s - the gump says '%s'" % (why, text or "(nothing)"))
        self._log("the journal says '%s'" % (" | ".join(lines) or "(nothing)"))

    # A known recipe is pressed as given; anything else has to be named by the page's text.
    # Rows are never pressed on a guess - each wrong one spends a piece's worth of ingots.
    def _choose_button(self, product, gump):
        known = self._config["recipes"].get(product)

        if known is not None:
            self._menu.remember_category(product, known[0])

            if not self._menu.has_button(known[0], gump):
                self._log("the menu has no category button %d for '%s'" % (known[0], product))

                return None, "noRow"

            page = self._menu.press(known[0], gump, self._config["gump_timeout"])

            if not page:
                return None, "noGump"

            if not self._menu.has_button(known[1], page):
                self._log("the menu has no row button %d for '%s'" % (known[1], product))

                return None, "noRow"

            return known[1], None

        gump, category = self._menu.find_category(product, gump)

        if category is None:
            return None, "noRow"

        if not gump:
            return None, "noGump"

        button = self._menu.named_row(product, gump)

        if button is None:
            self._log("no row on button %d's page reads '%s' - the page says '%s'"
                      % (category, product, " | ".join(self._menu.lines(gump)) or "(no text)"))

            return None, "noRow"

        return button, None

    # None from every new item is a tooltip that never came, which is not a wrong row
    def _made_product(self, new):
        verdicts = [self._items.is_product(item.Serial) for item in new]

        if True in verdicts:
            return True

        if False in verdicts:
            return False

        if not self._said_unjudged:
            self._said_unjudged = True
            self._log("the new item's tooltip did not arrive - taking the craft as the product")

        return True

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

    # A single craft off the row, so a wrong row costs one item's worth rather than a batch's
    def craft_once(self, product, material):
        gump, why = self._ready(material)

        if why is not None:
            return why

        button, outcome = self._choose_button(product, gump)

        if button is None:
            return outcome

        before = self._items.serials()

        def landed():
            return len(self._items.new_since(before)) > 0

        API.ClearJournal()

        opened = self._menu.press(button, gump, self._config["craft_timeout"])
        outcome = self._read_outcome(opened, landed)

        if outcome in ("made", None) and (landed() or settled(
                self._config["craft_settle"], self._config["craft_poll"], landed)):
            if not self._made_product(self._items.new_since(before)):
                self._log("button %d made %s, not a '%s'"
                          % (button, ", ".join("'%s'" % self._items.name_of(item.Serial)
                                               for item in self._items.new_since(before)),
                             product))

                return "wrongRow"

            self._item_buttons[product] = button
            self._said_unreadable = 0
            self._log("'%s' is the row on button %d" % (product, button))

            return "made"

        if outcome == "made":
            self._log("button %d made nothing that landed in the pack" % button)

            return "wrongRow"

        if outcome == "noMaterial":
            self._report_outcome("refused for materials", opened)
        elif outcome is None:
            self._report_outcome("nothing readable came back", opened)

        return outcome

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

        gump, category = self._menu.find_category(product, gump)

        if not gump or category is None:
            return "noGump", 0, 0

        details = self._menu.press_page(self._item_buttons[product] + 1, gump,
                                        self._config["gump_timeout"])

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

        if made > 0 and not self._made_product(self._items.new_since(before)):
            self._log("the batch made %d that are not a '%s' - the row moved" % (made, product))
            self.forget_row(product)

            return "wrongRow", made, failed

        return outcome, made, failed
