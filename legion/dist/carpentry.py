# Built from src/carpentry/index.py by build.py - do not edit.

import API
import time


# src/uo/boxes.py
# Read off the gump as one token per row and the number after it: 'OakBoard 850', boards then logs,
# a row only while the box holds any. The buttons are read off the gump's layout; the table is the
# fallback, right only while every board row is up, since a missing row shifts the ids after it.
WOOD_BOX = {
    "names": ["storage box"],
    "graphics": set(),
    "title": ["storage box"],
    "rows": {
        "Board": ("boards", None),
        "OakBoard": ("boards", "oak"),
        "AshBoard": ("boards", "ash"),
        "YewBoard": ("boards", "yew"),
        "HeartwoodBoard": ("boards", "heartwood"),
        "BloodwoodBoard": ("boards", "bloodwood"),
        "FrostwoodBoard": ("boards", "frostwood"),
        "Log": ("logs", None),
        "OakLog": ("logs", "oak"),
        "AshLog": ("logs", "ash"),
        "YewLog": ("logs", "yew"),
        "HeartwoodLog": ("logs", "heartwood"),
        "BloodwoodLog": ("logs", "bloodwood"),
        "FrostwoodLog": ("logs", "frostwood"),
    },
    "buttons": {
        "Board": 107,
        "OakBoard": 108,
        "AshBoard": 109,
        "YewBoard": 110,
        "HeartwoodBoard": 111,
        "BloodwoodBoard": 112,
        "FrostwoodBoard": 113,
    },
}


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

GAIN_PATH_TIMEOUT = 5.0
GAIN_PATH_POLL = 0.25


# src/carpentry/config.py
# One JSON object per attempt, for legion/skilldb.py. "" turns recording off. A bare name lands
# beside the script, in LegionScripts.
DATA_PATH = "skill-attempts.jsonl"

SKILL_NAMES = ["Carpentry"]

MIN_SKILL = 0.0

# Ceilings are exclusive, in the client's float percentage. Each is the row's minimum plus 25, where
# the stock recipe stops gaining, or earlier where a cheaper row opens: barrel lid at 11.0, the sign
# hanger at 42.1.
BANDS = [
    (11.0, "barrel staves"),
    (36.0, "barrel lid"),
    (40.7, "dartboard (south)"),
    (42.1, "wooden box"),
    (67.1, "dark wooden sign hanger"),
    (70.0, "ballot box"),
    (73.6, "bokuto"),
    (98.6, "quarter staff"),
    (103.9, "gnarled staff"),
    (105.0, "tetsubo"),
    (106.5, "black staff"),
    (111.8, "easel (south)"),
    (115.0, "plain wooden chest"),
    (119.7, "rustic bench (south)"),
    (None, "display case (south)"),
]

# The CATEGORIES rows, lowercased: where the group block ends and the item rows begin
CATEGORY_NAMES = ["other", "furniture", "containers", "weapons", "armor", "instruments",
                  "misc. add-ons", "misc add-ons", "misc. addons", "misc addons",
                  "tailoring and cooking", "anvils and forges", "training", "ingredients"]

# Every addon is a deed in the pack, one art for all of them
DEED_GRAPHICS = set([0x14F0])

# Name as the SELECTIONS row spells it, and the graphics it lands in the pack as. Stock art,
# unverified on UOAlive.
PRODUCTS = {
    "barrel staves": set([0x1EB1, 0x1EB2, 0x1EB3, 0x1EB4]),
    "barrel lid": set([0x1DB8]),
    "dartboard (south)": DEED_GRAPHICS,
    "wooden box": set([0x9AA]),
    # Lands as 'Wooden Signpost' 0x0B97 on UOAlive, an item and not the addon deed the rest are
    "dark wooden sign hanger": set([0x0B97]),
    "ballot box": DEED_GRAPHICS,
    "bokuto": set([0x27A8]),
    "quarter staff": set([0x0E89, 0x0E8A]),
    "gnarled staff": set([0x13F8, 0x13F9]),
    "tetsubo": set([0x27A6]),
    "black staff": set([0x0DF0, 0x0DF1]),
    "easel (south)": set([0x0F65, 0x0F66, 0x0F67]),
    "plain wooden chest": set([0x280B, 0x280C]),
    "rustic bench (south)": DEED_GRAPHICS,
    "display case (south)": DEED_GRAPHICS,
}

# Wood per craft, from the stock recipes. The pack is measured either side of a craft regardless;
# this only decides when the pack is too short to try and when to restock.
WOOD_COST = {
    "barrel staves": 5,
    "barrel lid": 4,
    "dartboard (south)": 5,
    "wooden box": 10,
    "dark wooden sign hanger": 5,
    "ballot box": 5,
    "bokuto": 6,
    "quarter staff": 6,
    "gnarled staff": 7,
    "tetsubo": 10,
    "black staff": 9,
    "easel (south)": 20,
    "plain wooden chest": 30,
    "rustic bench (south)": 35,
    "display case (south)": 40,
}

# For a product WOOD_COST lacks
MIN_CRAFT_WOOD = 5

# Stock art. "hammer" is not a name word: a smith's hammer carries it too.
TOOL_GRAPHICS = set([
    0x1034, 0x1035,  # saw
    0x1028, 0x1029,  # dovetail saw
    0x102A, 0x102B,  # hammer
    0x102C, 0x102D,  # moulding plane
    0x102E, 0x102F,  # nails
    0x1030, 0x1031,  # jointing plane
    0x1032, 0x1033,  # smoothing plane
    0x10E4,  # draw knife
    0x10E5,  # froe
    0x10E6,  # inshave
    0x10E7,  # scorp
])
TOOL_NAME_WORDS = ["saw", "plane", "nails", "froe", "inshave", "scorp"]

# Hue is deliberately not matched: a shard with special woods hues them, and those craft too
LOG_GRAPHICS = set([0x1BDD, 0x1BE0, 0x1BDE, 0x1BDF])
LOG_NAME_WORDS = ["log", "logs"]

BOARD_GRAPHICS = set([0x1BD7, 0x1BD9, 0x1BDA, 0x1BDB])
BOARD_NAME_WORDS = ["board", "boards"]

# Counted as one pool, reported apart
WOOD_KINDS = [
    ("logs", LOG_GRAPHICS, LOG_NAME_WORDS),
    ("boards", BOARD_GRAPHICS, BOARD_NAME_WORDS),
]

REGULAR_WOOD = "regular"

# What a craft can spend besides wood, for the consumed rows in DATA_PATH: the display case takes
# ingots. A stack not in here is not measured.
MATERIAL_GRAPHICS = set([0x1BEF, 0x1BF2])

# Read off the tooltip: '74 Oak Boards' is oak, '1580 Boards' is regular. Each is its own resource
# to the craft menu, which spends only the one it is set to.
WOOD_TYPES = ["oak", "ash", "yew", "heartwood", "bloodwood", "frostwood"]

# What the menu is set to: what a restock pulls and what counts as stock. Set the menu to match.
WOOD_TYPE = REGULAR_WOOD

# For the stack whose tooltip has not arrived. A colour in neither table is reported as unknown,
# never treated as regular.
WOOD_HUES = {
    0: REGULAR_WOOD,
    1191: "ash",
    2010: "oak",
}

# Wood of the wrong type is weight and nothing else. Off leaves it in the pack.
RETURN_WRONG_WOOD = True

# The shard's storage box, picked at the cursor beside chests and pack animals
BOX = WOOD_BOX

# What one restock draws from the box, in presses of 100
BOX_TAKE = 200

# How long the pack has to show a row's boards after the press, and how often it is read
BOX_PRESS_TIMEOUT = 3.0
BOX_PRESS_POLL = 0.25

# One tool is fetched at a time from the container the form picked; how long the pack has to show it
FETCH_TIMEOUT = 3.0
FETCH_POLL = 0.25

TOOL_MODES = [("stop", "Stop the run"), ("fetch", "Fetch from a container")]
OUTPUT_OPTIONS = [("unload", "Unload into a container"), ("keep", "Keep")]

# Every restock fills the pack to this
BATCH_SIZE = 300
RESTOCK_AT = 40

# Products in the pack, counted as amounts, before they are unloaded
DUMP_AT = 10

# With nothing picked to unload into, the run ends once the pack holds this many products
MAX_HELD = 60

# Unloads in a row that moved nothing before the run ends
MAX_DUMP_MISSES = 3

# The form the run is set up on. Closing it, Cancel, or no OK in the timeout ends the run.
SETUP = {
    "title": "Carpentry",
    "tool_noun": "carpentry tools",
    "tool_modes": TOOL_MODES,
    "outputs": OUTPUT_OPTIONS,
    "unsold_hint": None,
    "dump_at": DUMP_AT,
    "hue": 996,
    "poll": 0.25,
    "timeout": 600.0,
}

# Bounds Sources.pick only; the form adds sources one cursor at a time and never calls it
MAX_PICKS = 8

CONTAINER_RANGE = 2

CRAFT_TITLE = "CARPENTRY"

