# Built from src/craftmap/index.py by build.py - do not edit.

import API
import time


# src/craftmap/table.py
# The block a craft script's config.py pastes in: the shard's group names, then every row under
# its group, keyed the way Crafter looks a product up
def recipes_block(title, stamp, categories, rows):
    lines = ["# %s, read off the menu on %s" % (title, stamp), "CATEGORY_NAMES = ["]

    for label, _button in categories:
        lines.append('    "%s",' % label.lower())

    lines += ["]", "", "RECIPES = {"]
    seen = set()

    for label, category in categories:
        lines.append("    # %s (button %d)" % (label, category))

        for name, button in rows.get(category, []):
            key = name.lower()
            entry = '"%s": (%d, %d),' % (key, category, button)

            # The menu lists an item twice (bulletin board, east and south); the first is the table's
            if key in seen:
                lines.append("    # %s  listed again, the first kept" % entry)
            else:
                seen.add(key)
                lines.append("    " + entry)

    lines.append("}")

    return "\n".join(lines) + "\n"


# src/uo/entity.py
def hex_of(value):
    return "0x%x" % (value & 0xFFFFFFFF)


# src/uo/gump.py
# HasGump() only ever answers the last gump the shard sent, and a gump the shard re-sends on its own
# steals that slot: the id-addressed calls below do not go through it
def open_ids():
    found = []
    last = API.HasGump()

    if last:
        found.append(last)

    try:
        for gump in API.GetAllGumps() or []:
            serial = getattr(gump, "ServerSerial", 0)

            if serial and serial not in found:
                found.append(serial)
    except Exception:
        if API.StopRequested:
            raise

    return found


def is_open(ident):
    return bool(ident) and bool(API.WaitForGump(ident, 0))


def await_gump(ident, timeout):
    if not ident:
        return 0

    return ident if API.WaitForGump(ident, timeout) else 0


# A getter can throw on its own (Control.X does), which is not the whole gump being unreadable
def _field(control, name):
    try:
        return getattr(control, name, None)
    except Exception:
        if API.StopRequested:
            raise

        return None


# The controls in the order the layout drew them, every page at once, as (button id, text) with
# None for whichever a control lacks. None for the list is "could not read them", which no caller
# treats as "none": the shard drops the connection for a button the gump does not have, so an
# unreadable gump must not be mistaken for an empty one
def controls(ident):
    if not ident:
        return None

    try:
        gump = API.GetGump(ident)

        if gump is None:
            return None

        found = []

        for control in gump.Children or []:
            button = _field(control, "ButtonID")
            text = _field(control, "Text")

            found.append((None if button is None else int(button), text or None))

        return found
    except Exception:
        if API.StopRequested:
            raise

        return None


def button_ids(ident):
    read = controls(ident)

    if read is None:
        return None

    return set(button for button, _text in read if button is not None)


# A recognised gump wins; failing that, one that was not up before the use. Returns (id, recognised)
def await_recognised(known, before, timeout, poll):
    waited = 0.0
    newcomer = 0

    while waited < timeout:
        for ident in open_ids():
            if known(ident):
                return ident, True

            if not newcomer and ident not in before:
                newcomer = ident

        if newcomer:
            return newcomer, False

        API.Pause(poll)
        waited += poll

    return 0, False


# src/uo/text.py
def any_in(text, fragments):
    low = (text or "").lower()

    for fragment in fragments:
        if fragment in low:
            return True

    return False


def untagged(text):
    kept = []
    inside = False

    for char in text or "":
        if char == "<":
            inside = True
        elif char == ">":
            inside = False
        elif not inside:
            kept.append(char)

    return "".join(kept)


