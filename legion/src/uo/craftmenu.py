import API

from uo.entity import hex_of
from uo.gump import await_any
from uo.text import any_in


class CraftMenu(object):
    """A craft gump: opening it, finding the category, and finding the row."""

    def __init__(self, tools, config, log):
        self._tools = tools
        self._config = config
        self._log = log
        self._id = 0
        self._said_gump_text = False
        self._said_no_category = False
        self._said_no_row = set()
        self._category_buttons = {}
        self._category_rejects = {}

    def current_id(self):
        return self._id

    def button_id(self, kind, index):
        return 1 + kind + index * self._config["stride"]

    # False is the client saying the gump was gone before the press: not worth waiting out
    def press(self, button, gump, timeout):
        if not API.ReplyGump(button, gump):
            return 0

        found = await_any(timeout, self._config["gump_poll"])

        if found:
            self._id = found

        return found

    def is_craft_gump(self, ident):
        if not ident:
            return False

        if any_in(API.GetGumpContents(ident) or "", self._config["title_fragments"]):
            return True

        # GumpContains reads controls GetGumpContents may not put in text
        for phrase in self._config["title_text"]:
            if API.GumpContains(phrase, ident):
                return True

        return False

    def lines(self, gump):
        text = API.GetGumpContents(gump)

        return [line.strip() for line in (text or "").split("\n") if line.strip()]

    def open(self):
        found = API.HasGump()

        if found and (found == self._id or self.is_craft_gump(found)):
            self._id = found

            return found

        serial = self._tools.serial()

        if serial is None:
            return None

        # The wait below is for any gump, so a vendor's or status gump standing open would answer it
        if found:
            self._log("closing the gump that is in the way %s" % hex_of(found))
            API.CloseGump(found)
            API.Pause(self._config["gump_poll"])

        API.UseObject(serial)

        found = await_any(self._config["gump_timeout"], self._config["gump_poll"])

        if not found:
            return None

        # The title is a cliloc the client resolves; gating on it made a working menu read as none
        if not self._said_gump_text and not self.is_craft_gump(found):
            self._said_gump_text = True
            lines = self.lines(found)
            self._log("the %s opened a gump that does not name %s - it starts '%s'"
                      % (self._config["tool_noun"], self._config["title"],
                         lines[0] if lines else "(no text)"))

        self._id = found

        return found

    # The stock gump emits the group rows before the item rows
    def item_rows(self, gump):
        lines = self.lines(gump)
        start = None

        for index in range(len(lines)):
            if (lines[index].lower() in self._config["category_names"]
                    or lines[index].upper() == self._config["last_ten_label"]):
                start = index + 1

        return [] if start is None else lines[start:]

    # Whole row, never a substring: "crossbow" is inside "crossbow bolt", in another category
    def page_has(self, product, gump):
        rows = self.item_rows(gump)

        for row in rows:
            if row.lower() == product:
                return True

        return len(rows) == 0 and API.GumpContains(product, gump)

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

            if button in rejected:
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

    # The text first: unlike a category, a wrong row crafts the wrong item and spends the wood
    def candidate_buttons(self, product, gump):
        rows = self.item_rows(gump)
        order = []

        for index in range(len(rows)):
            if rows[index].lower() == product:
                order.append(self.button_id(self._config["item_type"], index))

        if len(order) == 0 and product not in self._said_no_row:
            self._said_no_row.add(product)
            self._log("the gump text does not name '%s' on a row of its own, walking the rows"
                      % product)
            self._log("rows seen: %s" % (", ".join(rows) if rows else "none"))

        for index in range(self._config["max_item_rows"]):
            button = self.button_id(self._config["item_type"], index)

            if button not in order:
                order.append(button)

        return order
