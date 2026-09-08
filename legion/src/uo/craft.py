import API

from uo.journal import journal_tail, matched_bucket
from uo.pack import count_of
from uo.retry import settled
from uo.text import clipped


class Crafter(object):
    def __init__(self, tools, menu, stock, buckets, config, log):
        self._tools = tools
        self._menu = menu
        self._stock = stock
        self._buckets = buckets
        self._config = config
        self._log = log
        self._item_buttons = {}
        self._item_probes = {}
        self._make_last = False
        self._said_unreadable = 0
        self._said_no_make_last = False
        # Products the recipe table got wrong on this shard, which the walk owns from then on
        self._walked = set()

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

    # The shard's own words for an outcome the script cannot act on, since a refusal nobody can read
    # cannot be fixed from the log
    def _report_outcome(self, why, gump):
        if self._said_unreadable >= self._config["max_reports"]:
            return

        self._said_unreadable += 1

        text = (clipped(" ".join(self._menu.lines(gump)), self._config["text_limit"])
                if gump else "")
        lines = journal_tail(self._config["tail_seconds"], self._config["tail_lines"])

        self._log("%s - the gump says '%s'" % (why, text or "(nothing)"))
        self._log("the journal says '%s'" % (" | ".join(lines) or "(nothing)"))
        self._log("the pack holds %s, and the menu is set to %s here"
                  % (self._stock.hue_report(), self._config["material"]))

    def _forget_row(self, product):
        self._make_last = False

        if product in self._item_buttons:
            del self._item_buttons[product]

        self._item_probes[product] = self._item_probes.get(product, 0) + 1

    # The button to press, or an outcome when there is none. MAKE LAST is the only path that skips
    # the category: an item button indexes whichever SELECTIONS page is showing.
    def _choose_button(self, product, gump):
        known = None if product in self._walked else self._config["recipes"].get(product)

        if self._make_last:
            if self._menu.has_button(self._config["make_last_button"], gump):
                return self._config["make_last_button"], None

            self._make_last = False

            if not self._said_no_make_last:
                self._said_no_make_last = True
                self._log("the menu has no MAKE LAST on button %d, pressing the row itself"
                          % self._config["make_last_button"])

        if known is not None:
            # Remembered too, so a later walk starts in the right category
            self._menu.remember_category(product, known[0])

            if not self._menu.has_button(known[0], gump):
                self._log("the menu has no category button %d for '%s'" % (known[0], product))

                return None, self._walk_instead(product)

            page = self._menu.press(known[0], gump, self._config["gump_timeout"])

            if not page:
                return None, "noGump"

            if not self._menu.has_button(known[1], page):
                self._log("the menu has no row button %d for '%s'" % (known[1], product))

                return None, self._walk_instead(product)

            return known[1], None

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

    def _walk_instead(self, product):
        if product in self._config["recipes"] and product not in self._walked:
            self._walked.add(product)
            self._log("the button table is out of date for '%s', walking the categories for it "
                      "instead" % product)

        self._forget_row(product)

        return "wrongRow"

    # Something was made and none of it was the product, so a row was wrong - unless the press was
    # MAKE LAST, which the shard forgets on its own and which says nothing about the proven row
    def _wrong_product(self, product, button):
        if button == self._config["make_last_button"]:
            self._make_last = False
            self._log("MAKE LAST did not make a '%s', pressing the row itself next time" % product)

            return "wrongRow"

        self._log("button %d did not make a '%s', trying the next row" % (button, product))

        return self._walk_instead(product)

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

        graphics = self._config["products"][product]
        before = count_of(graphics)

        def made_one():
            return count_of(graphics) > before

        API.ClearJournal()

        opened = self._menu.press(button, gump, self._config["craft_timeout"])
        outcome = self._read_outcome(opened, made_one)

        # The pack is the proof no wording can argue with: a shard that says nothing still delivers
        if outcome in ("made", None) and (made_one() or settled(
                self._config["craft_settle"], self._config["craft_poll"], made_one)):
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
