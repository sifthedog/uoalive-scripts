from uo.notoriety import CALL_ON_SIGHT, HOSTILE
from uo.phrases import (ATTACK_TEXT, GUARD_ZONE_TEXT, NO_GUARDS_TEXT, SAVE_DONE_TEXT, SAVING_TEXT,
                        STOPPED, THROTTLED_TEXT, UNGUARDED_TEXT, UNSKILLED_TEXT)
from uo.timings import (HEARTBEAT_EVERY, LOG_EVERY, PACK_LIMIT, SAVE_POLL, SAVE_WAIT, STALL_STOP,
                        STALL_WARN, STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

# Whole words and a list, so a plural still matches
PICKAXE_NAMES = ["pickaxe", "pickaxes"]

# Worth setting only if the spares are somewhere ItemsInContainer's recursive read does not reach
SPARE_BAG_SERIAL = None

# Land carries no name, so the table is the whole answer for it. Stock RunUO bands and a hypothesis
# about this shard - a dead-end run prints the arts it actually saw.
ORE_TILE_GRAPHICS = set()

for _first, _last in [(220, 251), (1339, 1359), (1361, 1383), (1386, 1394)]:
    for _art in range(_first, _last + 1):
        ORE_TILE_GRAPHICS.add(_art)

# A seed only - a refusal learned on the shard goes into the run's memory rather than back in here
NOT_ORE_GRAPHICS = set()

# Cave floors are statics, and those the client can name. 'rock' also names the pebbles scattered
# over half the world, which is the cheap direction to be wrong in: the first swing bans the art.
ORE_STATIC_NAME = ["cave", "rock", "mountain", "ore"]

# Where walking stops and swinging starts, not a range the shard enforces - the swing names no tile
MINE_RANGE = 2

# Distance is Chebyshev over x and y, so a mountain face 40 z up is 'one tile away' and the walk at
# it never closes
MINE_Z_RANGE = 20

SCAN_RADIUS = 12
SURVEY_ARTS = 15

# How long one blocking pathfind may take, in place of the web client's per-tile step budget
PATHFIND_TIMEOUT = 10

# Cycles spent walking to one vein before it is written off, where the web client counted single
# steps: a blocking pathfind covers the whole route in one
MAX_VEIN_WALKS = 4

# GetPath costs a call per candidate, where the web client's flood fill answered every tile at
# once, so only this many of the nearest matches are asked for a route
MAX_PATH_PROBES = 24

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms
RESPAWN_DELAY = 25 * 60.0
UNREACHABLE_DELAY = 5 * 60.0

# A swing plays its animation before the result arrives, so this has to outlast the animation
DIG_TIMEOUT = 8.0

DIG_TARGET_TIMEOUT = 4.0
DIG_TARGET_POLL = 0.1

# Waited on as the cursor itself, because HasTarget cannot be relied on - get this wrong and every
# swing reports no target cursor
DIG_PROMPT_TEXT = ["Where do you wish to dig"]

# A short window for a refusal worded a moment late; the journal was cleared just before the swing
NO_CURSOR_READ = 0.5

# A set to match against and nothing more: a pile of 33 arrives wearing the art the stock tables
# call a single, so a stack's size comes from item.Amount alone
ORE_GRAPHICS = set([0x19B7, 0x19BA, 0x19B9, 0x19B8])

# A whole word: 'ore' inside 'sycamore' would put something in the smelter
ORE_NAME_WORD = "ore"

INGOT_GRAPHICS = set([0x1BEF, 0x1BF0, 0x1BF1, 0x1BF2])

COMBINE_DELAY = 0.7
COMBINE_TIMEOUT = 2.0
COMBINE_POLL = 0.2
MAX_COMBINE_ATTEMPTS = 12

# ItemNameAndProps takes whole seconds
OPL_TIMEOUT = 1

ORE_METALS = set(
    [
        "iron",
        "dull copper",
        "shadow iron",
        "copper",
        "bronze",
        "gold",
        "agapite",
        "verite",
        "valorite",
    ]
)

# Letters only, so the divider the client draws between tooltip blocks is not read as a metal.
# The line must start with a letter and hold nothing but letters and these.
METAL_LINE_EXTRA = " '-"

# 'ore' because the name line is that word on its own
NOT_METAL_WORDS = set(
    [
        "blessed",
        "cursed",
        "insured",
        "exceptional",
        "newbie",
        "antique",
        "brittle",
        "unmovable",
        "weight",
        "contents",
        "ore",
    ]
)

METAL_MISSES = 3
METAL_ASKS = 3

# A tooltip that answers with no metal line is plain iron, and it has to key the same as one saying
# 'Iron' or two piles of the one metal sit apart for the whole run
PLAIN_METAL = "iron"

DIFFERENT_ORE_TEXT = ["You cannot combine ores of different metals"]

# A swing's ore arrives after the sentence that announced it
ORE_SETTLE_TIMEOUT = 1.5
ORE_SETTLE_POLL = 0.15

FIRE_BEETLE_GRAPHICS = set([0xA9])
FIRE_BEETLE_SERIAL = None

# A cursor at startup, so the beetle is chosen rather than guessed at by body and renamability -
# which picks a stranger's pet if theirs is the nearer one. ESC falls back to that search.
PICK_BEETLE = True

BEETLE_SCAN_RADIUS = 18
SMELT_RANGE = 2

# Waiting on a person rather than on the shard, unlike TARGET_TIMEOUT
PICK_TIMEOUT = 60.0

SMELT_DELAY = 0.7
SMELT_TIMEOUT = 4.0
SMELT_POLL = 0.2

# Two ore make an ingot, so a stack of one is refused - silently, in a way the pack diff cannot tell
# from a throttled attempt
MIN_SMELT_AMOUNT = 2

SMELT_ATTEMPTS = 3
MAX_SMELT_PASSES = 60

DISMOUNT_TIMEOUT = 2.0
DISMOUNT_POLL = 0.2
DISMOUNT_ATTEMPTS = 3

EQUIP_TIMEOUT = 2.0
EQUIP_POLL = 0.2
EQUIP_ATTEMPTS = 3

TARGET_TIMEOUT = 2.0

IDLE_POLL = 10.0
IDLE_LOG_EVERY = 60.0

MAX_CYCLES = 5000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_CURSOR = 20
MAX_NO_TOOL = 10

# Spots in a row with nothing in them before the run says ORE_TILE_GRAPHICS is probably wrong
NOTHING_NEARBY_HINT = 5

WATCH_FOR_TROUBLE = True

THREAT_RANGE = 12
GUARD_CALL = "guards"
GUARD_CALLS = 3
GUARD_CALL_DELAY = 10.0
GUARD_REPLY_WAIT = 0.8

# The smelt refusal is mining's own; the rest are the shard's general wording
SMELT_UNSKILLED_TEXT = ["You have no idea how to smelt this strange ore"] + UNSKILLED_TEXT


# Ordered, not a dict: InJournalAny answers yes/no, so the buckets are polled in order and the first
# holding a match wins. Guesses for a RunUO-family shard - correct them against the real journal.
OUTCOME_TEXT = [
    ("dug", ["You dig some", "You put", "You loosen some rocks"]),
    # Both wordings are in the wild: RunUO says metal, some shards say ore
    (
        "empty",
        [
            "There is no metal here to mine",
            "There is no ore here to mine",
            "You cannot mine there",
        ],
    ),
    # The shard answering about everything in reach rather than about a tile, which is what parks
    # the whole area and walks the character off
    (
        "nothingNearby",
        ["There are no harvestable resources nearby", "There is nothing here to harvest"],
    ),
    ("notOre", ["You can't mine that", "Try mining in rock", "You can only mine"]),
    ("tooFar", ["That is too far away", "You cannot reach that"]),
    ("notSeen", ["Target cannot be seen"]),
    # The ore is destroyed rather than dropped when this fires, so it triggers a consolidation
    ("packFull", ["Your backpack is full", "That container cannot hold more"]),
    ("wornOut", ["You have worn out your tool"]),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]
