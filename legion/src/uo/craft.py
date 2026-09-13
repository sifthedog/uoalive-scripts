import API

from uo.journal import journal_tail
from uo.text import any_in, clipped, untagged


class Crafter(object):
    """Presses the RECIPES row as written and reads only the shard's words for the outcome."""

    def __init__(self, tools, menu, stock, buckets, config, log, stamp=None):
        self._tools = tools
        self._menu = menu
        self._stock = stock
        self._buckets = buckets
        self._config = config
        self._log = log
        self._stamp = stamp
        self._make_last = False
        self._said_unreadable = 0
        self._said_no_make_last = False
        self._heard = ""

    def forget_last(self):
        self._make_last = False

    def _journal_bucket(self):
        for name, phrases in self._buckets:
            for phrase in phrases:
                # clearMatches, or a line already read answers the next wait as well
                if API.InJournalAny([phrase], True):
                    self._heard = "the journal said '%s'" % phrase

                    return name

        return None

    def _notice_bucket(self, gump):
        if not gump:
            return None

        text = API.GetGumpContents(gump)

        for name, phrases in self._buckets:
            for phrase in phrases:
                if any_in(text, [phrase.lower()]) or API.GumpContains(phrase, gump):
                    self._heard = "the gump said '%s'" % phrase

                    return name

        return None

    # The gump's NOTICES panel is read too because the shard writes refusals there, not the journal
    def _read_outcome(self, opened):
        waited = 0.0

        while not API.StopRequested:
            hit = self._journal_bucket()

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

        text = (clipped(untagged(" ".join(self._menu.lines(gump))), self._config["text_limit"])
                if gump else "")
        lines = journal_tail(self._config["tail_seconds"], self._config["tail_lines"], self._stamp)

        self._log("%s - the gump says '%s'" % (why, text or "(nothing)"))
        self._log("the journal says '%s'" % (" | ".join(lines) or "(nothing)"))
        self._log("the pack holds %s, and the menu is set to %s here"
                  % (self._stock.hue_report(), self._config["material"]))

    # MAKE LAST is the only path that skips the category: a row button is only in the gump once
    # its category is showing
    def _choose_button(self, product, gump):
        known = self._config["recipes"].get(product)

        if known is None:
            return None, "noRow"

        if self._make_last:
            if self._menu.has_button(self._config["make_last_button"], gump):
                return self._config["make_last_button"], None

            self._make_last = False

            if not self._said_no_make_last:
                self._said_no_make_last = True
                self._log("the menu has no MAKE LAST on button %d, pressing the row itself"
                          % self._config["make_last_button"])

        if not self._menu.press(known[0], gump, self._config["gump_timeout"]):
            return None, "noGump"

        return known[1], None

    def craft_once(self, product):
        # Asked apart from the gump, so an empty pack and a menu that will not open read differently
        if self._tools.serial() is None:
            return "noTool"

        gump = self._menu.open()

        if gump is None:
            return "noGump"

        button, outcome = self._choose_button(product, gump)

        if button is None:
            return outcome

        gump = self._menu.current_id() or gump

        API.ClearJournal()

        opened = self._menu.press(button, gump, self._config["craft_timeout"])
        outcome = self._read_outcome(opened)

        if outcome == "made":
            self._make_last = True
            self._said_unreadable = 0
        elif outcome == "noMaterial":
            self._report_outcome("refused for materials", opened)
        elif outcome is None:
            self._report_outcome("nothing readable came back", opened)

            if button == self._config["make_last_button"]:
                self._make_last = False
                self._log("MAKE LAST made nothing, pressing the row itself next time")

        return outcome
