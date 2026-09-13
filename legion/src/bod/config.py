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

# Used ahead of any other tool found
TOOL_PREFERENCE = set([0x0FBB, 0x0FBC])

# Opened at start so the client can see the tools inside. Matched as a name fragment.
TOOL_BAG_NAMES = ["salvage bag"]
OPEN_DELAY = 0.6

INGOT_GRAPHICS = set([0x1BF2, 0x1BEF])
INGOT_NAME_WORDS = ["ingot", "ingots"]

# What a deed that names no material wants, and the menu row it is set back to
PLAIN_MATERIAL = "iron"

# The material rows follow this toggle in the page's one-line text
MATERIAL_ROWS_AFTER = "do not color"

# The material page's rows in stock order, for a page whose text cannot be read
MATERIAL_ORDER = ["iron", "dull copper", "shadow iron", "copper", "bronze", "gold", "agapite",
                  "verite", "valorite"]

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

# Refuse to start on too few ingots or tool charges
CHECK_BEFORE_START = True
USES_TEXT = "uses remaining"

# Ingots per piece from uoalive.com/wiki/Blacksmithy, keyed as the deed names the item. Items
# that need more than ingots are left out.
INGOT_COST = {
    "ringmail gloves": 10, "ringmail leggings": 16, "ringmail sleeves": 14, "ringmail tunic": 18,
    "chainmail coif": 10, "chainmail leggings": 18, "chainmail tunic": 20,
    "platemail arms": 18, "platemail gloves": 12, "platemail gorget": 10, "platemail legs": 20,
    "platemail tunic": 25, "platemail": 25, "female plate": 20, "female platemail": 20,
    "platemail do": 28, "platemail haidate": 20, "platemail hiro sode": 16, "platemail mempo": 18,
    "platemail suneate": 20, "gargish amulet": 3, "gargish platemail arms": 18,
    "gargish platemail chest": 25, "gargish platemail kilt": 12, "gargish platemail leggings": 20,
    "dragon barding deed": 750,
    "bascinet": 15, "close helmet": 15, "helmet": 15, "norse helm": 15, "plate helm": 15,
    "chainmail hatsuburi": 20, "platemail hatsuburi": 20, "heavy platemail jingasa": 20,
    "light platemail jingasa": 20, "small platemail jingasa": 20,
    "decorative platemail kabuto": 25, "platemail battle kabuto": 25,
    "standard platemail kabuto": 25, "circlet": 6, "royal circlet": 6,
    "buckler": 10, "bronze shield": 12, "heater shield": 18, "metal shield": 14,
    "metal kite shield": 16, "tear kite shield": 8, "chaos shield": 25, "order shield": 25,
    "small plate shield": 12, "medium plate shield": 14, "large plate shield": 18,
    "gargish kite shield": 16, "gargish chaos shield": 25, "gargish order shield": 25,
    "axe": 14, "battle axe": 14, "double axe": 12, "executioner's axe": 14,
    "large battle axe": 12, "two handed axe": 16, "war axe": 16, "ornate axe": 18,
    "dual short axes": 24, "gargish axe": 14, "gargish battle axe": 14,
    "bardiche": 18, "bladed staff": 12, "double bladed staff": 16, "halberd": 20, "lance": 20,
    "pike": 12, "short spear": 6, "scythe": 14, "spear": 12, "war fork": 12,
    "dual pointed spear": 12, "gargish bardiche": 18, "gargish lance": 20, "gargish pike": 12,
    "gargish scythe": 14, "gargish war fork": 12,
    "bone harvester": 10, "broadsword": 10, "crescent blade": 14, "cutlass": 8, "dagger": 3,
    "katana": 8, "kryss": 8, "longsword": 12, "scimitar": 10, "viking sword": 14,
    "no-dachi": 18, "wakizashi": 8, "lajatang": 25, "daisho": 15, "tekagi": 12, "shuriken": 5,
    "kama": 14, "sai": 12, "radiant scimitar": 15, "war cleaver": 18, "elven spellblade": 14,
    "assassin spike": 9, "leafblade": 12, "rune blade": 15, "elven machete": 14,
    "bloodblade": 8, "shortblade": 12, "dread sword": 14, "gargish katana": 8,
    "gargish kryss": 8, "gargish bone harvester": 10, "gargish tekagi": 12, "gargish daisho": 15,
    "gargish talwar": 18, "gargish dagger": 3,
    "hammer pick": 16, "mace": 6, "maul": 10, "scepter": 10, "war mace": 14, "war hammer": 16,
    "diamond mace": 20, "disc mace": 20, "gargish maul": 10, "gargish war hammer": 16,
    "cannonball": 12, "boomerang": 5, "cyclone": 9, "soul glaive": 9, "metal keg": 25,
}

