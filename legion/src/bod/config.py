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

# Named apart from INGOT_HUES rather than derived from it: a stack is matched on its name first, so
# this has to hold every material, including any whose hue is not known
INGOT_MATERIALS = sorted(set(INGOT_HUES.values()), key=len, reverse=True)

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
    # Stripped in turn, so one list covers every trade: the deed is parsed before the trade is known
    "material_nouns": ["ingots", "boards"],
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

# Alchemy deeds: the mortar's menu, as craft-map.py read it on 2026-09-13. Same button layout as
# the smith menu down to CANCEL MAKE on 227, and no material page. A row's details page reads
# 'MAKE NOW MAKE NUMBER MAKE MAX BACK' on 1, 2, 3, 0, and names the reagent and the bottle
ALCHEMY_SKILL_NAMES = ["Alchemy"]
ALCHEMY_TOOL_GRAPHICS = set([0x0E9B])
ALCHEMY_TOOL_NAME_WORDS = ["mortar"]
ALCHEMY_CRAFT_TITLE_TEXT = ["ALCHEMY", "ALCHEMIST"]

ALCHEMY_CATEGORY_NAMES = [
    "healing and curative",
    "enhancement",
    "toxic",
    "explosive",
    "strange brew",
    "ingredients",
    "skill tinctures",
]

# Keyed as the deed names the potion
ALCHEMY_RECIPES = {
    # Healing and Curative (button 1)
    "refresh potion": (1, 2),
    "greater refreshment potion": (1, 22),
    "lesser heal potion": (1, 42),
    "heal potion": (1, 62),
    "greater heal potion": (1, 82),
    "lesser cure potion": (1, 102),
    "cure potion": (1, 122),
    "greater cure potion": (1, 142),
    # Enhancement (button 21)
    "agility potion": (21, 2),
    "greater agility potion": (21, 22),
    "night sight potion": (21, 42),
    "strength potion": (21, 62),
    "greater strength potion": (21, 82),
    "invisibility potion": (21, 102),
    # Toxic (button 41)
    "lesser poison potion": (41, 2),
    "poison potion": (41, 22),
    "greater poison potion": (41, 42),
    "deadly poison potion": (41, 62),
    # Explosive (button 61)
    "lesser explosion potion": (61, 2),
    "explosion potion": (61, 22),
    "greater explosion potion": (61, 42),
    "conflagration potion": (61, 62),
    "greater conflagration potion": (61, 82),
    "confusion blast potion": (61, 102),
    "greater confusion blast potion": (61, 122),
}

# Stock art, unverified on UOAlive
REAGENT_KINDS = {
    "empty bottles": set([0x0F0E]),
    "black pearl": set([0x0F7A]),
    "blood moss": set([0x0F7B]),
    "garlic": set([0x0F84]),
    "ginseng": set([0x0F85]),
    "mandrake root": set([0x0F86]),
    "nightshade": set([0x0F88]),
    "spider's silk": set([0x0F8D]),
    "sulfurous ash": set([0x0F8C]),
    "grave dust": set([0x0F8F]),
    "pig iron": set([0x0F8A]),
}


def _potion(reagent, count):
    return {"empty bottles": 1, reagent: count}


