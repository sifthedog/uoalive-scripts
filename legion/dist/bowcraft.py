# Built from src/bowcraft/index.py by build.py - do not edit.

import API
import time


# src/bowcraft/bands.py
# GetSkill answers None for a name it does not know, and a name the client does not carry throws
# rather than answering None on some builds
def find_skill_name(names):
    for name in names:
        try:
            if API.GetSkill(name) is not None:
                return name
        except Exception:
            continue

    return None


# The first row whose ceiling the value is under wins, so the ceilings are exclusive
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

# The item cap is per container
PACK_LIMIT = 120


# src/bowcraft/config.py
# GetSkill answers None for a name it does not know, so the shard's wording is found rather than
# asserted - the gump calls it "Bowcraft/Fletching" and the skill list may not
SKILL_NAMES = ["Bowcraft", "Bowcraft/Fletching", "Fletching"]

MIN_SKILL = 30.0

# The two bands that offer a choice. Flip these to "fukiya darts" and "yumi" without touching BANDS.
LOW_BAND_ITEM = "bow"
HIGH_BAND_ITEM = "repeating crossbow"

# The first row whose ceiling the value is under wins, so the ceilings are exclusive. Value is a
# float percentage here - the src/training tables are in the client's tenths and would be 10x out.
BANDS = [
    (60.0, LOW_BAND_ITEM),
    (70.0, "crossbow"),
    (80.0, "composite bow"),
    (90.0, "heavy crossbow"),
    (None, HIGH_BAND_ITEM),
]

# The CATEGORIES rows, lowercased. Only used to find where the group block ends and the item rows
# begin in the gump text.
CATEGORY_NAMES = ["materials", "ammunition", "weapons"]

# Name as the SELECTIONS row spells it, and the graphics it arrives in the pack as. The graphics are
# what proves a craft landed on the right row, and what the sell counter counts.
PRODUCTS = {
    "bow": set([0x13B2]),
    "crossbow": set([0x0F50]),
    "composite bow": set([0x26C2]),
    "heavy crossbow": set([0x13FD]),
    "repeating crossbow": set([0x26C3]),
    "yumi": set([0x27A5]),
    "fukiya darts": set([0x2806]),
}

PRODUCT_GRAPHICS = set()

for _product in PRODUCTS:
    PRODUCT_GRAPHICS.update(PRODUCTS[_product])

TOOL_GRAPHICS = set([0x1022])
TOOL_NAME_WORDS = ["fletcher", "fletchers"]

# A stack's graphic changes with its size, so match a set rather than one graphic. Hue is
# deliberately not part of the match: a shard with special woods hues them, and those craft too.
LOG_GRAPHICS = set([0x1BDD, 0x1BE0, 0x1BDE, 0x1BDF])
LOG_NAME_WORDS = ["log", "logs"]

# Boards are wood as far as this run is concerned: the menu takes them, and the lumberjack run
# brings boards home rather than logs because they weigh less for the same craft.
BOARD_GRAPHICS = set([0x1BD7, 0x1BD9, 0x1BDA, 0x1BDB])
BOARD_NAME_WORDS = ["board", "boards"]

# Counted as one pool, reported apart. A shard that turns out to craft from only one of the two says
# which kind is sitting in the pack being refused, rather than stalling on a full pack.
WOOD_KINDS = [
    ("logs", LOG_GRAPHICS, LOG_NAME_WORDS),
    ("boards", BOARD_GRAPHICS, BOARD_NAME_WORDS),
]

REGULAR_WOOD = "regular"

# The named woods, read straight off the tooltip: '74 Oak Boards' is oak, and '1580 Boards' with no
# word in front of it is regular. Each is its own resource to the craft menu, which spends the one it
# is set to and refuses every other - a pack full of oak is a pack full of nothing, as far as a menu
# set to regular is concerned.
WOOD_TYPES = ["oak", "ash", "yew", "heartwood", "bloodwood", "frostwood"]

