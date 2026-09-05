# Built from src/bowcraft/index.py by build.py - do not edit.

import API
import time


# src/bowcraft/bands.py
# A name the client does not carry throws on some builds rather than answering None
def find_skill_name(names):
    for name in names:
        try:
            if API.GetSkill(name) is not None:
                return name
        except Exception:
            continue

    return None


# Ceilings are exclusive
def band_for(bands, value):
    if value is None:
        return None

    for ceiling, product in bands:
        if ceiling is None or value < ceiling:
            return product

    return None


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

LOG_EVERY = 25
HEARTBEAT_EVERY = 30.0

STALL_WARN = 60
STALL_STOP = 300

STEP_DELAY = 0.3


# src/bowcraft/config.py
# One JSON object per attempt, for legion/skilldb.py. "" turns recording off. A bare name lands in
# TazUO's working directory, not beside the script.
DATA_PATH = "skill-attempts.jsonl"

# GetSkill answers None for a name it does not know: the gump says "Bowcraft/Fletching", the skill
# list may not
SKILL_NAMES = ["Bowcraft", "Bowcraft/Fletching", "Fletching"]

MIN_SKILL = 30.0

# The two bands that offer a choice: "fukiya darts" and "yumi" are the other way
LOW_BAND_ITEM = "bow"
HIGH_BAND_ITEM = "repeating crossbow"

# Ceilings are exclusive, in the client's float percentage - the src/training tables are in tenths
BANDS = [
    (60.0, LOW_BAND_ITEM),
    (70.0, "crossbow"),
    (80.0, "composite bow"),
    (90.0, "heavy crossbow"),
    (None, HIGH_BAND_ITEM),
]

# The CATEGORIES rows, lowercased: where the group block ends and the item rows begin
CATEGORY_NAMES = ["materials", "ammunition", "weapons"]

# Name as the SELECTIONS row spells it, and the graphics it lands in the pack as
PRODUCTS = {
    "bow": set([0x13B2]),
    "crossbow": set([0x0F50]),
    "composite bow": set([0x26C2]),
    "heavy crossbow": set([0x13FD]),
    "repeating crossbow": set([0x26C3]),
    "yumi": set([0x27A5]),
    "fukiya darts": set([0x2806]),
}

PRODUCT_GRAPHICS = set().union(*PRODUCTS.values())

TOOL_GRAPHICS = set([0x1022])
TOOL_NAME_WORDS = ["fletcher", "fletchers"]

# Hue is deliberately not matched: a shard with special woods hues them, and those craft too
LOG_GRAPHICS = set([0x1BDD, 0x1BE0, 0x1BDE, 0x1BDF])
LOG_NAME_WORDS = ["log", "logs"]

# Boards are wood too: the menu takes them, and the lumberjack run brings boards home
BOARD_GRAPHICS = set([0x1BD7, 0x1BD9, 0x1BDA, 0x1BDB])
BOARD_NAME_WORDS = ["board", "boards"]

# Counted as one pool, reported apart
WOOD_KINDS = [
    ("logs", LOG_GRAPHICS, LOG_NAME_WORDS),
    ("boards", BOARD_GRAPHICS, BOARD_NAME_WORDS),
]

REGULAR_WOOD = "regular"

# What a craft can spend besides wood, for the consumed rows in DATA_PATH. A stack not in here is
# not measured, so a wrong graphic under-reports rather than inventing a material.
MATERIAL_GRAPHICS = set([
    0x1BD1,  # feathers
    0x1BD4,  # shafts
])

# Read off the tooltip: '74 Oak Boards' is oak, '1580 Boards' is regular. Each is its own resource
# to the craft menu, which spends only the one it is set to.
WOOD_TYPES = ["oak", "ash", "yew", "heartwood", "bloodwood", "frostwood"]

# What the menu is set to: what a restock pulls and what counts as stock. Set the menu to match.
WOOD_TYPE = REGULAR_WOOD

# For the stack whose tooltip has not arrived. Incomplete on purpose: a colour in neither table is
# reported as unknown in the 'the pack holds ...' line, never treated as regular.
WOOD_HUES = {
    0: REGULAR_WOOD,
    1191: "ash",
    2010: "oak",
}

# Wood of the wrong type is weight and nothing else. Off leaves it in the pack.
RETURN_WRONG_WOOD = True

# Every restock fills the pack to this
BATCH_SIZE = 300
RESTOCK_AT = 25

# Counted as amounts: fukiya darts stack ten to a craft, so raise it for that band
SELL_AT = 20

# Matched against the name *and* the tooltip: "Alger" is "the bowyer" only in the tooltip
BOWYER_TITLES = ["bowyer", "fletcher", "archer", "bowyers", "fletchers"]

# The context entry first, matched by its text; the phrase for a menu with no such entry
SELL_ENTRY = "sell"
SELL_PHRASE = "vendor sell"

VENDOR_SCAN_RADIUS = 18

# Adjacent: two tiles away is heard on some shards and not others, and the context menu is refused
VENDOR_RANGE = 1

# A pathfind that ends early, a doorway and a vendor that stepped aside all look the same from here
VENDOR_STEPS = 3

CONTEXT_TIMEOUT = 3.0

# Set to a vendor's serial to skip the search
VENDOR_SERIAL = None

OPL_WAIT = 1.0

# A backstop only - the selection ends when you press ESC
MAX_PICKS = 8

CONTAINER_RANGE = 2

CRAFT_TITLE = "BOWCRAFT AND FLETCHING"

