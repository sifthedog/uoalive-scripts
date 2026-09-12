from uo.boxes import WOOD_BOX
from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT
from uo.timings import (HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STALL_STOP, STALL_WARN,
                        STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

# One JSON object per attempt, for legion/skilldb.py. "" turns recording off. A bare name lands in
# TazUO's working directory, not beside the script.
DATA_PATH = "skill-attempts.jsonl"

# GetSkill answers None for a name it does not know: the gump says "Bowcraft/Fletching", the skill
# list may not
SKILL_NAMES = ["Bowcraft", "Bowcraft/Fletching", "Fletching"]

MIN_SKILL = 30.0

# The two bands that offer a choice: "fukiya darts" and "yumi" are the other way
LOW_BAND_ITEM = "bow"
HIGH_BAND_ITEM = "yumi"

# Ceilings are exclusive, in the client's float percentage - the src/training tables are in tenths
BANDS = [
    (60.0, LOW_BAND_ITEM),
    (70.0, "crossbow"),
    (80.0, "composite bow"),
    (90.0, "heavy crossbow"),
    (100.0, "repeating crossbow"),
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

# The shard's storage box, picked at the cursor beside chests and pack animals
BOX = WOOD_BOX

# What one restock draws from the box, in presses of 100
BOX_TAKE = 200

# How long the pack has to show a row's boards after the press, and how often it is read
BOX_PRESS_TIMEOUT = 3.0
BOX_PRESS_POLL = 0.25

# Answered by the gump at the start; a closed gump means chests and pack animals, as before the box
SOURCE_CHOICE = {
    "text": "Draw wood from the storage box, or from the chests and pack animals you point at?",
    "hue": 996,
    "poll": 0.5,
    "timeout": 60.0,
}
SOURCE_OPTIONS = [("box", "Storage box"), ("containers", "Chests and animals")]

# Every restock fills the pack to this
BATCH_SIZE = 300
RESTOCK_AT = 25

# Counted as amounts, as DUMP_AT is: fukiya darts stack ten to a craft, so raise both for that band
SELL_AT = 10

# Matched against the name *and* the tooltip: "Alger" is "the bowyer" only in the tooltip
BOWYER_TITLES = ["bowyer", "fletcher", "archer", "bowyers", "fletchers"]

# Who buys each band's product: the noun for the log, and the titles matched against the name and
# the tooltip. None when nobody buys it - the bowyer refuses a yumi - and it is unloaded instead.
VENDORS = {
    "bow": ("bowyer", BOWYER_TITLES),
    "crossbow": ("bowyer", BOWYER_TITLES),
    "composite bow": ("bowyer", BOWYER_TITLES),
    "heavy crossbow": ("bowyer", BOWYER_TITLES),
    "repeating crossbow": ("bowyer", BOWYER_TITLES),
    "fukiya darts": ("bowyer", BOWYER_TITLES),
    "yumi": None,
}

# Answered by the gump at the start; ESC on the unload cursor and a closed gump both mean keep. Sell
# still asks for the container once a band nobody buys from is ahead.
OUTPUT_CHOICE = {
    "text": "Sell what is made to the bowyer, unload it into a container, or keep it?",
    "hue": 996,
    "poll": 0.5,
    "timeout": 60.0,
}
OUTPUT_OPTIONS = [("sell", "Sell"), ("unload", "Unload"), ("keep", "Keep")]

# Products the run made before they are unloaded: every band under Unload, the unsold under Sell
DUMP_AT = 10

# Keeping them, or selling with nowhere to put the unsold, the run ends once the pack holds this many
MAX_HELD = 60

# Unloads in a row that moved nothing before the run ends
MAX_DUMP_MISSES = 3

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

# The shard refusing a move for weight. With products in the pack the run sells before it loads.
TOO_HEAVY_TEXT = ["That container cannot hold more weight"]

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
