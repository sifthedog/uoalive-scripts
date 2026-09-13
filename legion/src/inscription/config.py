from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT, UNSKILLED_TEXT
from uo.timings import (HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STALL_STOP, STALL_WARN,
                        STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

# One JSON object per attempt, for legion/skilldb.py. "" turns recording off. A bare name lands
# beside the script, in LegionScripts.
DATA_PATH = "skill-attempts.jsonl"

SKILL_NAMES = ["Inscription", "Inscribe"]

# Below this the sensible thing is to buy the skill from an NPC mage or scribe
MIN_SKILL = 30.0

# Ceilings are exclusive, in the client's float percentage: the AFK guides' circle per band, and
# the spell with the fewest reagents in each. Any SPELLS row goes here.
BANDS = [
    (55.0, "lightning"),
    (65.0, "magic reflection"),
    (85.0, "reveal"),
    (94.0, "flamestrike"),
    (None, "resurrection"),
]

BLACK_PEARL = "black pearl"
BLOODMOSS = "bloodmoss"
GARLIC = "garlic"
GINSENG = "ginseng"
MANDRAKE = "mandrake root"
NIGHTSHADE = "nightshade"
SILK = "spider's silk"
ASH = "sulfurous ash"
BLANK = "blank scrolls"

# Stock art, unverified on UOAlive; an art learned by name joins its set. Whole words, so 'ash' is
# not a name word: ash boards carry it too.
STOCK_KINDS = [
    # 0x0E34 is the same scroll turned the other way
    (BLANK, set([0x0EF3, 0x0E34]), ["blank scroll", "blank scrolls"]),
    (BLACK_PEARL, set([0x0F7A]), ["black pearl", "pearl"]),
    (BLOODMOSS, set([0x0F7B]), ["bloodmoss", "blood moss"]),
    (GARLIC, set([0x0F84]), ["garlic"]),
    (GINSENG, set([0x0F85]), ["ginseng"]),
    (MANDRAKE, set([0x0F86]), ["mandrake"]),
    (NIGHTSHADE, set([0x0F88]), ["nightshade"]),
    (ASH, set([0x0F8C]), ["sulfurous"]),
    (SILK, set([0x0F8D]), ["silk"]),
]

KIND_ORDER = [kind for kind, _graphics, _words in STOCK_KINDS]

# Stock RunUO: what inscribing a scroll of each circle costs in mana
MANA_BY_CIRCLE = {4: 11, 5: 14, 6: 20, 7: 40, 8: 50}

# Row name as the SELECTIONS row spells it: circle, the scroll's art, and its reagents. The art is
# 0x1F2D plus the spell's id: stock RunUO puts reactive armor out of sequence at 0x1F2D and every
# scroll after it one under 0x1F2E plus the id. UOAlive's lightning scroll reads 0x1F4A (8010).
SPELLS = {
    "arch cure": (4, 0x1F45, [GARLIC, GINSENG, MANDRAKE]),
    "arch protection": (4, 0x1F46, [GARLIC, GINSENG, MANDRAKE, ASH]),
    "curse": (4, 0x1F47, [GARLIC, NIGHTSHADE, ASH]),
    "fire field": (4, 0x1F48, [BLACK_PEARL, SILK, ASH]),
    "greater heal": (4, 0x1F49, [GARLIC, GINSENG, MANDRAKE, SILK]),
    "lightning": (4, 0x1F4A, [MANDRAKE, ASH]),
    "mana drain": (4, 0x1F4B, [BLACK_PEARL, MANDRAKE, SILK]),
    "recall": (4, 0x1F4C, [BLACK_PEARL, BLOODMOSS, MANDRAKE]),
    "blade spirits": (5, 0x1F4D, [BLACK_PEARL, MANDRAKE, NIGHTSHADE]),
    "dispel field": (5, 0x1F4E, [BLACK_PEARL, GARLIC, SILK, ASH]),
    "incognito": (5, 0x1F4F, [BLOODMOSS, GARLIC, NIGHTSHADE]),
    "magic reflection": (5, 0x1F50, [GARLIC, MANDRAKE, SILK]),
    "mind blast": (5, 0x1F51, [BLACK_PEARL, MANDRAKE, NIGHTSHADE, ASH]),
    "paralyze": (5, 0x1F52, [GARLIC, MANDRAKE, SILK]),
    "poison field": (5, 0x1F53, [BLACK_PEARL, NIGHTSHADE, SILK]),
    "summon creature": (5, 0x1F54, [BLOODMOSS, MANDRAKE, SILK]),
    "dispel": (6, 0x1F55, [GARLIC, MANDRAKE, ASH]),
    "energy bolt": (6, 0x1F56, [BLACK_PEARL, NIGHTSHADE]),
    "explosion": (6, 0x1F57, [BLOODMOSS, MANDRAKE, NIGHTSHADE]),
    "invisibility": (6, 0x1F58, [BLOODMOSS, NIGHTSHADE]),
    "mark": (6, 0x1F59, [BLACK_PEARL, BLOODMOSS, MANDRAKE]),
    "mass curse": (6, 0x1F5A, [GARLIC, MANDRAKE, NIGHTSHADE, ASH]),
    "paralyze field": (6, 0x1F5B, [BLACK_PEARL, GINSENG, SILK]),
    "reveal": (6, 0x1F5C, [BLOODMOSS, ASH]),
    "chain lightning": (7, 0x1F5D, [BLACK_PEARL, BLOODMOSS, MANDRAKE, ASH]),
    "energy field": (7, 0x1F5E, [BLACK_PEARL, MANDRAKE, SILK, ASH]),
    "flamestrike": (7, 0x1F5F, [SILK, ASH]),
    "gate travel": (7, 0x1F60, [BLACK_PEARL, MANDRAKE, ASH]),
    "mana vampire": (7, 0x1F61, [BLACK_PEARL, BLOODMOSS, MANDRAKE, SILK]),
    "mass dispel": (7, 0x1F62, [BLACK_PEARL, GARLIC, MANDRAKE, ASH]),
    "meteor swarm": (7, 0x1F63, [BLOODMOSS, MANDRAKE, SILK, ASH]),
    "polymorph": (7, 0x1F64, [BLOODMOSS, MANDRAKE, SILK]),
    "earthquake": (8, 0x1F65, [BLOODMOSS, GINSENG, MANDRAKE, ASH]),
    "energy vortex": (8, 0x1F66, [BLACK_PEARL, BLOODMOSS, MANDRAKE, NIGHTSHADE]),
    "resurrection": (8, 0x1F67, [BLOODMOSS, GARLIC, GINSENG]),
    "summon air elemental": (8, 0x1F68, [BLOODMOSS, MANDRAKE, SILK]),
    "summon daemon": (8, 0x1F69, [BLOODMOSS, MANDRAKE, SILK, ASH]),
    "summon earth elemental": (8, 0x1F6A, [BLOODMOSS, MANDRAKE, SILK]),
    "summon fire elemental": (8, 0x1F6B, [BLOODMOSS, MANDRAKE, SILK, ASH]),
    "summon water elemental": (8, 0x1F6C, [BLOODMOSS, MANDRAKE, SILK]),
}


def needs_of(reagents):
    needs = {BLANK: 1}

    for kind in reagents:
        needs[kind] = 1

    return needs


PRODUCTS = dict((name, set([SPELLS[name][1]])) for name in SPELLS)
PRODUCT_GRAPHICS = set().union(*PRODUCTS.values())
NEEDS = dict((name, needs_of(SPELLS[name][2])) for name in SPELLS)
MANA = dict((name, MANA_BY_CIRCLE[SPELLS[name][0]]) for name in SPELLS)

# The CATEGORIES rows, lowercased, as craft-map.py read them off UOAlive's menu
CATEGORY_NAMES = [
    "first - second circle",
    "third - fourth circle",
    "fifth - sixth circle",
    "seventh - eighth circle",
    "spells of necromancy",
    "other",
    "spells of mysticism",
]

TOOL_GRAPHICS = set([0x0FBF, 0x0FC0])
TOOL_NAME_WORDS = ["pen"]

# Every restock fills each kind the band spends to this. Blank scrolls weigh a stone each.
BATCH_SIZE = 100

# Crafts the pack can still pay for before a restock
RESTOCK_AT = 20

# The shard refusing a move for weight. With scrolls in the pack the run unloads before it loads.
TOO_HEAVY_TEXT = ["That container cannot hold more weight"]

# Answered by the gump at the start; ESC on the unload cursor and a closed gump both mean keep
OUTPUT_CHOICE = {
    "text": "Sell the scrolls to a mage, unload them into a container, or keep them?",
    "hue": 996,
    "poll": 0.5,
    "timeout": 60.0,
}
OUTPUT_OPTIONS = [("sell", "Sell"), ("unload", "Unload"), ("keep", "Keep")]

# Counted as amounts, the run's own scrolls only
SELL_AT = 20
DUMP_AT = 20

# Keeping them, the run ends once the pack holds this many
MAX_HELD = 60

# Unloads in a row that moved nothing before the run ends
MAX_DUMP_MISSES = 3

# Matched against the name and the tooltip
VENDOR_TITLES = ["mage", "scribe"]
VENDOR_NOUN = "mage or scribe"

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

SELL_TIMEOUT = 15.0
SELL_POLL = 0.5

# Sell trips in a row that bought nothing before the trips pause. Never ends the run.
MAX_SELL_MISSES = 3
SELL_RETRY_AFTER = 25

# A backstop only - the selection ends when you press ESC
MAX_PICKS = 8

PICK_TIMEOUT = 60.0
OPEN_DELAY = 0.6
CONTAINER_RANGE = 2

MEDITATION = "Meditation"

# The BuffIconType the client publishes while a trance is running
MEDITATION_BUFF = "ActiveMeditation"

# Off waits for natural regeneration instead: slower, always available
MEDITATE = True

# The last band charges 50 a scroll, so a pool topped right up pays for several
MEDITATE_TO_FULL = True

MEDITATE_TIMEOUT = 20.0
MEDITATE_ATTEMPTS = 4
MEDITATE_START_TIMEOUT = 2.0
MANA_WAIT_SLICE = 0.2

MANA_POLL = 0.5
MANA_LOG_EVERY = 10.0

REGEN_TIMEOUT = 120.0

# Waits in a row that brought the pool no higher than the band needs before the run ends
MAX_DRY = 5

CRAFT_TITLE = "INSCRIPTION"

# Only ever to *recognise* a gump, never to refuse one: the header is a cliloc, and a build whose
# GetGumpContents answers nothing for it made every craft read as 'no craft menu'
CRAFT_TITLE_TEXT = [CRAFT_TITLE, "INSCRIBE"]
CRAFT_TITLE_FRAGMENTS = [phrase.lower() for phrase in CRAFT_TITLE_TEXT]

# Its own button rather than a group, so it does not count toward the category index
LAST_TEN_LABEL = "LAST TEN"

# Buttons are 1 + type + index * 20, as bowcraft found on this shard's menu; MAKE LAST is assumed to
# sit where it does there
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MAKE_LAST_BUTTON = 47

# (category button, row button) for every row, as craft-map.py read them off UOAlive's menu. Run
# craft-map.py again and paste its block over this one when the menu changes.
RECIPES = {
    # First - Second Circle (button 1)
    "reactive armor": (1, 2),
    "clumsy": (1, 22),
    "create food": (1, 42),
    "feeblemind": (1, 62),
    "heal": (1, 82),
    "magic arrow": (1, 102),
    "night sight": (1, 122),
    "weaken": (1, 142),
    "agility": (1, 162),
    "cunning": (1, 182),
    "cure": (1, 202),
    "harm": (1, 222),
    "magic trap": (1, 242),
    "magic untrap": (1, 262),
    "protection": (1, 282),
    "strength": (1, 302),
    # Third - Fourth Circle (button 21)
    "bless": (21, 2),
    "fireball": (21, 22),
    "magic lock": (21, 42),
    "poison": (21, 62),
    "telekinesis": (21, 82),
    "teleport": (21, 102),
    "unlock": (21, 122),
    "wall of stone": (21, 142),
    "arch cure": (21, 162),
    "arch protection": (21, 182),
    "curse": (21, 202),
    "fire field": (21, 222),
    "greater heal": (21, 242),
    "lightning": (21, 262),
    "mana drain": (21, 282),
    "recall": (21, 302),
    # Fifth - Sixth Circle (button 41)
    "blade spirits": (41, 2),
    "dispel field": (41, 22),
    "incognito": (41, 42),
    "magic reflection": (41, 62),
    "mind blast": (41, 82),
    "paralyze": (41, 102),
    "poison field": (41, 122),
    "summon creature": (41, 142),
    "dispel": (41, 162),
    "energy bolt": (41, 182),
    "explosion": (41, 202),
    "invisibility": (41, 222),
    "mark": (41, 242),
    "mass curse": (41, 262),
    "paralyze field": (41, 282),
    "reveal": (41, 302),
    # Seventh - Eighth Circle (button 61)
    "chain lightning": (61, 2),
    "energy field": (61, 22),
    "flamestrike": (61, 42),
    "gate travel": (61, 62),
    "mana vampire": (61, 82),
    "mass dispel": (61, 102),
    "meteor swarm": (61, 122),
    "polymorph": (61, 142),
    "earthquake": (61, 162),
    "energy vortex": (61, 182),
    "resurrection": (61, 202),
    "summon air elemental": (61, 222),
    "summon daemon": (61, 242),
    "summon earth elemental": (61, 262),
    "summon fire elemental": (61, 282),
    "summon water elemental": (61, 302),
    # Spells of Necromancy (button 81)
    "animate dead": (81, 2),
    "blood oath": (81, 22),
    "corpse skin": (81, 42),
    "curse weapon": (81, 62),
    "evil omen": (81, 82),
    "horrific beast": (81, 102),
    "lich form": (81, 122),
    "mind rot": (81, 142),
    "pain spike": (81, 162),
    "poison strike": (81, 182),
    "strangle": (81, 202),
    "summon familiar": (81, 222),
    "vampiric embrace": (81, 242),
    "vengeful spirit": (81, 262),
    "wither": (81, 282),
    "wraith form": (81, 302),
    "exorcism": (81, 322),
    # Other (button 101)
    "enchanted switch": (101, 2),
    "runed prism": (101, 22),
    "runebook": (101, 42),
    "bulk order book": (101, 62),
    "spellbook": (101, 82),
    "scrapper's compendium": (101, 102),
    "spellbook engraving tool": (101, 122),
    "mysticism spellbook": (101, 142),
    "necromancer spellbook": (101, 162),
    "exodus summoning rite": (101, 182),
    "prophetic manuscript": (101, 202),
    "blank scroll": (101, 222),
    "scroll binder": (101, 242),
    "book (100 pages)": (101, 262),
    "book (200 pages)": (101, 282),
    "runic atlas": (101, 302),
    # Spells of Mysticism (button 121)
    "nether bolt": (121, 2),
    "healing stone": (121, 22),
    "purge magic": (121, 42),
    "enchant": (121, 62),
    "sleep": (121, 82),
    "eagle strike": (121, 102),
    "animated weapon": (121, 122),
    "stone form": (121, 142),
    "spell trigger": (121, 162),
    "mass sleep": (121, 182),
    "cleansing winds": (121, 202),
    "bombard": (121, 222),
    "spell plague": (121, 242),
    "hail storm": (121, 262),
    "nether cyclone": (121, 282),
    "rising colossus": (121, 302),
}

# Whole seconds: the API takes an int here
PATHFIND_TIMEOUT = 10

GUMP_TIMEOUT = 5.0
GUMP_POLL = 0.15

# Has to outlast the craft animation, which plays before the shard answers
CRAFT_TIMEOUT = 10.0
CRAFT_POLL = 0.2

# A failed craft's refund arrives after the journal line; the consumed row waits this long for it
REFUND_SETTLE = 1.5
REFUND_POLL = 0.25

MOVE_DELAY = 0.7

SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25

MAX_CYCLES = 20000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_TOOL = 10
MAX_EMPTY_MOVES = 3

# Refusals for material while the pack holds what the recipe takes: the row is not the spell
MAX_NO_MATERIAL = 3

# What an unreadable outcome reports before it goes quiet, and how much of it
MAX_UNREADABLE_REPORTS = 2
UNREADABLE_TEXT_LIMIT = 400
JOURNAL_TAIL_SECONDS = 20.0
JOURNAL_TAIL_LINES = 4

# The whole gump and journal behind a report, appended here so the game window stays quiet. "" turns
# it off; a bare name lands beside the script.
NOTES_PATH = "inscription-notes.log"
NOTES_TAIL_SECONDS = 60.0

# Ordered: 'failed' before 'made' because "You failed to create the item" contains "create the item"
OUTCOME_TEXT = [
    (
        "failed",
        [
            "You fail to inscribe the scroll",
            "You failed to create the item",
            "You fail to create",
            "You have failed to create",
            "lost some of the raw material",
        ],
    ),
    (
        "made",
        [
            "You inscribe the spell and put the scroll",
            "You create the item",
            "You create an exceptional",
            "You put the",
        ],
    ),
    # Said in the gump's NOTICES panel, which the journal may never carry
    (
        "noMana",
        [
            "You don't have enough mana to inscribe",
            "You do not have enough mana",
            "Insufficient mana",
        ],
    ),
    (
        "noMaterial",
        [
            "You don't have enough blank scrolls",
            "You do not have enough blank scrolls",
            "You don't have the components needed",
            "You do not have the components needed",
            "You don't have the resources",
            "You do not have the resources",
            "You do not have enough reagents",
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

# trance is the only wording here that is not a guess: it is the client's own documented example
MEDITATE_OUTCOME_TEXT = [
    ("trance", ["You enter a meditative trance."]),
    ("full", ["You are at peace"]),
    # Before unfocused, whose trailing full stop is deliberate: without it 'You cannot focus your
    # concentration' would also match the equipped-weapon sentence.
    (
        "blocked",
        [
            "You cannot focus your concentration with an equipped weapon",
            "You cannot focus your concentration with an equipped shield",
            "You are preoccupied with thoughts of battle",
        ],
    ),
    ("unfocused", ["You cannot focus your concentration.", "You lose your concentration"]),
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("throttled", ["You must wait a few moments to use another skill"] + THROTTLED_TEXT),
]