# Only ever to *recognise* a gump, never to refuse one: the header is a cliloc, and a build whose
# GetGumpContents answers nothing for it made every craft read as 'no craft menu'
CRAFT_TITLE_TEXT = [CRAFT_TITLE, "CARPENTER"]
CRAFT_TITLE_FRAGMENTS = [phrase.lower() for phrase in CRAFT_TITLE_TEXT]

# Its own button rather than a group, so it does not count toward the category index
LAST_TEN_LABEL = "LAST TEN"

# Buttons are 1 + type + index * 20, as bowcraft found on this shard's menu. MAKE LAST is the stock
# GetButtonID(6, 2): 1 + 6 + 2 * 20
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MAKE_LAST_BUTTON = 47

# (category button, row button). Empty on purpose: the walk finds each row and logs its button, and
# a guessed table mis-presses on a shard whose rows are in another order. Copy the log lines in here.
RECIPES = {}

MAX_CATEGORIES = 12

# The item buttons count across the pages: UOAlive's Misc. Add-Ons runs to 59 rows over six pages
MAX_ITEM_ROWS = 80

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

SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25

MAX_CYCLES = 20000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_TOOL = 10
MAX_EMPTY_MOVES = 3

# The shard refusing a move for weight. With products in the pack the run unloads before it loads.
TOO_HEAVY_TEXT = ["That container cannot hold more weight"]

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
        ],
    ),
    # Said in the gump's NOTICES panel, which the journal may never carry
    (
        "noMaterial",
        [
            "You do not have sufficient wood",
            "You do not have sufficient metal",
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


# src/uo/entity.py
# API.Player is None whenever the client is between world states - a recall, a server line change,
# the moment around a death - and reading through it threw a live restock away
def player():
    try:
        return API.Player
    except Exception:
        if API.StopRequested:
            raise

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


# src/uo/target.py
# The serial one cursor answered, or None for ESC or a timeout. Clears a cursor left open from
# before, and the one just answered too, so a target flag never survives past it.
def request_one(timeout):
    if API.HasTarget():
        API.CancelTarget()

    serial = API.RequestTarget(timeout)

    if API.HasTarget():
        API.CancelTarget()

    return serial or None


# src/uo/dump.py
class Dump(object):
    """The container the products are unloaded into: a trash barrel, or a chest."""

    # products is the script's name -> graphics table, read live: an art the crafter learns lands
    # in it after this, and a frozen union of it would never see the item to unload
    def __init__(self, sources, products, config, log):
        self._sources = sources
        self._products_of = products
        self._names = None
        self._config = config
        self._log = log
        self._entry = None
        keep_graphics = config.get("keep_graphics", self._graphics())
        # Carpentry narrows this to the deed art, which doubles as a house deed's - keeping every
        # matching graphic locked out leftover, un-dumped stock from a previous run for good
        self._kept = (set(item.Serial for item in pack_contents()
                           if item.Graphic in keep_graphics)
                      if config["keep_existing"] else set())

    def _graphics(self):
        names = self._names if self._names is not None else self._products_of

        return set().union(*[self._products_of[name] for name in names])

    def _products(self):
        graphics = self._graphics()

        return [item for item in pack_contents() if item.Graphic in graphics]

    def items(self):
        return [item for item in self._products() if item.Serial not in self._kept]

    def held(self):
        return sum(amount_of(item) for item in self.items())

    def picked(self):
        return self._entry is not None

    def name(self):
        return self._sources.name_of(self._entry) if self._entry is not None else "nothing"

    # Sell watches only what nobody buys; the kept set was read against every product, a superset
    def limit_to(self, names):
        self._names = list(names)

    def line(self):
        return "'%s' %s" % (self.name(), hex_of(self._entry["serial"]))

    def _refusal(self, serial):
        if serial == API.Backpack:
            return "that is your own pack"

        entry = self._sources.entry_for(serial)

        if entry is None:
            return "%s is neither a container nor a creature" % hex_of(serial)

        if entry["kind"] == "box":
            return ("'%s' is a storage box, which takes nothing you made - pick a barrel or a "
                    "chest" % self._sources.name_of(entry))

        if self._sources.open(entry) is None:
            return "'%s' has no backpack to unload into" % self._sources.name_of(entry)

        return None

    # (the picked container's line, None), (None, why it was refused), or (None, None) for ESC
    def pick_line(self):
        serial = request_one(self._config["pick_timeout"])

        if serial is None:
            return None, None

        refusal = self._refusal(serial)

        if refusal is not None:
            self._log(refusal)

            return None, refusal

        self._entry = self._sources.entry_for(serial)
        self._log("unloading into %s" % self.line())

        return self.line(), None

    def pick(self):
        self._log("target the container to unload into, a trash barrel or a chest - ESC to keep "
                  "everything in the pack")

        line, _refusal = self.pick_line()

        return self._entry if line is not None else None

    def run(self):
        items = self.items()

        if self._entry is None or len(items) == 0:
            return 0

        if not self._sources.reach(self._entry):
            self._log("cannot reach '%s' to unload" % self.name())

            return 0

        container = self._sources.open(self._entry)

        if container is None:
            self._log("'%s' has no backpack to unload into" % self.name())

            return 0

        before = self.held()

        for item in items:
            API.MoveItem(item.Serial, container, amount_of(item))
            API.Pause(self._config["move_delay"])

        moved = before - self.held()

        if moved > 0:
            self._log("unloaded %d into '%s'" % (moved, self.name()))
        else:
            self._log("'%s' took nothing" % self.name())

        return moved


# src/uo/cost.py
def cost_of(product, costs, fallback):
    return costs.get(product, fallback)


def short_by(product, held, costs, fallback):
    return max(0, cost_of(product, costs, fallback) - held)


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


def phrase_in(text, phrase):
    found = words_of(text)
    wanted = words_of(phrase)

    for start in range(len(found) - len(wanted) + 1):
        if found[start:start + len(wanted)] == wanted:
            return True

    return len(wanted) == 0


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


def clipped(text, limit):
    flat = " ".join((text or "").split())

    return flat if len(flat) <= limit else flat[:limit] + "..."


# src/uo/journal.py
def said(texts):
    for text in texts:
        if API.InJournal(text, False):
            return True

    return False


# A craft's mana coming back gains Meditation and Focus, which buries the one line that matters
SKILL_GAIN_TEXT = ["your skill in", "has changed by"]


# matchingText is left off on purpose: the client only applies it as a regex, so a plain string
# there filters everything out
def journal_tail(seconds, limit, stamp=None):
    try:
        entries = API.GetJournalEntries(seconds)
    except Exception:
        if API.StopRequested:
            raise

        return []

    texts = []
    stamps = [stamp] if stamp else []

    for entry in entries if entries else []:
        text = getattr(entry, "Text", None)

        if (text and text.strip() and not any_in(text, SKILL_GAIN_TEXT)
                and not any_in(text, stamps)):
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


# src/uo/craft.py
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

    # A row the menu named by its exact label is proof the pack cannot overrule: the shard said made
    # and no art in the table landed, so the table is what is wrong
    def _trust_named(self, product, button, held):
        if product not in self._trusted:
            if self._menu.named_button(product) != button:
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


def gump_says(gump, texts):
    for text in texts:
        if API.GumpContains(text, gump):
            return True

    return False


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
        self._said_no_category = False
        self._said_no_row = set()
        self._said_no_details = False
        self._said_no_button = set()
        self._said_not_menu = False
        self._category_buttons = {}
        self._category_rejects = {}
        self._named_buttons = {}

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

    def item_rows(self, gump):
        return [label for label, _button in self.rows_of(gump)]

    # The row's button by its name, or None when the menu does not name it
    def named_row(self, product, gump):
        for label, button in self.rows_of(gump):
            if label.lower() == product:
                return button

        return None

    # The row an exact label match found, which a wrong product graphic must not be allowed to blame
    def named_button(self, product):
        return self._named_buttons.get(product)

    def _say_no_row(self, product, rows):
        if product in self._said_no_row:
            return

        self._said_no_row.add(product)
        self._log("no SELECTIONS row reads '%s' - walking the rows" % product)
        self._log("rows seen: %s" % (", ".join(label for label, _button in rows) or "none"))

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

    # A row the menu names is taken on its name. Otherwise the details page (its button plus one,
    # which costs nothing to open) of each row whose name carries the product is opened until one
    # names it; with no names to read, every row's is. A details page shows the row's own name, so
    # a row whose name lacks the product is not opened. None sends the caller to the walk;
    # (gump, None) is a category that has no such row.
    def find_row(self, product, gump):
        category = self._category_buttons.get(product)

        if category is None or button_ids(gump) is None:
            return None

        named = self.named_row(product, gump)

        if named is not None:
            self._named_buttons[product] = named
            self._log("'%s' is the row on button %d - the menu names it there" % (product, named))

            return (gump, named)

        rows = self.rows_of(gump)

        # A gump with buttons but no readable names is reported by the walk instead
        if rows:
            self._say_no_row(product, rows)
            order = [button for label, button in rows if phrase_in(label, product)]
        else:
            order = self._walk_order(product, rows)

        for button in order:
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

        if self.named_row(product, gump) is None:
            self._say_no_row(product, rows)

        order = self._walk_order(product, rows)
        known = button_ids(gump)

        return order if known is None else [button for button in order if button in known]


# src/uo/craftrun.py
"""The bookkeeping bowcraft, carpentry, tinkering and inscription all repeat: ending a cycle
through the stall watch, running a sell or unload trip, recording a craft's materials, and freeing
pack weight by selling or unloading when a restock is refused for it."""


def end_cycle(stall, phase, cycle, tally, stop):
    """Ends the cycle through the stall watch, keeping whichever stop reason came first: the
    caller's own, or the stall's if the caller had none yet."""
    stall.end_cycle(phase, cycle, tally)

    return stop if stop is not None else stall.reason()


class Unloader(object):
    """One dump, and how many trips in a row moved nothing."""

    def __init__(self, dump):
        self._dump = dump
        self.misses = 0

    def run(self):
        if self._dump.run() > 0:
            self.misses = 0

            return True

        self.misses += 1

        return False


class CraftRecorder(object):
    """Measured either side of the craft rather than read off the recipe: a failure refunds part
    of it."""

    def __init__(self, recorder, materials, refund_settle, refund_poll):
        self._recorder = recorder
        self._materials = materials
        self._refund_settle = refund_settle
        self._refund_poll = refund_poll

    def record(self, outcome, skill_from, before, product):
        if not self._recorder.recording():
            return

        after = self._materials.settled_snapshot(self._refund_settle, self._refund_poll)
        self._recorder.record(skill_from, outcome, product, self._materials.spent(before, after))


# A pack the shard will not load for weight is emptied first, the way the band's products leave.
# sell and unload are each None, or (applies, held, run): zero-arg callables answering whether the
# trip is on for this band right now, how much is held, and whether running it moved anything.
# Tried in order, first one that applies and still holds something wins.
def make_room(restock, log, noun, sell=None, unload=None):
    if not restock.refused_for_weight():
        return None

    for phase, path in (("selling", sell), ("unloading", unload)):
        if path is None:
            continue

        applies, held_of, run = path

        if not applies():
            continue

        held = held_of()

        if held == 0:
            continue

        log("%s %d before loading more%s" % (phase, held, " " + noun if noun else ""))

        return phase if run() else None

    return None


# src/uo/tool.py
# Books carry the client's container flag, so the flag alone opens every spellbook in the pack
NOT_BAG_GRAPHICS = set([
    0x0EFA,  # spellbook
    0x2253,  # necromancer spellbook
    0x2252,  # book of chivalry
    0x238C,  # book of bushido
    0x23A0,  # book of ninjitsu
    0x2D50,  # spellweaving spellbook
    0x2D9D,  # mysticism spellbook
    0x22C5,  # runebook
    0x9C16,  # runic atlas
    0x2259,  # bulk order book
])
NOT_BAG_NAMES = ["spellbook", "runebook", "book", "atlas"]


def is_bag(item):
    if not getattr(item, "IsContainer", False) or getattr(item, "Opened", False):
        return False

    if item.Graphic in NOT_BAG_GRAPHICS:
        return False

    return not word_in(item.Name, NOT_BAG_NAMES)


# A bag the client has not opened this session reads as empty, whatever is in it. extra_serial, a
# spare bag outside the pack, joins the search if it is not open yet either. opened is mutated:
# every bag this call sends a double-click to is remembered so a later call leaves it alone.
def open_unopened_bags(noun, log, opened, extra_serial=None):
    bags = [item for item in pack_contents() if is_bag(item)]

    if extra_serial is not None:
        spare = API.FindItem(extra_serial)

        if spare is not None and not getattr(spare, "Opened", False):
            bags.append(spare)

    bags = [bag for bag in bags if bag.Serial not in opened]

    if not bags:
        return False

    # A cursor left up would take the double-click as its answer
    if API.HasTarget():
        API.CancelTarget()

    log("opening %d bag(s) to look inside for a %s" % (len(bags), noun))

    for bag in bags:
        opened.add(bag.Serial)
        API.UseObject(bag.Serial)

    return True


# search is called fresh each time: opening the bags is asynchronous, so what it finds only
# improves after settled() gives the pack a chance to catch up
def find_after_opening_bags(search, noun, log, opened, timeout, poll, extra_serial=None):
    found = search()

    if found is None and open_unopened_bags(noun, log, opened, extra_serial):
        settled(timeout, poll, lambda: search() is not None)
        found = search()

    return found


# src/uo/crafttool.py
class CraftTool(object):
    """A crafting tool, used out of the pack rather than equipped."""

    def __init__(self, noun, graphics, name_words, log, prefer=None):
        self._noun = noun
        self._graphics = graphics
        self._name_words = name_words
        self._log = log
        self._prefer = prefer or set()
        self._opened = set()

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

    def serials(self):
        return [item.Serial for item in pack_contents() if self.is_tool(item)]

    def serial(self):
        found = None

        for item in pack_contents():
            if not self.is_tool(item):
                continue

            if item.Graphic in self._prefer:
                return item.Serial

            if found is None:
                found = item.Serial

        return found

    def find(self, timeout, poll):
        return find_after_opening_bags(self.serial, self._noun, self._log, self._opened,
                                       timeout, poll)


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


# By the value as well as the base: with no base reported, or a lifted value, the run never ends
def skill_capped(name):
    def clause():
        skill = API.GetSkill(name) if name is not None else None

        if skill is None:
            return None

        base = getattr(skill, "Base", None) or 0.0
        value = skill.Value

        if max(base, value) <= 0 or max(base, value) < skill.Cap:
            return None

        if base >= skill.Cap:
            return "%s is capped at %.1f" % (name, base)

        if base > 0:
            return ("%s shows %.1f against its %.1f cap while its base is %.1f - take off what lifts "
                    "it to keep gaining" % (name, value, skill.Cap, base))

        return "%s is capped at %.1f" % (name, value)

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


# src/uo/materials.py
class Materials(object):
    """What a craft spent, measured either side of it. Whitelisted: a potion drunk is not a cost."""

    def __init__(self, stock, extra_graphics):
        self._stock = stock
        self._extra = extra_graphics
        # Learned while the stack is there: the one that paid for a craft is often gone by the diff
        self._names = {}

    def _counted(self, item):
        return self._stock.is_stock(item) or item.Graphic in self._extra

    def _name_of(self, item):
        kind = self._stock.kind_of(item)

        if kind is not None:
            name = self._stock.type_of(item)

            return kind if name is None else "%s %s" % (name, kind)

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

    # The lost side only: the product lands in the same pack and is not a cost
    def spent(self, before, after):
        _gained, lost = diff_counts(before, after)
        rows = []

        for key in sorted(lost):
            graphic, hue = key
            rows.append((self._names.get(key) or hex_of(graphic), graphic, hue, lost[key]))

        return rows


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


# src/uo/gainpath.py
COMMAND = "[SkillGainMode"
PROMPT = "skill gain path is"
PATHS = ("Modern", "Legacy", "Perilous")


def _named(text):
    low = (text or "").lower()
    at = low.find(PROMPT)

    if at < 0:
        return None

    words = words_of(text[at + len(PROMPT):])

    for path in PATHS:
        if path.lower() in words:
            return path

    return None


# Sent once per run, ahead of the loop that records attempts: the client answers "Your skill gain
# path is Modern. This character's ..." and every recorded row carries whichever of Modern, Legacy
# or Perilous follows.
def read_gain_path(budget, poll, log):
    API.Msg(COMMAND)

    waited = 0.0

    while not API.StopRequested:
        for entry in API.GetJournalEntries(budget + poll) or []:
            path = _named(getattr(entry, "Text", None))

            if path is not None:
                return path

        if waited >= budget:
            log("no skill gain path reported - recording without one")
            return None

        API.Pause(poll)
        waited += poll

    return None


# src/uo/record.py
# Written by hand rather than with json.dumps, so the key order stays the one the README shows
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

    A row is buffered when the attempt resolves and written when the *next* attempt is recorded,
    carrying that attempt's starting value as its own end: the client applies a gain some time after
    the outcome, and a value read on the next cycle still misses one that lands during a pause,
    where the next attempt's read cannot. close() writes the last row at the end of the run. The
    cost is one row in the air at any moment, which a killed script loses; the alternative is a
    file that under-reports every gain it exists to measure.
    """

    def __init__(self, path, character, serial, skill, log, append=None, gain_path=None):
        self._path = path or ""
        self._character = character or ""
        self._serial = serial
        self._skill = skill
        self._gain_path = gain_path
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

    # used is what the attempt was made with: the spell, the product, the creature, the weapon.
    # consumed and gained are lists of (name, graphic, hue, quantity) - measured, so an attempt that
    # spent nothing passes nothing rather than a guess at what the recipe charges
    def record(self, skill_from, outcome, used, consumed=None, gained=None):
        if self._off or skill_from is None:
            return

        # The previous row ends where this attempt starts: the latest read there is
        self._flush(skill_from)

        self._seq += 1
        self._pending = {
            "id": "%s/%d/%d" % (hex_of(self._serial), self._run, self._seq),
            "at": now(),
            "from": skill_from,
            "used": used,
            "outcome": outcome,
            "consumed": list(consumed) if consumed else [],
            "gained": list(gained) if gained else [],
        }

    # The end of the run. skill_to is None only where no reading ever arrived, and the row is
    # written all the same with its end unknown rather than lost with the run
    def close(self, skill_to):
        self._flush(skill_to)

    def _flush(self, skill_to):
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
            '"gainPath":%s' % (quoted(self._gain_path) if self._gain_path else "null"),
            '"used":%s' % quoted(row["used"]),
            '"from":%s' % skill_json(row["from"]),
            '"to":%s' % skill_json(skill_to),
            '"outcome":%s' % quoted(row["outcome"]),
        ]

        for key in ("consumed", "gained"):
            if row[key]:
                fields.append('"%s":[%s]' % (key, ",".join(
                    '{"name":%s,"graphic":%s,"hue":%d,"qty":%d}'
                    % (quoted(name), quoted(hex_of(graphic)), hue, quantity)
                    for name, graphic, hue, quantity in row[key]
                )))

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

    where = beside_script(path)

    if where:
        log("recording to %s" % where)

    gain_path = read_gain_path(GAIN_PATH_TIMEOUT, GAIN_PATH_POLL, log) if where else None

    return AttemptLog(where, getattr(me, "Name", ""), getattr(me, "Serial", 0), skill, log,
                       gain_path=gain_path)


# src/uo/stock.py
class StockBook(object):
    """What in the pack is the craft's material, which type it is, and how much the menu will spend."""

    def __init__(self, config, log):
        self._noun = config["noun"]
        self._kinds = config["kinds"]
        # Longest first: 'copper' would otherwise take 'dull copper'
        self._types = sorted(config["types"], key=lambda name: -len(words_of(name)))
        self._hues = config["hues"]
        self._wanted = config["wanted"]
        self._move_delay = config["move_delay"]
        self._log = log

    def noun(self):
        return self._noun

    def wanted(self):
        return self._wanted

    # For a snapshot key, which has no item left to read a name off
    def is_stock_graphic(self, graphic):
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

    def is_stock(self, item):
        return self.kind_of(item) is not None

    # The name is where the shard writes it; a hue in neither table is not guessed at
    def type_of(self, item):
        words = words_of(item.Name)

        for name in self._types:
            wanted = words_of(name)

            for start in range(len(words) - len(wanted) + 1):
                if words[start:start + len(wanted)] == wanted:
                    return name

        return self._hues.get(hue_of(item))

    def usable(self, item):
        return self.is_stock(item) and self.type_of(item) == self._wanted

    def wrong(self, item):
        return self.is_stock(item) and self.type_of(item) != self._wanted

    def usable_kind(self, item, kind):
        return self.usable(item) and self.kind_of(item) == kind

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

            name = self.type_of(item) or "unknown"
            counts[name] = counts.get(name, 0) + amount_of(item)

        return counts

    def other_report(self, counts):
        parts = ["%d %s" % (counts[name], name)
                 for name in sorted(counts, key=lambda name: -counts[name])]

        return ", ".join(parts)

    # In kind order, so it reads the same each time
    def report(self, counts):
        parts = []

        for kind, _graphics, _words in self._kinds:
            if counts.get(kind, 0) > 0:
                parts.append("%d %s" % (counts[kind], kind))

        return ", ".join(parts) if parts else "no %s" % self._noun

    def pack_stock(self):
        return self.counts(pack_contents())

    def pack_other(self):
        return self.other_counts(pack_contents())

    def in_pack(self):
        return total_of(self.pack_stock())

    def pack_report(self):
        text = self.report(self.pack_stock())
        other = self.other_report(self.pack_other())

        return text if not other else "%s (%s set aside)" % (text, other)

    # By hue: oak, ash and yew are all 'boards' by graphic. Missing hue rows come from here.
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

        return ", ".join(parts) if parts else "no %s" % self._noun

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
            self._log("brought %d %s up out of the bags in your pack" % (moved, self._noun))

        return moved


def total_of(counts):
    return sum(counts[kind] for kind in counts)


# src/uo/vitals.py
def weight_reading():
    me = player()

    return "?/?" if me is None else "%d/%d" % (me.Weight, me.WeightMax)


def where():
    me = player()

    return "somewhere" if me is None else "at %d,%d" % (me.X, me.Y)


def position_and_weight():
    return "%s, %s" % (where(), weight_reading())


# src/uo/restock.py
class Restock(object):
    def __init__(self, wood, sources, config, log):
        self._wood = wood
        self._sources = sources
        self._config = config
        self._log = log
        self._heavy = False

    def refused_for_weight(self):
        return self._heavy

    # One pool by default; a table of kind -> fill-to pulls each kind on its own, so a craft that
    # spends several things does not fill the pack with whichever pile the container lists first
    def _targets(self, targets):
        if targets is None:
            return [(None, self._config["batch"] - self._wood.in_pack())]

        held = self._wood.pack_stock()

        return [(kind, targets[kind] - held.get(kind, 0)) for kind in sorted(targets)]

    def _grew(self, before, after):
        return ", ".join(sorted(name for name in after if after[name] > before.get(name, 0)))

    def _pull(self, entry, kind, wanted):
        moved = 0
        stalled = 0
        cap = self._sources.cap(entry)

        if cap is not None:
            wanted = min(wanted, cap)

        while moved < wanted and stalled < self._config["max_empty_moves"]:
            if not self._sources.has_stock(entry, kind):
                break

            before = self._wood.in_pack()
            others = self._wood.pack_other()
            token = self._sources.take(entry, kind, wanted - moved)
            gained = self._wood.in_pack() - before

            # Every container answers the same, so the first refusal ends the whole pull
            if gained <= 0 and matched_bucket([("heavy", self._config["heavy_text"])]):
                self._heavy = True
                self._log("the shard will not load more %s - too heavy at %s"
                          % (self._wood.noun(), weight_reading()))
                break

            if gained <= 0:
                gave = self._grew(others, self._wood.pack_other())

                if gave:
                    self._sources.took_wrong(entry, token, gave)

                stalled += 1
            else:
                stalled = 0
                moved += gained

        return moved

    # Moves are asynchronous: the pack is re-counted after each rather than a return value read
    def run(self, targets=None):
        self._heavy = False
        lifted = self._wood.lift_from_bags()

        # After the lift: in_pack reads bags too, and counting the lift twice left it short
        wanted = dict(self._targets(targets))
        moved = 0

        for entry in self._sources.picked():
            if max(wanted.values()) <= 0 or self._heavy:
                break

            if not self._sources.reach(entry):
                self._log("cannot reach '%s', trying the next" % self._sources.name_of(entry))
                continue

            if self._sources.open(entry) is None:
                self._log("'%s' did not open" % self._sources.name_of(entry))
                continue

            if self._config["return_wrong_wood"]:
                self._sources.put_back(entry)

            for kind in sorted(wanted, key=lambda name: name or ""):
                if wanted[kind] <= 0 or self._heavy:
                    continue

                pulled = self._pull(entry, kind, wanted[kind])
                wanted[kind] -= pulled
                moved += pulled

        if moved > 0:
            self._log("pulled %d %s, %s in the pack, %d left in what you picked"
                      % (moved, self._wood.noun(), self._wood.pack_report(),
                         self._sources.stock_left()))

        return lifted + moved


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


# src/uo/gumpwait.py
# Waits behind a gump the script drew, one poll slice at a time, until resolve() answers a reason
# to stop (checked first, so a click wins over the gump closing), the gump is disposed, stop_reason
# gives one, or timeout seconds pass - timeout=None means no ceiling. each(), when given, runs once
# a slice before resolve(), so an alarm or a heartbeat keeps going while the gump is up. Disposes
# the gump before returning why. The click only arrives through ProcessCallbacks, and a stopped
# script's client calls all answer with nothing, so the stop flag is the one read that still means
# something then.
def wait_for_gump(gump, stop_reason, poll, resolve, closed_message="the gump was closed",
                  timeout=None, each=None):
    waited = 0.0
    why = None

    while why is None:
        if API.StopRequested:
            why = "the run is being stopped"
            break

        if each is not None:
            each()

        API.ProcessCallbacks()

        why = resolve()

        if why is not None:
            pass
        elif gump.IsDisposed:
            why = closed_message
        elif stop_reason() is not None:
            why = "the run has a reason to stop"
        elif timeout is not None and waited >= timeout:
            why = "nothing was pressed in %.0fs" % timeout
        else:
            API.Pause(poll)
            waited += poll

    if not gump.IsDisposed:
        gump.Dispose()

    return why


# src/uo/setup.py
SETUP_WIDTH = 720
MARGIN = 16
LABEL_X = 16
FIELD_X = 160
VALUE_X = 316
ROW = 28
LINE = 22
TITLE_HEIGHT = 40
BUTTON_HEIGHT = 24
FONT = 15
SOURCE_LINES = 4
LINE_CHARS = 92
RADIO_CHAR = 8
RADIO_GAP = 40
DUMP_AT_WIDTH = 56

TEXT = "#E6E6E6"
MUTED = "#8C8C8C"
CURRENT = "#F2C14E"
WARN = "#FF7B6B"


class Setup(object):
    """The form the run is set up on: tools, wood sources, what is made, and the band table."""

    def __init__(self, config, log, stop_reason):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason
        self._pending = None
        self._sources = []
        self._tools_line = None
        self._unload_line = None
        self._message = None
        self._controls = {}

    def _presser(self, key):
        def press():
            self._pending = key

        return press

    def _label(self, gump, text, x, y, color=TEXT, width=None):
        label = API.Gumps.CreateGumpTTFLabel(text, FONT, color)
        label.SetRect(x, y, width if width is not None else SETUP_WIDTH - x - MARGIN, LINE)
        gump.Add(label)

        return label

    def _button(self, gump, key, caption, x, y, width):
        button = API.Gumps.CreateSimpleButton(caption, width, BUTTON_HEIGHT)
        button.SetPos(x, y)
        API.Gumps.AddControlOnClick(button, self._presser(key))
        gump.Add(button)

        return button

    def _show(self, heading, rows):
        outputs = self._config["outputs"]
        height = (TITLE_HEIGHT + ROW * 2 + ROW + LINE * SOURCE_LINES + ROW * 3
                  + LINE * (len(rows) + 1) + ROW * 2 + BUTTON_HEIGHT + MARGIN * 4)

        gump = API.Gumps.CreateGump(True, True)

        if gump is None:
            return None

        gump.SetRect(0, 0, SETUP_WIDTH, height)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.9, "#1E1E1E")
        background.SetRect(0, 0, SETUP_WIDTH, height)
        gump.Add(background)

        title = API.Gumps.CreateGumpLabel(self._config["title"], self._config["hue"])
        title.SetPos(MARGIN, 12)
        gump.Add(title)

        y = TITLE_HEIGHT
        c = self._controls

        self._label(gump, self._config["tool_noun"].capitalize(), LABEL_X, y)
        self._label(gump, "When they run out:", FIELD_X, y, MUTED, 150)
        c["modes"] = API.Gumps.CreateDropDown(200, [caption for _key, caption in
                                                    self._config["tool_modes"]], 0)
        c["modes"].SetPos(VALUE_X, y - 2)
        gump.Add(c["modes"])
        y += ROW

        c["tools_button"] = self._button(gump, "tools", "Pick tool container", FIELD_X, y, 148)
        c["tools_value"] = self._label(gump, "", VALUE_X, y + 3, MUTED)
        y += ROW + MARGIN // 2

        self._label(gump, "Wood", LABEL_X, y)
        self._button(gump, "source", "Add a source", FIELD_X, y, 140)
        self._button(gump, "clear", "Clear", FIELD_X + 148, y, 70)
        y += ROW

        c["sources"] = []

        for index in range(SOURCE_LINES):
            c["sources"].append(self._label(gump, "", FIELD_X, y + index * LINE, MUTED))

        y += LINE * SOURCE_LINES + MARGIN // 2

        self._label(gump, "What is made", LABEL_X, y)
        c["outputs"] = []

        x = FIELD_X

        # Spaced by caption: the classic font runs about RADIO_CHAR pixels a letter
        for index in range(len(outputs)):
            radio = API.Gumps.CreateGumpRadioButton(outputs[index][1], 1, 0x00D0, 0x00D1,
                                                    self._config["hue"], index == 0)
            radio.SetPos(x, y)
            gump.Add(radio)
            c["outputs"].append(radio)
            x += RADIO_GAP + RADIO_CHAR * len(outputs[index][1])

        y += ROW

        c["unload_button"] = self._button(gump, "unload", "Pick container", FIELD_X, y, 148)
        c["unload_value"] = self._label(gump, "", VALUE_X, y + 3, MUTED)
        y += ROW

        c["dump_label"] = self._label(gump, "Unload every", FIELD_X, y + 3, MUTED, 148)
        c["dump_at"] = API.Gumps.CreateGumpTextBox(str(self._config["dump_at"]), DUMP_AT_WIDTH,
                                                   BUTTON_HEIGHT, False, FONT)
        c["dump_at"].SetPos(VALUE_X, y)
        gump.Add(c["dump_at"])
        c["dump_unit"] = self._label(gump, "products", VALUE_X + DUMP_AT_WIDTH + 8, y + 3, MUTED)
        y += ROW + MARGIN // 2

        self._label(gump, "Training", LABEL_X, y)
        self._label(gump, heading, FIELD_X, y)
        y += LINE

        for text, current in rows:
            self._label(gump, ("> " if current else "   ") + text, FIELD_X, y,
                        CURRENT if current else MUTED)
            y += LINE

        y += MARGIN // 2
        c["message"] = self._label(gump, "", LABEL_X, y, WARN)
        y += ROW

        c["debug_logs"] = API.Gumps.CreateGumpCheckbox("Debug logs", self._config["hue"], True)
        c["debug_logs"].SetPos(LABEL_X, y)
        gump.Add(c["debug_logs"])
        y += ROW

        self._button(gump, "cancel", "Cancel", SETUP_WIDTH - MARGIN - 96 - 8 - 96, y, 96)
        self._button(gump, "ok", "OK", SETUP_WIDTH - MARGIN - 96, y, 96)

        API.Gumps.AddGump(gump)

        return gump

    def _mode(self):
        return self._config["tool_modes"][self._controls["modes"].GetSelectedIndex()][0]

    def _output(self):
        for index in range(len(self._controls["outputs"])):
            if self._controls["outputs"][index].GetIsChecked():
                return self._config["outputs"][index][0]

        return self._config["outputs"][0][0]

    def _debug_logs(self):
        return self._controls["debug_logs"].GetIsChecked()

    def _dump_at(self):
        text = (self._controls["dump_at"].Text or "").strip()

        return int(text) if text.isdigit() and int(text) > 0 else None

    def _unloading(self, actions):
        output = self._output()
        unsold = output == "sell" and actions["unsold_ahead"] is not None \
            and actions["unsold_ahead"]()

        return output == "unload" or unsold

    def _say(self, message):
        self._message = message
        self._controls["message"].SetText(message or "")

    def _refresh(self, actions):
        c = self._controls
        fetching = self._mode() == "fetch"
        c["tools_button"].IsVisible = fetching
        c["tools_value"].IsVisible = fetching
        c["tools_value"].SetText(clipped(self._tools_line or "required", LINE_CHARS))

        lines = list(self._sources)

        if len(lines) > SOURCE_LINES:
            lines[SOURCE_LINES - 1:] = ["... and %d more" % (len(lines) - SOURCE_LINES + 1)]

        for index in range(SOURCE_LINES):
            if index < len(lines):
                c["sources"][index].SetText(clipped(lines[index], LINE_CHARS))
            elif index == 0:
                c["sources"][0].SetText("nothing picked - the run works through the wood you carry")
            else:
                c["sources"][index].SetText("")

        showing = self._unloading(actions)

        for key in ("unload_button", "unload_value", "dump_label", "dump_at", "dump_unit"):
            c[key].IsVisible = showing

        if self._unload_line is not None:
            c["unload_value"].SetText(clipped(self._unload_line, LINE_CHARS))
        else:
            c["unload_value"].SetText(self._config["unsold_hint"] if self._output() == "sell"
                                      else "required")

    def _validate(self, actions):
        if self._mode() == "fetch" and not actions["tools_ready"]():
            return ("pick a container holding %s, or choose to stop when they run out"
                    % self._config["tool_noun"])

        if self._output() == "unload" and not actions["unload_ready"]():
            return "pick the container to unload into"

        if self._unloading(actions) and self._dump_at() is None:
            return "unload every: a whole number of products, 1 or more"

        if len(self._sources) == 0 and not actions["has_wood"]():
            return "add a source of wood, or carry some"

        return None

    def _run(self, pending, actions):
        if pending == "source":
            self._log("target a chest, a storage box or a pack animal holding wood")
            line, refusal = actions["source"]()

            if line is not None:
                self._sources.append(line)

            self._say(refusal)
        elif pending == "clear":
            actions["clear"]()
            del self._sources[:]
            self._say(None)
        elif pending == "tools":
            self._log("target the container holding %s" % self._config["tool_noun"])
            line, refusal = actions["tools"]()

            if line is not None:
                self._tools_line = line

            self._say(refusal)
        elif pending == "unload":
            self._log("target the container to unload into, a trash barrel or a chest")
            line, refusal = actions["unload"]()

            if line is not None:
                self._unload_line = line

            self._say(refusal)
        elif pending == "ok":
            failure = self._validate(actions)
            self._say(failure)

            return "ok" if failure is None else None
        elif pending == "cancel":
            return "cancel"

        return None

    def ask(self, actions):
        if API.HasTarget():
            API.CancelTarget()

        heading, rows = actions["table"]()
        gump = self._show(heading, rows)

        # API.Stop() only lands at the next Pause, and every client call before it answers nothing
        if gump is None:
            self._log("not asking - the run is being stopped")

            return None

        self._log("asking - the start-up form")
        self._refresh(actions)
        answers = [None]

        def resolve():
            pending, self._pending = self._pending, None
            done = self._run(pending, actions) if pending is not None else None

            self._refresh(actions)

            if done == "ok":
                dump_at = self._dump_at()
                answers[0] = {"tools": self._mode(), "output": self._output(),
                              "sources": len(self._sources),
                              "dump_at": dump_at if dump_at is not None else self._config["dump_at"],
                              "debug_logs": self._debug_logs()}

                return "OK was pressed"

            return "Cancel was pressed" if done == "cancel" else None

        why = wait_for_gump(gump, self._stop_reason, self._config["poll"], resolve,
                            closed_message="the form was closed", timeout=self._config["timeout"])

        self._log(why)

        return answers[0]


# src/uo/skill.py
# A name the client does not carry throws on some builds rather than answering None
def find_skill_name(names):
    for name in names:
        try:
            if API.GetSkill(name) is not None:
                return name
        except Exception:
            if API.StopRequested:
                raise

            continue

    return None


def reading(value):
    return "unknown" if value is None else "%.1f" % value


class SkillReader(object):
    """Value reads 0.0 before the skill list arrives, which is also a real skill value."""

    def __init__(self, name):
        self._name = name
        self._seen = False
        self._last = None

    def read(self):
        skill = API.GetSkill(self._name)

        if skill is None:
            return None

        value = skill.Value

        if value <= 0.0 and not self._seen:
            return None

        self._seen = True
        self._last = value

        return value

    # Once the stop button is pressed the client answers nothing, so the last row of a run would
    # end unknown; the latest reading that did arrive is never further off than that
    def last(self):
        value = self.read()

        return value if value is not None else self._last

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
                return self._accept_zero()

            API.Pause(poll)
            waited += poll

        return None

    # A 0 the client still answers once the wait is over is a real 0, not an unsent skill list
    def _accept_zero(self):
        skill = API.GetSkill(self._name)

        if skill is None:
            return None

        self._seen = True
        self._last = skill.Value

        return skill.Value


# src/uo/box.py
def _is_int(token):
    return token.lstrip("-").isdigit()


# The packet is the strings, one a line, then the layout: 'text x y hue index', 'button x y ... id'
def _split_layout(packet):
    lines = (packet or "").replace("\x00", "").split("\n")

    for start in range(len(lines)):
        tokens = lines[start].split()

        if len(tokens) > 1 and tokens[0].isalpha() and tokens[0].islower() \
                and all(_is_int(token) for token in tokens[1:]):
            return lines[:start], [line.split() for line in lines[start:] if line.split()]

    return lines, []


# A row's button is the nearest one to the left of its label on the same line of the layout
def layout_buttons(packet, labels):
    strings, layout = _split_layout(packet)
    texts = {}
    buttons = []

    for tokens in layout:
        if tokens[0] in ("text", "croppedtext") and len(tokens) >= 5:
            texts[int(tokens[-1])] = (int(tokens[1]), int(tokens[2]))
        elif tokens[0] == "button" and len(tokens) >= 8:
            buttons.append((int(tokens[1]), int(tokens[2]), int(tokens[-1])))

    found = {}

    lowered = [string.lower() for string in strings]

    for label in labels:
        if label.lower() not in lowered:
            continue

        spot = texts.get(lowered.index(label.lower()))

        if spot is None:
            continue

        beside = [(x, ident) for x, y, ident in buttons if y == spot[1] and x < spot[0]]

        if beside:
            found[label] = max(beside)[1]

    return found


class StorageBox(object):
    """The shard's resource box: stock read off its gump, drawn a button press at a time."""

    def __init__(self, table, config, log):
        self._table = table
        self._rows = dict((label.lower(), label) for label in table["rows"])
        self._config = config
        self._log = log
        self._id = 0
        self._serial = None
        self._seen = {}
        self._skipped = set()
        self._said = set()

    def _say_once(self, key, text):
        if key in self._said:
            return

        self._said.add(key)
        self._log(text)

    def is_box_gump(self, ident):
        if not ident:
            return False

        if any_in(API.GetGumpContents(ident) or "", self._table["title"]):
            return True

        return gump_says(ident, self._table["title"])

    def _showing(self):
        if self._id and is_open(self._id):
            return self._id

        for ident in open_ids():
            if self.is_box_gump(ident):
                self._id = ident

                return ident

        return 0

    def open(self, serial):
        showing = self._showing()

        if showing and self._serial in (None, serial):
            self._serial = serial
            self._seen[serial] = self._parse(showing)

            return showing

        before = open_ids()
        API.UseObject(serial)

        found, recognised = await_recognised(self.is_box_gump, before,
                                             self._config["gump_timeout"],
                                             self._config["gump_poll"])

        if not found or not recognised:
            return 0

        self._id = found
        self._serial = serial
        self._seen[serial] = self._parse(found)

        return found

    # Keyed by the table's spelling of a label, whatever case the gump shows it in
    def _parse(self, gump):
        rows = {}
        tokens = untagged(API.GetGumpContents(gump) or "").split()

        for index in range(1, len(tokens)):
            if tokens[index].isdigit():
                label = tokens[index - 1]

                if label.lower() in self._rows:
                    rows[self._rows[label.lower()]] = int(tokens[index])
                else:
                    self._say_once(("row", label.lower()),
                                   "the box lists '%s', which the BOX rows do not name" % label)

        return rows

    # Live while the gump is up, else as last seen: UseObject from across the house opens nothing
    def rows(self, serial):
        showing = self._showing()

        if showing and self._serial == serial:
            self._seen[serial] = self._parse(showing)

        return self._seen.get(serial, {})

    def _kind_of(self, label):
        return self._table["rows"][label][0]

    def _type_of(self, label):
        wood_type = self._table["rows"][label][1]

        return wood_type if wood_type is not None else self._config["plain"]

    def _labels(self, kind, wanted):
        return [label for label in self._table["rows"]
                if (kind is None or self._kind_of(label) == kind)
                and self._type_of(label) == wanted]

    def counts(self, serial, wanted):
        rows = self.rows(serial)
        counts = {}

        for label in self._labels(None, wanted):
            if rows.get(label, 0) > 0:
                kind = self._kind_of(label)
                counts[kind] = counts.get(kind, 0) + rows[label]

        return counts

    def other_counts(self, serial, wanted):
        rows = self.rows(serial)
        counts = {}

        for label in rows:
            if self._type_of(label) != wanted and rows[label] > 0:
                name = self._type_of(label)
                counts[name] = counts.get(name, 0) + rows[label]

        return counts

    def _pressable(self, serial, kind, wanted):
        rows = self.rows(serial)
        labels = [label for label in self._labels(kind, wanted)
                  if label not in self._skipped and rows.get(label, 0) > 0]
        labels.sort(key=lambda label: -rows[label])

        return labels

    def has_stock(self, serial, kind, wanted):
        return len(self._pressable(serial, kind, wanted)) > 0

    # One press lands per_press; the caller re-counts the pack rather than trusting the reply
    def take(self, serial, kind, wanted):
        labels = self._pressable(serial, kind, wanted)

        if len(labels) == 0:
            return None

        label = labels[0]
        gump = self.open(serial)

        if not gump:
            return None

        button = self._button_for(label, gump)

        if button is None:
            self._skipped.add(label)
            self._say_once(("button", label),
                           "no button known for the '%s' row - run box-probe.py and fill the BOX "
                           "buttons" % label)

            return None

        known = button_ids(gump)

        if known is not None and button not in known:
            self._skipped.add(label)
            self._say_once(("missing", label), "gump %s has no button %d for '%s' - not pressing it"
                           % (hex_of(gump), button, label))

            return None

        if not API.ReplyGump(button, gump):
            return None

        # The reply disposes the gump, so the next read opens it again
        self._id = 0

        return label

    # Read off the gump's own layout; the table is for a client that hands back no packet text
    def _button_for(self, label, gump):
        try:
            found = API.GetGump(gump)
            packet = getattr(found, "PacketGumpText", None) if found is not None else None
        except Exception:
            if API.StopRequested:
                raise

            packet = None

        derived = layout_buttons(packet, [label]) if packet else {}

        if label in derived:
            return derived[label]

        return self._table["buttons"].get(label)

    def wrong_row(self, label, gave):
        self._skipped.add(label)
        self._log("the button table is out of date for '%s' - it gave %s" % (label, gave))


# src/uo/sources.py
KIND_NOUNS = {"item": "container", "mobile": "pack animal", "box": "storage box"}


class Sources(object):
    """The containers, storage boxes and pack animals the wood is drawn from."""

    def __init__(self, wood, config, log):
        self._wood = wood
        self._config = config
        self._log = log
        self._picked = []
        self._box = StorageBox(config["box"], config, log) if config["box"] else None

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
        if entry["kind"] == "box":
            return None

        if entry["kind"] == "mobile":
            return self._animal_pack(entry["serial"])

        return entry["serial"]

    def _is_box(self, item):
        if self._box is None:
            return False

        table = self._config["box"]

        return item.Graphic in table["graphics"] or any_in(item.Name, table["names"])

    def entry_for(self, serial):
        item = API.FindItem(serial)

        if item is not None:
            return {"kind": "box" if self._is_box(item) else "item", "serial": serial,
                    "name": item.Name or "?", "spot": (item.X, item.Y, item.Z)}

        animal = API.FindMobile(serial)

        if animal is None:
            return None

        return {"kind": "mobile", "serial": serial, "name": animal.Name or "?", "spot": None}

    # ItemsInContainer reads nothing out of a container the client has never seen inside
    def open(self, entry):
        if entry["kind"] == "box":
            return self._box.open(entry["serial"]) or None

        container = self.container_of(entry)

        if container is None:
            return None

        API.UseObject(container)
        API.Pause(self._config["open_delay"])

        return container

    def _noun_of(self, allowed):
        if allowed is None:
            return ("container, storage box or pack animal" if self._box is not None
                    else "container or pack animal")

        return " or ".join(KIND_NOUNS[kind] for kind in allowed if kind in KIND_NOUNS)

    def clear(self):
        del self._picked[:]

    def line_for(self, entry):
        other = self._wood.other_report(self.other_counts(entry))

        return "'%s' %s, %s in it%s" % (self.name_of(entry), hex_of(entry["serial"]),
                                        self._wood.report(self.counts(entry)),
                                        "" if not other else " (%s it will not use)" % other)

    def _refusal(self, serial, allowed):
        me = player()

        if serial == API.Backpack or (me is not None and serial == me.Serial):
            return "your own pack is always counted, no need to pick it"

        if serial in [entry["serial"] for entry in self._picked]:
            return "%s is already picked" % hex_of(serial)

        entry = self.entry_for(serial)

        if entry is None:
            return "%s is neither a container nor a creature" % hex_of(serial)

        if allowed is not None and entry["kind"] not in allowed:
            return ("'%s' is a %s - the gump chose the %s"
                    % (self.name_of(entry), KIND_NOUNS[entry["kind"]], self._noun_of(allowed)))

        # One storage box holds everything, and its gump is read one box at a time
        if entry["kind"] == "box" and any(held["kind"] == "box" for held in self._picked):
            return "'%s' is a second storage box - one holds everything" % self.name_of(entry)

        return None

    # One cursor, one answer: (the picked entry's line, None), (None, why it was refused), or
    # (None, None) for ESC
    def pick_one(self, allowed=None):
        serial = request_one(self._config["pick_timeout"])

        if serial is None:
            return None, None

        refusal = self._refusal(serial, allowed)

        if refusal is not None:
            self._log(refusal)

            return None, refusal

        entry = self.entry_for(serial)

        # Opened now, while it is in reach
        if self.open(entry) is None:
            refusal = "'%s' did not open" % self.name_of(entry)
            self._log(refusal)

            return None, refusal

        self._picked.append(entry)
        line = self.line_for(entry)
        self._log("picked %s" % line)

        return line, None

    # Every kind by default; a list of kinds, as the gump at the start chose, refuses the others
    def pick(self, allowed=None):
        single = allowed == ["box"]

        if single:
            self._log("target the storage box holding %s" % self._wood.noun())
        else:
            self._log("target every %s holding %s, ESC when done"
                      % (self._noun_of(allowed), self._wood.noun()))

        for _pick in range(self._config["max_picks"]):
            line, refusal = self.pick_one(allowed)

            # ESC or a timed-out cursor, either ends the selection
            if line is None and refusal is None:
                break

            if line is not None and single:
                break

        if API.HasTarget():
            API.CancelTarget()

        return self._picked

    # Only the type the menu is set to, and only one kind of it when a kind is named
    def container_wood(self, serial, kind=None):
        items = API.ItemsInContainer(serial, True)
        piles = [item for item in (items or [])
                 if (self._wood.usable(item) if kind is None
                     else self._wood.usable_kind(item, kind))]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def wood(self, entry):
        container = self.container_of(entry)

        return [] if container is None else self.container_wood(container)

    # Wrong type included, for the report lines
    def all_wood(self, entry):
        container = self.container_of(entry)
        items = API.ItemsInContainer(container, True) if container else None

        return [item for item in items if self._wood.is_stock(item)] if items else []

    def counts(self, entry):
        if entry["kind"] == "box":
            return self._box.counts(entry["serial"], self._wood.wanted())

        return self._wood.counts(self.wood(entry))

    def other_counts(self, entry):
        if entry["kind"] == "box":
            return self._box.other_counts(entry["serial"], self._wood.wanted())

        return self._wood.other_counts(self.all_wood(entry))

    def total(self, entry):
        return total_of(self.counts(entry))

    def stock_left(self):
        return sum(self.total(entry) for entry in self._picked)

    def stock_line(self):
        if len(self._picked) == 0:
            return "nothing picked to restock from"

        return "%d in the %d you picked" % (self.stock_left(), len(self._picked))

    def has_stock(self, entry, kind):
        if entry["kind"] == "box":
            return self._box.has_stock(entry["serial"], kind, self._wood.wanted())

        container = self.container_of(entry)

        return container is not None and len(self.container_wood(container, kind)) > 0

    # The most one restock draws from a source; None is as much as it asks for
    def cap(self, entry):
        return self._config["box_take"] if entry["kind"] == "box" else None

    # Moves are asynchronous: the caller re-counts the pack rather than reading a return value
    def take(self, entry, kind, amount):
        if entry["kind"] == "box":
            before = self._wood.in_pack()
            label = self._box.take(entry["serial"], kind, self._wood.wanted())

            # A press counted before its boards land is pressed again, and lands twice
            if label is not None:
                settled(self._config["press_timeout"], self._config["press_poll"],
                        lambda: self._wood.in_pack() != before)

            return label

        container = self.container_of(entry)
        piles = self.container_wood(container, kind) if container is not None else []

        if len(piles) == 0:
            return None

        API.MoveItem(piles[0].Serial, API.Backpack, min(amount, amount_of(piles[0])))
        API.Pause(self._config["move_delay"])

        return None

    def took_wrong(self, entry, token, gave):
        if entry["kind"] == "box" and token is not None:
            self._box.wrong_row(token, gave)

    # Wrong wood goes back while its container is open and in reach, the one moment it costs nothing
    def put_back(self, entry):
        container = self.container_of(entry)

        if container is None:
            return 0

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


# src/uo/stages.py
# Ceilings are exclusive; None catches everything above the last one
def band_for(bands, value):
    if value is None:
        return None

    for ceiling, product in bands:
        if ceiling is None or value < ceiling:
            return product

    return None


def _edge(value):
    return ("%.1f" % value).replace(".0", "") if value is not None else "cap"


# One row per band for the form: the range, the product, a third column, and which is current.
# The first row starts where the script starts, which the table itself does not say.
def band_rows(bands, value, describe, floor):
    rows = []
    current = band_for(bands, value)

    for ceiling, product in bands:
        span = "%s - %s" % (_edge(floor), _edge(ceiling))
        rows.append(("%s  %s  %s" % (span, product, describe(product)), product == current))
        floor = ceiling

    return rows


# src/uo/toolstore.py
class ToolStore(object):
    """The container the craft tools are fetched from, one at a time, once the pack runs out."""

    def __init__(self, tools, sources, config, log):
        self._tools = tools
        self._sources = sources
        self._config = config
        self._log = log
        self._entry = None

    def picked(self):
        return self._entry is not None

    def name(self):
        return self._sources.name_of(self._entry) if self._entry is not None else "nothing"

    def _inside(self):
        container = self._sources.container_of(self._entry) if self._entry is not None else None
        items = API.ItemsInContainer(container, True) if container else None

        return [item for item in (items or []) if self._tools.is_tool(item)]

    def count(self):
        return len(self._inside())

    def line(self):
        return "'%s' %s - %d %s" % (self.name(), hex_of(self._entry["serial"]), self.count(),
                                    self._config["noun"])

    def _refusal(self, serial):
        if serial == API.Backpack:
            return "that is your own pack"

        entry = self._sources.entry_for(serial)

        if entry is None:
            return "%s is neither a container nor a creature" % hex_of(serial)

        if entry["kind"] == "box":
            return ("'%s' is a storage box, which holds no %s - pick a chest or a pack animal"
                    % (self._sources.name_of(entry), self._config["noun"]))

        if self._sources.open(entry) is None:
            return "'%s' did not open" % self._sources.name_of(entry)

        return None

    # (the container's line, None) or (line, why OK will refuse it), (None, why it was refused),
    # or (None, None) for ESC
    def pick(self):
        serial = request_one(self._config["pick_timeout"])

        if serial is None:
            return None, None

        refusal = self._refusal(serial)

        if refusal is not None:
            self._log(refusal)

            return None, refusal

        self._entry = self._sources.entry_for(serial)
        line = self.line()
        self._log("fetching %s from %s" % (self._config["noun"], line))

        if self.count() == 0:
            return line, "'%s' holds no %s" % (self.name(), self._config["noun"])

        return line, None

    # True once the pack holds a tool again; the move is asynchronous, so the pack is watched
    def fetch(self):
        if self._entry is None:
            return False

        if not self._sources.reach(self._entry):
            self._log("cannot reach '%s' for a tool" % self.name())

            return False

        if self._sources.open(self._entry) is None:
            self._log("'%s' did not open for a tool" % self.name())

            return False

        inside = self._inside()

        if len(inside) == 0:
            self._log("'%s' has no %s left" % (self.name(), self._config["noun"]))

            return False

        API.MoveItem(inside[0].Serial, API.Backpack)
        API.Pause(self._config["move_delay"])

        landed = settled(self._config["fetch_timeout"], self._config["fetch_poll"],
                         lambda: self._tools.serial() is not None)

        if landed:
            self._log("fetched a tool from '%s', %d left" % (self.name(), self.count()))
        else:
            self._log("'%s' gave up no tool" % self.name())

        return landed


# src/carpentry/index.py
log = make_log("carpentry")
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


def wood_cost(item):
    return cost_of(item, WOOD_COST, MIN_CRAFT_WOOD)


def wood_short(item):
    return short_by(item, wood.in_pack(), WOOD_COST, MIN_CRAFT_WOOD)


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

tools = CraftTool("carpentry tool", TOOL_GRAPHICS, TOOL_NAME_WORDS, log)
wood = StockBook({
    "noun": "wood",
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
    "move_delay": MOVE_DELAY,
    "container_range": CONTAINER_RANGE,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "box": BOX,
    "plain": REGULAR_WOOD,
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
    "box_take": BOX_TAKE,
    "press_timeout": BOX_PRESS_TIMEOUT,
    "press_poll": BOX_PRESS_POLL,
}, log)
restock = Restock(wood, sources, {
    "batch": BATCH_SIZE,
    "move_delay": MOVE_DELAY,
    "max_empty_moves": MAX_EMPTY_MOVES,
    "return_wrong_wood": RETURN_WRONG_WOOD,
    "heavy_text": TOO_HEAVY_TEXT,
}, log)
dump = Dump(sources, PRODUCTS, {
    "pick_timeout": PICK_TIMEOUT,
    "move_delay": MOVE_DELAY,
    "keep_existing": True,
    "keep_graphics": DEED_GRAPHICS,
}, log)
tool_store = ToolStore(tools, sources, {
    "noun": "carpentry tools",
    "pick_timeout": PICK_TIMEOUT,
    "move_delay": MOVE_DELAY,
    "fetch_timeout": FETCH_TIMEOUT,
    "fetch_poll": FETCH_POLL,
}, log)
setup = Setup(SETUP, log, stop_reason)
menu = CraftMenu(tools, {
    "stride": BUTTON_STRIDE,
    "category_type": CATEGORY_BUTTON_TYPE,
    "item_type": ITEM_BUTTON_TYPE,
    "category_names": CATEGORY_NAMES,
    "last_ten_label": LAST_TEN_LABEL,
    "title": CRAFT_TITLE,
    "title_text": CRAFT_TITLE_TEXT,
    "title_fragments": CRAFT_TITLE_FRAGMENTS,
    "tool_noun": "carpentry tools",
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
    "material": WOOD_TYPE,
}, log, log.stamp)

start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)