# Only ever to *recognise* a gump, never to refuse one: the header is a cliloc, and a build whose
# GetGumpContents answers nothing for it made every craft read as 'no craft menu'
CRAFT_TITLE_TEXT = [CRAFT_TITLE, "BOWCRAFT", "FLETCHING"]
CRAFT_TITLE_FRAGMENTS = [phrase.lower() for phrase in CRAFT_TITLE_TEXT]

# Its own button rather than a group, so it does not count toward the category index
LAST_TEN_LABEL = "LAST TEN"

# Buttons are 1 + type + index * 20, read off this shard's menu: categories 1, 21, 41 and the row
# arrows 2, 22, 42, ... The stock 7-step numbering puts MAKE LAST on the Ammunition category.
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MAKE_LAST_BUTTON = 47

# (category button, row button). A shortcut, not the truth: a row this gets wrong is walked for
RECIPES = {
    "bow": (41, 2),
    "crossbow": (41, 22),
    "heavy crossbow": (41, 42),
    "composite bow": (41, 62),
    "repeating crossbow": (41, 82),
    "yumi": (41, 102),
    "arrow": (21, 2),
    "crossbow bolt": (21, 22),
    "fukiya darts": (21, 42),
    "kindling": (1, 22),
    "shaft": (1, 42),
}

MAX_CATEGORIES = 6
MAX_ITEM_ROWS = 12

# Each miss costs one item's worth of wood, which is why the gump text is read first
MAX_ITEM_PROBES = 8

# Seconds throughout - API.Pause takes seconds
PICK_TIMEOUT = 60.0

# Whole seconds: the API takes an int here
PATHFIND_TIMEOUT = 10

GUMP_TIMEOUT = 5.0
GUMP_POLL = 0.15

# Has to outlast the craft animation, which plays before the shard answers
CRAFT_TIMEOUT = 10.0
CRAFT_POLL = 0.2

# How long the pack has to show the new item once the shard has answered
CRAFT_SETTLE = 1.5

# A failed craft's refund arrives after the journal line; the consumed row waits this long for it
REFUND_SETTLE = 1.5
REFUND_POLL = 0.25

OPEN_DELAY = 0.6
MOVE_DELAY = 0.7

SELL_TIMEOUT = 15.0
SELL_POLL = 0.5

SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25

MAX_CYCLES = 20000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_TOOL = 10
MAX_EMPTY_MOVES = 3

# Sell trips in a row that bought nothing before the trips pause. Never ends the run.
MAX_SELL_MISSES = 3
SELL_RETRY_AFTER = 25

# The largest recipe in BANDS: under this there is nothing the run can make
MIN_CRAFT_WOOD = 10

# Refusals for material while the pack holds wood a restock cannot add to: the wrong kind of wood
MAX_NO_MATERIAL = 3

# What an unreadable outcome reports before it goes quiet, and how much of it
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
    (
        "made",
        [
            "You create the item",
            "You put the",
            "You have worked the wood",
        ],
    ),
    # Said in the gump's NOTICES panel, which the journal may never carry
    (
        "noMaterial",
        [
            "You do not have sufficient wood",
            "You don't have the resources",
            "You do not have the resources",
            "There is not enough wood",
        ],
    ),
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


def matched_bucket(buckets):
    for name, phrases in buckets:
        # clearMatches, or a line already read answers the next wait as well
        if API.InJournalAny(phrases, True):
            return name

    return None


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


def counts_by_graphic(items):
    counts = {}

    for item in items:
        key = (item.Graphic, hue_of(item))
        counts[key] = counts.get(key, 0) + amount_of(item)

    return counts


def diff_counts(before, after):
    gained = {}
    lost = {}

    for key in set(list(before.keys()) + list(after.keys())):
        change = after.get(key, 0) - before.get(key, 0)

        if change > 0:
            gained[key] = change
        elif change < 0:
            lost[key] = -change

    return gained, lost


def count_of(graphics):
    return sum(amount_of(item) for item in pack_contents() if item.Graphic in graphics)


# src/uo/retry.py
def settled(timeout, poll, landed):
    waited = 0.0

    while waited < timeout:
        API.Pause(poll)
        waited += poll

        if landed():
            return True

    return False


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


# src/bowcraft/craft.py
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
                  % (self._wood.hue_report(), self._config["wood_type"]))

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
            return self._config["make_last_button"], None

        if known is not None:
            # Remembered too, so a later walk starts in the right category
            self._menu.remember_category(product, known[0])

            if not self._menu.press(known[0], gump, self._config["gump_timeout"]):
                return None, "noGump"

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

    # Something was made and none of it was the product, so a row was wrong - unless the press was
    # MAKE LAST, which the shard forgets on its own and which says nothing about the proven row
    def _wrong_product(self, product, button):
        if button == self._config["make_last_button"]:
            self._make_last = False
            self._log("MAKE LAST did not make a '%s', pressing the row itself next time" % product)

            return "wrongRow"

        self._log("button %d did not make a '%s', trying the next row" % (button, product))

        if product in self._config["recipes"] and product not in self._walked:
            self._walked.add(product)
            self._log("the button table is out of date for '%s', walking the categories for it "
                      "instead" % product)

        self._forget_row(product)

        return "wrongRow"

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


# unknown is what an unanswered client reads as, so the caller pathfinds and asks again rather than
# treating silence as arm's length
def chebyshev(x, y, unknown):
    me = player()

    if me is None:
        return unknown

    return max(abs(me.X - x), abs(me.Y - y))


