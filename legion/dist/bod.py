# Built from src/bod/index.py by build.py - do not edit.

import API
import time


# src/uo/entity.py
# API.Player is None whenever the client is between world states - a recall, a server line change,
# the moment around a death - and reading through it threw a live restock away
def player():
    try:
        return API.Player
    except Exception:
        return None


def hex_of(value):
    return "0x%x" % (value & 0xFFFFFFFF)


# src/uo/gump.py
# For a menu whose pages all share one type id: HasGump answers the gump's *type*, and ReplyGump
# disposes the gump it answers before the shard sends the next page, so the wait is for the menu to
# be back rather than for a different id
def await_any(timeout, poll):
    waited = 0.0

    while waited < timeout:
        found = API.HasGump()

        if found:
            return found

        API.Pause(poll)
        waited += poll

    return 0


def gump_says(gump, texts):
    for text in texts:
        if API.GumpContains(text, gump):
            return True

    return False


# src/uo/journal.py
def said(texts):
    for text in texts:
        if API.InJournal(text, False):
            return True

    return False


# matchingText is left off on purpose: the client only applies it as a regex, so a plain string
# there filters everything out
def journal_tail(seconds, limit):
    try:
        entries = API.GetJournalEntries(seconds)
    except Exception:
        return []

    texts = []

    for entry in entries if entries else []:
        text = getattr(entry, "Text", None)

        if text and text.strip():
            texts.append(text.strip())

    return texts[-limit:]


# Line by line rather than the whole journal: a wholesale clear before every swing wiped the ambush
# warning before the threat watch got its once-a-cycle look at it
def forget(phrases):
    for text in phrases:
        API.ClearJournal(text)


def matched_bucket(buckets):
    for name, phrases in buckets:
        # clearMatches, or a line already read answers the next wait as well
        if API.InJournalAny(phrases, True):
            return name

    return None


# src/uo/text.py
def words_of(text):
    letters = []

    for char in (text or "").lower():
        letters.append(char if char.isalnum() else " ")

    return "".join(letters).split()


def word_in(text, words):
    found = words_of(text)

    for word in words:
        if word in found:
            return True

    return False


def any_in(text, fragments):
    low = (text or "").lower()

    for fragment in fragments:
        if fragment in low:
            return True

    return False


def clipped(text, limit):
    flat = " ".join((text or "").split())

    return flat if len(flat) <= limit else flat[:limit] + "..."


# src/bod/combine.py
class DeedCombiner(object):
    """One item into the deed, through the deed's own gump and the cursor it raises."""

    def __init__(self, deed, items, buckets, config, log):
        self._deed = deed
        self._items = items
        self._buckets = buckets
        self._config = config
        self._log = log
        self._said_gump_text = False
        self._reported = 0

    def _lines(self, gump):
        text = API.GetGumpContents(gump)

        return [line.strip() for line in (text or "").split("\n") if line.strip()]

    # Whatever is up - the craft menu, the last deed gump - would answer the wait below
    def _open(self):
        up = API.HasGump()

        if up:
            API.CloseGump(up)
            API.Pause(self._config["gump_poll"])

        API.UseObject(self._deed.serial)

        found = await_any(self._config["gump_timeout"], self._config["gump_poll"])

        if found and not self._said_gump_text and not gump_says(found, self._config["gump_text"]):
            self._said_gump_text = True
            lines = self._lines(found)
            self._log("the deed opened a gump that does not say bulk order - it starts '%s'"
                      % (lines[0] if lines else "(no text)"))

        return found

    def _report(self, why, gump):
        if self._reported >= self._config["max_reports"]:
            return

        self._reported += 1
        text = clipped(" ".join(self._lines(gump)), self._config["text_limit"]) if gump else ""
        lines = journal_tail(self._config["tail_seconds"], self._config["tail_lines"])

        self._log("%s - the gump says '%s'" % (why, text or "(nothing)"))
        self._log("the journal says '%s'" % (" | ".join(lines) or "(nothing)"))

    # The item leaving the pack is the proof no wording can argue with
    def _read_outcome(self, serial):
        waited = 0.0

        while not API.StopRequested:
            hit = matched_bucket(self._buckets)

            if hit is not None:
                return hit

            if serial not in self._items.serials():
                return "combined"

            if waited >= self._config["combine_timeout"]:
                return None

            API.Pause(self._config["combine_poll"])
            waited += self._config["combine_poll"]

    # The shard re-sends the deed gump before it raises the cursor, so one is left up either way
    def _close(self):
        if API.HasTarget():
            API.CancelTarget()

        up = API.HasGump()

        if up:
            API.CloseGump(up)

    def combine(self, serial):
        gump = self._open()

        if not gump:
            return "noGump"

        API.ClearJournal()

        if not API.ReplyGump(self._config["combine_button"], gump):
            return "noGump"

        if not API.WaitForTarget("any", self._config["target_timeout"]):
            self._report("no cursor came up for the combine", gump)
            self._close()

            return "noCursor"

        API.Target(serial)

        outcome = self._read_outcome(serial)

        if outcome is None:
            self._report("nothing readable came back for %s" % hex_of(serial), gump)

        self._close()

        return outcome


