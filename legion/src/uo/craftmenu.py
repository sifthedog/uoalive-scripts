import API

from uo.entity import hex_of
from uo.gump import await_gump, await_recognised, button_ids, controls, is_open, open_ids
from uo.text import any_in, phrase_in

# The client's own page-turn labels, drawn between the pages of a long category
PAGE_LABELS = ["NEXT PAGE", "PREV PAGE"]


class CraftMenu(object):
    """A craft gump: opening it, finding the category, and finding the row."""

    def __init__(self, tools, config, log):
        self._tools = tools
        self._config = config
        self._log = log
        self._id = 0
        self._page = 0
        self._ignored = set()
        self._said_gump_text = False
        self._said_no_category = False
        self._said_no_row = set()
        self._said_no_named = set()
        self._said_no_details = False
        self._said_no_button = set()
        self._said_not_menu = False
        self._category_buttons = {}
        self._category_rejects = {}

    def current_id(self):
        return self._id

    def button_id(self, kind, index):
        return 1 + kind + index * self._config["stride"]

    def has_button(self, button, gump):
        known = button_ids(gump)

        return known is None or button in known

    # The shard drops the connection for a button the gump does not have, so nothing is sent blind
    def _send(self, button, gump):
        if not self.has_button(button, gump):
            if button not in self._said_no_button:
                self._said_no_button.add(button)
                self._log("gump %s has no button %d - not pressing it" % (hex_of(gump), button))

            return False

        return bool(API.ReplyGump(button, gump))

    def reply(self, button, gump):
        if not gump or gump != self._id:
            if not self._said_not_menu:
                self._said_not_menu = True
                self._log("not pressing button %d on %s - it is not the craft menu"
                          % (button, hex_of(gump)))

            return False

        return self._send(button, gump)

    def press(self, button, gump, timeout):
        if not self.reply(button, gump):
            return 0

        return await_gump(self._id, timeout)

    # For a button that opens another gump: the one that was not up before answers, else the menu
    def press_page(self, button, gump, timeout):
        before = open_ids() + list(self._ignored)

        if not self.reply(button, gump):
            return 0

        found, _recognised = await_recognised(lambda ident: False, before, timeout,
                                              self._config["gump_poll"])

        if not found:
            found = await_gump(self._id, 0)

        self._page = found

        return found

    def reply_page(self, button, page):
        if not page or page != self._page:
            return False

        return self._send(button, page)

    def is_craft_gump(self, ident):
        if not ident:
            return False

        if any_in(API.GetGumpContents(ident) or "", self._config["title_fragments"]):
            return True

        # GumpContains reads controls GetGumpContents may not put in text
        for phrase in self._config["title_text"]:
            if API.GumpContains(phrase, ident):
                return True

        # The title is a cliloc that may not render; the group rows are read here regardless
        for line in self.lines(ident):
            if (line.lower() in self._config["category_names"]
                    or line.upper() == self._config["last_ten_label"]):
                return True

        return False

    def lines(self, gump):
        text = API.GetGumpContents(gump)

        return [line.strip() for line in (text or "").split("\n") if line.strip()]

    def _ignore(self, ident):
        if ident in self._ignored:
            return

        self._ignored.add(ident)
        lines = self.lines(ident)
        self._log("ignoring gump %s - it is not the craft menu, it starts '%s'"
                  % (hex_of(ident), lines[0] if lines else "(no text)"))

    def open(self):
        if self._id and is_open(self._id):
            return self._id

        before = open_ids()

        for ident in before:
            if self.is_craft_gump(ident):
                self._id = ident

                return ident

            self._ignore(ident)

        serial = self._tools.serial()

        if serial is None:
            return None

        API.UseObject(serial)

        # A foreign gump the shard re-sends during the wait is not what the tools opened
        found, recognised = await_recognised(self.is_craft_gump, before + list(self._ignored),
                                             self._config["gump_timeout"],
                                             self._config["gump_poll"])

        if not found:
            return None

        if not recognised and not self._said_gump_text:
            self._said_gump_text = True
            lines = self.lines(found)
            self._log("the %s opened a gump that does not name %s - it starts '%s'"
                      % (self._config["tool_noun"], self._config["title"],
                         lines[0] if lines else "(no text)"))

        self._id = found

        return found

    def _is_item_button(self, button):
        return (button is not None and button > 0
                and (button - 1 - self._config["item_type"]) % self._config["stride"] == 0)

    # The stock layout draws a SELECTIONS row as its button, its name, then its details button, and
    # every page's rows are in the gump at once: the pairs are read off the controls whichever page
    # shows. A page-turn label follows a page button, so it never pairs.
    def rows_of(self, gump):
        read = controls(gump)

        if read is None:
            return []

        rows = []
        pending = None

        for button, text in read:
            if text is None:
                pending = button if self._is_item_button(button) else None
                continue

            label = text.strip()

            if pending is not None and label:
                rows.append((label, pending))

            pending = None

        return rows

    # The text as a last resort: the stock gump emits the group rows before the item rows, and a
    # build that hands the menu back as one line has no rows in it
    def _text_rows(self, gump):
        lines = self.lines(gump)
        start = None

        for index in range(len(lines)):
            if (lines[index].lower() in self._config["category_names"]
                    or lines[index].upper() == self._config["last_ten_label"]):
                start = index + 1

        if start is None:
            return []

        return [line for line in lines[start:] if line.upper() not in PAGE_LABELS]

    def item_rows(self, gump):
        rows = [label for label, _button in self.rows_of(gump)]

        return rows if rows else self._text_rows(gump)

    # Whole row, never a substring: "crossbow" is inside "crossbow bolt", in another category.
    # A menu that reads as one line has no rows, and GumpContains is case-sensitive
    def page_has(self, product, gump):
        rows = self.item_rows(gump)

        for row in rows:
            if row.lower() == product:
                return True

        if len(rows) > 0:
            return False

        return phrase_in(API.GetGumpContents(gump), product) or API.GumpContains(product, gump)

    def remember_category(self, product, button):
        self._category_buttons[product] = button

    def forget_category(self, product):
        if product in self._category_buttons:
            del self._category_buttons[product]

    def reject_category(self, product, button):
        rejected = self._category_rejects.setdefault(product, set())
        rejected.add(button)

        return len(rejected)

    # Pressing a category only redraws the SELECTIONS panel, so walking them costs no wood
    def find_category(self, product, gump):
        known = self._category_buttons.get(product)

        if known is not None:
            return (self.press(known, gump, self._config["gump_timeout"]), known)

        rejected = self._category_rejects.get(product, set())

        for index in range(self._config["max_categories"]):
            button = self.button_id(self._config["category_type"], index)

            if button in rejected or not self.has_button(button, gump):
                continue

            opened = self.press(button, gump, self._config["gump_timeout"])

            # A press that answered nothing is not a verdict on the category
            if not opened:
                return (0, 0)

            if self.page_has(product, opened):
                self._category_buttons[product] = button
                self._log("'%s' is in the category on button %d" % (product, button))

                return (opened, button)

            gump = opened

        if not self._said_no_category:
            self._said_no_category = True
            self._log("no category lists '%s' - check the name against the SELECTIONS rows"
                      % product)

        return (gump, None)

    # The pen is used again when the details page took the menu down with it
    def _back_to(self, category):
        menu = self.open()

        if not menu:
            return 0

        return self.press(category, menu, self._config["gump_timeout"])

    # A row the menu names is taken on its name. Otherwise each row's details page (its button plus
    # one, which costs nothing to open) is opened until one names the product, the rows whose names
    # carry it first. None sends the caller to the walk; (gump, None) is a category that has no
    # such row.
    def find_row(self, product, gump):
        category = self._category_buttons.get(product)

        if category is None or button_ids(gump) is None:
            return None

        rows = self.rows_of(gump)

        for label, button in rows:
            if label.lower() == product:
                self._log("'%s' is the row on button %d - the menu names it there"
                          % (product, button))

                return (gump, button)

        if rows and product not in self._said_no_named:
            self._said_no_named.add(product)
            self._log("no SELECTIONS row reads '%s', opening each row's details page instead"
                      % product)
            self._log("rows seen: %s" % ", ".join(label for label, _button in rows))

        for button in self._walk_order(product, rows):
            if not self.has_button(button, gump):
                continue

            if not self.has_button(button + 1, gump):
                return None

            before = self.lines(gump)
            details = self.press_page(button + 1, gump, self._config["gump_timeout"])

            if not details:
                return None

            text = self.lines(details)

            if text == before:
                if not self._said_no_details:
                    self._said_no_details = True
                    self._log("button %d opened no details page, walking the rows instead"
                              % (button + 1))

                return None

            named = phrase_in(" ".join(text), product)
            API.CloseGump(details)
            gump = self._back_to(category)

            if not gump:
                return (0, None)

            if named:
                self._log("'%s' is the row on button %d - its details page names it"
                          % (product, button))

                return (gump, button)

        return (gump, None)

    # The row's button by its name, or None when the menu does not name it. With no controls to
    # read, the row's place in the text stands in for its index
    def named_row(self, product, gump):
        rows = self.rows_of(gump)

        if rows:
            for label, button in rows:
                if label.lower() == product:
                    return button

            return None

        text = self._text_rows(gump)

        for index in range(len(text)):
            if text[index].lower() == product:
                return self.button_id(self._config["item_type"], index)

        return None

    # The rows named for the product, then the rows whose names carry it, then every row in order
    def _walk_order(self, product, rows):
        order = [button for label, button in rows if label.lower() == product]

        for label, button in rows:
            if button not in order and phrase_in(label, product):
                order.append(button)

        for index in range(self._config["max_item_rows"]):
            button = self.button_id(self._config["item_type"], index)

            if button not in order:
                order.append(button)

        return order

    # The named rows first: unlike a category, a wrong row crafts the wrong item and spends the wood
    def candidate_buttons(self, product, gump):
        rows = self.rows_of(gump)
        order = self._walk_order(product, rows)
        named = self.named_row(product, gump)

        if named is not None and named in order:
            order.remove(named)
            order.insert(0, named)

        if named is None and product not in self._said_no_row:
            self._said_no_row.add(product)
            self._log("the gump text does not name '%s' on a row of its own, walking the rows"
                      % product)
            seen = self.item_rows(gump)
            self._log("rows seen: %s" % (", ".join(seen) if seen else "none"))

        known = button_ids(gump)

        return order if known is None else [button for button in order if button in known]
