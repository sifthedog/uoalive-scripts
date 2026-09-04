import API

from uo.journal import journal_tail, matched_bucket
from uo.pack import amount_of, pack_contents
from uo.retry import settled
from uo.text import clipped


class Crafter(object):
    def __init__(self, tools, menu, wood, buckets, config, log):
        self._tools = tools
        self._menu = menu
        self._wood = wood
        self._buckets = buckets
        self._config = config
        self._log = log
        self._item_buttons = {}
        self._item_probes = {}
        self._make_last = False
        self._said_unreadable = 0
        # Products the recipe table got wrong on this shard, which the walk owns from then on
        self._walked = set()

    def forget_last(self):
        self._make_last = False

    def counts_of(self, graphics):
        return sum(amount_of(item) for item in pack_contents() if item.Graphic in graphics)

    def _notice_bucket(self, gump):
        if not gump:
            return None

        for name, phrases in self._buckets:
            for phrase in phrases:
                if API.GumpContains(phrase, gump):
                    return name

        return None

    # Three things every pass, and the pack is one of them. The journal is not read first because
    # the shard writes its refusals into the NOTICES panel; the pack is not read *last* because a
    # success whose wording this table has not got is still a success - and waiting out the timeout
    # for a line that was never coming is a silent ten-second stall on a craft that worked.
    def _read_outcome(self, opened, landed):
        waited = 0.0

        while True:
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

    # The shard's own words for an outcome this script cannot act on - the gump's panel and the
    # journal it cleared before the press, so what comes back belongs to this craft and nothing
    # older. A refusal nobody can read is the one thing that cannot be fixed from the log.
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
                  % (self._wood.hue_report(), self._config["wood_type"]))

    def _forget_row(self, product):
        self._make_last = False

        if product in self._item_buttons:
            del self._item_buttons[product]

        self._item_probes[product] = self._item_probes.get(product, 0) + 1

    # MAKE LAST is the only path that skips the category: an item button indexes whichever
    # SELECTIONS page is showing, so a remembered one crafts whatever sits on that row of the wrong
    # page
    def craft_once(self, product):
        # Asked apart from the gump, so an empty pack and a menu that will not open are not one
        # message
        if self._tools.serial() is None:
            return "noTool"

        gump = self._menu.open()

        if gump is None:
            return "noGump"

        button = self._item_buttons.get(product)
        known = None if product in self._walked else self._config["recipes"].get(product)

        if self._make_last and button is not None:
            button = self._config["make_last_button"]
        elif known is not None:
            # Remembered too, so a walk that starts later - after a worn tool, say - starts in the
            # right category rather than from the first one
            self._menu.remember_category(product, known[0])

            gump = self._menu.press(known[0], gump, self._config["gump_timeout"])

            if not gump:
                return "noGump"

            button = known[1]
        else:
            gump, category = self._menu.find_category(product, gump)

            if category is None:
                return "noRow"

            if not gump:
                return "noGump"

            if button is None:
                order = self._menu.candidate_buttons(product, gump)
                probe = self._item_probes.get(product, 0)

                if probe >= min(self._config["max_probes"], len(order)):
                    rejected = self._menu.reject_category(product, category)
                    self._menu.forget_category(product)

                    if rejected >= self._config["max_categories"]:
                        return "noRow"

                    self._item_probes[product] = 0
                    self._log("no row on button %d's page made a '%s', trying another category"
                              % (category, product))

                    return "wrongRow"

                button = order[probe]

        graphics = self._config["products"][product]
        before = self.counts_of(graphics)

        def made_one():
            return self.counts_of(graphics) > before

        API.ClearJournal()

        opened = self._menu.press(button, gump, self._config["craft_timeout"])
        outcome = self._read_outcome(opened, made_one)

        # The one proof no wording can argue with, and it is checked before the wordings are
        # trusted: a shard that says nothing on a success still puts the bow in the pack
        if outcome == "made" or outcome is None:
            if made_one() or settled(self._config["craft_settle"], self._config["craft_poll"],
                                     made_one):
                if self._item_buttons.get(product) is None:
                    self._item_buttons[product] = button
                    self._log("'%s' is the row on button %d" % (product, button))

                self._make_last = True
                self._said_unreadable = 0

                return "made"

        if outcome != "made":
            # Nothing was made and nothing was said. MAKE LAST is the first thing to doubt - the
            # shard forgets what was last made for reasons this script cannot see - so the next
            # craft goes back through the category and the row, which is the path that proved itself.
            if outcome == "noMaterial":
                self._report_outcome("refused for materials", opened)

            if outcome is None:
                self._report_outcome("nothing readable came back", opened)

                if button == self._config["make_last_button"]:
                    self._make_last = False
                    self._log("MAKE LAST made nothing, pressing the row itself next time")

            return outcome

        # It said it made something and none of it was the wanted product, so the row was wrong
        self._log("button %d did not make a '%s', trying the next row" % (button, product))

        # A row the recipe table named is a row this shard has moved, so the walk takes it over
        if product in self._config["recipes"] and product not in self._walked:
            self._walked.add(product)
            self._log("the button table is out of date for '%s', walking the categories for it "
                      "instead" % product)

        self._forget_row(product)

        return "wrongRow"