# src/uo/phrases.py
"""The shard's own wordings, as far as they are the same whatever the script is doing."""

SAVING_TEXT = ["The world is saving", "Saving world", "World save started"]
SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"]

# Ends in a bare 'You must wait', which longer refusals contain - so a bucket that has to be told
# apart from a throttle is ordered before this one
THROTTLED_TEXT = [
    "You must wait to perform another action",
    "You must wait a moment",
    "You must wait",
]

STOPPED = "stopped from the script manager"


# src/uo/timings.py
"""The constants the scripts agreed on. Every one is in seconds - API.Pause takes seconds."""

SAVE_WAIT = 60.0
SAVE_POLL = 1.0

THROTTLE_BACKOFF = 1.0
THROTTLE_BACKOFF_MAX = 8.0
HEARTBEAT_EVERY = 30.0

STALL_WARN = 60
STALL_STOP = 300

STEP_DELAY = 0.3


# src/bod/config.py
SKILL_NAMES = ["Blacksmithy", "Blacksmith"]

TOOL_GRAPHICS = set([
    0x13E3, 0x13E4,  # smith's hammer
    0x0FBB, 0x0FBC,  # tongs
    0x0FB4, 0x0FB5,  # sledge hammer
])

# Whole words: 'smith' is in "smith's hammer" and not in "war hammer"
TOOL_NAME_WORDS = ["tongs", "smith"]

INGOT_GRAPHICS = set([0x1BF2, 0x1BEF])
INGOT_NAME_WORDS = ["ingot", "ingots"]

# What a deed that names no material wants, and the menu row it is set back to
PLAIN_MATERIAL = "iron"

# The deed's wording first, then how the menu row and the item's tooltip may shorten it
MATERIAL_ALIASES = {
    "shadow iron": ["shadow"],
}

# For the 'the pack holds ...' line only. Incomplete on purpose: an unknown hue is reported as such
INGOT_HUES = {
    0: "iron",
    0x973: "dull copper",
    0x966: "shadow iron",
    0x96D: "copper",
    0x972: "bronze",
    0x8A5: "gold",
    0x979: "agapite",
    0x89F: "verite",
    0x8AB: "valorite",
}

# The tooltip's own lines, lower-cased
DEED_TEXT = {
    "large": "large bulk order",
    "amount": "amount to make:",
    "exceptional": "must be exceptional",
    "material_before": "must be made with",
    "material_after": "ingots",
}

ARTICLES = ["a ", "an "]
EXCEPTIONAL_TEXT = "exceptional"

# Lower-cased, both spellings the stock clilocs may resolve to
CATEGORY_NAMES = [
    "metal armor", "helmets", "shields", "bladed", "bladed weapons", "axes", "polearms",
    "pole arms", "bashing", "bashing weapons", "cannons", "high seas cannons", "throwing",
    "throwing weapons", "miscellaneous",
]

CRAFT_TITLE = "BLACKSMITHY"
CRAFT_TITLE_TEXT = [CRAFT_TITLE, "BLACKSMITH"]
CRAFT_TITLE_FRAGMENTS = [phrase.lower() for phrase in CRAFT_TITLE_TEXT]
LAST_TEN_LABEL = "LAST TEN"