# Deeds in the pack, for the large flow: the stock art, or the name
DEED_GRAPHICS = set([0x2258])
DEED_NAME_WORDS = ["bulk order deed"]

# The Bulk Order Deed Box: one large deed in, the smalls and the large back in the pack
BOX_NAMES = ["bulk order deed box"]
MOVE_DELAY = 0.7
BOX_TIMEOUT = 10.0
BOX_POLL = 0.5

# The large deed's own gump: 2 raises a cursor for a filled small deed
LARGE_COMBINE_BUTTON = 2

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

# The CATEGORIES rows, lowercased, as craft-map.py read them off UOAlive's menu
CATEGORY_NAMES = [
    "metal armor",
    "helmets",
    "shields",
    "bladed",
    "axes",
    "polearms",
    "bashing",
    "cannons",
    "throwing",
    "miscellaneous",
]

CRAFT_TITLE = "BLACKSMITHY"
CRAFT_TITLE_TEXT = [CRAFT_TITLE, "BLACKSMITH"]
CRAFT_TITLE_FRAGMENTS = [phrase.lower() for phrase in CRAFT_TITLE_TEXT]
LAST_TEN_LABEL = "LAST TEN"

# Buttons are 1 + type + index * 20 on this shard: categories 1, 21, 41 ..., rows 2, 22, 42 ...,
# a row's details 3, 23, 43 ..., the material page on 7 with its rows on 6, 26, 46 ...
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MATERIAL_ROW_TYPE = 5
MATERIAL_BUTTON_TYPE = 6

MAX_MATERIAL_ROWS = 12