# Before the cursor: a capped character has nothing to pick containers for
capped = skill_capped(skill_name)()

if start is None:
    log("%s is not reading yet - start it again once the skill list has arrived" % skill_name)
    API.Stop()
elif start < MIN_SKILL:
    log("%s is at %.1f and the table starts at %.1f - train it up by hand first"
        % (skill_name, start, MIN_SKILL))
    API.Stop()
elif capped is not None:
    log(capped)
    API.Stop()

cap = skill.cap()


def training_rows():
    heading = "%s %s%s" % (skill_name, reading(start),
                           " / %.1f" % cap if cap is not None and cap > 0 else "")

    return heading, band_rows(BANDS, start, lambda name: "%d wood" % WOOD_COST[name], MIN_SKILL)


answers = setup.ask({
    "table": training_rows,
    "tools": tool_store.pick,
    "tools_ready": lambda: tool_store.count() > 0,
    "source": sources.pick_one,
    "clear": sources.clear,
    "unload": dump.pick_line,
    "unload_ready": dump.picked,
    "has_wood": lambda: wood.in_pack() > 0,
    "unsold_ahead": None,
})

# The stop lands at the next Pause, so the lines until then read a form that was never answered
output = answers["output"] if answers is not None else "keep"
dump_at = answers["dump_at"] if answers is not None else DUMP_AT
log.enabled = answers["debug_logs"] if answers is not None else False