# Buttons are 1 + type + index * 20 on this shard: categories 1, 21, 41 ..., rows 2, 22, 42 ...,
# the material page on 7 with its rows on 6, 26, 46 ..., MAKE LAST on 47
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MATERIAL_ROW_TYPE = 5
MATERIAL_BUTTON_TYPE = 6
MAKE_LAST_BUTTON = 47

MAX_CATEGORIES = 10
MAX_ITEM_ROWS = 20
MAX_MATERIAL_ROWS = 12

# Each miss spends one item's worth of ingots
MAX_ITEM_PROBES = 4

BOD_COMBINE_BUTTON = 2
BOD_GUMP_TEXT = ["bulk order", "Combine this deed"]

# Seconds throughout - API.Pause takes seconds
PICK_TIMEOUT = 60.0

# Whole seconds: the API takes an int here
OPL_TIMEOUT = 2

# Tooltip reads one item gets before it is given up on for the pass
OPL_ASKS = 3
OPL_SETTLE = 0.5

GUMP_TIMEOUT = 5.0
GUMP_POLL = 0.15

CRAFT_TIMEOUT = 10.0
CRAFT_POLL = 0.2
CRAFT_SETTLE = 1.5

TARGET_TIMEOUT = 4.0
COMBINE_TIMEOUT = 4.0
COMBINE_POLL = 0.2

# How long the deed's tooltip has to show a combine the pack already proved
REREAD_SETTLE = 3.0
REREAD_POLL = 0.5

MAX_CYCLES = 2000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_TOOL = 5
MAX_NO_CURSOR = 3

MAX_UNREADABLE_REPORTS = 2
UNREADABLE_TEXT_LIMIT = 160
JOURNAL_TAIL_SECONDS = 20.0
JOURNAL_TAIL_LINES = 4

# Ordered: 'failed' before 'made' because "You failed to create the item" contains "create the item"
OUTCOME_TEXT = [
    (
        "failed",
        [
            "You failed to create the item",
            "You fail to create",
            "You have failed to create",
            "lost some of the raw material",
        ],
    ),
    ("made", ["You create the item", "You put the"]),
    (
        "noMaterial",
        [
            "You do not have sufficient metal",
            "You don't have the resources",
            "You do not have the resources",
            "not enough ingots",
            "You have insufficient",
        ],
    ),
    ("noAnvil", ["near an anvil and a forge", "anvil and forge"]),
    (
        "skillTooLow",
        [
            "You have no idea how to make that",
            "You do not have enough skill",
            "You are not skilled enough",
            "lack the skill",
        ],
    ),
    ("toolWorn", ["You have worn out your tool", "worn out your tool"]),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]

COMBINE_TEXT = [
    ("combined", ["has been combined with the deed"]),
    ("full", ["maximum amount of requested items"]),
    ("notRequested", ["The item is not in the request"]),
    ("wrongMaterial", ["not made from the requested resource"]),
    ("notExceptional", ["The item must be exceptional"]),
    ("notInPack", ["must have the item in your backpack"]),
    ("tooMany", ["provided more than"]),
]


# src/uo/retry.py
def settled(timeout, poll, landed):
    waited = 0.0

    while waited < timeout:
        API.Pause(poll)
        waited += poll

        if landed():
            return True

    return False


# src/bod/craft.py
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


# src/bod/deed.py
def strip_article(name, articles):
    for article in articles:
        if name.startswith(article):
            return name[len(article):]

    return name


def to_int(text):
    try:
        return int(text.strip())
    except ValueError:
        return None


def parse_deed(lines, config):
    text = config["text"]
    low = [line.strip().lower() for line in lines if line and line.strip()]
    total = None
    exceptional = False
    material = config["plain"]
    items = []

    for line in low:
        if text["large"] in line:
            return None, "a large bulk order - only small deeds are handled"

        if line.startswith(text["amount"]):
            total = to_int(line[len(text["amount"]):])
        elif text["exceptional"] in line:
            exceptional = True
        elif text["material_before"] in line:
            after = line.split(text["material_before"], 1)[1]
            material = after.replace(text["material_after"], "").strip(" .")
        elif ":" in line:
            name, count = line.rsplit(":", 1)
            done = to_int(count)

            if done is not None:
                items.append((strip_article(name.strip(), config["articles"]), done))

    if len(items) > 1:
        return None, "lists %d items, which is a large deed" % len(items)

    if total is None or len(items) == 0:
        return None, "could not read it - the tooltip says '%s'" % " | ".join(low)

    return {
        "item": items[0][0],
        "done": items[0][1],
        "total": total,
        "exceptional": exceptional,
        "material": material,
    }, None