# What the menu is set to, and so what a restock pulls and what counts as stock. Set it to one of
# WOOD_TYPES to work that wood instead, and set the menu to match by hand.
WOOD_TYPE = REGULAR_WOOD

# Hue to wood, for the stack whose tooltip has not arrived - the name is the first thing read, and
# this is what answers when there is no name yet. Incomplete on purpose: these were read off this
# shard, and the log's 'the pack holds ... hue 0x...' line is where the missing ones come from. A
# colour that is in neither table is not treated as regular, whatever else it might be.
WOOD_HUES = {
    0: REGULAR_WOOD,
    1191: "ash",
    2010: "oak",
}

# Wood of the wrong type is weight and nothing else. Off leaves it in the pack.
RETURN_WRONG_WOOD = True

# Above the largest recipe, so a craft never refuses for wood the run thinks it still has. What is
# actually pulled is the smaller of this and what the weight has room for.
BATCH_SIZE = 300
RESTOCK_AT = 25

# What one wood weighs, and only a starting guess: it is learned from the first move that shifts any,
# because a board and a log do not weigh the same and a shard can change either. Pulling a batch
# without it is what put a run at 400/386 in one move.
WOOD_WEIGHT = 1.0

# Counted as amounts, so fukiya darts - which stack ten to a craft - reach this in three crafts.
# Raise it if you run the darts band.
SELL_AT = 20

# Matched against the name *and* the tooltip: a shopkeeper is named "Alger" and titled "the bowyer",
# and only the tooltip carries the title. Matching the name alone found no vendor to sell to.
BOWYER_TITLES = ["bowyer", "fletcher", "archer", "bowyers", "fletchers"]
# Tried before the phrase, and matched against the menu's own text so no entry index is guessed. The
# menu wants you next to the vendor, which is where the run should be standing anyway.
SELL_ENTRY = "sell"
SELL_PHRASE = "vendor sell"

VENDOR_SCAN_RADIUS = 18

# Adjacent. Two tiles away is heard on some shards and not on others, and the context menu is
# refused outright - a sell trip that stopped short is a sell trip that did nothing.
VENDOR_RANGE = 1

# Walks at the vendor before giving up on reaching it. More than one because a pathfind that ends
# early, a doorway and a vendor that stepped aside all look the same from here.
VENDOR_STEPS = 3

CONTEXT_TIMEOUT = 3.0

# Set this to a vendor's serial to skip the search entirely
VENDOR_SERIAL = None

# How long the tooltips have to arrive once they have been asked for
OPL_WAIT = 1.0

# A backstop only - the selection ends when you press ESC
MAX_PICKS = 8

CONTAINER_RANGE = 2

CRAFT_TITLE = "BOWCRAFT AND FLETCHING"

# Any one of them, matched case-insensitively, and only ever to *recognise* a gump - never to refuse
# one. The header is a cliloc the client resolves, and a build whose GetGumpContents answers nothing
# for it made every craft read as 'no craft menu'.
CRAFT_TITLE_TEXT = [CRAFT_TITLE, "BOWCRAFT", "FLETCHING"]
CRAFT_TITLE_FRAGMENTS = [phrase.lower() for phrase in CRAFT_TITLE_TEXT]

# Its own button rather than a group, so it does not count toward the category index
LAST_TEN_LABEL = "LAST TEN"

# This gump numbers its buttons 1 + type + index * 20: categories are type 0 (1, 21, 41), the arrow
# on a SELECTIONS row is type 1 (2, 22, 42, ...), and the fixed buttons sit where this shard puts
# them. Read off a working script for this shard. The stock 7-step numbering this file used to
# assume put MAKE LAST on 21, which is the Ammunition category - so every craft pressed a category.
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MAKE_LAST_BUTTON = 47