if answers is None:
    API.Stop()

# The radio, not the cursor: a container picked before switching to Keep stays unused
unloading = output == "unload"

if unloading:
    log("unloading every %d products" % dump_at)
else:
    log("keeping what is made - the run ends once the pack holds %d products" % MAX_HELD)

# A picked tool container fills an empty pack before the first craft
if (tools.find(FETCH_TIMEOUT, FETCH_POLL) is None
        and not (tool_store.picked() and tool_store.fetch())):
    log("no carpentry tools in the pack")
    API.Stop()

log("%s at %s%s, %s in the pack, %s"
    % (skill_name, reading(start), "/%.1f" % cap if cap is not None and cap > 0 else "",
       wood.pack_report(), sources.stock_line()))

if wood.in_pack() < RESTOCK_AT:
    restock.run()

recorder = attempt_log(DATA_PATH, skill_name, log)
materials = Materials(wood, MATERIAL_GRAPHICS)
craft_recorder = CraftRecorder(recorder, materials, REFUND_SETTLE, REFUND_POLL)
unloader = Unloader(dump)

stop = None
tally = 0
fails = 0
unknown = 0
throttled = 0
no_tool = 0
no_material = 0
throttle_tally = 0
said_throttle = False
reported = 0
cycle = 0
product = None
last_skill = start