class Deed(object):
    def __init__(self, serial, config, log):
        self.serial = serial
        self._config = config
        self._log = log
        self.request = None
        self._said_behind = False

    def _lines(self):
        props = API.ItemNameAndProps(self.serial, True, self._config["opl_timeout"]) or ""

        return [line.strip() for line in props.splitlines() if line.strip()]

    def read(self):
        request, why = parse_deed(self._lines(), self._config)

        if request is not None:
            self.request = request

        return request, why

    def describe(self):
        request = self.request

        return "%s x%d, %d done%s, %s" % (
            request["item"], request["total"], request["done"],
            ", exceptional" if request["exceptional"] else "", request["material"])

    # The pack proved the combine; the tooltip catches up later, or on some builds never
    def settle_after_combine(self, count):
        waited = 0.0

        while True:
            request, _why = parse_deed(self._lines(), self._config)

            if request is not None and request["done"] >= count:
                if request["done"] > count:
                    self._log("the deed says %d done, more than the %d counted - taking the deed's"
                              % (request["done"], count))

                self.request["done"] = request["done"]

                return request["done"]

            if waited >= self._config["reread_settle"]:
                break

            API.Pause(self._config["reread_poll"])
            waited += self._config["reread_poll"]

        if not self._said_behind:
            self._said_behind = True
            self._log("the deed's tooltip is behind the count - trusting the pack from here on")

        self.request["done"] = count

        return count


# src/uo/pack.py
def pack_contents():
    items = API.ItemsInContainer(API.Backpack, True)

    return items if items else []


# The item cap is per container, so the guard and the combine both count the top level only
def pack_top_level():
    items = API.ItemsInContainer(API.Backpack, False)

    return items if items else []


# None is an unreported stack, not an empty one: counted as 0 it would hide the ore a swing just
# delivered, which is the proof that the swing landed
def amount_of(item):
    amount = getattr(item, "Amount", None)

    return amount if amount is not None else 1


def hue_of(item):
    return getattr(item, "Hue", 0) or 0


# src/bod/items.py
class ItemBook(object):
    """What the tooltip says each pack item is, and whether the deed would take it."""

    def __init__(self, request, config, log):
        self._request = request
        self._config = config
        self._log = log
        self._verdicts = {}
        self._asked = {}
        self._rejected = set()
        self._primed = False

    def _material_names(self):
        material = self._request["material"]

        return [material] + list(self._config["aliases"].get(material, []))

    def _plain(self):
        return self._request["material"] == self._config["plain"]

    # Stock folds the material into the name: 'dull copper platemail gorget'
    def _product_names(self):
        item = self._request["item"]
        names = [item]

        if not self._plain():
            names.extend("%s %s" % (name, item) for name in self._material_names())

        return names

    def _judge(self, lines):
        name = strip_article(lines[0].lower(), self._config["articles"])
        body = [line.lower() for line in lines[1:]]
        product = name in self._product_names()
        exceptional = word_in(" ".join(body), [self._config["exceptional_text"]])

        if self._plain():
            material = True
        else:
            wanted = [words_of(alias) for alias in self._material_names()]
            material = (name != self._request["item"]
                        or len([line for line in body if words_of(line) in wanted]) > 0)

        return {
            "product": product,
            "qualifies": product and material and (exceptional or not self._request["exceptional"]),
        }

    def look(self, serial):
        if serial in self._verdicts:
            return self._verdicts[serial]

        if self._asked.get(serial, 0) >= self._config["asks"]:
            return None

        self._asked[serial] = self._asked.get(serial, 0) + 1
        props = API.ItemNameAndProps(serial, True, self._config["opl_timeout"]) or ""
        lines = [line.strip() for line in props.splitlines() if line.strip()]

        if len(lines) == 0:
            return None

        self._verdicts[serial] = self._judge(lines)

        return self._verdicts[serial]

    def is_product(self, serial):
        verdict = self.look(serial)

        return None if verdict is None else verdict["product"]

    def reject(self, serial):
        self._rejected.add(serial)

    def serials(self):
        return set(item.Serial for item in pack_top_level())

    def new_since(self, before):
        return [item for item in pack_top_level() if item.Serial not in before]

    # One request for the whole pack, so the first pass does not wait per item
    def prime(self):
        if self._primed:
            return

        self._primed = True
        API.RequestOPLData(list(self.serials()))
        API.Pause(self._config["opl_settle"])

    def qualifying(self):
        self.prime()

        for item in pack_top_level():
            if item.Serial in self._rejected:
                continue

            verdict = self.look(item.Serial)

            if verdict is not None and verdict["qualifies"]:
                return item.Serial

        return None

    # The shard reissues the serial of an item the deed took
    def forget_missing(self):
        here = self.serials()

        for serial in list(self._verdicts.keys()):
            if serial not in here:
                del self._verdicts[serial]
                self._asked.pop(serial, None)