# src/uo/craftmenu.py
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
        self._said_no_button = set()
        self._said_not_menu = False

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

    def _is_button_of(self, kind, button):
        return (button is not None and button > 0
                and (button - 1 - kind) % self._config["stride"] == 0)

    # The stock layout draws a row as its button then its name (a SELECTIONS row's details button
    # follows), and every page's rows are in the gump at once: the pairs are read off the controls
    # whichever page shows. A page-turn label follows a page button, so it never pairs.
    def _labelled(self, gump, kind):
        read = controls(gump)

        if read is None:
            return []

        rows = []
        pending = None

        for button, text in read:
            if text is None:
                pending = button if self._is_button_of(kind, button) else None
                continue

            label = text.strip()

            if pending is not None and label:
                rows.append((label, pending))

            pending = None

        return rows

    def rows_of(self, gump):
        return self._labelled(gump, self._config["item_type"])

    def categories_of(self, gump):
        return self._labelled(gump, self._config["category_type"])

    def item_rows(self, gump):
        return [label for label, _button in self.rows_of(gump)]


# src/uo/log.py
def make_log(prefix):
    stamp = prefix + ": "

    def log(message):
        if log.enabled:
            API.SysMsg(stamp + message)

    # The client puts a SysMsg in the journal beside the shard's own lines, so a script reading the
    # journal back needs to know which lines it wrote itself - without this a report of an unreadable
    # outcome quotes the last report of an unreadable outcome. Lowercase, because that is how the
    # journal readers compare. Carried on the function itself rather than a module-level list: a
    # bundle is one script and one prefix, and a shared list would leak between scripts sharing this
    # process, such as the test suite.
    log.stamp = stamp.lower()
    log.enabled = True

    return log


# src/uo/paths.py
# TazUO's working directory is its own folder, and the scripts live in this subfolder of it
SCRIPTS_FOLDER = "LegionScripts"


# A bare name lands in TazUO's working directory; beside the script is where anyone looks for it.
# A name with a folder in it, relative or absolute, is left as written.
def beside_script(name):
    if not name or "/" in name or "\\" in name:
        return name

    script = getattr(API, "ScriptPath", None) or ""
    cut = max(script.rfind("/"), script.rfind("\\"))

    # A client that does not say where the script is still runs it out of the standard folder
    if cut < 0:
        return SCRIPTS_FOLDER + "/" + name

    return script[:cut + 1] + name


# src/craftmap/index.py
OUT = "craft-map.txt"

# Buttons are 1 + type + index * 20 on this shard's menus, as every craft script's config says
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1

GUMP_TIMEOUT = 5.0

# The redraw lands a moment after WaitForGump answers
REDRAW_DELAY = 0.4

log = make_log("craft-map")


class NoTool(object):
    def serial(self):
        return None


menu = CraftMenu(NoTool(), {
    "stride": BUTTON_STRIDE,
    "category_type": CATEGORY_BUTTON_TYPE,
    "item_type": ITEM_BUTTON_TYPE,
}, log)


def title_of(gump):
    for _button, text in controls(gump) or []:
        if text and "MENU" in text.upper():
            return untagged(text).strip()

    return "CRAFT MENU"


found = None
categories = []

for ident in open_ids():
    categories = menu.categories_of(ident)

    if categories:
        found = ident
        break

if found is None:
    log("no craft menu is open - open one with its tool, then run this again")
    API.Stop()

title = title_of(found)
log("%s on gump %s, %d categories" % (title, hex_of(found), len(categories)))

rows = {}

for label, button in categories:
    if not menu.has_button(button, found):
        log("gump %s has no button %d for '%s' - skipping it" % (hex_of(found), button, label))
        continue

    API.ReplyGump(button, found)

    if not API.WaitForGump(found, GUMP_TIMEOUT):
        log("the menu did not come back after pressing '%s' (button %d) - stopping" % (label, button))
        break

    API.Pause(REDRAW_DELAY)
    rows[button] = menu.rows_of(found)
    log("%s (button %d): %d rows" % (label, button, len(rows[button])))

path = beside_script(OUT)
handle = open(path, "w")
handle.write(recipes_block(title, time.strftime("%Y-%m-%d"), categories, rows))
handle.close()

log("wrote %s - paste its RECIPES and CATEGORY_NAMES into the script's config.py" % path)