# src/bowcraft/materials.py
class Materials(object):
    """What a craft spent, measured either side of it. Whitelisted: a potion drunk is not a cost."""

    def __init__(self, wood, extra_graphics):
        self._wood = wood
        self._extra = extra_graphics
        # Learned while the stack is there: the one that paid for a craft is often gone by the diff
        self._names = {}

    def _counted(self, item):
        return self._wood.is_wood(item) or item.Graphic in self._extra

    def _name_of(self, item):
        kind = self._wood.kind_of(item)

        if kind is not None:
            wood = self._wood.type_of(item)

            return kind if wood is None else "%s %s" % (wood, kind)

        return (getattr(item, "Name", "") or "").strip() or hex_of(item.Graphic)

    def snapshot(self):
        wanted = [item for item in pack_contents() if self._counted(item)]

        for item in wanted:
            key = (item.Graphic, hue_of(item))

            if key not in self._names:
                self._names[key] = self._name_of(item)

        return counts_by_graphic(wanted)

    # The failure line lands before the deduction and refund, so a pack that has not moved yet is
    # not settled: only one that moved and then held still for a poll is
    def settled_snapshot(self, timeout, poll):
        last = self.snapshot()
        waited = 0.0
        moved = False

        while waited < timeout:
            API.Pause(poll)
            waited += poll
            now = self.snapshot()

            if now != last:
                moved = True
                last = now
            elif moved:
                return now

        return last

    def wood_total(self, counts):
        return sum(counts[key] for key in counts if self._wood.is_wood_graphic(key[0]))

    # The lost side only: the product lands in the same pack and is not a cost
    def spent(self, before, after):
        _gained, lost = diff_counts(before, after)
        rows = []

        for key in sorted(lost):
            graphic, hue = key
            rows.append((self._names.get(key) or hex_of(graphic), graphic, hue, lost[key]))

        return rows


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


# src/bowcraft/menu.py
class CraftMenu(object):
    """The fletcher's craft gump: opening it, finding the category, and finding the row."""

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
            self._log("the tools opened a gump that does not name %s - it starts '%s'"
                      % (self._config["title"], lines[0] if lines else "(no text)"))

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