# src/bod/material.py
class MaterialPicker(object):
    """The craft menu's material page: pressed once, and again when the deed says it was wrong."""

    def __init__(self, menu, config, log):
        self._menu = menu
        self._config = config
        self._log = log
        self._selected = None

    def needs(self, material):
        return self._selected != material

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

    def select(self, material, gump):
        timeout = self._config["gump_timeout"]
        page = self._menu.press(self._menu.button_id(self._config["button_type"], 0), gump, timeout)

        if not page:
            return 0, "noGump"

        rows = self._menu.item_rows(page)
        index = self.row_of(material, rows)

        if index is None:
            self._log("no material row reads '%s' - rows seen: %s"
                      % (material, ", ".join(rows) if rows else "none"))

            return page, "noMaterialRow"

        button = self._menu.button_id(self._config["row_type"], index)
        opened = self._menu.press(button, page, timeout)

        if not opened:
            return 0, "noGump"

        self._selected = material
        self._log("the menu is set to %s, the material row on button %d" % (material, button))

        return opened, None


# src/uo/craftmenu.py
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


# src/uo/crafttool.py
class CraftTool(object):
    """A crafting tool, used out of the pack rather than equipped."""

    def __init__(self, noun, graphics, name_words, log):
        self._noun = noun
        self._graphics = graphics
        self._name_words = name_words
        self._log = log

    def is_tool(self, item):
        if item is None:
            return False

        if item.Graphic in self._graphics:
            return True

        if not word_in(item.Name, self._name_words):
            return False

        self._graphics.add(item.Graphic)
        self._log("%s '%s' is a %s too, remembering the art"
                  % (hex_of(item.Graphic), item.Name, self._noun))

        return True

    def serial(self):
        for item in pack_contents():
            if self.is_tool(item):
                return item.Serial

        return None


# src/uo/guards.py
def first_reason(clauses):
    for clause in clauses:
        reason = clause()

        if reason is not None:
            return reason

    return None


def stopped(text):
    def clause():
        return text if API.StopRequested else None

    return clause


def dead():
    def clause():
        me = player()

        return "you are dead" if me is not None and me.IsDead else None

    return clause


# src/uo/clock.py
def now():
    return time.time()


# src/uo/heartbeat.py
class Heartbeat(object):
    """Proof of life: a loop standing still in silence looks exactly like a hung one."""

    def __init__(self, every, log, noun, vitals):
        self._every = every
        self._log = log
        self._noun = noun
        self._vitals = vitals
        self._last = None

    # The clock, not the cycle counter: a cycle can be 300ms or 8s depending on which waits it hit
    def beat(self, phase, cycle, tally):
        moment = now()

        # The first call sets the clock rather than logging: the run has just said what it is doing
        if self._last is None:
            self._last = moment
            return

        if moment - self._last < self._every:
            return

        self._last = moment
        self._log("still here - %s, cycle %d, %s, %d %s"
                  % (phase, cycle, self._vitals(), tally, self._noun))

    def reset(self):
        self._last = now()


# src/uo/log.py
def make_log(prefix):
    def log(message):
        API.SysMsg(prefix + ": " + message)

    return log


# src/uo/loop.py
def backoff_for(count, step, cap):
    return min(step * count, cap)


