from uo.phrases import SAVING_TEXT, THROTTLED_TEXT

KEG = "keg"
POTION_KEG = "potion keg"

STAVES = "barrel staves"
LID = "barrel lid"
HOOPS = "barrel hoops"
BOTTLE = "bottle"
TAP = "barrel tap"
BOARDS = "boards"
INGOTS = "ingots"

CLOCK_FRAME = "clock frame"
CLOCK_PARTS = "clock parts"
# The menu spells it out; a bare "clock" is not a row on either table
CLOCK = "clock (right)"

# Stock art, unverified on UOAlive; an art learned by name joins its set. Board hue is not matched:
# the menu spends whichever wood it is set to, so set it to the boards in the pack.
PART_KINDS = [
    (BOARDS, set([0x1BD7, 0x1BD9, 0x1BDA, 0x1BDB]), ["board", "boards"]),
    (INGOTS, set([0x1BEF, 0x1BF2]), ["ingot", "ingots"]),
    (STAVES, set([0x1EB1, 0x1EB2, 0x1EB3, 0x1EB4]), ["staves"]),
    (LID, set([0x1DB8]), ["lid"]),
    (HOOPS, set([0x1DB7]), ["hoops"]),
    (KEG, set([0x1940]), ["keg"]),
    (BOTTLE, set([0x0F0E]), ["bottle", "bottles"]),
    (TAP, set([0x1004]), ["tap"]),
    (CLOCK_FRAME, set([0x104D, 0x104E]), ["frame"]),
    (CLOCK_PARTS, set([0x104F, 0x1050]), ["parts"]),
]
PART_ORDER = [kind for kind, _graphics, _words in PART_KINDS]

# A made potion keg is the same 0x1940 as the empty keg it took; only the name tells them apart
MADE_KEG_TYPES = ["specially lined"]

# One (key, caption, stages) per radio option. A stage is (row, menu, what one press spends), a part
# always above whatever spends it: the run presses the first row the next product still lacks,
# counted back through the pack, so parts already there are used first. The last row is the product.
# Bottles have no row on either menu. Stock DefCarpentry and DefTinkering.
#
# The clock's rows are the ones a 10-clock run was watched pressing. Its clock parts are the Parts
# group's, which spends ingots, not the Assemblies group's axle with gears and springs.
ASSEMBLIES = [
    ("keg", "Keg", [
        (STAVES, "carpentry", {BOARDS: 5}),
        (LID, "carpentry", {BOARDS: 4}),
        (HOOPS, "tinkering", {INGOTS: 5}),
        (KEG, "carpentry", {STAVES: 3, LID: 1, HOOPS: 1}),
    ]),
    ("potion keg", "Potion keg", [
        (STAVES, "carpentry", {BOARDS: 5}),
        (LID, "carpentry", {BOARDS: 4}),
        (HOOPS, "tinkering", {INGOTS: 5}),
        (TAP, "tinkering", {INGOTS: 2}),
        (KEG, "carpentry", {STAVES: 3, LID: 1, HOOPS: 1}),
        (POTION_KEG, "tinkering", {KEG: 1, BOTTLE: 10, LID: 1, TAP: 1}),
    ]),
    ("clock", "Clock", [
        (CLOCK_PARTS, "tinkering", {INGOTS: 5}),
        (CLOCK_FRAME, "tinkering", {BOARDS: 6}),
        (CLOCK, "tinkering", {CLOCK_FRAME: 1, CLOCK_PARTS: 1}),
    ]),
]

# One craft menu each, as craft-map.py read them off UOAlive; only the rows the stages press
MENUS = {
    "carpentry": {
        "tool_noun": "carpentry tools",
        "tool_graphics": set([
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
        ]),
        "tool_name_words": ["saw", "plane", "nails", "froe", "inshave", "scorp"],
        "title": "CARPENTRY",
        "title_text": ["CARPENTRY", "CARPENTER"],
        "category_names": ["other", "furniture", "containers", "weapons", "armor", "instruments",
                           "misc. add-ons", "tailoring and cooking", "anvils and forges",
                           "training"],
        "recipes": {STAVES: (1, 2), LID: (1, 22), KEG: (41, 382)},
    },
    "tinkering": {
        "tool_noun": "tinker's tools",
        "tool_graphics": set([0x1EB8, 0x1EB9]),
        "tool_name_words": ["tinker", "tinkers"],
        "title": "TINKERING",
        "title_text": ["TINKERING", "TINKER"],
        "category_names": ["jewelry", "wooden items", "tools", "parts", "utensils",
                           "miscellaneous", "assemblies", "traps", "magic jewelry"],
        "recipes": {TAP: (61, 42), HOOPS: (61, 102), POTION_KEG: (121, 142), CLOCK_FRAME: (21, 82),
                    CLOCK_PARTS: (61, 22), CLOCK: (121, 62)},
    },
}

START_PROMPT = {
    "text": "What to make",
    "options": [(key, caption) for key, caption, _stages in ASSEMBLIES],
    "assembly_default": "potion keg",
    "count_text": "How many?",
    "default": 1,
    "hue": 996,
    "poll": 0.25,
}

WEIGHT_BUFFER = 40

# Its own button rather than a group, so it does not count toward the category index
LAST_TEN_LABEL = "LAST TEN"

# Buttons are 1 + type + index * 20 on this shard's menus. MAKE LAST is the stock
# GetButtonID(6, 2): 1 + 6 + 2 * 20
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MAKE_LAST_BUTTON = 47

GUMP_TIMEOUT = 5.0
GUMP_POLL = 0.15

# Has to outlast the craft animation, which plays before the shard answers
CRAFT_TIMEOUT = 10.0
CRAFT_POLL = 0.2

MOVE_DELAY = 0.7

MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_TOOL = 10

# What an unreadable outcome reports before it goes quiet, and how much of it
MAX_UNREADABLE_REPORTS = 2
UNREADABLE_TEXT_LIMIT = 160
JOURNAL_TAIL_SECONDS = 20.0
JOURNAL_TAIL_LINES = 4

# The whole gump and journal behind a report, appended here so the game window stays quiet. "" turns
# it off; a bare name lands beside the script.
NOTES_PATH = "assembly-notes.log"
NOTES_TAIL_SECONDS = 60.0

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
            "You create an exceptional",
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
