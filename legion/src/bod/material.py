import API

from uo.text import words_of


class MaterialPicker(object):
    """The craft menu's material page: pressed once, and again when the deed says it was wrong."""

    def __init__(self, menu, config, log):
        self._menu = menu
        self._config = config
        self._log = log
        self._selected = None
        self._said_unsplit = False

    # A deed that names no material (a potion deed) never opens the page
    def needs(self, material):
        return material is not None and self._selected != material

    def forget(self):
        self._selected = None

    def _names_for(self, material):
        return [material] + list(self._config["aliases"].get(material, []))

    # Matched on the leading words, so 'copper' does not take 'DULL COPPER (12)'
    def row_of(self, material, rows):
        wanted = [words_of(name) for name in self._names_for(material)]

        for index in range(min(len(rows), self._config["max_rows"])):
            words = words_of(rows[index])

            for name in wanted:
                if len(name) > 0 and words[:len(name)] == name:
                    return index

        return None

    # GetGumpContents hands the page back as one line; the material rows in it read 'IRON (1587)
    # DULL COPPER (111) ...' after the DO NOT COLOR toggle, so they are split on the counts
    def rows_from_text(self, text):
        low = (text or "").lower()
        marker = self._config["rows_after"]

        if marker in low:
            text = text[low.index(marker) + len(marker):]

        rows = []
        words = []

        for token in (text or "").split():
            if token.startswith("(") and token.endswith(")") and token[1:-1].isdigit():
                if len(words) > 0:
                    rows.append(" ".join(words) + " " + token)

                words = []
            else:
                words.append(token)

        return rows

    # The stock order, for a page whose text could not be split into rows
    def _stock_index(self, material):
        order = self._config["order"]

        return order.index(material) if material in order else None

    def select(self, material, gump):
        timeout = self._config["gump_timeout"]
        page = self._menu.press(self._menu.button_id(self._config["button_type"], 0), gump, timeout)

        if not page:
            return 0, "noGump"

        rows = self._menu.item_rows(page)

        if len(rows) == 0:
            rows = self.rows_from_text(API.GetGumpContents(page))

        index = self.row_of(material, rows)

        if index is None and len(rows) == 0:
            index = self._stock_index(material)

            if index is not None and not self._said_unsplit:
                self._said_unsplit = True
                self._log("the material page names no rows - pressing row %d for %s on the stock "
                          "order; the page says '%s'"
                          % (index, material, " | ".join(self._menu.lines(page)) or "(no text)"))

        if index is None:
            self._log("no material row reads '%s' - the page says '%s'"
                      % (material, " | ".join(rows or self._menu.lines(page)) or "(no text)"))

            return page, "noMaterialRow"

        button = self._menu.button_id(self._config["row_type"], index)
        opened = self._menu.press(button, page, timeout)

        if not opened:
            return 0, "noGump"

        self._selected = material
        self._log("the menu is set to %s, the material row on button %d" % (material, button))

        return opened, None