# A pack the shard will not load for weight is unloaded first, when there is anything in it to move
def try_make_room():
    return make_room(restock, log, "wood", unload=(lambda: unloading, dump.held, unloader.run))


def out_of_wood():
    return ("out of %s wood - %s in the pack, none left in what you picked, and one %s takes %d"
            % (WOOD_TYPE, wood.pack_report(), product, wood_cost(product)))


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
            stop = end_cycle(stall, "saving", cycle, tally, stop)
            continue

        value = skill.read()

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

        held = dump.held()

        if unloading and held >= dump_at:
            if unloader.run():
                stop = end_cycle(stall, "unloading", cycle, tally, stop)
                continue

            if unloader.misses >= MAX_DUMP_MISSES:
                stop = ("%d unloads in a row moved nothing into '%s'"
                        % (unloader.misses, dump.name()))
                break
        elif not unloading and held >= MAX_HELD:
            stop = "the pack holds %d products and nothing was picked to unload into" % held
            break

        if wood.in_pack() < RESTOCK_AT:
            # An unreachable container also pulls nothing, which the stall watch ends
            pulled = restock.run()

            phase = try_make_room()

            if phase is not None:
                stop = end_cycle(stall, phase, cycle, tally, stop)
                continue

            if pulled == 0 and sources.stock_left() == 0 and wood_short(product) > 0:
                stop = out_of_wood()
                break

            # A short pack that can still make something crafts
            if wood_short(product) > 0:
                stop = end_cycle(stall, "restocking", cycle, tally, stop)
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

            craft_recorder.record(outcome, value, spent_before, product)
            no_material = 0
            stall.progressed()
        elif outcome == "noMaterial":
            pulled = restock.run()

            phase = try_make_room()

            if phase is not None:
                stop = end_cycle(stall, phase, cycle, tally, stop)
                continue

            if pulled > 0:
                no_material = 0
                stall.progressed()
            elif wood_short(product) > 0 and sources.stock_left() == 0:
                stop = out_of_wood()
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
            log("the tool wore out, looking for another")
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s at %s" % (product, reading(value))
            break
        elif outcome == "noRow":
            stop = "could not find the SELECTIONS row for '%s'" % product
            break
        elif outcome == "noTool" and tool_store.picked() and tool_store.fetch():
            crafter.forget_last()
            stall.progressed()
            log("the tools ran out - fetched another")
        elif outcome in ("noTool", "noGump"):
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = ("no carpentry tools left" if outcome == "noTool"
                        else "the craft menu will not open")
                break

            log("%s (%d/%d), trying again"
                % ("no carpentry tools in the pack" if outcome == "noTool"
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
                   wood.report(wood.pack_stock()))
            )

        stop = end_cycle(stall, outcome if outcome is not None else "unknown", cycle, tally, stop)
        API.Pause(STEP_DELAY)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error
finally:
    recorder.close(skill.last())

if API.Pathfinding():
    API.CancelPathfinding()

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES
ended = skill.read()

log(
    "%d made, %d failed, %d throttled, %s %.1f -> %s"
    % (tally, fails, throttle_tally, skill_name, start, reading(ended))
)
log("stopping - %s" % reason)
API.Stop()
