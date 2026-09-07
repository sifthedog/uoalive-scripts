from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT
from uo.timings import (HEARTBEAT_EVERY, SAVE_POLL, SAVE_WAIT, STALL_STOP, STALL_WARN, STEP_DELAY,
                        THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

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
