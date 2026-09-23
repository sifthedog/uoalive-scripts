from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT
from uo.timings import (HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STALL_STOP, STALL_WARN,
                        STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

# One JSON object per attempt, for legion/skilldb.py. "" turns recording off. A bare name lands
# beside the script, in LegionScripts.
DATA_PATH = "skill-attempts.jsonl"

SKILL_NAMES = ["Tinkering"]

MIN_SKILL = 0.0

# Ceilings are exclusive, in the client's float percentage
BANDS = [
    (20.0, "spoon (left)"),
    (30.0, "scissors"),
    (40.0, "butcher knife"),
    (45.0, "tongs"),
    (95.0, "lockpick"),
    (111.8, "ring"),
    (None, "fancy wind chimes"),
]

# The CATEGORIES rows, lowercased, as craft-map.py read them off UOAlive's menu
CATEGORY_NAMES = [
    "jewelry",
    "wooden items",
    "tools",
    "parts",
    "utensils",
    "miscellaneous",
    "assemblies",
    "traps",
    "magic jewelry",
]

# Name as the SELECTIONS row spells it, and the graphics it lands in the pack as. Stock art,
# unverified on UOAlive.
PRODUCTS = {
    "spoon (left)": set([0x09F4, 0x09F5]),
    "scissors": set([0x0F9E, 0x0F9F]),
    "butcher knife": set([0x13F6, 0x13F7]),
    "tongs": set([0x0FBB, 0x0FBC]),
    "lockpick": set([0x14FC]),
    "ring": set([0x108A]),
    "fancy wind chimes": set([0x2833]),
}

PRODUCT_GRAPHICS = set().union(*PRODUCTS.values())

# Ingots per craft, from the stock recipes. The pack is measured either side of a craft regardless;
# this only decides when the pack is too short to try.
INGOT_COST = {
    "spoon (left)": 1,
    "scissors": 2,
    "butcher knife": 2,
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
# the wind chimes, and the three low bands are not offered to anyone - and it is unloaded into the
# container picked at the start instead.
VENDORS = {
    "spoon (left)": None,
    "scissors": None,
    "butcher knife": None,
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

# (category button, row button) for every row, as craft-map.py read them off UOAlive's menu. Run
# craft-map.py again and paste its block over this one when the menu changes.
RECIPES = {
    # Jewelry (button 1)
    "ring": (1, 2),
    "bracelet": (1, 22),
    "gargish necklace": (1, 42),
    "gargish bracelet": (1, 62),
    "gargish ring": (1, 82),
    "gargish earrings": (1, 102),
    "star sapphire ring": (1, 122),
    "star sapphire necklace (silver)": (1, 142),
    "star sapphire necklace (jewelled)": (1, 162),
    "star sapphire earrings": (1, 182),
    "star sapphire necklace (golden)": (1, 202),
    "star sapphire bracelet": (1, 222),
    "emerald ring": (1, 242),
    "emerald necklace (silver)": (1, 262),
    "emerald necklace (jewelled)": (1, 282),
    "emerald earrings": (1, 302),
    "emerald necklace (golden)": (1, 322),
    "emerald bracelet": (1, 342),
    "sapphire ring": (1, 362),
    "sapphire necklace (silver)": (1, 382),
    "sapphire necklace (jewelled)": (1, 402),
    "sapphire earrings": (1, 422),
    "sapphire necklace (golden)": (1, 442),
    "sapphire bracelet": (1, 462),
    "ruby ring": (1, 482),
    "ruby necklace (silver)": (1, 502),
    "ruby necklace (jewelled)": (1, 522),
    "ruby earrings": (1, 542),
    "ruby necklace (golden)": (1, 562),
    "ruby bracelet": (1, 582),
    "citrine ring": (1, 602),
    "citrine necklace (silver)": (1, 622),
    "citrine necklace (jewelled)": (1, 642),
    "citrine earrings": (1, 662),
    "citrine necklace (golden)": (1, 682),
    "citrine bracelet": (1, 702),
    "amethyst ring": (1, 722),
    "amethyst necklace (silver)": (1, 742),
    "amethyst necklace (jewelled)": (1, 762),
    "amethyst earrings": (1, 782),
    "amethyst necklace (golden)": (1, 802),
    "amethyst bracelet": (1, 822),
    "tourmaline ring": (1, 842),
    "tourmaline necklace (silver)": (1, 862),
    "tourmaline necklace (jewelled)": (1, 882),
    "tourmaline earrings": (1, 902),
    "tourmaline necklace (golden)": (1, 922),
    "tourmaline bracelet": (1, 942),
    "amber ring": (1, 962),
    "amber necklace (silver)": (1, 982),
    "amber necklace (jewelled)": (1, 1002),
    "amber earrings": (1, 1022),
    "amber necklace (golden)": (1, 1042),
    "amber bracelet": (1, 1062),
    "diamond ring": (1, 1082),
    "diamond necklace (silver)": (1, 1102),
    "diamond necklace (jewelled)": (1, 1122),
    "diamond earrings": (1, 1142),
    "diamond necklace (golden)": (1, 1162),
    "diamond bracelet": (1, 1182),
    "krampus minion earrings": (1, 1202),
    "candied staff": (1, 1222),
    # Wooden Items (button 21)
    "nunchaku": (21, 2),
    "jointing plane": (21, 22),
    "moulding planes": (21, 42),
    "smoothing plane": (21, 62),
    "clock frame": (21, 82),
    "axle": (21, 102),
    "rolling pin": (21, 122),
    "ramrod": (21, 142),
    "softened reeds": (21, 162),
    "round basket": (21, 182),
    "bushel": (21, 202),
    "small bushel": (21, 222),
    "picnic basket": (21, 242),
    "winnowing basket": (21, 262),
    "square basket": (21, 282),
    "basket": (21, 302),
    "tall round basket": (21, 322),
    "small square basket": (21, 342),
    "tall basket": (21, 362),
    "small round basket": (21, 382),
    "enchanted picnic basket": (21, 402),
    # Tools (button 41)
    "scissors": (41, 2),
    "mortar and pestle": (41, 22),
    "scorp": (41, 42),
    "tinker's tools": (41, 62),
    "hatchet": (41, 82),
    "draw knife": (41, 102),
    "sewing kit": (41, 122),
    "saw": (41, 142),
    "dovetail saw": (41, 162),
    "froe": (41, 182),
    "shovel": (41, 202),
    "hammer": (41, 222),
    "tongs": (41, 242),
    "smith's hammer": (41, 262),
    "sledge hammer": (41, 282),
    "inshave": (41, 302),
    "pickaxe": (41, 322),
    "lockpick": (41, 342),
    "skillet": (41, 362),
    "flour sifter": (41, 382),
    "fletcher's tools": (41, 402),
    "mapmaker's pen": (41, 422),
    "scribe's pen": (41, 442),
    "clippers": (41, 462),
    "metal container engraving tool": (41, 482),
    "pitchfork": (41, 502),
    # Parts (button 61)
    "gears": (61, 2),
    "clock parts": (61, 22),
    "barrel tap": (61, 42),
    "springs": (61, 62),
    "sextant parts": (61, 82),
    "barrel hoops": (61, 102),
    "hinge": (61, 122),
    "bola balls": (61, 142),
    "jeweled filigree": (61, 162),
    # Utensils (button 81)
    "butcher knife": (81, 2),
    "spoon (left)": (81, 22),
    "spoon (right)": (81, 42),
    "plate": (81, 62),
    "fork (left)": (81, 82),
    "fork (right)": (81, 102),
    "cleaver": (81, 122),
    "knife (left)": (81, 142),
    "knife (right)": (81, 162),
    "goblet": (81, 182),
    "pewter mug": (81, 202),
    "pewter bowl": (81, 222),
    "a plant bowl": (81, 242),
    "skinning knife": (81, 262),
    "gargish cleaver": (81, 282),
    "gargish butcher's knife": (81, 302),
    # Miscellaneous (button 101)
    "key ring": (101, 2),
    "candelabra": (101, 22),
    "scales": (101, 42),
    "iron key": (101, 62),
    "globe": (101, 82),
    "spyglass": (101, 102),
    "lantern": (101, 122),
    "heating stand": (101, 142),
    "shoji lantern": (101, 162),
    "paper lantern": (101, 182),
    "round paper lantern": (101, 202),
    "wind chimes": (101, 222),
    "fancy wind chimes": (101, 242),
    "ter-mur style candelabra": (101, 262),
    "communication crystal": (101, 282),
    "gorgon lens": (101, 302),
    "a scale collar": (101, 322),
    "dragon lamp": (101, 342),
    "stained glass lamp": (101, 362),
    "tall double lamp": (101, 382),
    "curled metal sign hanger": (101, 402),
    "flourished metal sign hanger": (101, 422),
    "inward curled metal sign hanger": (101, 442),
    "end curled metal sign hanger": (101, 462),
    "left metal door (s in)": (101, 482),
    "right metal door (s in)": (101, 502),
    "left metal door (e out)": (101, 522),
    "right metal door (e out)": (101, 542),
    "currency wall safe": (101, 562),
    "left metal door (e in)": (101, 582),
    "right metal door (e in)": (101, 602),
    "left metal door (s out)": (101, 622),
    "right metal door (s out)": (101, 642),
    "kotl power core": (101, 662),
    "weathered bronze globe sculpture": (101, 682),
    "weathered bronze man on a bench sculpture": (101, 702),
    "weathered bronze fairy sculpture": (101, 722),
    "weathered bronze archer sculpture": (101, 742),
    "barbed whip": (101, 762),
    "spiked whip": (101, 782),
    "bladed whip": (101, 802),
    # Assemblies (button 121)
    "axle with gears": (121, 2),
    # "clock parts": (121, 22),  listed again, the first kept
    # "sextant parts": (121, 42),  listed again, the first kept
    "clock (right)": (121, 62),
    "clock (left)": (121, 82),
    "sextant": (121, 102),
    "bola": (121, 122),
    "potion keg": (121, 142),
    "leather wolf assembly": (121, 162),
    "clockwork scorpion assembly": (121, 182),
    "vollem assembly": (121, 202),
    "hitching rope": (121, 222),
    "hitching post (replica)": (121, 242),
    "arcanic rune stone": (121, 262),
    "void orb": (121, 282),
    "advanced training dummy (south)": (121, 302),
    "advanced training dummy (east)": (121, 322),
    "distillery (south)": (121, 342),
    "distillery (east)": (121, 362),
    "kotl automaton": (121, 382),
    "telescope": (121, 402),
    "oracle of the sea": (121, 422),
    # Traps (button 141)
    "dart trap": (141, 2),
    "poison trap": (141, 22),
    "explosion trap": (141, 42),
    # Magic Jewelry (button 161)
    "brilliant amber bracelet": (161, 2),
    "fire ruby bracelet": (161, 22),
    "dark sapphire bracelet": (161, 42),
    "white pearl bracelet": (161, 62),
    "ecru citrine ring": (161, 82),
    "blue diamond ring": (161, 102),
    "perfect emerald ring": (161, 122),
    "turquoise ring": (161, 142),
    "resilient bracer": (161, 162),
    "essence of battle": (161, 182),
    "pendant of the magi": (161, 202),
    "dr. spector's lenses": (161, 222),
    "bracelet of primal consumption": (161, 242),
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

# The whole gump and journal behind a report, appended here so the game window stays quiet. "" turns
# it off; a bare name lands beside the script.
NOTES_PATH = "tinkering-notes.log"
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
