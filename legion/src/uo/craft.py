import API

from uo.journal import journal_tail
from uo.entity import hex_of
from uo.pack import count_of, counts_by_graphic, diff_counts, hue_of, pack_contents
from uo.retry import settled
from uo.text import any_in, clipped, phrase_in, untagged


class Crafter(object):
    def __init__(self, tools, menu, stock, buckets, config, log, stamp=None):
        self._tools = tools
        self._menu = menu
        self._stock = stock
        self._buckets = buckets
        self._config = config
        self._log = log
        self._stamp = stamp
        self._item_buttons = {}
        self._item_probes = {}
        # Products whose art the table has wrong, proven made on a row the menu named
        self._trusted = set()
        # RECIPES rows whose label on the menu read as the product, as good as a row the walk found
        self._labelled = {}
        self._make_last = False
        self._said_unreadable = 0
        self._said_no_make_last = False
        self._heard = ""
        # Products the recipe table got wrong on this shard, which the walk owns from then on
        self._walked = set()

    def forget_last(self):
        self._make_last = False

    # The phrase is kept so a made that never landed can say what was believed and where
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

    # Pack first: a success this table has no wording for would otherwise wait out the timeout.
    # The gump's NOTICES panel is read too because the shard writes refusals there, not the journal.
    def _read_outcome(self, opened, landed):
        waited = 0.0

        while not API.StopRequested:
            if landed():
                self._heard = "the pack gained it"

                return "made"

            hit = self._journal_bucket()

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

        text = (clipped(untagged(" ".join(self._menu.lines(gump))), self._config["text_limit"])
                if gump else "")
        lines = journal_tail(self._config["tail_seconds"], self._config["tail_lines"], self._stamp)

        self._log("%s - the gump says '%s'" % (why, text or "(nothing)"))
        self._log("the journal says '%s'" % (" | ".join(lines) or "(nothing)"))
        self._log("the pack holds %s, and the menu is set to %s here"
                  % (self._stock.hue_report(), self._config["material"]))

    def _forget_row(self, product):
        self._make_last = False
        self._labelled.pop(product, None)

        if product in self._item_buttons:
            del self._item_buttons[product]

        self._item_probes[product] = self._item_probes.get(product, 0) + 1

    # The button to press, or an outcome when there is none. MAKE LAST is the only path that skips
    # the category: a row button is only in the gump once its category is showing.
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

            # The table is checked against the row's own label when the menu shows one: a row
            # that reads as the product is as good as one the walk found, and one that reads
            # otherwise is a shard that reordered the menu, not a row to press blind
            label = self._menu.label_of(known[1], page)

            if label is not None and label.lower() != product:
                self._log("button %d reads '%s', not '%s'" % (known[1], label, product))

                return None, self._walk_instead(product)

            if label is not None:
                self._labelled[product] = known[1]

            return known[1], None

        gump, category = self._menu.find_category(product, gump)

        if category is None:
            return None, "noRow"

        if not gump:
            return None, "noGump"

        button = self._item_buttons.get(product)

        if button is not None:
            return button, None

        probe = self._item_probes.get(product, 0)
        found = self._menu.find_row(product, gump) if probe == 0 else None

        if found is None:
            order = self._menu.candidate_buttons(product, gump)
        else:
            gump, button = found

            if not gump:
                return None, "noGump"

            if button is not None:
                self._item_buttons[product] = button

                return button, None

            order = []

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

    def _named_for(self, item, product):
        props = API.ItemNameAndProps(item.Serial) or ""
        name = props.split("\n")[0] if props else (item.Name or "")

        return phrase_in(name, product)

    # The shard said made and the table's art never landed: a new art in the pack whose name says
    # the product is it under this shard's number. UOAlive's lightning scroll is not stock 0x1F4B.
    def _learn_art(self, product, held):
        items = pack_contents()
        gained, _lost = diff_counts(held, counts_by_graphic(items))
        arts = set()

        for item in items:
            if (item.Graphic, hue_of(item)) in gained and self._named_for(item, product):
                arts.add(item.Graphic)

        if len(arts) != 1:
            return False

        art = arts.pop()
        # Rebound rather than added to: carpentry's addon products share one set object
        self._config["products"][product] = set(self._config["products"][product]) | set([art])
        self._log("'%s' landed as %s, not the art in the table - put %s in it"
                  % (product, hex_of(art), hex_of(art)))

        return True

    def _keep_row(self, product, button):
        if button != self._config["make_last_button"]:
            self._item_buttons[product] = button

        self._make_last = True

    # A row the menu named by its exact label, found by the walk or checked off RECIPES, is proof
    # the pack cannot overrule: the shard said made and no art in the table landed, so the table is
    # what is wrong
    def _trust_named(self, product, button, held):
        if product not in self._trusted:
            if button not in (self._menu.named_button(product), self._labelled.get(product)):
                return False

            self._trusted.add(product)
            gained, _lost = diff_counts(held, counts_by_graphic(pack_contents()))
            arts = sorted(set(graphic for graphic, _hue in gained))
            self._log("'%s' landed as %s, which the product table does not list - counting the row "
                      "the menu named as made; put it in the table"
                      % (product, ", ".join(hex_of(art) for art in arts) or "nothing new"))

        self._keep_row(product, button)

        return True

    # Something was made and none of it was the product, so a row was wrong - unless the press was
    # MAKE LAST, which the shard forgets on its own and which says nothing about the proven row
    def _wrong_product(self, product, button):
        if button == self._config["make_last_button"]:
            self._make_last = False
            self._log("MAKE LAST did not make a '%s', pressing the row itself next time" % product)

            return "wrongRow"

        self._log("button %d did not make a '%s' - %s - trying the next row"
                  % (button, product, self._heard))

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

        # The details pages may have taken the menu down and brought it back
        gump = self._menu.current_id() or gump

        graphics = self._config["products"][product]
        before = count_of(graphics)
        held = counts_by_graphic(pack_contents())

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
            if self._learn_art(product, held):
                self._keep_row(product, button)

                return "made"

            if self._trust_named(product, button, held):
                return "made"

            return self._wrong_product(product, button)

        if outcome == "noMaterial":
            self._report_outcome("refused for materials", opened)
        elif outcome is None:
            self._report_outcome("nothing readable came back", opened)

            if button == self._config["make_last_button"]:
                self._make_last = False
                self._log("MAKE LAST made nothing, pressing the row itself next time")

        return outcome