class StallWatch(object):
    def __init__(self, without, warn_at, stop_at, heartbeat, log):
        self._without = without
        self._warn_at = warn_at
        self._stop_at = stop_at
        self._heartbeat = heartbeat
        self._log = log
        self._since = 0
        self._reason = None

    def end_cycle(self, phase, cycle, tally):
        self._heartbeat.beat(phase, cycle, tally)
        self._since += 1

        if self._since == self._warn_at:
            self._log("%d %s, last was '%s'" % (self._warn_at, self._without, phase))

        if self._since >= self._stop_at:
            self._reason = "no progress in %d cycles, last was '%s'" % (self._stop_at, phase)

    def progressed(self):
        self._since = 0

    def reason(self):
        return self._reason


# src/uo/save.py
class SaveWatch(object):
    def __init__(self, saving_text, done_text, wait, poll, log, heartbeat, stop_reason):
        self._saving_text = saving_text
        self._done_text = done_text
        self._wait = wait
        self._poll = poll
        self._log = log
        self._heartbeat = heartbeat
        self._stop_reason = stop_reason

    def is_saving(self):
        return said(self._saving_text)

    def wait_out(self):
        self._log("the world is saving, waiting it out")

        # Read before the clear: a save can start and finish inside one cycle, and clearing first
        # threw the completion away and then stood still for the whole of the wait
        ended = "the shard had already finished" if said(self._done_text) else None

        forget(self._saving_text + self._done_text)

        waited = 0.0

        while ended is None and waited < self._wait:
            API.Pause(self._poll)
            waited += self._poll

            if said(self._done_text):
                ended = "the shard says it is done"
            elif self._stop_reason() is not None:
                ended = "the run has a reason to stop"

        self._log("%s, carrying on" % (ended or "nothing said in %ds" % int(self._wait)))
        self._heartbeat.reset()


# src/uo/skill.py
# A name the client does not carry throws on some builds rather than answering None
def find_skill_name(names):
    for name in names:
        try:
            if API.GetSkill(name) is not None:
                return name
        except Exception:
            continue

    return None


def reading(value):
    return "unknown" if value is None else "%.1f" % value


class SkillReader(object):
    """Value reads 0.0 before the skill list arrives, which is also a real skill value."""

    def __init__(self, name):
        self._name = name
        self._seen = False

    def read(self):
        skill = API.GetSkill(self._name)

        if skill is None:
            return None

        value = skill.Value

        if value <= 0.0 and not self._seen:
            return None

        self._seen = True

        return value

    def name(self):
        skill = API.GetSkill(self._name)

        return skill.Name if skill is not None and skill.Name else self._name

    def cap(self):
        skill = API.GetSkill(self._name)

        return skill.Cap if skill is not None else None

    def wait(self, timeout, poll):
        waited = 0.0

        while not API.StopRequested:
            value = self.read()

            if value is not None:
                return value

            if waited >= timeout:
                return None

            API.Pause(poll)
            waited += poll


# src/uo/vitals.py
def weight_reading():
    me = player()

    return "?/?" if me is None else "%d/%d" % (me.Weight, me.WeightMax)


def where():
    me = player()

    return "somewhere" if me is None else "at %d,%d" % (me.X, me.Y)


def position_and_weight():
    return "%s, %s" % (where(), weight_reading())


# src/bod/index.py
log = make_log("bod")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "combined", position_and_weight)
stall = StallWatch("cycles without progress", STALL_WARN, STALL_STOP, heartbeat, log)

if API.HasTarget():
    API.CancelTarget()


def stop_reason():
    return first_reason([stopped(STOPPED), dead()])


def is_ingot(item):
    return item.Graphic in INGOT_GRAPHICS or word_in(item.Name, INGOT_NAME_WORDS)


def ingot_report():
    counts = {}

    for item in pack_contents():
        if not is_ingot(item):
            continue

        hue = hue_of(item)
        name = INGOT_HUES.get(hue, "hue %s" % hex_of(hue))
        counts[name] = counts.get(name, 0) + amount_of(item)

    if len(counts) == 0:
        return "no ingots"

    return ", ".join("%d %s" % (counts[name], name) for name in sorted(counts))


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)
skill_name = find_skill_name(SKILL_NAMES)
skill = SkillReader(skill_name) if skill_name is not None else None

