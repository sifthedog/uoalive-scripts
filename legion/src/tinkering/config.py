from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT
from uo.timings import (HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STALL_STOP, STALL_WARN,
                        STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

# One JSON object per attempt, for legion/skilldb.py. "" turns recording off. A bare name lands
# beside the script, in LegionScripts.
DATA_PATH = "skill-attempts.jsonl"

SKILL_NAMES = ["Tinkering"]

MIN_SKILL = 20.0

# Ceilings are exclusive, in the client's float percentage
BANDS = [
    (30.0, "iron key"),
    (40.0, "hammer"),
    (45.0, "tongs"),
    (95.0, "lockpick"),
    (111.8, "ring"),
    (None, "fancy wind chimes"),
]

# The CATEGORIES rows, lowercased: where the group block ends and the item rows begin
CATEGORY_NAMES = ["wooden items", "tools", "parts", "utensils", "misc", "miscellaneous", "jewelry",
                  "multi-component items", "assemblies", "traps", "magic jewelry"]

# Name as the SELECTIONS row spells it, and the graphics it lands in the pack as. Iron key and
# hammer are read off UOAlive; the rest are stock art.
PRODUCTS = {
    "iron key": set([0x1010]),
    "hammer": set([0x102A]),
    "tongs": set([0x0FBB, 0x0FBC]),
    "lockpick": set([0x14FC]),
    "ring": set([0x108A]),
    "fancy wind chimes": set([0x2833]),
}

PRODUCT_GRAPHICS = set().union(*PRODUCTS.values())

# Ingots per craft, from the stock recipes. The pack is measured either side of a craft regardless;
# this only decides when the pack is too short to try.
INGOT_COST = {
    "iron key": 3,
    "hammer": 1,
    "tongs": 1,
    "lockpick": 1,
    "ring": 3,
    "fancy wind chimes": 15,
}

# For a product INGOT_COST lacks
MIN_CRAFT_INGOTS = 1

# Stock art, unverified on UOAlive: an art learned by name joins the set
TOOL_GRAPHICS = set([0x1EB8, 0x1EB9])
TOOL_NAME_WORDS = ["tinker", "tinkers"]

INGOT_GRAPHICS = set([0x1BEF, 0x1BF2])
INGOT_NAME_WORDS = ["ingot", "ingots"]

STOCK_KINDS = [("ingots", INGOT_GRAPHICS, INGOT_NAME_WORDS)]

# The only ingot spent or counted. Leave the menu's material on it.
IRON = "iron"

# For the stack whose tooltip has not arrived, and to name what is set aside. A hue not in here is
# reported as unknown, never treated as iron.
INGOT_HUES = {
    0: IRON,
    0x973: "dull copper",
    0x966: "shadow iron",
    0x96D: "copper",
    0x972: "bronze",
    0x8A5: "gold",
    0x979: "agapite",
    0x89F: "verite",
    0x8AB: "valorite",
}

INGOT_TYPES = sorted(set(INGOT_HUES.values()))

# Nothing but ingots goes into these six, so only the ingots are measured for the consumed rows
MATERIAL_GRAPHICS = set()

# Counted as amounts
SELL_AT = 10

TINKER_TITLES = ["tinker"]

# Who buys each band's product: the noun for the log, and the titles matched against the name and
# the tooltip. Stand near the right one for the band. None when nobody buys it - a tinker refused
# the wind chimes - and it is unloaded into the container picked at the start instead.
VENDORS = {
    "iron key": ("tinker", TINKER_TITLES),
    "hammer": ("tinker", TINKER_TITLES),
    "tongs": ("blacksmith or tinker", ["blacksmith", "tinker"]),
    "lockpick": ("provisioner", ["provisioner"]),
    "ring": ("jeweler", ["jeweler", "jeweller"]),
    "fancy wind chimes": None,
}

# Answered by the gump at the start; ESC on the unload cursor and a closed gump both mean keep. Sell
# still asks for the container once a band nobody buys from is ahead.
OUTPUT_CHOICE = {
    "text": "Sell what is made to the vendor that buys it, unload it into a container, or keep it?",
    "hue": 996,
    "poll": 0.5,
    "timeout": 60.0,
}
OUTPUT_OPTIONS = [("sell", "Sell"), ("unload", "Unload"), ("keep", "Keep")]

# Products the run made, counted as amounts, before they are unloaded: every band under Unload, the
# unsold ones under Sell
DUMP_AT = 10

# Keeping them, or selling with nowhere to put the unsold, the run ends once the pack holds this many
MAX_HELD = 60

# Unloads in a row that moved nothing before the run ends
MAX_DUMP_MISSES = 3

PICK_TIMEOUT = 60.0
OPEN_DELAY = 0.6
CONTAINER_RANGE = 2

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

CRAFT_TITLE = "TINKERING"

# Only ever to *recognise* a gump, never to refuse one: the header is a cliloc, and a build whose
# GetGumpContents answers nothing for it made every craft read as 'no craft menu'
CRAFT_TITLE_TEXT = [CRAFT_TITLE, "TINKER"]
CRAFT_TITLE_FRAGMENTS = [phrase.lower() for phrase in CRAFT_TITLE_TEXT]

# Its own button rather than a group, so it does not count toward the category index
LAST_TEN_LABEL = "LAST TEN"

# Buttons are 1 + type + index * 20, as bowcraft found on this shard's menu; MAKE LAST is assumed to
# sit where it does there
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MAKE_LAST_BUTTON = 47

# (category button, row button), from the 'is the row on button' log lines. Item buttons count on
# across the pages, ten rows a page: Misc's second page, third row, is index 12
RECIPES = {
    "fancy wind chimes": (101, 242),
}

MAX_CATEGORIES = 10

# The stock Tools group runs past twenty rows and the item buttons count across its pages
MAX_ITEM_ROWS = 24

# Each miss costs one item's worth of ingots, which is why the gump text is read first
MAX_ITEM_PROBES = 8

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

MOVE_DELAY = 0.7

SELL_TIMEOUT = 15.0
SELL_POLL = 0.5

SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25

MAX_CYCLES = 20000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_TOOL = 10

# Sell trips in a row that bought nothing before the trips pause. Never ends the run.
MAX_SELL_MISSES = 3
SELL_RETRY_AFTER = 25

# Refusals for material while the pack holds enough iron: the menu is set to another metal
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
            "You do not have sufficient metal",
            "You don't have the resources",
            "You do not have the resources",
            "not enough ingots",
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
