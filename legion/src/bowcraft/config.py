from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT
from uo.timings import (HEARTBEAT_EVERY, LOG_EVERY, PACK_LIMIT, SAVE_POLL, SAVE_WAIT, STALL_STOP,
                        STALL_WARN, STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

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