# Per potion, stock RunUO counts. Only greater heal is read off the menu's details page, which says
# 'Ginseng 7 Empty Bottles 1'; the rest follow the stock table
POTION_COST = {
    "refresh potion": _potion("black pearl", 1),
    "greater refreshment potion": _potion("black pearl", 5),
    "lesser heal potion": _potion("ginseng", 1),
    "heal potion": _potion("ginseng", 3),
    "greater heal potion": _potion("ginseng", 7),
    "lesser cure potion": _potion("garlic", 1),
    "cure potion": _potion("garlic", 3),
    "greater cure potion": _potion("garlic", 6),
    "agility potion": _potion("blood moss", 1),
    "greater agility potion": _potion("blood moss", 3),
    "night sight potion": _potion("spider's silk", 1),
    "strength potion": _potion("mandrake root", 2),
    "greater strength potion": _potion("mandrake root", 5),
    "invisibility potion": {"empty bottles": 1, "blood moss": 4, "nightshade": 3},
    "lesser poison potion": _potion("nightshade", 1),
    "poison potion": _potion("nightshade", 2),
    "greater poison potion": _potion("nightshade", 4),
    "deadly poison potion": _potion("nightshade", 8),
    "lesser explosion potion": _potion("sulfurous ash", 3),
    "explosion potion": _potion("sulfurous ash", 5),
    "greater explosion potion": _potion("sulfurous ash", 10),
    "conflagration potion": _potion("grave dust", 5),
    "greater conflagration potion": _potion("grave dust", 10),
    "confusion blast potion": _potion("pig iron", 5),
    "greater confusion blast potion": _potion("pig iron", 10),
}