# src/bowcraft/wood.py
class WoodBook(object):
    """What in the pack is wood, which wood it is, and how much of it the menu will spend."""

    def __init__(self, config, log):
        self._kinds = config["kinds"]
        self._types = config["types"]
        self._hues = config["hues"]
        self._wanted = config["wanted"]
        self._move_delay = config["move_delay"]
        self._log = log

    # For a snapshot key, which has no item left to read a name off
    def is_wood_graphic(self, graphic):
        for _kind, graphics, _words in self._kinds:
            if graphic in graphics:
                return True

        return False

    # Names are empty until the tooltip arrives, so the graphic is tried first across every kind
    def kind_of(self, item):
        if item is None:
            return None

        for kind, graphics, _words in self._kinds:
            if item.Graphic in graphics:
                return kind

        for kind, graphics, words in self._kinds:
            if word_in(item.Name, words):
                graphics.add(item.Graphic)
                self._log("%s '%s' counts as %s, remembering the art"
                          % (hex_of(item.Graphic), item.Name, kind))

                return kind

        return None

    def is_wood(self, item):
        return self.kind_of(item) is not None

    # The name is where the shard writes it; a hue in neither table is not guessed at
    def type_of(self, item):
        for wood in self._types:
            if word_in(item.Name, [wood]):
                return wood

        return self._hues.get(hue_of(item))

    def usable(self, item):
        return self.is_wood(item) and self.type_of(item) == self._wanted

    def wrong(self, item):
        return self.is_wood(item) and self.type_of(item) != self._wanted

    # Only what the menu will spend: counting oak let a run sit on a full pack and craft none
    def counts(self, items):
        counts = {}

        for item in items:
            if not self.usable(item):
                continue

            kind = self.kind_of(item)
            counts[kind] = counts.get(kind, 0) + amount_of(item)

        return counts

    # The rest, by type, so a pack that reads as empty says why
    def other_counts(self, items):
        counts = {}

        for item in items:
            if not self.wrong(item):
                continue

            wood = self.type_of(item) or "unknown"
            counts[wood] = counts.get(wood, 0) + amount_of(item)

        return counts

    def other_report(self, counts):
        parts = ["%d %s" % (counts[wood], wood)
                 for wood in sorted(counts, key=lambda name: -counts[name])]

        return ", ".join(parts)

    # In kind order, so it reads the same each time
    def report(self, counts):
        parts = []

        for kind, _graphics, _words in self._kinds:
            if counts.get(kind, 0) > 0:
                parts.append("%d %s" % (counts[kind], kind))

        return ", ".join(parts) if parts else "no wood"

    def pack_wood(self):
        return self.counts(pack_contents())

    def pack_other(self):
        return self.other_counts(pack_contents())

    def in_pack(self):
        return total_of(self.pack_wood())

    def pack_report(self):
        text = self.report(self.pack_wood())
        other = self.other_report(self.pack_other())

        return text if not other else "%s (%s set aside)" % (text, other)

    # By hue: oak, ash and yew are all 'boards' by graphic. Missing WOOD_HUES rows come from here.
    def hue_report(self):
        counts = {}

        for item in pack_contents():
            kind = self.kind_of(item)

            if kind is None:
                continue

            key = (kind, hue_of(item), self.type_of(item) or "unknown")
            counts[key] = counts.get(key, 0) + amount_of(item)

        parts = ["%d %s %s hue %s" % (counts[key], key[2], key[0], hex_of(key[1]))
                 for key in sorted(counts, key=lambda pair: -counts[pair])]

        return ", ".join(parts) if parts else "no wood"

    def wrong_piles(self):
        return [item for item in pack_contents() if self.wrong(item)]

    # The craft may not reach into a bag inside the pack
    def _nested(self):
        top = set(item.Serial for item in pack_top_level())
        piles = [item for item in pack_contents()
                 if item.Serial not in top and self.usable(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def lift_from_bags(self):
        moved = 0

        for pile in self._nested():
            before = total_of(self.counts(pack_top_level()))

            API.MoveItem(pile.Serial, API.Backpack, amount_of(pile))
            API.Pause(self._move_delay)

            gained = total_of(self.counts(pack_top_level())) - before

            if gained > 0:
                moved += gained

        if moved > 0:
            self._log("brought %d wood up out of the bags in your pack" % moved)

        return moved


def total_of(counts):
    return sum(counts[kind] for kind in counts)


# src/bowcraft/restock.py
class Restock(object):
    def __init__(self, wood, sources, config, log):
        self._wood = wood
        self._sources = sources
        self._config = config
        self._log = log

    # Wrong wood goes back while its container is open and in reach, the one moment it costs nothing
    def _put_back(self, container):
        before = total_of(self._wood.pack_other())

        if before == 0:
            return 0

        for pile in self._wood.wrong_piles():
            API.MoveItem(pile.Serial, container, amount_of(pile))
            API.Pause(self._config["move_delay"])

        moved = before - total_of(self._wood.pack_other())

        if moved > 0:
            self._log("put %d wood the menu will not spend back" % moved)

        return moved

    # Moves are asynchronous: the pack is re-counted after each rather than MoveItem's return read
    def run(self):
        lifted = self._wood.lift_from_bags()

        # After the lift: in_pack reads bags too, and counting the lift twice left it short
        wanted = self._config["batch"] - self._wood.in_pack()
        moved = 0

        for entry in self._sources.picked():
            if moved >= wanted:
                break

            if not self._sources.reach(entry):
                self._log("cannot reach '%s', trying the next" % self._sources.name_of(entry))
                continue

            container = self._sources.open(entry)

            if container is None:
                self._log("'%s' has no backpack to draw from" % self._sources.name_of(entry))
                continue

            if self._config["return_wrong_wood"]:
                self._put_back(container)

            stalled = 0

            while moved < wanted and stalled < self._config["max_empty_moves"]:
                piles = self._sources.container_wood(container)

                if len(piles) == 0:
                    break

                before = self._wood.in_pack()

                API.MoveItem(piles[0].Serial, API.Backpack,
                             min(wanted - moved, amount_of(piles[0])))
                API.Pause(self._config["move_delay"])

                gained = self._wood.in_pack() - before

                if gained <= 0:
                    stalled += 1
                else:
                    stalled = 0
                    moved += gained

        if moved > 0:
            self._log("pulled %d wood, %s in the pack, %d left in what you picked"
                      % (moved, self._wood.pack_report(), self._sources.stock_left()))

        return lifted + moved


# src/bowcraft/sources.py
class Sources(object):
    """The containers and pack animals the wood is drawn from."""

    def __init__(self, wood, config, log):
        self._wood = wood
        self._config = config
        self._log = log
        self._picked = []

    def picked(self):
        return self._picked

    def name_of(self, entry):
        return entry["name"] or hex_of(entry["serial"])

    # Never UseObject the animal itself: on a rideable body that mounts you
    def _animal_pack(self, serial):
        animal = API.FindMobile(serial)

        if animal is None:
            return None

        pack = getattr(animal, "Backpack", None)

        if pack is None:
            pack = API.FindLayer("backpack", serial)

        if pack is None:
            return None

        return getattr(pack, "Serial", pack)

    def container_of(self, entry):
        if entry["kind"] == "mobile":
            return self._animal_pack(entry["serial"])

        return entry["serial"]

    def _entry_for(self, serial):
        item = API.FindItem(serial)

        if item is not None:
            return {"kind": "item", "serial": serial, "name": item.Name or "?",
                    "spot": (item.X, item.Y, item.Z)}

        animal = API.FindMobile(serial)

        if animal is None:
            return None

        return {"kind": "mobile", "serial": serial, "name": animal.Name or "?", "spot": None}

    # ItemsInContainer reads nothing out of a container the client has never seen inside
    def open(self, entry):
        container = self.container_of(entry)

        if container is None:
            return None

        API.UseObject(container)
        API.Pause(self._config["open_delay"])

        return container

    def pick(self):
        self._log("target every container or pack animal holding logs or boards, ESC when done")

        me = player()
        mine = me.Serial if me is not None else None

        for _pick in range(self._config["max_picks"]):
            if API.HasTarget():
                API.CancelTarget()

            serial = API.RequestTarget(self._config["pick_timeout"])

            # ESC or a timed-out cursor, either ends the selection
            if not serial:
                break

            if serial == API.Backpack or (mine is not None and serial == mine):
                self._log("your own pack is always counted, no need to pick it")
                continue

            if serial in [entry["serial"] for entry in self._picked]:
                continue

            entry = self._entry_for(serial)

            if entry is None:
                self._log("%s is neither a container nor a creature" % hex_of(serial))
                continue

            # Opened now, while it is in reach
            if self.open(entry) is None:
                self._log("'%s' has no backpack to draw from" % self.name_of(entry))
                continue

            self._picked.append(entry)

            other = self._wood.other_report(self._wood.other_counts(self.all_wood(entry)))

            self._log("picked '%s' %s, %s in it%s"
                      % (self.name_of(entry), hex_of(serial),
                         self._wood.report(self.counts(entry)),
                         "" if not other else " (%s it will not use)" % other))

        if API.HasTarget():
            API.CancelTarget()

        return self._picked

    # Only the type the menu is set to
    def container_wood(self, serial):
        items = API.ItemsInContainer(serial, True)
        piles = [item for item in (items or []) if self._wood.usable(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def wood(self, entry):
        container = self.container_of(entry)

        return [] if container is None else self.container_wood(container)

    # Wrong type included, for the report lines
    def all_wood(self, entry):
        container = self.container_of(entry)
        items = API.ItemsInContainer(container, True) if container else None

        return [item for item in items if self._wood.is_wood(item)] if items else []

    def counts(self, entry):
        return self._wood.counts(self.wood(entry))

    def total(self, entry):
        return total_of(self.counts(entry))

    def stock_left(self):
        return sum(self.total(entry) for entry in self._picked)

    def stock_line(self):
        if len(self._picked) == 0:
            return "nothing picked to restock from"

        return "%d in the %d you picked" % (self.stock_left(), len(self._picked))

    # Re-resolved after the walk: a pathfind that ends early leaves you short
    def reach(self, entry):
        within = self._config["container_range"]

        if entry["kind"] == "mobile":
            animal = API.FindMobile(entry["serial"])

            if animal is None:
                return False

            if animal.Distance <= within:
                return True

            API.PathfindEntity(entry["serial"], within, True, self._config["pathfind_timeout"])
            API.CancelPathfinding()

            animal = API.FindMobile(entry["serial"])

            return animal is not None and animal.Distance <= within

        spot = entry["spot"]

        # A container inside the pack has no world position
        if spot is None or (spot[0] == 0 and spot[1] == 0):
            return True

        if chebyshev(spot[0], spot[1], within + 1) <= within:
            return True

        API.Pathfind(spot[0], spot[1], spot[2], within, True, self._config["pathfind_timeout"])

        return chebyshev(spot[0], spot[1], within + 1) <= within


# src/bowcraft/tools.py
class Tools(object):
    """The fletcher's tools, which are used out of the pack rather than equipped."""

    def __init__(self, graphics, name_words, log):
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
        self._log("%s '%s' is a fletcher's tool too, remembering the art"
                  % (hex_of(item.Graphic), item.Name))

        return True

    def serial(self):
        for item in pack_contents():
            if self.is_tool(item):
                return item.Serial

        return None


# src/uo/menu.py
# ContextMenu opens the menu itself, and cannot tell an entry that is missing from one that never
# arrived - both come back False
def context_menu(serial, texts, timeout):
    for text in texts:
        # Guarded: a build whose ContextMenu throws for a serial it cannot resolve would otherwise
        # end the run over a vendor that stepped away
        try:
            if API.ContextMenu(serial, text, timeout):
                return True
        except Exception:
            continue

    return False


# src/bowcraft/vendor.py
def tooltip_of(mobile):
    try:
        return mobile.NameAndProps(False) or ""
    except Exception:
        return ""


class Vendor(object):
    def __init__(self, wood, menu, config, log, heartbeat, products_in_pack):
        self._wood = wood
        self._menu = menu
        self._config = config
        self._log = log
        self._heartbeat = heartbeat
        self._products_in_pack = products_in_pack
        self._said_no_vendor = False
        self._said_sell_how = False

    def _candidates(self):
        me = player()
        mine = me.Serial if me is not None else None
        found = []

        for mobile in API.GetAllMobiles(None, self._config["scan_radius"]) or []:
            # Only your own pets rename, and they are most of what stands around a crafter
            if mobile.IsDead or mobile.Serial == mine or mobile.IsRenamable:
                continue

            found.append(mobile)

        return found

    # Tooltips cost a round trip each, and "Alger" is "the bowyer" only in the tooltip
    def _find(self):
        if self._config["serial"]:
            return API.FindMobile(self._config["serial"])

        candidates = self._candidates()

        for mobile in candidates:
            if any_in(mobile.Name, self._config["titles"]):
                return mobile

        if len(candidates) == 0:
            return None

        API.RequestOPLData([mobile.Serial for mobile in candidates])
        API.Pause(self._config["opl_wait"])

        for mobile in candidates:
            if any_in(tooltip_of(mobile), self._config["titles"]):
                return mobile

        return None

    # Re-resolved every pass: a pathfind that ends early leaves you short
    def _walk_to(self, serial):
        within = self._config["range"]

        for _step in range(self._config["steps"]):
            here = API.FindMobile(serial)

            if here is None:
                return None

            if here.Distance <= within:
                return here

            API.PathfindEntity(serial, within, True, self._config["pathfind_timeout"], True)
            API.CancelPathfinding()
            API.Pause(self._config["step_delay"])

        here = API.FindMobile(serial)

        return here if here is not None and here.Distance <= within else None

    # The vendor's own Sell entry first; the phrase for a menu without one
    def _ask_to_sell(self, serial):
        asked = context_menu(serial, [self._config["sell_entry"]],
                             self._config["context_timeout"])

        if not asked:
            API.Msg(self._config["sell_phrase"])

        if not self._said_sell_how:
            self._said_sell_how = True
            self._log("selling by %s" % ("the vendor's own Sell menu" if asked
                                         else "saying '%s'" % self._config["sell_phrase"]))

        return asked

    def sell_trip(self):
        vendor = self._find()

        if vendor is None:
            if not self._said_no_vendor:
                self._said_no_vendor = True
                names = [mobile.Name or "?" for mobile in self._candidates()]
                self._log("no bowyer within %d - looked at %d: %s"
                          % (self._config["scan_radius"], len(names),
                             clipped(", ".join(names), self._config["text_limit"]) or "nobody"))

            return False

        self._said_no_vendor = False

        name = vendor.Name or hex_of(vendor.Serial)
        here = self._walk_to(vendor.Serial)

        if here is None:
            self._log("could not get next to '%s', trying again next time" % name)

            return False

        before = self._products_in_pack()
        self._log("selling %d to '%s'" % (before, name))

        self._ask_to_sell(vendor.Serial)

        sold = settled(self._config["sell_timeout"], self._config["sell_poll"],
                       lambda: self._products_in_pack() < before)

        # Never the bare CloseGump: it closes the last gump, as likely the craft menu
        found = API.HasGump()

        if found and found != self._menu.current_id() and not self._menu.is_craft_gump(found):
            API.CloseGump(found)

        if not sold:
            self._log("the vendor bought nothing - is the auto-sell agent on?")
        else:
            self._log("sold, %d left in the pack" % self._products_in_pack())

        self._heartbeat.reset()

        return sold


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


def skill_capped(name):
    def clause():
        skill = API.GetSkill(name) if name is not None else None

        if skill is not None and skill.Value > 0 and skill.Value >= skill.Cap:
            return "%s is capped at %.1f" % (name, skill.Value)

        return None

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


# src/uo/record.py
# Written by hand rather than with json.dumps: the bundler admits API and time and nothing else, and
# a row of numbers and two short strings is not worth relaxing that rule for.
def quoted(text):
    out = ['"']

    for character in text:
        code = ord(character)

        if character == '"' or character == "\\":
            out.append("\\" + character)
        elif character == "\n":
            out.append("\\n")
        elif character == "\r":
            out.append("\\r")
        elif character == "\t":
            out.append("\\t")
        # Non-ASCII escaped rather than written through: a character name carrying an accent is
        # ordinary here, and what encoding the runtime picked for the file is not knowable from in
        # here
        elif code < 0x20 or code > 0x7E:
            out.append("\\u%04x" % code)
        else:
            out.append(character)

    out.append('"')

    return "".join(out)


def skill_json(value):
    return "null" if value is None else "%.1f" % value


def append_line(path, line):
    handle = open(path, "a")

    try:
        handle.write(line + "\n")
    finally:
        handle.close()


class AttemptLog(object):
    """One JSON object per attempt, appended as it happens.

    A row is buffered when the attempt resolves and written on the *next* skill read, because the
    client applies a gain some time after the outcome and a value read straight away is usually
    still the old one. The cost of that is one row in the air at any moment, which a killed script
    loses; the alternative is a file that under-reports every gain it exists to measure.
    """

    def __init__(self, path, character, serial, skill, log, append=None):
        self._path = path or ""
        self._character = character or ""
        self._serial = serial
        self._skill = skill
        self._log = log
        self._append = append if append is not None else append_line
        self._off = not self._path
        # Milliseconds, not seconds: two runs started inside the same second would mint the
        # same ids, and the converter reads a repeated id as the same row arriving twice
        self._run = int(now() * 1000)
        self._seq = 0
        self._pending = None
        self._said = False

    # Asked before an attempt so a caller can skip the work of measuring what it spent
    def recording(self):
        return not self._off

    # consumed is a list of (name, graphic, hue, quantity) - measured, so an attempt that spent
    # nothing passes nothing rather than a guess at what the recipe charges
    def record(self, skill_from, outcome, success, consumed=None, stock=None):
        if self._off or skill_from is None:
            return

        # A caller that records twice without settling in between would otherwise drop the first
        # row. This later read is exactly what the missed settle would have passed.
        self.settle(skill_from)

        self._seq += 1
        self._pending = {
            "id": "%s/%d/%d" % (hex_of(self._serial), self._run, self._seq),
            "at": now(),
            "from": skill_from,
            "outcome": outcome,
            "ok": success,
            "consumed": list(consumed) if consumed else [],
            # (before, after) totals of the material the attempt is costed in, written raw so the
            # subtraction in 'consumed' can be checked without trusting it
            "stock": tuple(stock) if stock else None,
        }

    def settle(self, skill_to):
        pending = self._pending
        self._pending = None

        if pending is None or self._off:
            return

        self._write(pending, skill_to)

    def _line(self, row, skill_to):
        fields = [
            '"v":1',
            '"id":%s' % quoted(row["id"]),
            '"t":%.3f' % row["at"],
            '"char":%s' % quoted(self._character),
            '"serial":%s' % quoted(hex_of(self._serial)),
            '"skill":%s' % quoted(self._skill),
            '"from":%s' % skill_json(row["from"]),
            '"to":%s' % skill_json(skill_to),
            '"outcome":%s' % quoted(row["outcome"]),
            '"ok":%s' % ("true" if row["ok"] else "false"),
        ]

        if row.get("stock"):
            fields.append('"stock_from":%d,"stock_to":%d' % (row["stock"][0], row["stock"][1]))

        if row["consumed"]:
            fields.append('"consumed":[%s]' % ",".join(
                '{"name":%s,"graphic":%s,"hue":%d,"qty":%d}'
                % (quoted(name), quoted(hex_of(graphic)), hue, quantity)
                for name, graphic, hue, quantity in row["consumed"]
            ))

        return "{%s}" % ",".join(fields)

    # A run that cannot write its log is still a run: the recorder retires itself and says so once,
    # rather than ending the training over a file
    def _write(self, row, skill_to):
        try:
            self._append(self._path, self._line(row, skill_to))
        except Exception as error:
            self._off = True

            if not self._said:
                self._said = True
                self._log("cannot write %s (%s) - not recording this run" % (self._path, error))


# The character is read once, here, rather than on every row: it cannot change under a running
# script, and a client between world states answers None for the player without that meaning the
# run should stop recording.
def attempt_log(path, skill, log):
    me = player()

    if me is None and path:
        log("the client is not reporting the character - rows will not name it")

    return AttemptLog(path, getattr(me, "Name", ""), getattr(me, "Serial", 0), skill, log)


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

        API.ClearJournal()

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

        while True:
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


# src/bowcraft/index.py
log = make_log("bowcraft")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "made", position_and_weight)
stall = StallWatch("cycles without a craft", STALL_WARN, STALL_STOP, heartbeat, log)

if API.HasTarget():
    API.CancelTarget()

skill_name = find_skill_name(SKILL_NAMES)

if skill_name is None:
    log("the client reports none of %s - check SKILL_NAMES" % ", ".join(SKILL_NAMES))
    API.Stop()

skill = SkillReader(skill_name)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(skill_name)])


def products_in_pack():
    return count_of(PRODUCT_GRAPHICS)


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

tools = Tools(TOOL_GRAPHICS, TOOL_NAME_WORDS, log)
wood = WoodBook({
    "kinds": WOOD_KINDS,
    "types": WOOD_TYPES,
    "hues": WOOD_HUES,
    "wanted": WOOD_TYPE,
    "move_delay": MOVE_DELAY,
}, log)
sources = Sources(wood, {
    "max_picks": MAX_PICKS,
    "pick_timeout": PICK_TIMEOUT,
    "open_delay": OPEN_DELAY,
    "container_range": CONTAINER_RANGE,
    "pathfind_timeout": PATHFIND_TIMEOUT,
}, log)
restock = Restock(wood, sources, {
    "batch": BATCH_SIZE,
    "move_delay": MOVE_DELAY,
    "max_empty_moves": MAX_EMPTY_MOVES,
    "return_wrong_wood": RETURN_WRONG_WOOD,
}, log)
menu = CraftMenu(tools, {
    "stride": BUTTON_STRIDE,
    "category_type": CATEGORY_BUTTON_TYPE,
    "item_type": ITEM_BUTTON_TYPE,
    "category_names": CATEGORY_NAMES,
    "last_ten_label": LAST_TEN_LABEL,
    "title": CRAFT_TITLE,
    "title_text": CRAFT_TITLE_TEXT,
    "title_fragments": CRAFT_TITLE_FRAGMENTS,
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
    "max_categories": MAX_CATEGORIES,
    "max_item_rows": MAX_ITEM_ROWS,
}, log)
crafter = Crafter(tools, menu, wood, OUTCOME_TEXT, {
    "recipes": RECIPES,
    "products": PRODUCTS,
    "make_last_button": MAKE_LAST_BUTTON,
    "gump_timeout": GUMP_TIMEOUT,
    "craft_timeout": CRAFT_TIMEOUT,
    "craft_poll": CRAFT_POLL,
    "craft_settle": CRAFT_SETTLE,
    "max_probes": MAX_ITEM_PROBES,
    "max_categories": MAX_CATEGORIES,
    "max_reports": MAX_UNREADABLE_REPORTS,
    "text_limit": UNREADABLE_TEXT_LIMIT,
    "tail_seconds": JOURNAL_TAIL_SECONDS,
    "tail_lines": JOURNAL_TAIL_LINES,
    "wood_type": WOOD_TYPE,
}, log)
vendor = Vendor(wood, menu, {
    "serial": VENDOR_SERIAL,
    "titles": BOWYER_TITLES,
    "scan_radius": VENDOR_SCAN_RADIUS,
    "range": VENDOR_RANGE,
    "steps": VENDOR_STEPS,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "step_delay": STEP_DELAY,
    "sell_entry": SELL_ENTRY,
    "sell_phrase": SELL_PHRASE,
    "context_timeout": CONTEXT_TIMEOUT,
    "sell_timeout": SELL_TIMEOUT,
    "sell_poll": SELL_POLL,
    "opl_wait": OPL_WAIT,
    "text_limit": UNREADABLE_TEXT_LIMIT,
}, log, heartbeat, products_in_pack)

start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)