# (category button, row button) for the rows this menu is known to carry, so the common products
# cost no probing at all. A product that is not here, or a row this table gets wrong, is found by
# walking the categories exactly as before - the pack is what settles it either way.
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

# Crafts spent finding the right SELECTIONS row when the gump text does not name it. Each miss costs
# one item's worth of wood, which is why the text is read first.
MAX_ITEM_PROBES = 8

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms
PICK_TIMEOUT = 60.0

# Whole seconds: the API takes an int here where API.Pause takes a float
PATHFIND_TIMEOUT = 10

GUMP_TIMEOUT = 5.0
GUMP_POLL = 0.15

# A craft plays its animation before the shard answers, so this has to outlast the animation
CRAFT_TIMEOUT = 10.0
CRAFT_POLL = 0.2

# How long the pack has to show the new item once the shard has answered
CRAFT_SETTLE = 1.5

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

# Sell trips in a row that bought nothing before the run stops trying for a while. It never ends the
# run: crafting is what takes weight off a pack nothing will buy from.
MAX_SELL_MISSES = 3
SELL_RETRY_AFTER = 25

# The largest recipe in BANDS. Under this there is nothing the run can make, which is the only thing
# that makes a short pack worth another restock cycle rather than a craft.
MIN_CRAFT_WOOD = 10

# Refusals for material while the pack still holds wood a restock cannot add to. One is the shard
# and the run disagreeing about a stack; this many in a row is the wrong kind of wood.
MAX_NO_MATERIAL = 3

# What an unreadable outcome reports before it goes quiet again, and how much of it. Without this
# the one wording that would fix OUTCOME_TEXT is the one thing nothing ever prints.
MAX_UNREADABLE_REPORTS = 2
UNREADABLE_TEXT_LIMIT = 160
JOURNAL_TAIL_SECONDS = 20.0
JOURNAL_TAIL_LINES = 4

# The shard's own pacing, counted rather than narrated: a line per throttle would outnumber the
# progress lines, and a wait nobody can see is what makes a working run look hung.
SAY_THROTTLE_ONCE = True

# Buffer, so the sell trip lands before the shard starts refusing to move the next batch of wood
WEIGHT_BUFFER = 40

