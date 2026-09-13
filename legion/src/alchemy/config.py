from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT
from uo.timings import (HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STALL_STOP, STALL_WARN,
                        STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

# One JSON object per attempt, for legion/skilldb.py. "" turns recording off. A bare name lands
# beside the script, in LegionScripts.
DATA_PATH = "skill-attempts.jsonl"

SKILL_NAMES = ["Alchemy"]

MIN_SKILL = 0.0

# Ceilings are exclusive, in the client's float percentage. Stock RunUO floors (lesser poison -5,
# poison 15, greater agility 35, greater poison 55, deadly poison 90; success is (skill - floor) /
# 50), each row ridden until the next cheap one rather than swapped for the greater strength and
# greater cure the wiki's path takes in between. A failure keeps the bottle and loses half the
# reagents, never fewer than one.
BANDS = [
    (15.0, "lesser poison"),
    (35.0, "poison"),
    (73.0, "greater agility"),
    (90.0, "greater poison"),
    (None, "deadly poison"),
]

BOTTLE = "empty bottles"
NIGHTSHADE = "nightshade"
BLOODMOSS = "blood moss"
MANDRAKE = "mandrake root"
GARLIC = "garlic"

# Stock art, unverified on UOAlive; an art learned by name joins its set
STOCK_KINDS = [
    (BOTTLE, set([0x0F0E]), ["bottle", "bottles"]),
    (NIGHTSHADE, set([0x0F88]), ["nightshade"]),
    (BLOODMOSS, set([0x0F7B]), ["bloodmoss", "blood moss"]),
    (MANDRAKE, set([0x0F86]), ["mandrake"]),
    (GARLIC, set([0x0F84]), ["garlic"]),
]

KIND_ORDER = [kind for kind, _graphics, _words in STOCK_KINDS]

# Row name as the SELECTIONS row spells it: the potion's art, its reagent and how many. Stock RunUO:
# every poison lands as 0x0F0A, and every potion takes one bottle besides.
POTIONS = {
    "lesser poison": (0x0F0A, NIGHTSHADE, 1),
    "poison": (0x0F0A, NIGHTSHADE, 2),
    "greater agility": (0x0F08, BLOODMOSS, 3),
    "greater strength": (0x0F09, MANDRAKE, 5),
    "greater poison": (0x0F0A, NIGHTSHADE, 4),
    "greater cure": (0x0F07, GARLIC, 6),
    "deadly poison": (0x0F0A, NIGHTSHADE, 8),
}

PRODUCTS = dict((name, set([POTIONS[name][0]])) for name in POTIONS)
PRODUCT_GRAPHICS = set().union(*PRODUCTS.values())
NEEDS = dict((name, {BOTTLE: 1, POTIONS[name][1]: POTIONS[name][2]}) for name in POTIONS)

# Every restock fills each kind the band spends to this many crafts' worth: a flat count per kind
# would sit under RESTOCK_AT for deadly poison's eight nightshade and restock every cycle. Bottles
# weigh a stone each, which bounds it.
BATCH_CRAFTS = 30

# Crafts the pack can still pay for before a restock
RESTOCK_AT = 5

# The shard refusing a move for weight. With potions in the pack the run unloads before it loads.
TOO_HEAVY_TEXT = ["That container cannot hold more weight"]

# Mortar and pestle, 3739
TOOL_GRAPHICS = set([0x0E9B])
TOOL_NAME_WORDS = ["mortar"]

# Potion keg, 6464. Stock RunUO names an empty one "A specially lined keg" and a started one "A keg
# of <potion> potions": a keg whose name lacks KEG_FILLED_TEXT is empty. Unverified on UOAlive.
KEG_GRAPHICS = set([0x1940])
KEG_NAME_WORDS = ["keg"]
KEG_FILLED_TEXT = ["keg of"]

# Keg runs in a row that poured nothing - no empty keg, or the drop refused - before the run ends
MAX_KEG_MISSES = 3

TOOL_MODES = [("stop", "Stop the run"), ("fetch", "Fetch from a container")]
OUTPUT_OPTIONS = [("kegs", "Kegs"), ("unload", "Unload into a container"), ("keep", "Keep")]

# Products in the pack, counted as amounts, before they are unloaded
DUMP_AT = 10

# With nothing picked to unload into, the run ends once the pack holds this many products
MAX_HELD = 60

# Unloads in a row that moved nothing before the run ends
MAX_DUMP_MISSES = 3

# The form the run is set up on. Closing it, Cancel, or no OK in the timeout ends the run.
SETUP = {
    "title": "Alchemy",
    "tool_noun": "mortars and pestles",
    "material": "reagents",
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

# One tool is fetched at a time from the container the form picked; how long the pack has to show it
FETCH_TIMEOUT = 3.0
FETCH_POLL = 0.25

# Seconds throughout - API.Pause takes seconds
PICK_TIMEOUT = 60.0

# Whole seconds: the API takes an int here
PATHFIND_TIMEOUT = 10

OPEN_DELAY = 0.6
MOVE_DELAY = 0.7

SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25

GUMP_TIMEOUT = 5.0
GUMP_POLL = 0.15

# Has to outlast the craft animation, which plays before the shard answers
CRAFT_TIMEOUT = 10.0
CRAFT_POLL = 0.2

# A failed craft's refund arrives after the journal line; the consumed row waits this long for it
REFUND_SETTLE = 1.5
REFUND_POLL = 0.25

MAX_CYCLES = 20000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_TOOL = 10
MAX_EMPTY_MOVES = 3

# Refusals for material while the pack holds what the recipe takes: the row is not the potion
MAX_NO_MATERIAL = 3

# What an unreadable outcome reports before it goes quiet, and how much of it
MAX_UNREADABLE_REPORTS = 2
UNREADABLE_TEXT_LIMIT = 160
JOURNAL_TAIL_SECONDS = 20.0
JOURNAL_TAIL_LINES = 4

# The whole gump and journal behind a report, appended here so the game window stays quiet. "" turns
# it off; a bare name lands beside the script.
NOTES_PATH = "alchemy-notes.log"
NOTES_TAIL_SECONDS = 60.0

CRAFT_TITLE = "ALCHEMY"

# Only ever to *recognise* a gump, never to refuse one: the header is a cliloc, and a build whose
# GetGumpContents answers nothing for it made every craft read as 'no craft menu'
CRAFT_TITLE_TEXT = [CRAFT_TITLE, "ALCHEMIST"]
CRAFT_TITLE_FRAGMENTS = [phrase.lower() for phrase in CRAFT_TITLE_TEXT]

# Its own button rather than a group, so it does not count toward the category index
LAST_TEN_LABEL = "LAST TEN"

# Buttons are 1 + type + index * 20, as bowcraft found on this shard's menu; MAKE LAST is assumed to
# sit where it does there
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MAKE_LAST_BUTTON = 47

# Stock DefAlchemy wordings, unverified on UOAlive. Ordered: 'failed' before 'made' because "You
# failed to create the item" contains "create the item". noMaterial names each resource rather than
# a bare "You do not have enough", which skillTooLow's "You do not have enough skill" contains.
OUTCOME_TEXT = [
    (
        "failed",
        [
            "You fail to create a useful potion",
            "You failed to create the item",
            "You fail to create",
            "You have failed to create",
            "lost some of the raw material",
        ],
    ),
    (
        "made",
        [
            "You pour the potion into a bottle",
            # Read off UOAlive's NOTICES panel with a keg in the pack: the potion never lands
            "You create the potion and pour it into a keg",
            "You create the item",
            "You create an exceptional",
            "You put the",
        ],
    ),
    # Said in the gump's NOTICES panel, which the journal may never carry
    (
        "noMaterial",
        [
            "You don't have the components",
            "You do not have the components",
            "You don't have the resources",
            "You do not have the resources",
            "enough empty bottles",
            "enough nightshade",
            "enough blood moss",
            "enough bloodmoss",
            "enough mandrake",
            "enough garlic",
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

# ALCHEMY MENU, read off the menu on 2026-09-13
CATEGORY_NAMES = [
    "healing and curative",
    "enhancement",
    "toxic",
    "explosive",
    "strange brew",
    "ingredients",
    "skill tinctures",
]

RECIPES = {
    # Healing and Curative (button 1)
    "refresh": (1, 2),
    "greater refreshment": (1, 22),
    "lesser heal": (1, 42),
    "heal": (1, 62),
    "greater heal": (1, 82),
    "lesser cure": (1, 102),
    "cure": (1, 122),
    "greater cure": (1, 142),
    "elixir of rebirth": (1, 162),
    "barrab hemolymph concentrate": (1, 182),
    # Enhancement (button 21)
    "agility": (21, 2),
    "greater agility": (21, 22),
    "night sight": (21, 42),
    "strength": (21, 62),
    "greater strength": (21, 82),
    "invisibility": (21, 102),
    "jukari burn poultice": (21, 122),
    "kurak ambusher's essence": (21, 142),
    "barako draft of might": (21, 162),
    "urali trance tonic": (21, 182),
    "sakkhra prophylaxis potion": (21, 202),
    # Toxic (button 41)
    "lesser poison": (41, 2),
    "poison": (41, 22),
    "greater poison": (41, 42),
    "deadly poison": (41, 62),
    "parasitic": (41, 82),
    "darkglow": (41, 102),
    "scouring toxin": (41, 122),
    # Explosive (button 61)
    "lesser explosion": (61, 2),
    "explosion": (61, 22),
    "greater explosion": (61, 42),
    "conflagration": (61, 62),
    "greater conflagration": (61, 82),
    "confusion blast": (61, 102),
    "greater confusion blast": (61, 122),
    "black powder": (61, 142),
    "fuse cord": (61, 162),
    # Strange Brew (button 81)
    "smoke bomb": (81, 2),
    "hovering wisp": (81, 22),
    "natural dye": (81, 42),
    "nexus core": (81, 62),
    # Ingredients (button 101)
    "plant pigment": (101, 2),
    "color fixative": (101, 22),
    "crystal granules": (101, 42),
    "crystal dust": (101, 62),
    "softened reeds": (101, 82),
    "vial of vitriol": (101, 102),
    "bottle of ichor": (101, 122),
    "potash": (101, 142),
    "gold dust": (101, 162),
    # Skill Tinctures (button 121)
    "tincture of shadows": (121, 2),
    "tincture of the minstrel": (121, 22),
}
