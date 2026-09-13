from uo.boxes import WOOD_BOX
from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT
from uo.timings import (HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STALL_STOP, STALL_WARN,
                        STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

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
    (None, "small display case (south)"),
]

# The CATEGORIES rows, lowercased, as craft-map.py read them off UOAlive's menu
CATEGORY_NAMES = [
    "other",
    "furniture",
    "containers",
    "weapons",
    "armor",
    "instruments",
    "misc. add-ons",
    "tailoring and cooking",
    "anvils and forges",
    "training",
]

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
    "small display case (south)": DEED_GRAPHICS,
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
    "small display case (south)": 40,
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

# (category button, row button) for every row, as craft-map.py read them off UOAlive's menu. Each
# is checked against the label the menu draws on that button before it is pressed, so a row that
# moves is walked for, not mis-pressed. Run craft-map.py again and paste its block over this one.
RECIPES = {
    # Other (button 1)
    "barrel staves": (1, 2),
    "barrel lid": (1, 22),
    "short music stand (left)": (1, 42),
    "short music stand (right)": (1, 62),
    "tall music stand (left)": (1, 82),
    "tall music stand (right)": (1, 102),
    "easel (south)": (1, 122),
    "easel (east)": (1, 142),
    "easel (north)": (1, 162),
    "red hanging lantern": (1, 182),
    "white hanging lantern": (1, 202),
    "shoji screen": (1, 222),
    "bamboo screen": (1, 242),
    "fishing pole": (1, 262),
    "wooden container engraving tool": (1, 282),
    "runed switch": (1, 302),
    "arcanist statue (south)": (1, 322),
    "arcanist statue (east)": (1, 342),
    "warrior statue (south)": (1, 362),
    "warrior statue (east)": (1, 382),
    "squirrel statue (south)": (1, 402),
    "squirrel statue (east)": (1, 422),
    "giant replica acorn": (1, 442),
    "mounted dread horn": (1, 462),
    "acid proof rope": (1, 482),
    "gargish banner": (1, 502),
    "an incubator": (1, 522),
    "a chicken coop": (1, 542),
    "exodus summoning altar": (1, 562),
    "dark wooden sign hanger": (1, 582),
    "light wooden sign hanger": (1, 602),
    # Furniture (button 21)
    "foot stool": (21, 2),
    "stool": (21, 22),
    "straw chair": (21, 42),
    "wooden chair": (21, 62),
    "vesper-style chair": (21, 82),
    "trinsic-style chair": (21, 102),
    "wooden bench": (21, 122),
    "wooden throne": (21, 142),
    "magincia-style throne": (21, 162),
    "small table": (21, 182),
    "writing table": (21, 202),
    "yew-wood table": (21, 222),
    "large table": (21, 242),
    "elegant low table": (21, 262),
    "plain low table": (21, 282),
    "ornate table (south)": (21, 302),
    "ornate table (east)": (21, 322),
    "hardwood table (south)": (21, 342),
    "hardwood table (east)": (21, 362),
    "elven podium": (21, 382),
    "ornate elven chair": (21, 402),
    "cozy elven chair": (21, 422),
    "reading chair": (21, 442),
    "ter-mur style chair": (21, 462),
    "ter-mur style table": (21, 482),
    "upholstered chair": (21, 502),
    # Containers (button 41)
    "wooden box": (41, 2),
    "small crate": (41, 22),
    "medium crate": (41, 42),
    "large crate": (41, 62),
    "wooden chest": (41, 82),
    "wooden shelf": (41, 102),
    "armoire (red)": (41, 122),
    "armoire": (41, 142),
    "plain wooden chest": (41, 162),
    "ornate wooden chest": (41, 182),
    "gilded wooden chest": (41, 202),
    "wooden footlocker": (41, 222),
    "finished wooden chest": (41, 242),
    "tall cabinet": (41, 262),
    "short cabinet": (41, 282),
    "red armoire": (41, 302),
    "elegant armoire": (41, 322),
    "maple armoire": (41, 342),
    "cherry armoire": (41, 362),
    "keg": (41, 382),
    "arcane bookshelf (south)": (41, 402),
    "arcane bookshelf (east)": (41, 422),
    "ornate elven chest (south)": (41, 442),
    "ornate elven chest (east)": (41, 462),
    "elven wash basin (south)": (41, 482),
    "elven wash basin (east)": (41, 502),
    "elven dresser (south)": (41, 522),
    "elven dresser (east)": (41, 542),
    "elven armoire (fancy)": (41, 562),
    "elven armoire (simple)": (41, 582),
    "rarewood chest": (41, 602),
    "decorative box": (41, 622),
    "academic bookcase": (41, 642),
    "gargish chest": (41, 662),
    "empty liquor barrel": (41, 682),
    # Weapons (button 61)
    "shepherd's crook": (61, 2),
    "quarter staff": (61, 22),
    "gnarled staff": (61, 42),
    "bokuto": (61, 62),
    "fukiya": (61, 82),
    "tetsubo": (61, 102),
    "wild staff": (61, 122),
    "phantom staff": (61, 142),
    "arcanist's wild staff": (61, 162),
    "ancient wild staff": (61, 182),
    "thorned wild staff": (61, 202),
    "hardened wild staff": (61, 222),
    "serpentstone staff": (61, 242),
    "gargish gnarled staff": (61, 262),
    "club": (61, 282),
    "black staff": (61, 302),
    "kotl black rod": (61, 322),
    # Armor (button 81)
    "wooden shield": (81, 2),
    "woodland chest": (81, 22),
    "woodland arms": (81, 42),
    "woodland gauntlets": (81, 62),
    "woodland leggings": (81, 82),
    "woodland gorget": (81, 102),
    "raven helm": (81, 122),
    "vulture helm": (81, 142),
    "winged helm": (81, 162),
    "ironwood crown": (81, 182),
    "bramble coat": (81, 202),
    "darkwood crown": (81, 222),
    "darkwood chest": (81, 242),
    "darkwood gorget": (81, 262),
    "darkwood leggings": (81, 282),
    "darkwood pauldrons": (81, 302),
    "darkwood gauntlets": (81, 322),
    "gargish wooden shield": (81, 342),
    "pirate shield": (81, 362),
    # Instruments (button 101)
    "lap harp": (101, 2),
    "standing harp": (101, 22),
    "drum": (101, 42),
    "lute": (101, 62),
    "tambourine": (101, 82),
    "tambourine (tassel)": (101, 102),
    "bamboo flute": (101, 122),
    "aud-char": (101, 142),
    "snake charmer flute": (101, 162),
    "cello": (101, 182),
    "wall mounted bell (south)": (101, 202),
    "wall mounted bell (east)": (101, 222),
    "trumpet": (101, 242),
    "cowbell": (101, 262),
    # Misc. Add-Ons (button 121)
    "bulletin board": (121, 2),
    # "bulletin board": (121, 22),  listed again, the first kept
    "parrot perch": (121, 42),
    "arcane circle": (121, 62),
    "tall elven bed (south)": (121, 82),
    "tall elven bed (east)": (121, 102),
    "elven bed (south)": (121, 122),
    "elven bed (east)": (121, 142),
    "elven loveseat (east)": (121, 162),
    "elven loveseat (south)": (121, 182),
    "alchemist table (south)": (121, 202),
    "alchemist table (east)": (121, 222),
    "small bed (south)": (121, 242),
    "small bed (east)": (121, 262),
    "large bed (south)": (121, 282),
    "large bed (east)": (121, 302),
    "dartboard (south)": (121, 322),
    "dartboard (east)": (121, 342),
    "ballot box": (121, 362),
    "pentagram": (121, 382),
    "abbatoir": (121, 402),
    "gargish couch (east)": (121, 422),
    "gargish couch (south)": (121, 442),
    "gargish short table": (121, 462),
    "long table (south)": (121, 482),
    "long table (east)": (121, 502),
    "ter-mur style dresser (east)": (121, 522),
    "ter-mur style dresser (south)": (121, 542),
    "rustic bench (south)": (121, 562),
    "rustic bench (east)": (121, 582),
    "plain wooden shelf (south)": (121, 602),
    "plain wooden shelf (east)": (121, 622),
    "fancy wooden shelf (south)": (121, 642),
    "fancy wooden shelf (east)": (121, 662),
    "fancy loveseat (south)": (121, 682),
    "fancy loveseat (east)": (121, 702),
    "plush loveseat (south)": (121, 722),
    "plush loveseat (east)": (121, 742),
    "plant tapestry (south)": (121, 762),
    "plant tapestry (east)": (121, 782),
    "metal table (south)": (121, 802),
    "metal table (east)": (121, 822),
    "long metal table (south)": (121, 842),
    "long metal table (east)": (121, 862),
    "wooden table (south)": (121, 882),
    "wooden table (east)": (121, 902),
    "long wooden table (south)": (121, 922),
    "long wooden table (east)": (121, 942),
    "small display case (south)": (121, 962),
    "small display case (east)": (121, 982),
    "fancy loveseat (north)": (121, 1002),
    "fancy loveseat (west)": (121, 1022),
    "fancy couch (north)": (121, 1042),
    "fancy couch (west)": (121, 1062),
    "fancy couch (south)": (121, 1082),
    "fancy couch (east)": (121, 1102),
    "small elegant aquarium": (121, 1122),
    "wall mounted aquarium": (121, 1142),
    "large elegant aquarium": (121, 1162),
    # Tailoring and Cooking (button 141)
    "dressform (front)": (141, 2),
    "dressform (side)": (141, 22),
    "elven spinning wheel (east)": (141, 42),
    "elven spinning wheel (south)": (141, 62),
    "elven oven (south)": (141, 82),
    "elven oven (east)": (141, 102),
    "spinning wheel (east)": (141, 122),
    "spinning wheel (south)": (141, 142),
    "loom (east)": (141, 162),
    "loom (south)": (141, 182),
    "stone oven (east)": (141, 202),
    "stone oven (south)": (141, 222),
    "flour mill (east)": (141, 242),
    "flour mill (south)": (141, 262),
    "water trough (east)": (141, 282),
    "water trough (south)": (141, 302),
    # Anvils and Forges (button 161)
    "elven forge": (161, 2),
    "soulforge": (161, 22),
    "small forge": (161, 42),
    "large forge (east)": (161, 62),
    "large forge (south)": (161, 82),
    "anvil (east)": (161, 102),
    "anvil (south)": (161, 122),
    # Training (button 181)
    "training dummy (east)": (181, 2),
    "training dummy (south)": (181, 22),
    "pickpocket dip (east)": (181, 42),
    "pickpocket dip (south)": (181, 62),
}

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
