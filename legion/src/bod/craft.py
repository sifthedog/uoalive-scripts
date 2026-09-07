import API

from uo.journal import journal_tail, matched_bucket
from uo.retry import settled
from uo.text import clipped


class DeedCrafter(object):
    def __init__(self, tool, menu, items, picker, buckets, config, log):
        self._tool = tool
        self._menu = menu
        self._items = items
        self._picker = picker
        self._buckets = buckets
        self._config = config
        self._log = log
        self._item_buttons = {}
        self._item_probes = {}
        self._make_last = False
        self._said_unreadable = 0
        self._said_unjudged = False

    def forget_last(self):
        self._make_last = False

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

    def _forget_row(self, product):
        self._make_last = False

        if product in self._item_buttons:
            del self._item_buttons[product]

        self._item_probes[product] = self._item_probes.get(product, 0) + 1

    # MAKE LAST is the only path that skips the category: an item button indexes whichever
    # SELECTIONS page is showing
    def _choose_button(self, product, gump):
        if self._make_last:
            return self._config["make_last_button"], None

        gump, category = self._menu.find_category(product, gump)

        if category is None:
            return None, "noRow"

        if not gump:
            return None, "noGump"

        button = self._item_buttons.get(product)

        if button is not None:
            return button, None

        order = self._menu.candidate_buttons(product, gump)
        probe = self._item_probes.get(product, 0)

        if probe < min(self._config["max_probes"], len(order)):
            return order[probe], None

        rejected = self._menu.reject_category(product, category)
        self._menu.forget_category(product)

        if rejected >= self._config["max_categories"]:
            return None, "noRow"

        self._item_probes[product] = 0
        self._log("no row on button %d's page made a '%s', trying another category"
                  % (category, product))

        return None, "wrongRow"

    def _wrong_product(self, product, button):
        if button == self._config["make_last_button"]:
            self._make_last = False
            self._log("MAKE LAST did not make a '%s', pressing the row itself next time" % product)

            return "wrongRow"

        self._log("button %d did not make a '%s', trying the next row" % (button, product))
        self._forget_row(product)

        return "wrongRow"

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

    def craft_once(self, product, material):
        if self._tool.serial() is None:
            return "noTool"

        gump = self._menu.open()

        if gump is None:
            return "noGump"

        if self._picker.needs(material):
            gump, why = self._picker.select(material, gump)

            if why is not None:
                return why

            self._make_last = False

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
                return self._wrong_product(product, button)

            if self._item_buttons.get(product) is None:
                self._item_buttons[product] = button
                self._log("'%s' is the row on button %d" % (product, button))

            self._make_last = True
            self._said_unreadable = 0

            return "made"

        if outcome == "made":
            return self._wrong_product(product, button)

        if outcome == "noMaterial":
            self._report_outcome("refused for materials", opened)
        elif outcome is None:
            self._report_outcome("nothing readable came back", opened)

            if button == self._config["make_last_button"]:
                self._make_last = False
                self._log("MAKE LAST made nothing, pressing the row itself next time")

        return outcome