# (category button, row button) for every row, as craft-map.py read them off UOAlive's menu, keyed
# as the deed names the item. Run craft-map.py again and paste its block over this one when the
# menu changes.
RECIPES = {
    # Metal Armor (button 1)
    "ringmail gloves": (1, 2),
    "ringmail leggings": (1, 22),
    "ringmail sleeves": (1, 42),
    "ringmail tunic": (1, 62),
    "chainmail coif": (1, 82),
    "chainmail leggings": (1, 102),
    "chainmail tunic": (1, 122),
    "platemail arms": (1, 142),
    "platemail gloves": (1, 162),
    "platemail gorget": (1, 182),
    "platemail legs": (1, 202),
    "platemail (tunic)": (1, 222),
    "platemail (female)": (1, 242),
    "universal barding deed": (1, 262),
    "platemail mempo": (1, 282),
    "platemail do": (1, 302),
    "platemail hiro sode": (1, 322),
    "platemail suneate": (1, 342),
    "platemail haidate": (1, 362),
    "gargish platemail arms": (1, 382),
    "gargish platemail chest": (1, 402),
    "gargish platemail leggings": (1, 422),
    "gargish platemail kilt": (1, 442),
    # "gargish platemail arms": (1, 462),  listed again, the first kept
    # "gargish platemail chest": (1, 482),  listed again, the first kept
    # "gargish platemail leggings": (1, 502),  listed again, the first kept
    # "gargish platemail kilt": (1, 522),  listed again, the first kept
    "gargish amulet": (1, 542),
    "britches of warding": (1, 562),
    # Helmets (button 21)
    "bascinet": (21, 2),
    "close helmet": (21, 22),
    "helmet": (21, 42),
    "norse helm": (21, 62),
    "plate helm": (21, 82),
    "chainmail hatsuburi": (21, 102),
    "platemail hatsuburi": (21, 122),
    "heavy platemail jingasa": (21, 142),
    "light platemail jingasa": (21, 162),
    "small platemail jingasa": (21, 182),
    "decorative platemail kabuto": (21, 202),
    "platemail battle kabuto": (21, 222),
    "standard platemail kabuto": (21, 242),
    "circlet": (21, 262),
    "royal circlet": (21, 282),
    "gemmed circlet": (21, 302),
    # Shields (button 41)
    "buckler": (41, 2),
    "bronze shield": (41, 22),
    "heater shield": (41, 42),
    "metal shield": (41, 62),
    "metal kite shield": (41, 82),
    "tear kite shield": (41, 102),
    "chaos shield": (41, 122),
    "order shield": (41, 142),
    "small plate shield": (41, 162),
    "gargish kite shield": (41, 182),
    "large plate shield": (41, 202),
    "medium plate shield": (41, 222),
    "gargish chaos shield": (41, 242),
    "gargish order shield": (41, 262),
    # Bladed (button 61)
    "bone harvester": (61, 2),
    "broadsword": (61, 22),
    "crescent blade": (61, 42),
    "cutlass": (61, 62),
    "dagger": (61, 82),
    "katana": (61, 102),
    "kryss": (61, 122),
    "longsword": (61, 142),
    "scimitar": (61, 162),
    "viking sword": (61, 182),
    "paladin sword": (61, 202),
    "no-dachi": (61, 222),
    "wakizashi": (61, 242),
    "lajatang": (61, 262),
    "daisho": (61, 282),
    "tekagi": (61, 302),
    "shuriken": (61, 322),
    "kama": (61, 342),
    "sai": (61, 362),
    "radiant scimitar": (61, 382),
    "war cleaver": (61, 402),
    "elven spellblade": (61, 422),
    "assassin spike": (61, 442),
    "leafblade": (61, 462),
    "rune blade": (61, 482),
    "elven machete": (61, 502),
    "rune carving knife": (61, 522),
    "cold forged blade": (61, 542),
    "overseer sundered blade": (61, 562),
    "luminous rune blade": (61, 582),
    "true spellblade": (61, 602),
    "icy spellblade": (61, 622),
    "fiery spellblade": (61, 642),
    "spellblade of defense": (61, 662),
    "true assassin spike": (61, 682),
    "charged assassin spike": (61, 702),
    "magekiller assassin spike": (61, 722),
    "wounding assassin spike": (61, 742),
    "true leafblade": (61, 762),
    "luckblade": (61, 782),
    "magekiller leafblade": (61, 802),
    "leafblade of ease": (61, 822),
    "knight's war cleaver": (61, 842),
    "butcher's war cleaver": (61, 862),
    "serrated war cleaver": (61, 882),
    "true war cleaver": (61, 902),
    "adventurer's machete": (61, 922),
    "orcish machete": (61, 942),
    "machete of defense": (61, 962),
    "diseased machete": (61, 982),
    "runesabre": (61, 1002),
    "mage's rune blade": (61, 1022),
    "rune blade of knowledge": (61, 1042),
    "corrupted rune blade": (61, 1062),
    "true radiant scimitar": (61, 1082),
    "darkglow scimitar": (61, 1102),
    "icy scimitar": (61, 1122),
    "twinkling scimitar": (61, 1142),
    "bone machete": (61, 1162),
    "gargish katana": (61, 1182),
    "gargish kryss": (61, 1202),
    "gargish bone harvester": (61, 1222),
    "gargish tekagi": (61, 1242),
    "gargish daisho": (61, 1262),
    "dread sword": (61, 1282),
    "gargish talwar": (61, 1302),
    "gargish dagger": (61, 1322),
    "bloodblade": (61, 1342),
    "shortblade": (61, 1362),
    # Axes (button 81)
    "axe": (81, 2),
    "battle axe": (81, 22),
    "double axe": (81, 42),
    "executioner's axe": (81, 62),
    "large battle axe": (81, 82),
    "two handed axe": (81, 102),
    "war axe": (81, 122),
    "ornate axe": (81, 142),
    "guardian axe": (81, 162),
    "singing axe": (81, 182),
    "thundering axe": (81, 202),
    "heavy ornate axe": (81, 222),
    "gargish battle axe": (81, 242),
    "gargish axe": (81, 262),
    "dual short axes": (81, 282),
    # Polearms (button 101)
    "bardiche": (101, 2),
    "bladed staff": (101, 22),
    "double bladed staff": (101, 42),
    "halberd": (101, 62),
    "lance": (101, 82),
    "pike": (101, 102),
    "short spear": (101, 122),
    "scythe": (101, 142),
    "spear": (101, 162),
    "war fork": (101, 182),
    "gargish bardiche": (101, 202),
    "gargish war fork": (101, 222),
    "gargish scythe": (101, 242),
    "gargish pike": (101, 262),
    "gargish lance": (101, 282),
    "dual pointed spear": (101, 302),
    # Bashing (button 121)
    "hammer pick": (121, 2),
    "mace": (121, 22),
    "maul": (121, 42),
    "scepter": (121, 62),
    "war mace": (121, 82),
    "war hammer": (121, 102),
    "tessen": (121, 122),
    "diamond mace": (121, 142),
    "shard thrasher": (121, 162),
    "ruby mace": (121, 182),
    "emerald mace": (121, 202),
    "sapphire mace": (121, 222),
    "silver-etched mace": (121, 242),
    "gargish war hammer": (121, 262),
    "gargish maul": (121, 282),
    "gargish tessen": (121, 302),
    "disc mace": (121, 322),
    # Cannons (button 141)
    "cannonball": (141, 2),
    "grapeshot": (141, 22),
    "culverin": (141, 42),
    "carronade": (141, 62),
    # Throwing (button 161)
    "boomerang": (161, 2),
    "cyclone": (161, 22),
    "soul glaive": (161, 42),
    # Miscellaneous (button 181)
    "dragon gloves": (181, 2),
    "dragon helm": (181, 22),
    "dragon leggings": (181, 42),
    "dragon sleeves": (181, 62),
    "dragon breastplate": (181, 82),
    "crushed glass": (181, 102),
    "powdered iron": (181, 122),
    "metal keg": (181, 142),
    "exodus sacrificial dagger": (181, 162),
    "gloves of feudal grip": (181, 182),
    # As the deed words the two rows the menu brackets
    "platemail tunic": (1, 222),
    "platemail": (1, 222),
    "female plate": (1, 242),
    "female platemail": (1, 242),
}