# Ordered, not a dict: the buckets are polled in order and the first holding a match wins. 'failed'
# is declared before 'made' because "You failed to create the item" contains "create the item".
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
    # The gump says this in its NOTICES panel and the journal may never carry it, which is why the
    # outcome is read from both
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

    # False is the client saying the gump was gone before the button was pressed, which is a
    # different fact from the page not coming back and is worth not waiting out the timeout for
    def press(self, button, gump, timeout):
        if not API.ReplyGump(button, gump):
            return 0

        found = await_any(timeout, self._config["gump_poll"])

        # Only ever the craft menu presses buttons here, so whatever answered is the next page
        if found:
            self._id = found

        return found

    def is_craft_gump(self, ident):
        if not ident:
            return False

        if any_in(API.GetGumpContents(ident) or "", self._config["title_fragments"]):
            return True

        # The client's own search gets a turn: it reads controls GetGumpContents may not put in text
        for phrase in self._config["title_text"]:
            if API.GumpContains(phrase, ident):
                return True

        return False

    def lines(self, gump):
        text = API.GetGumpContents(gump)

        return [line.strip() for line in (text or "").split("\n") if line.strip()]

    def open(self):
        found = API.HasGump()

        # The one already being driven, or one that names itself
        if found and (found == self._id or self.is_craft_gump(found)):
            self._id = found

            return found

        serial = self._tools.serial()

        if serial is None:
            return None

        # Any other server gump has to go first: the wait below is for a gump to be *there*, and a
        # vendor's or a status gump standing open answers it before the tools have opened anything
        if found:
            self._log("closing the gump that is in the way %s" % hex_of(found))
            API.CloseGump(found)
            API.Pause(self._config["gump_poll"])

        API.UseObject(serial)

        found = await_any(self._config["gump_timeout"], self._config["gump_poll"])

        if not found:
            return None

        # Whatever the tools opened is the menu. The title is not a gate - it is a cliloc the client
        # resolves, and refusing a gump over it is what made a working craft menu read as no menu.
        if not self._said_gump_text and not self.is_craft_gump(found):
            self._said_gump_text = True
            lines = self.lines(found)
            self._log("the tools opened a gump that does not name %s - it starts '%s'"
                      % (self._config["title"], lines[0] if lines else "(no text)"))

        self._id = found

        return found

    # The stock gump emits the group rows before the item rows, so everything past the last group
    # name is this page's SELECTIONS. A shard that emits them the other way round leaves this empty.
    def item_rows(self, gump):
        lines = self.lines(gump)
        start = None

        for index in range(len(lines)):
            if (lines[index].lower() in self._config["category_names"]
                    or lines[index].upper() == self._config["last_ten_label"]):
                start = index + 1

        return [] if start is None else lines[start:]

    # A whole row, never a substring: "crossbow" is inside "crossbow bolt", so a substring match
    # finds the wanted item in the Ammunition category and never reaches Weapons at all
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

    # Pressing a category only redraws the SELECTIONS panel, so walking them costs nothing - which
    # is why the category is found this way and the row below is not
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

            # A category that answered nothing says nothing about the category, so the caller
            # retries rather than ending the run over it
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

    # The text is read first and only falls back to walking the rows, because unlike a category a
    # wrong row here crafts the wrong item and spends the wood for it
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
    """What in the pack is wood, which wood it is, and how much of it the menu will actually spend."""

    def __init__(self, config, log):
        self._kinds = config["kinds"]
        self._types = config["types"]
        self._hues = config["hues"]
        self._wanted = config["wanted"]
        self._move_delay = config["move_delay"]
        self._log = log

    # Graphic first across every kind, name second: names are empty until the client has tooltip
    # data, and an art learned by name joins its kind's set, so it costs one name read and no more.
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

    # The name first, because that is where the shard writes it. A name that has not arrived leaves
    # the hue: plain is regular, coloured is a wood this table has no word for, neither is guessed.
    def type_of(self, item):
        for wood in self._types:
            if word_in(item.Name, [wood]):
                return wood

        return self._hues.get(hue_of(item))

    def usable(self, item):
        return self.is_wood(item) and self.type_of(item) == self._wanted

    def wrong(self, item):
        return self.is_wood(item) and self.type_of(item) != self._wanted

    # Only what the menu will spend. Wood of another type is not stock, however much of it there is
    # - counting it is what let a run sit on 300 oak boards reporting a full pack and crafting none.
    def counts(self, items):
        counts = {}

        for item in items:
            if not self.usable(item):
                continue

            kind = self.kind_of(item)
            counts[kind] = counts.get(kind, 0) + amount_of(item)

        return counts

    # The rest of the wood, by the name the shard gives it, so a pack that reads as empty says why
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

    # In kind order, so two runs of the same pack read the same
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

    # What the pack holds, in one phrase: what the menu will spend, and what it will not
    def pack_report(self):
        text = self.report(self.pack_wood())
        other = self.other_report(self.pack_other())

        return text if not other else "%s (%s set aside)" % (text, other)

    # Hue is what tells one wood from another - oak, ash, yew and heartwood are all 'boards' by name
    # and graphic, and the menu spends only the one it is set to
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

    # Wood in a bag inside the pack is wood the craft may not reach, and it is nearer than a source
    def _nested(self):
        top = set(item.Serial for item in pack_top_level())
        piles = [item for item in pack_contents()
                 if item.Serial not in top and self.usable(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    # Moves inside the pack cost no weight, so this is free and always worth doing first
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


# src/uo/vitals.py
def weight_reading():
    me = player()

    return "?/?" if me is None else "%d/%d" % (me.Weight, me.WeightMax)


def where():
    me = player()

    return "somewhere" if me is None else "at %d,%d" % (me.X, me.Y)


def position_and_weight():
    return "%s, %s" % (where(), weight_reading())


# src/uo/weight.py
# Unknown is not overweight, the same call WeightMax == 0 gets: WeightMax reads 0 before the client
# has been told, against which every weight is overweight - a live mining run ended at 436/453 on it
def over_buffer(buffer):
    me = player()

    if me is None:
        return False

    ceiling = me.WeightMax

    return ceiling > 0 and me.Weight > ceiling - buffer


# src/bowcraft/restock.py
class Restock(object):
    def __init__(self, wood, sources, config, log):
        self._wood = wood
        self._sources = sources
        self._config = config
        self._log = log
        self._each = config["wood_weight"]

    def _carried(self):
        me = player()

        return None if me is None else me.Weight

    # None when the client has not said, which reads as no limit - the same call over_buffer makes
    def _room_for_wood(self):
        me = player()

        if me is None or me.WeightMax <= 0:
            return None

        return int((me.WeightMax - self._config["buffer"] - me.Weight) / max(self._each, 0.1))

    def _learn_weight(self, each):
        # Sanity: a move the client mis-timed can read as any weight at all
        if each < 0.1 or each > 50 or abs(each - self._each) < 0.05:
            return

        self._each = each
        self._log("one wood weighs %.1f here, pulling to fit" % each)

    # Wood of another type is weight and nothing else, and the container it came out of is open and
    # in reach at exactly this moment - which is the only moment putting it back costs nothing
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

    # Moves are asynchronous, so the pack is re-counted between them rather than MoveItem's return
    # value being trusted. A move that gains nothing enough times running is a container that is done.
    def run(self):
        # The pack is read before anything is fetched: what is already here, bags included, counts
        moved = self._wood.lift_from_bags()

        wanted = self._config["batch"] - self._wood.in_pack()

        if wanted <= 0:
            return moved

        buffer = self._config["buffer"]

        for entry in self._sources.picked():
            if moved >= wanted or over_buffer(buffer):
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

            while (moved < wanted and stalled < self._config["max_empty_moves"]
                   and not over_buffer(buffer)):
                piles = self._sources.container_wood(container)

                if len(piles) == 0:
                    break

                room = self._room_for_wood()
                take = min(wanted - moved, amount_of(piles[0]))

                if room is not None:
                    take = min(take, room)

                # Not a stall: there is wood there and no room for it, which the caller reports
                if take <= 0:
                    break

                before = self._wood.in_pack()
                heavy = self._carried()

                API.MoveItem(piles[0].Serial, API.Backpack, take)
                API.Pause(self._config["move_delay"])

                gained = self._wood.in_pack() - before

                if gained <= 0:
                    stalled += 1
                else:
                    stalled = 0
                    moved += gained

                    now = self._carried()

                    if heavy is not None and now is not None and now > heavy:
                        self._learn_weight((now - heavy) / float(gained))

        if moved > 0:
            self._log("pulled %d wood, %s in the pack, %d left in what you picked"
                      % (moved, self._wood.pack_report(), self._sources.stock_left()))

        if over_buffer(buffer) and moved < wanted:
            self._log("stopped short of the batch at %s" % weight_reading())

        return moved


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

    # The animal holds nothing itself - what is read and drawn from is the backpack it wears. Never
    # UseObject the animal to open that: on a rideable body a double-click mounts you, and nothing
    # in this script dismounts.
    def _animal_pack(self, serial):
        animal = API.FindMobile(serial)

        if animal is None:
            return None

        pack = getattr(animal, "Backpack", None)

        if pack is None:
            pack = API.FindLayer("backpack", serial)

        if pack is None:
            return None

        # A build that answers with the serial itself rather than the item is fine too
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

    # ItemsInContainer reads nothing out of a container the client has never seen inside, so a
    # source is opened before it is counted or drawn from
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

            # Falsy is ESC or a cursor that timed out, and either one ends the selection
            if not serial:
                break

            # Your own pack is where the wood is being counted from in the first place
            if serial == API.Backpack or (mine is not None and serial == mine):
                self._log("your own pack is always counted, no need to pick it")
                continue

            if serial in [entry["serial"] for entry in self._picked]:
                continue

            entry = self._entry_for(serial)

            # Not an ending: a misclick on the ground should cost the click and nothing more
            if entry is None:
                self._log("%s is neither a container nor a creature" % hex_of(serial))
                continue

            # Opened here, and the spot recorded now, because this is the one moment it is in reach
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

    # Only the type the menu is set to: pulling a pile of oak into a pack a regular menu will not
    # spend it from is the whole of what went wrong before
    def container_wood(self, serial):
        items = API.ItemsInContainer(serial, True)
        piles = [item for item in (items or []) if self._wood.usable(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def wood(self, entry):
        container = self.container_of(entry)

        return [] if container is None else self.container_wood(container)

    # Every wood in there, wrong type included, for the lines that report what a source is holding
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

    # Re-resolved rather than the picked entry trusted: a pathfind that ends early leaves you short
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

        # A container picked inside the pack has no world position worth walking to
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
            # Your own pets are the bulk of what stands around a crafter, and only yours rename
            if mobile.IsDead or mobile.Serial == mine or mobile.IsRenamable:
                continue

            found.append(mobile)

        return found

    # Name first because it costs nothing, tooltips second because they cost a round trip each: a
    # shopkeeper is "Alger" by name and "the bowyer" only in the tooltip, which is why the name pass
    # alone kept answering that there was no bowyer in sight.
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

    # Re-resolved every pass rather than the found mobile trusted: a pathfind that ends early leaves
    # you short, and the only way to know is to ask where the vendor is now.
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

    # The context menu first: it is the vendor's own 'Sell', matched by its text, and it does not
    # depend on the shard hearing a phrase. The phrase is still there for a menu with no such entry.
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

        # Never the bare form: it closes the last gump, which is as likely to be the craft menu
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
    "buffer": WEIGHT_BUFFER,
    "move_delay": MOVE_DELAY,
    "max_empty_moves": MAX_EMPTY_MOVES,
    "wood_weight": WOOD_WEIGHT,
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


def products_in_pack():
    return sum(amount_of(item) for item in pack_contents()
               if item.Graphic in PRODUCT_GRAPHICS)


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

# Nothing picked is only an ending when the pack is empty too: a run that starts on the wood it is
# already carrying is a run that needed no cursor at all
if len(sources.picked()) == 0 and wood.in_pack() == 0:
    log("nothing picked and no wood in the pack")
    API.Stop()

log("%s at %.1f, %s in the pack, %s" % (skill_name, start, wood.pack_report(),
                                        sources.stock_line()))

if wood.in_pack() < RESTOCK_AT:
    restock.run()

stop = None
tally = 0
fails = 0
unknown = 0
throttled = 0
no_tool = 0
no_material = 0
throttle_tally = 0
said_throttle = False
said_overweight = False
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


# Weight stops nothing here. It is reported when it starts and when it clears, and that is all: the
# run has no way to put the pack down that is not selling it, and it is already trying to sell.
def warn_overweight():
    global said_overweight

    if over_buffer(0):
        if not said_overweight:
            said_overweight = True
            log("overweight at %s - carrying on, crafting is what takes it off" % weight_reading())
    elif said_overweight:
        said_overweight = False
        log("no longer overweight, at %s" % weight_reading())


try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1

        stop = stop_reason()

        if stop is not None:
            break

        # Everything below reads a frozen shard as its own failure: a craft that answers nothing is
        # an unreadable outcome, a move that gains nothing is an empty container
        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
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

        # Weight is never an ending. Said once a stretch, because a run that cannot sell can still
        # craft, and every craft turns wood the pack is carrying into one lighter item.
        warn_overweight()

        wants_sale = (
            products_in_pack() >= SELL_AT
            or over_buffer(WEIGHT_BUFFER)
            or len(pack_top_level()) >= PACK_LIMIT
        )

        if wants_sale and cycle >= sell_paused_until:
            if vendor.sell_trip():
                sell_misses = 0

                end_cycle("selling")
                continue

            sell_misses += 1

            # The trip is worth retrying, but not every cycle for ever: without this it walks to the
            # vendor and back on each pass and the crafting never gets a turn
            if sell_misses >= MAX_SELL_MISSES:
                sell_misses = 0
                sell_paused_until = cycle + SELL_RETRY_AFTER
                log("%d sell trips bought nothing - crafting on, and asking again in %d cycles"
                    % (MAX_SELL_MISSES, SELL_RETRY_AFTER))

        if wood.in_pack() < RESTOCK_AT:
            # Weight and an unreachable container also pull nothing, and neither is an empty
            # container - the stall watch is what ends those
            pulled = restock.run()

            if pulled == 0 and sources.stock_left() == 0 and wood.in_pack() < MIN_CRAFT_WOOD:
                stop = ("out of %s wood - %s in the pack, none left in what you picked"
                        % (WOOD_TYPE, wood.pack_report()))
                break

            # Only a pack with nothing makeable in it is worth spending the cycle on: a short pack
            # that can still make something crafts, which is also what takes weight off
            if wood.in_pack() < MIN_CRAFT_WOOD:
                end_cycle("restocking")
                continue

        outcome = crafter.craft_once(product)

        if outcome == "made":
            tally += 1
            unknown = 0
            throttled = 0
            no_material = 0
            stall.progressed()
        elif outcome == "failed":
            # Still a gain and still spends the wood, so it counts as the loop getting somewhere
            fails += 1
            unknown = 0
            throttled = 0
            no_material = 0
            stall.progressed()
        elif outcome == "noMaterial":
            unknown = 0
            pulled = restock.run()

            if pulled > 0:
                no_material = 0
                stall.progressed()
            elif wood.in_pack() < RESTOCK_AT and sources.stock_left() == 0:
                stop = "the shard says there is not enough wood and there is none left to pull"
                break
            else:
                # Wood in the pack that a restock cannot add to, refused all the same: what a shard
                # that crafts from only one of logs and boards looks like from in here
                no_material += 1

                if no_material >= MAX_NO_MATERIAL:
                    stop = ("the shard refused %s in the pack %d times - read the gump's own words "
                            "above; if it wants another wood, set WOOD_TYPE and the menu to match"
                            % (wood.pack_report(), no_material))
                    break
        elif outcome == "wrongRow":
            unknown = 0
            stall.progressed()
        elif outcome == "toolWorn":
            crafter.forget_last()
            unknown = 0
            stall.progressed()
            log("the tools wore out, looking for another pair")
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s at %s" % (product, reading(value))
            break
        elif outcome == "noRow":
            stop = "could not find the SELECTIONS row for '%s'" % product
            break
        elif outcome == "noTool" or outcome == "noGump":
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

            # Said once, then only tallied: the pause itself is the shard's, and it is normal
            if SAY_THROTTLE_ONCE and not said_throttle:
                said_throttle = True
                log("the shard is pacing the crafts - waiting %.1fs, and counting these from here on"
                    % waiting)

            API.Pause(waiting)
        elif outcome == "saving":
            unknown = 0
            stall.progressed()
        else:
            unknown += 1
            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        if outcome != "noTool" and outcome != "noGump":
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

log(
    "%d made, %d failed, %d throttled, %s %.1f -> %s"
    % (tally, fails, throttle_tally, skill_name, start, reading(ended))
)
log("stopping - %s" % reason)
API.Stop()