if start is None:
    log("%s is not reading yet - start it again once the skill list has arrived" % skill_name)
    API.Stop()
elif start < MIN_SKILL:
    log("%s is at %.1f and the table starts at %.1f - train it up by hand first"
        % (skill_name, start, MIN_SKILL))
    API.Stop()

if tools.serial() is None:
    log("no fletcher's tools in the pack")
    API.Stop()

sources.pick()

# A run that starts on the wood it is already carrying needed no cursor at all
if len(sources.picked()) == 0 and wood.in_pack() == 0:
    log("nothing picked and no wood in the pack")
    API.Stop()

log("%s at %.1f, %s in the pack, %s" % (skill_name, start, wood.pack_report(),
                                        sources.stock_line()))

if wood.in_pack() < RESTOCK_AT:
    restock.run()

recorder = attempt_log(DATA_PATH, skill_name, log)
materials = Materials(wood, MATERIAL_GRAPHICS)

stop = None
tally = 0
fails = 0
unknown = 0
throttled = 0
no_tool = 0
no_material = 0
throttle_tally = 0
said_throttle = False
sell_misses = 0
sell_paused_until = 0
reported = 0
cycle = 0
product = None
last_skill = start


def end_cycle(phase):
    global stop

    stall.end_cycle(phase, cycle, tally)

    if stop is None:
        stop = stall.reason()