log("target the small bulk order deed to fill, ESC to stop")

picked = API.RequestTarget(PICK_TIMEOUT)

if API.HasTarget():
    API.CancelTarget()

if not picked:
    log("nothing targeted - stopping")
    API.Stop()

deed = Deed(picked, {
    "text": DEED_TEXT,
    "plain": PLAIN_MATERIAL,
    "articles": ARTICLES,
    "opl_timeout": OPL_TIMEOUT,
    "reread_settle": REREAD_SETTLE,
    "reread_poll": REREAD_POLL,
}, log)

request, refused = deed.read()

if request is None:
    log("%s is not a deed this run can fill: %s" % (hex_of(picked), refused))
    API.Stop()

deed_item = API.FindItem(picked)
root = getattr(deed_item, "RootContainer", None) if deed_item is not None else None

if root is not None and root != API.Backpack:
    log("the deed has to be in your pack - the shard refuses a combine from anywhere else")
    API.Stop()

tool = CraftTool("smith's tool", TOOL_GRAPHICS, TOOL_NAME_WORDS, log)

if tool.serial() is None:
    log("no smith's hammer or tongs in the pack")
    API.Stop()

items = ItemBook(request, {
    "aliases": MATERIAL_ALIASES,
    "plain": PLAIN_MATERIAL,
    "articles": ARTICLES,
    "exceptional_text": EXCEPTIONAL_TEXT,
    "opl_timeout": OPL_TIMEOUT,
    "opl_settle": OPL_SETTLE,
    "asks": OPL_ASKS,
}, log)
menu = CraftMenu(tool, {
    "stride": BUTTON_STRIDE,
    "category_type": CATEGORY_BUTTON_TYPE,
    "item_type": ITEM_BUTTON_TYPE,
    "category_names": CATEGORY_NAMES,
    "last_ten_label": LAST_TEN_LABEL,
    "title": CRAFT_TITLE,
    "title_text": CRAFT_TITLE_TEXT,
    "title_fragments": CRAFT_TITLE_FRAGMENTS,
    "tool_noun": "smith's tools",
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
    "max_categories": MAX_CATEGORIES,
    "max_item_rows": MAX_ITEM_ROWS,
}, log)
picker = MaterialPicker(menu, {
    "aliases": MATERIAL_ALIASES,
    "button_type": MATERIAL_BUTTON_TYPE,
    "row_type": MATERIAL_ROW_TYPE,
    "max_rows": MAX_MATERIAL_ROWS,
    "gump_timeout": GUMP_TIMEOUT,
}, log)
crafter = DeedCrafter(tool, menu, items, picker, OUTCOME_TEXT, {
    "make_last_button": MAKE_LAST_BUTTON,
    "craft_timeout": CRAFT_TIMEOUT,
    "craft_poll": CRAFT_POLL,
    "craft_settle": CRAFT_SETTLE,
    "max_probes": MAX_ITEM_PROBES,
    "max_categories": MAX_CATEGORIES,
    "max_reports": MAX_UNREADABLE_REPORTS,
    "text_limit": UNREADABLE_TEXT_LIMIT,
    "tail_seconds": JOURNAL_TAIL_SECONDS,
    "tail_lines": JOURNAL_TAIL_LINES,
}, log)
combiner = DeedCombiner(deed, items, COMBINE_TEXT, {
    "combine_button": BOD_COMBINE_BUTTON,
    "gump_text": BOD_GUMP_TEXT,
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
    "target_timeout": TARGET_TIMEOUT,
    "combine_timeout": COMBINE_TIMEOUT,
    "combine_poll": COMBINE_POLL,
    "max_reports": MAX_UNREADABLE_REPORTS,
    "text_limit": UNREADABLE_TEXT_LIMIT,
    "tail_seconds": JOURNAL_TAIL_SECONDS,
    "tail_lines": JOURNAL_TAIL_LINES,
}, log)

start = skill.read() if skill is not None else None

log("%s: %s%s, %s in the pack"
    % (deed.describe(), skill_name or "Blacksmithy", " at %s" % reading(start), ingot_report()))

stop = None
done = request["done"]
combined = 0
made = 0
fails = 0
unknown = 0
throttled = 0
no_tool = 0
no_cursor = 0
cycle = 0
said_throttle = False