# On the row's details page: 1 MAKE NOW, 2 MAKE NUMBER, 3 MAKE MAX. CANCEL MAKE is 1 + 6 + 11 * 20
MAKE_NUMBER_BUTTON = 2
CANCEL_MAKE_BUTTON = 227

# How long the shard's number prompt takes to arrive before it is answered
PROMPT_DELAY = 0.8

# A craft's animation plus the auto craft's own gap, for the batch's time budget
CRAFT_INTERVAL = 3.0

# No new piece and no failure line for this long ends a batch
BATCH_IDLE = 8.0

# 'Combine this deed with contained items', aimed at the bag; 2 is the one-item combine
BOD_COMBINE_BUTTON = 4
BOD_GUMP_TEXT = ["bulk order", "Combine this deed"]

# Once the deed is full: the bag's context menu entry, matched by its text
SALVAGE_AT_END = True
SALVAGE_ENTRIES = ["Salvage All"]
CONTEXT_TIMEOUT = 3.0
SALVAGE_SETTLE = 2.0

# Played once on this Mac when the deed is filled, so the client's sound setting does not matter.
# An empty list turns it off
DONE_SOUND = ["afplay", "/System/Library/Sounds/Glass.aiff"]

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

# The whole gump and journal behind a report, appended here so the game window stays quiet. "" turns
# it off; a bare name lands beside the script.
NOTES_PATH = "bod-notes.log"
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
    ("made", ["You create the item", "You create an exceptional", "You put the"]),
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

LARGE_COMBINE_TEXT = [
    ("combined", ["orders have been combined"]),
    ("full", ["maximum amount of requested items"]),
    ("notComplete", ["is not completed"]),
    ("wrongDeed", ["not a bulk order for this large request"]),
    ("notBulk", ["That is not a bulk order"]),
    ("exceptionalMismatch", ["must be of exceptional quality"]),
    ("materialMismatch", ["same resource type"]),
    ("amountMismatch", ["different requested amounts"]),
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