# Measured either side of the craft rather than read off the recipe: a failure refunds part of it
def record_craft(outcome, skill_from, before):
    if not recorder.recording():
        return

    after = materials.settled_snapshot(REFUND_SETTLE, REFUND_POLL)
    recorder.record(skill_from, outcome, outcome == "made", materials.spent(before, after),
                    (materials.wood_total(before), materials.wood_total(after)))


try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1

        stop = stop_reason()

        if stop is not None:
            break

        # A frozen shard reads as every failure below, so it is waited out before any of them
        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        value = skill.read()

        # The client applies a gain some time after the outcome, so the row waits a cycle for it
        recorder.settle(value)

        if value is not None and value != last_skill:
            last_skill = value
            stall.progressed()

        wanted = band_for(BANDS, value if value is not None else last_skill)

        if wanted is None:
            stop = "%s reads %s and no band covers it" % (skill_name, reading(value))
            break

        if wanted != product:
            log("%s at %s, making %s" % (skill_name, reading(value), wanted))
            product = wanted
            crafter.forget_last()

        if products_in_pack() >= SELL_AT and cycle >= sell_paused_until:
            if vendor.sell_trip():
                sell_misses = 0

                end_cycle("selling")
                continue

            sell_misses += 1

            # Retried, but not every cycle: otherwise the crafting never gets a turn
            if sell_misses >= MAX_SELL_MISSES:
                sell_misses = 0
                sell_paused_until = cycle + SELL_RETRY_AFTER
                log("%d sell trips bought nothing - crafting on, and asking again in %d cycles"
                    % (MAX_SELL_MISSES, SELL_RETRY_AFTER))

        if wood.in_pack() < RESTOCK_AT:
            # An unreachable container also pulls nothing, which the stall watch ends
            pulled = restock.run()

            if pulled == 0 and sources.stock_left() == 0 and wood.in_pack() < MIN_CRAFT_WOOD:
                stop = ("out of %s wood - %s in the pack, none left in what you picked"
                        % (WOOD_TYPE, wood.pack_report()))
                break

            # A short pack that can still make something crafts
            if wood.in_pack() < MIN_CRAFT_WOOD:
                end_cycle("restocking")
                continue

        spent_before = materials.snapshot() if recorder.recording() else {}
        outcome = crafter.craft_once(product)

        if outcome != "throttled":
            throttled = 0

        if outcome is not None:
            unknown = 0

        if outcome in ("made", "failed"):
            if outcome == "made":
                tally += 1
            else:
                fails += 1

            record_craft(outcome, value, spent_before)
            no_material = 0
            stall.progressed()
        elif outcome == "noMaterial":
            pulled = restock.run()

            if pulled > 0:
                no_material = 0
                stall.progressed()
            elif wood.in_pack() < RESTOCK_AT and sources.stock_left() == 0:
                stop = "the shard says there is not enough wood and there is none left to pull"
                break
            else:
                # Wood in the pack, refused, nothing to add to it: the wrong kind of wood
                no_material += 1

                if no_material >= MAX_NO_MATERIAL:
                    stop = ("the shard refused %s in the pack %d times - read the gump's own words "
                            "above; if it wants another wood, set WOOD_TYPE and the menu to match"
                            % (wood.pack_report(), no_material))
                    break
        elif outcome in ("wrongRow", "saving"):
            stall.progressed()
        elif outcome == "toolWorn":
            crafter.forget_last()
            stall.progressed()
            log("the tools wore out, looking for another pair")
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s at %s" % (product, reading(value))
            break
        elif outcome == "noRow":
            stop = "could not find the SELECTIONS row for '%s'" % product
            break
        elif outcome in ("noTool", "noGump"):
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = ("no fletcher's tools left" if outcome == "noTool"
                        else "the craft menu will not open")
                break

            log("%s (%d/%d), trying again"
                % ("no fletcher's tools in the pack" if outcome == "noTool"
                   else "the tools opened no craft menu", no_tool, MAX_NO_TOOL))
            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
        elif outcome == "throttled":
            throttled += 1
            throttle_tally += 1

            if throttled >= MAX_THROTTLED:
                stop = "%d throttled crafts in a row" % MAX_THROTTLED
                break

            waiting = backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

            # Said once, then only tallied: the pause is the shard's, and it is normal
            if not said_throttle:
                said_throttle = True
                log("the shard is pacing the crafts - waiting %.1fs, and counting these from here on"
                    % waiting)

            API.Pause(waiting)
        else:
            unknown += 1
            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        if outcome not in ("noTool", "noGump"):
            no_tool = 0

        if unknown >= MAX_UNKNOWN:
            stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
            break

        if tally >= reported + LOG_EVERY:
            reported = tally
            log(
                "%d made, %d failed, %d throttled, %s at %s, %s left"
                % (tally, fails, throttle_tally, skill_name, reading(value),
                   wood.report(wood.pack_wood()))
            )

        end_cycle(outcome if outcome is not None else "unknown")
        API.Pause(STEP_DELAY)
except Exception as error:
    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error

if API.Pathfinding():
    API.CancelPathfinding()

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES
ended = skill.read()
recorder.settle(ended)

log(
    "%d made, %d failed, %d throttled, %s %.1f -> %s"
    % (tally, fails, throttle_tally, skill_name, start, reading(ended))
)
log("stopping - %s" % reason)
API.Stop()