# The shard pours a craft into a keg of that potion instead of a bottle, so a keg is its own stop
ALCHEMY_OUTCOME_TEXT = [
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
    ("keg", ["pour it into a keg"]),
    (
        "made",
        [
            "You pour the potion into a bottle",
            "You create the item",
            "You create an exceptional",
            "You put the",
        ],
    ),
    (
        "noMaterial",
        [
            "You don't have the components",
            "You do not have the components",
            "You don't have the resources",
            "You do not have the resources",
            "enough empty bottles",
            "enough black pearl",
            "enough blood moss",
            "enough bloodmoss",
            "enough garlic",
            "enough ginseng",
            "enough mandrake",
            "enough nightshade",
            "enough spider",
            "enough sulfurous",
            "enough grave dust",
            "enough pig iron",
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

# Carpentry deeds: the menu's rows as craft-map.py read them on 2026-09-13, transcribed from
# src/carpentry rather than imported - build.py refuses two modules that define the same top-level
# name, and both configs carry RECIPES, CATEGORY_NAMES and OUTCOME_TEXT
CARPENTRY_SKILL_NAMES = ["Carpentry"]
CARPENTRY_TOOL_GRAPHICS = set([
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

# Whole words: 'hammer' is left out on purpose, a smith's hammer carries it
CARPENTRY_TOOL_NAME_WORDS = ["saw", "plane", "nails", "froe", "inshave", "scorp"]

CARPENTRY_CRAFT_TITLE_TEXT = ["CARPENTRY", "CARPENTER"]

CARPENTRY_CATEGORY_NAMES = [
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

# Hue is deliberately not matched: a shard with special woods hues them, and those craft too
BOARD_GRAPHICS = set([0x1BD7, 0x1BD9, 0x1BDA, 0x1BDB])

# No name words to go with the graphics: pack_contents reaches into the bag, and a crafted
# 'bulletin board' in there would otherwise be counted as board stock
CARPENTRY_STOCK_WORDS = []

# What a deed that names no wood wants, and the menu row it is set back to. Not None: that is the
# flag for a trade with no material page at all, and carpentry has one
PLAIN_WOOD = "regular"

WOOD_TYPES = ["oak", "ash", "yew", "heartwood", "bloodwood", "frostwood"]

# Named apart from WOOD_HUES because that table is short: a stack is matched on its name first
WOOD_MATERIALS = [PLAIN_WOOD] + WOOD_TYPES

# The material page's rows in stock order, for a page whose text cannot be read
WOOD_ORDER = [PLAIN_WOOD] + WOOD_TYPES

# The deed's wording first, then how the menu row and the item's tooltip may shorten it
WOOD_ALIASES = {
    PLAIN_WOOD: ["wood", "plain"],
}

# Unverified: the smith page's toggle, which the carpentry page need not carry. A marker that is
# not on the page leaves the split untrimmed, and select() logs the page when no row reads the wood
WOOD_ROWS_AFTER = "do not color"

# For the stack whose tooltip has not arrived. Incomplete on purpose: an unknown hue is reported
# as such, never treated as regular
WOOD_HUES = {
    0: PLAIN_WOOD,
    1191: "ash",
    2010: "oak",
}

CARPENTRY_RECIPES = {
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

# Boards per piece from uoalive.com/wiki/Carpentry, keyed as the deed names the item. Items that
# need more than boards are left out - the keg wants staves, the pirate shield and the display case
# want ingots, every instrument but the flute wants cloth, and the woodland and darkwood armour
# wants reagents. A left-out item is a preflight note, not a refusal, so an unclear row is omitted
# rather than guessed: understating only runs the pack dry mid-batch, overstating refuses the run.
BOARD_COST = {
    # Other (button 1)
    "barrel staves": 5,
    "barrel lid": 4,
    "short music stand (left)": 15,
    "short music stand (right)": 15,
    "tall music stand (left)": 20,
    "tall music stand (right)": 20,
    "easel (south)": 20,
    "easel (east)": 20,
    "easel (north)": 20,
    "arcanist statue (south)": 250,
    "arcanist statue (east)": 250,
    "warrior statue (south)": 250,
    "warrior statue (east)": 250,
    "squirrel statue (south)": 250,
    "squirrel statue (east)": 250,
    "giant replica acorn": 35,
    "mounted dread horn": 50,
    "an incubator": 100,
    "a chicken coop": 150,
    "dark wooden sign hanger": 5,
    "light wooden sign hanger": 5,
    # Furniture (button 21)
    "foot stool": 9,
    "stool": 9,
    "straw chair": 13,
    "wooden chair": 13,
    "vesper-style chair": 15,
    "trinsic-style chair": 15,
    "wooden bench": 17,
    "wooden throne": 17,
    "magincia-style throne": 19,
    "small table": 17,
    "writing table": 17,
    "yew-wood table": 27,
    "large table": 23,
    "elegant low table": 35,
    "plain low table": 35,
    "ornate table (south)": 60,
    "ornate table (east)": 60,
    "hardwood table (south)": 50,
    "hardwood table (east)": 50,
    "elven podium": 20,
    "ornate elven chair": 30,
    "cozy elven chair": 40,
    "reading chair": 30,
    "ter-mur style chair": 40,
    "ter-mur style table": 50,
    # Containers (button 41)
    "wooden box": 10,
    "small crate": 8,
    "medium crate": 15,
    "large crate": 18,
    "wooden chest": 20,
    "wooden shelf": 25,
    "armoire": 35,
    "plain wooden chest": 30,
    "ornate wooden chest": 30,
    "gilded wooden chest": 30,
    "wooden footlocker": 30,
    "finished wooden chest": 30,
    "tall cabinet": 35,
    "short cabinet": 35,
    "elegant armoire": 40,
    "maple armoire": 40,
    "cherry armoire": 40,
    "arcane bookshelf (south)": 80,
    "arcane bookshelf (east)": 80,
    "ornate elven chest (south)": 40,
    "ornate elven chest (east)": 40,
    "elven wash basin (south)": 40,
    "elven wash basin (east)": 40,
    "elven dresser (south)": 45,
    "elven dresser (east)": 45,
    "elven armoire (fancy)": 60,
    "elven armoire (simple)": 60,
    "rarewood chest": 30,
    "decorative box": 25,
    "gargish chest": 30,
    "empty liquor barrel": 50,
    # Weapons (button 61)
    "shepherd's crook": 7,
    "quarter staff": 6,
    "gnarled staff": 7,
    "bokuto": 6,
    "fukiya": 8,
    "tetsubo": 10,
    "wild staff": 16,
    "gargish gnarled staff": 7,
    "club": 10,
    "black staff": 9,
    # Armor (button 81)
    "wooden shield": 9,
    "gargish wooden shield": 9,
    # Instruments (button 101)
    "bamboo flute": 15,
    # Misc. Add-ons (button 121)
    "bulletin board": 50,
    "parrot perch": 50,
    "elven loveseat (east)": 50,
    "elven loveseat (south)": 50,
    "alchemist table (south)": 70,
    "alchemist table (east)": 70,
    "dartboard (south)": 5,
    "dartboard (east)": 5,
    "ballot box": 5,
    "gargish couch (east)": 75,
    "gargish couch (south)": 75,
    "gargish short table": 60,
    "long table (south)": 80,
    "long table (east)": 80,
    "ter-mur style dresser (east)": 60,
    "ter-mur style dresser (south)": 60,
    "rustic bench (south)": 35,
    "rustic bench (east)": 35,
    "plain wooden shelf (south)": 15,
    "plain wooden shelf (east)": 15,
    "fancy wooden shelf (south)": 15,
    "fancy wooden shelf (east)": 15,
    "wooden table (south)": 20,
    "wooden table (east)": 20,
    "long wooden table (south)": 80,
    "long wooden table (east)": 80,
    # Tailoring and Cooking (button 141)
    "elven oven (south)": 80,
    "elven oven (east)": 80,
    # Anvils and Forges (button 161)
    "elven forge": 200,
}

# Ordered: 'failed' before 'made' because "You failed to create the item" contains "create the item"
CARPENTRY_OUTCOME_TEXT = [
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
            # An exceptional craft says nothing else, and went unread as a result
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

# Tinkering deeds: the menu's rows as craft-map.py read them on 2026-09-13, transcribed from
# src/tinkering rather than imported - build.py refuses two modules that define the same top-level
# name, and both configs carry RECIPES, CATEGORY_NAMES and OUTCOME_TEXT. A tinker spends the smith's
# ingots, so the material page, hues and aliases above are the ones this trade uses too.
TINKERING_SKILL_NAMES = ["Tinkering"]

# Stock art, unverified on UOAlive: an art learned by name joins the set
TINKERING_TOOL_GRAPHICS = set([0x1EB8, 0x1EB9])
TINKERING_TOOL_NAME_WORDS = ["tinker", "tinkers"]

TINKERING_CRAFT_TITLE_TEXT = ["TINKERING", "TINKER"]

# The CATEGORIES rows, lowercased, as craft-map.py read them off UOAlive's menu
TINKERING_CATEGORY_NAMES = [
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

# (category button, row button) for every row, as craft-map.py read them off UOAlive's menu. Run
# craft-map.py again and paste its block over this one when the menu changes.
TINKERING_RECIPES = {
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
    # As the deed words a row the menu names otherwise. The deed uses the item's own name, the menu
    # its recipe's: 'frypan' is made by the skillet row and 'arrow fletching' by the fletcher's
    # tools row, and the utensils the menu brackets left and right the deed names bare.
    # uo.com/wiki/ultima-online-wiki/skills/tinkering/tinker-bulk-orders lists the four groups a
    # large tinker deed draws from. Every item in them is below or above except 'earrings', which
    # the menu only offers gemmed, one row per gem - an earrings deed stops on noRow by design
    # rather than spending a gem on a guess
    "spoon": (81, 22),
    "fork": (81, 82),
    "knife": (81, 142),
    "frypan": (41, 362),
    "arrow fletching": (41, 402),
}

# Ingots per piece from uoalive.com/wiki/Tinkering, keyed as the deed names the item. Only the rows
# whose whole cost is ingots: a number is ingots of the deed's material, so anything wanting gems,
# boards, shafts or a part made first is left out - the gemmed and magic jewelry, every wooden item,
# the paper and shoji lanterns, the candied staff, the three traps, every assembly, the jewelled
# filigree, the engraving tool, the lamps, the kotl core, the gorgon lens and the scale collar. The
# four weathered bronze sculptures want 200 *bronze* ingots, which a plain number cannot say. A
# left-out item is a preflight note, not a refusal.
TINKERING_INGOT_COST = {
    # Jewelry (button 1)
    "ring": 3, "bracelet": 3, "gargish necklace": 3, "gargish bracelet": 3, "gargish ring": 3,
    "gargish earrings": 3, "krampus minion earrings": 3,
    # Tools (button 41)
    "scissors": 2, "mortar and pestle": 3, "scorp": 2, "tinker's tools": 2, "hatchet": 4,
    "draw knife": 2, "sewing kit": 2, "saw": 4, "dovetail saw": 4, "froe": 2, "shovel": 4,
    "hammer": 1, "tongs": 1, "smith's hammer": 4, "sledge hammer": 4, "inshave": 2, "pickaxe": 4,
    "lockpick": 1, "skillet": 4, "flour sifter": 3, "fletcher's tools": 3, "mapmaker's pen": 1,
    "scribe's pen": 1, "clippers": 4, "pitchfork": 8,
    # Parts (button 61)
    "gears": 2, "clock parts": 1, "barrel tap": 2, "springs": 2, "sextant parts": 4,
    "barrel hoops": 5, "hinge": 2, "bola balls": 10,
    # Utensils (button 81)
    "butcher knife": 2, "spoon (left)": 1, "spoon (right)": 1, "plate": 2, "fork (left)": 1,
    "fork (right)": 1, "cleaver": 3, "knife (left)": 1, "knife (right)": 1, "goblet": 2,
    "pewter mug": 2, "pewter bowl": 2, "skinning knife": 2, "gargish cleaver": 3,
    "gargish butcher's knife": 2,
    # Miscellaneous (button 101)
    "key ring": 2, "candelabra": 4, "scales": 4, "iron key": 3, "globe": 4, "spyglass": 4,
    "lantern": 4, "heating stand": 4, "wind chimes": 15, "fancy wind chimes": 15,
    "ter-mur style candelabra": 4, "curled metal sign hanger": 8,
    "flourished metal sign hanger": 8, "inward curled metal sign hanger": 8,
    "end curled metal sign hanger": 8, "left metal door (s in)": 8, "right metal door (s in)": 8,
    "left metal door (e out)": 8, "right metal door (e out)": 8, "left metal door (e in)": 8,
    "right metal door (e in)": 8, "left metal door (s out)": 8, "right metal door (s out)": 8,
    "currency wall safe": 20,
    # As the deed words the rows above: the bracketed utensils, the skillet and the fletcher's tools
    "spoon": 1, "fork": 1, "knife": 1, "frypan": 4, "arrow fletching": 3,
}

# Ordered: 'failed' before 'made' because "You failed to create the item" contains "create the item"
TINKERING_OUTCOME_TEXT = [
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

# The first trade whose recipes make every item on the deed fills it. A number cost is ingots of
# the deed's material; a dict cost is stock per kind. plain is what a deed with no material line
# wants: None means there is no material page to press
TRADES = [
    ("smith", {
        "skill_names": SKILL_NAMES,
        "tool_noun": "smith's tool",
        "tool_graphics": TOOL_GRAPHICS,
        "tool_words": TOOL_NAME_WORDS,
        "tool_preference": TOOL_PREFERENCE,
        "title": CRAFT_TITLE,
        "title_text": CRAFT_TITLE_TEXT,
        "category_names": CATEGORY_NAMES,
        "recipes": RECIPES,
        "costs": INGOT_COST,
        "kinds": {},
        "stock_graphics": INGOT_GRAPHICS,
        "stock_words": INGOT_NAME_WORDS,
        "stock_noun": "ingots",
        "materials": INGOT_MATERIALS,
        "hues": INGOT_HUES,
        "material_aliases": MATERIAL_ALIASES,
        "material_order": MATERIAL_ORDER,
        "material_rows_after": MATERIAL_ROWS_AFTER,
        "outcome_text": OUTCOME_TEXT,
        "salvage": SALVAGE_AT_END,
        "plain": PLAIN_MATERIAL,
    }),
    # Every potion cost is a dict, so the stock keys are empty rather than unused: reagents are
    # counted by art through kinds, and an ingot in the pack is not this run's stock
    ("alchemy", {
        "skill_names": ALCHEMY_SKILL_NAMES,
        "tool_noun": "mortar and pestle",
        "tool_graphics": ALCHEMY_TOOL_GRAPHICS,
        "tool_words": ALCHEMY_TOOL_NAME_WORDS,
        "tool_preference": None,
        "title": ALCHEMY_CRAFT_TITLE_TEXT[0],
        "title_text": ALCHEMY_CRAFT_TITLE_TEXT,
        "category_names": ALCHEMY_CATEGORY_NAMES,
        "recipes": ALCHEMY_RECIPES,
        "costs": POTION_COST,
        "kinds": REAGENT_KINDS,
        "stock_graphics": set(),
        "stock_words": [],
        "stock_noun": None,
        "materials": [],
        "hues": {},
        "material_aliases": {},
        "material_order": [],
        # Never read behind a plain of None, and "" leaves the row split a no-op where None throws
        "material_rows_after": "",
        "outcome_text": ALCHEMY_OUTCOME_TEXT,
        "salvage": False,
        "plain": None,
    }),
    # Boards are one pool told apart by the wood they are, so the cost is a number and kinds is
    # empty - the same shape as the smith's ingots
    ("carpentry", {
        "skill_names": CARPENTRY_SKILL_NAMES,
        "tool_noun": "carpentry tool",
        "tool_graphics": CARPENTRY_TOOL_GRAPHICS,
        "tool_words": CARPENTRY_TOOL_NAME_WORDS,
        "tool_preference": None,
        "title": CARPENTRY_CRAFT_TITLE_TEXT[0],
        "title_text": CARPENTRY_CRAFT_TITLE_TEXT,
        "category_names": CARPENTRY_CATEGORY_NAMES,
        "recipes": CARPENTRY_RECIPES,
        "costs": BOARD_COST,
        "kinds": {},
        "stock_graphics": BOARD_GRAPHICS,
        "stock_words": CARPENTRY_STOCK_WORDS,
        "stock_noun": "boards",
        "materials": WOOD_MATERIALS,
        "hues": WOOD_HUES,
        "material_aliases": WOOD_ALIASES,
        "material_order": WOOD_ORDER,
        "material_rows_after": WOOD_ROWS_AFTER,
        "outcome_text": CARPENTRY_OUTCOME_TEXT,
        "salvage": False,
        "plain": PLAIN_WOOD,
    }),
    # A tinker spends the smith's ingot pool and needs no forge, so the stock tables above are
    # reused whole and the outcome set carries no noAnvil. Nothing salvages a pewter mug
    ("tinkering", {
        "skill_names": TINKERING_SKILL_NAMES,
        "tool_noun": "tinker's tools",
        "tool_graphics": TINKERING_TOOL_GRAPHICS,
        "tool_words": TINKERING_TOOL_NAME_WORDS,
        "tool_preference": None,
        "title": TINKERING_CRAFT_TITLE_TEXT[0],
        "title_text": TINKERING_CRAFT_TITLE_TEXT,
        "category_names": TINKERING_CATEGORY_NAMES,
        "recipes": TINKERING_RECIPES,
        "costs": TINKERING_INGOT_COST,
        "kinds": {},
        "stock_graphics": INGOT_GRAPHICS,
        "stock_words": INGOT_NAME_WORDS,
        "stock_noun": "ingots",
        "materials": INGOT_MATERIALS,
        "hues": INGOT_HUES,
        "material_aliases": MATERIAL_ALIASES,
        "material_order": MATERIAL_ORDER,
        "material_rows_after": MATERIAL_ROWS_AFTER,
        "outcome_text": TINKERING_OUTCOME_TEXT,
        "salvage": False,
        "plain": PLAIN_MATERIAL,
    }),
]
