from uo.boxes import WOOD_BOX
from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT
from uo.timings import (HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STALL_STOP, STALL_WARN,
                        STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

# One JSON object per attempt, for legion/skilldb.py. "" turns recording off. A bare name lands in
# TazUO's working directory, not beside the script.
DATA_PATH = "skill-attempts.jsonl"

SKILL_NAMES = ["Carpentry"]

MIN_SKILL = 0.0

# Ceilings are exclusive, in the client's float percentage. Each is the row's minimum plus 25,
# where the stock recipe stops gaining; the cheapest recipe still under that is the row.
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
    "dark wooden sign hanger": DEED_GRAPHICS,
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

PRODUCT_GRAPHICS = set().union(*PRODUCTS.values())

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
RESTOCK_AT = 40

# Products in the pack, counted as amounts, before they are unloaded
DUMP_AT = 10

# With nothing picked to unload into, the run ends once the pack holds this many products
MAX_HELD = 60

# Unloads in a row that moved nothing before the run ends
MAX_DUMP_MISSES = 3

# A backstop only - the selection ends when you press ESC
MAX_PICKS = 8

CONTAINER_RANGE = 2

CRAFT_TITLE = "CARPENTRY"

# Only ever to *recognise* a gump, never to refuse one: the header is a cliloc, and a build whose
# GetGumpContents answers nothing for it made every craft read as 'no craft menu'
CRAFT_TITLE_TEXT = [CRAFT_TITLE, "CARPENTER"]
CRAFT_TITLE_FRAGMENTS = [phrase.lower() for phrase in CRAFT_TITLE_TEXT]

# Its own button rather than a group, so it does not count toward the category index
LAST_TEN_LABEL = "LAST TEN"

# Buttons are 1 + type + index * 20, as bowcraft found on this shard's menu; MAKE LAST is assumed to
# sit where it does there
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MAKE_LAST_BUTTON = 47

# (category button, row button). Empty on purpose: the walk finds each row and logs its button, and
# a guessed table mis-presses on a shard whose rows are in another order. Copy the log lines in here.
RECIPES = {}

MAX_CATEGORIES = 12

# Furniture and the add-ons run to forty rows, and the item buttons count across the pages
MAX_ITEM_ROWS = 48

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