def end_cycle(phase):
    global stop

    stall.end_cycle(phase, cycle, combined)

    if stop is None:
        stop = stall.reason()


def owed():
    return request["total"] - done


try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1

        stop = stop_reason()

        if stop is not None:
            break

        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        if owed() <= 0:
            stop = "the deed is full"
            break

        candidate = items.qualifying()

        if candidate is not None:
            outcome = combiner.combine(candidate)

            if outcome == "combined":
                combined += 1
                no_cursor = 0
                items.forget_missing()
                done = deed.settle_after_combine(done + 1)
                stall.progressed()
                log("combined %s (%d/%d)" % (hex_of(candidate), done, request["total"]))
            elif outcome == "full":
                stop = "the deed is full"
                break
            elif outcome in ("notRequested", "notExceptional", "wrongMaterial", "tooMany"):
                items.reject(candidate)
                stall.progressed()
                log("the deed refused %s (%s), leaving it in the pack" % (hex_of(candidate), outcome))

                if outcome == "wrongMaterial":
                    picker.forget()
                    crafter.forget_last()
            elif outcome == "notInPack":
                stop = "the shard says the item is not in your pack - is the deed in a bag?"
                break
            elif outcome in ("noCursor", "noGump"):
                no_cursor += 1

                if no_cursor >= MAX_NO_CURSOR:
                    stop = ("the deed's gump raised no cursor %d times - check BOD_COMBINE_BUTTON"
                            % MAX_NO_CURSOR)
                    break

                API.Pause(backoff_for(no_cursor, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
            else:
                unknown += 1
                log("unreadable combine outcome (%d/%d), check COMBINE_TEXT" % (unknown, MAX_UNKNOWN))

            if unknown >= MAX_UNKNOWN:
                stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
                break

            end_cycle(outcome if outcome is not None else "unknown")
            API.Pause(STEP_DELAY)
            continue

        outcome = crafter.craft_once(request["item"], request["material"])

        if outcome != "throttled":
            throttled = 0

        if outcome is not None:
            unknown = 0

        if outcome in ("made", "failed"):
            if outcome == "made":
                made += 1
            else:
                fails += 1

            stall.progressed()
        elif outcome == "noMaterial":
            stop = ("the shard says there are not enough %s ingots - %s in the pack, %d still owed"
                    % (request["material"], ingot_report(), owed()))
            break
        elif outcome in ("wrongRow", "saving"):
            stall.progressed()
        elif outcome == "toolWorn":
            crafter.forget_last()
            stall.progressed()
            log("the tool wore out, looking for another")
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s" % request["item"]
            break
        elif outcome == "noAnvil":
            stop = "stand next to an anvil and a forge"
            break
        elif outcome == "noRow":
            stop = "could not find the SELECTIONS row for '%s'" % request["item"]
            break
        elif outcome == "noMaterialRow":
            stop = "the material page has no row for %s" % request["material"]
            break
        elif outcome in ("noTool", "noGump"):
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = ("no smith's tool left" if outcome == "noTool"
                        else "the craft menu will not open")
                break

            log("%s (%d/%d), trying again"
                % ("no smith's tool in the pack" if outcome == "noTool"
                   else "the tool opened no craft menu", no_tool, MAX_NO_TOOL))
            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
        elif outcome == "throttled":
            throttled += 1

            if throttled >= MAX_THROTTLED:
                stop = "%d throttled crafts in a row" % MAX_THROTTLED
                break

            waiting = backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

            if not said_throttle:
                said_throttle = True
                log("the shard is pacing the crafts - waiting %.1fs" % waiting)

            API.Pause(waiting)
        else:
            unknown += 1
            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        if outcome not in ("noTool", "noGump"):
            no_tool = 0

        if unknown >= MAX_UNKNOWN:
            stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
            break

        end_cycle(outcome if outcome is not None else "unknown")
        API.Pause(STEP_DELAY)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    if stop is None:
        stop = "threw - %s" % error

up = API.HasGump()

if up:
    API.CloseGump(up)

if API.HasTarget():
    API.CancelTarget()

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES

log("%d combined, %d made, %d failed, %d/%d in the deed"
    % (combined, made, fails, done, request["total"]))
log("stopping - %s" % reason)
API.Stop()
