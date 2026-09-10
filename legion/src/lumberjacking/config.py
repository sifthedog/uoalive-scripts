from uo.phrases import (AMBUSH_TEXT, SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT,
                        UNSKILLED_TEXT)
from uo.timings import (HEARTBEAT_EVERY, LOG_EVERY, PACK_LIMIT, SAVE_POLL, SAVE_WAIT, STALL_STOP,
                        STALL_WARN, STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

# Whole words and a list, never a substring: "axe" is inside "pickaxe", so a substring match picks
# the mining tool out of the pack the moment the real axe breaks - and a pickaxe is a working tool,
# so it equips, swings, and digs. Every RunUO lumberjacking tool carries the word 'axe' except the
# hatchet. The exclusion is what the veto below rests on, so add to it rather than trimming the list.
AXE_NAMES = ["axe", "axes", "hatchet", "hatchets"]
NOT_AXE_NAMES = ["pickaxe", "pickaxes", "shovel", "shovels"]

# Worth setting only if the spares are somewhere ItemsInContainer's recursive read does not reach
SPARE_BAG_SERIAL = None

# The client flags trees itself, so there is no table of arts to keep. Both sets ship empty and are
# the override for a shard the flag and the name both get wrong - a dead-end run prints what it saw.
TREE_GRAPHICS = set()
NOT_TREE_GRAPHICS = set()

# The fallback behind ApiStatic.IsTree, for a build that leaves the flag unset
TREE_NAME = ["tree"]

CHOP_RANGE = 2

# A tree 40 z up passes the 2D distance test and the walk at it never closes
CHOP_Z_RANGE = 20

SCAN_RADIUS = 12

# Swept only on the cycle the SCAN_RADIUS box comes back dry, which is the one that would stand still
ROAM_RADIUS = 24

SURVEY_ARTS = 15

# Whole seconds: the API takes an int here where API.Pause takes a float
PATHFIND_TIMEOUT = 10

# Cycles spent walking to one tree before it is written off
MAX_TREE_WALKS = 4

# How many of the nearest matches a sweep pays an API.GetPath for
MAX_PATH_PROBES = 24

# A stump grows back, so a tile that ran out of wood is a cooldown and never a write-off
REGROW_DELAY = 25 * 60.0
UNREACHABLE_DELAY = 5 * 60.0

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms
# How the target cursor is answered. True answers with yourself and lets the shard pick whatever is
# in reach, which is how mining.py and mine-here.py swing and what this shard is known to accept.
# False names the scanned tree's tile and its art instead, the way the ClassicUO script does - keep
# that for a shard where a self-target harvests nothing, and read the two notes at the branches in
# the loop, because which one is used changes what an 'empty' and a 'notTree' are evidence about.
AIM_AT_SELF = True

# A swing plays its animation before the result arrives, so this has to outlast the animation
CHOP_TIMEOUT = 8.0

CHOP_TARGET_TIMEOUT = 4.0
CHOP_TARGET_POLL = 0.1

# Waited on as the cursor itself, because HasTarget cannot be relied on - get this wrong and every
# swing reports no target cursor
CHOP_PROMPT_TEXT = [
    "What do you want to use this on",
    "Select a tree",
    "Where do you wish to chop",
]

# A short window for a refusal worded a moment late; the journal was cleared just before the swing
NO_CURSOR_READ = 0.5

# A stack's graphic changes with its size, so match a set rather than one graphic. Hue is
# deliberately not part of the match: a shard with special woods hues its logs, and those still
# count, still convert and still need hauling.
LOG_GRAPHICS = set([0x1BDD, 0x1BE0, 0x1BDE, 0x1BDF])

# Whole words, or 'log' inside 'logic' would put something in the converter. Both numbers, because
# words_of("Oak Logs") answers 'logs' and nothing would ever match the singular.
LOG_NAME_WORDS = ["log", "logs"]

# A seed only: the real board graphic is learned by diffing the pack across the first conversion
BOARD_GRAPHICS = set([0x1BD7, 0x1BD9, 0x1BDA, 0x1BDB])

# So a haul still works on a run where no conversion has landed yet to name the art
BOARD_NAME_WORDS = ["board", "boards"]

# Pauses after each conversion and each move, to stay under the server's action throttle
CONVERT_DELAY = 0.7
MOVE_DELAY = 0.7

# Polled rather than slept through: the throttle can delay a conversion well past a fixed pause, and
# reading too early looks like a failure
CONVERT_TIMEOUT = 4.0
CONVERT_POLL = 0.2

# More than one, because a throttled or stale attempt also looks silent, and giving up on hue 0
# means hauling ordinary logs
CONVERT_ATTEMPTS = 3

# One pass converts one stack, so this caps a haul
MAX_CONVERT_PASSES = 60

# Empty spots in a row before it says the tree test is probably matching scenery
EMPTY_HINT = 5

# Pack horse, pack llama, giant beetle. Unverified on this shard; the search logs the body it finds.
PACK_ANIMAL_GRAPHICS = set([0x123, 0x124, 0x317])

# Optional: pin the animals instead of discovering them. Order does not matter - the haul walks to
# whichever is nearest first either way.
PACK_ANIMAL_SERIALS = []

# A cursor at startup to click the animals, ESC to fall back to PACK_ANIMAL_SERIALS or the search
PICK_PACK_ANIMALS = True

# A backstop only - the selection ends when you press ESC
MAX_PICKS = 8

# It waits on a person, not the shard
PICK_TIMEOUT = 60.0

ANIMAL_SCAN_RADIUS = 18

UNLOAD_RANGE = 2

# Boards a pack animal takes before it refuses the next one, seen on UOAlive. A stack bigger than
# what is left is refused whole, so the haul moves only the slice that still fits.
PACK_ANIMAL_BOARDS = 1600

PACK_OPEN_DELAY = 0.6

# Also what the shard says to a board dropped on an animal that walked off mid-load
TOO_FAR_TEXT = ["That is too far away", "You cannot reach that"]

# Deliberately wider than WEIGHT_BUFFER, so hauling always gets its turn before the overweight stop
HAUL_BUFFER = 120

# Hauls in a row that freed no weight before the animals are taken to be full. Without it a run
# whose animals fill up spends every remaining cycle walking to them and never swings again, and
# ends on the stall watch saying 'no progress' when the real answer is 'they are full'.
MAX_EMPTY_HAULS = 3

# Buffer, so the stop lands before the shard starts refusing to move the new logs
WEIGHT_BUFFER = 40

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

WATCH_FOR_TROUBLE = True

THREAT_RANGE = 12
AMBUSH_WARNING = "AMBUSHED!"
AMBUSH_HUE = 33

# Run on this Mac, outside the game, so the client's sound setting does not matter. An empty list
# turns the one off. The alarm restarts while trouble lasts, up to AMBUSH_REPEATS starts
AMBUSH_ALARM = ["afplay", "/System/Library/Sounds/Sosumi.aiff"]
AMBUSH_NOTICES = [
    ["osascript", "-e", 'display notification "You have been ambushed!" with title "Ultima Online"'],
]
AMBUSH_REPEATS = 30

# The run stands still behind a gump until its button is pressed - no swing, no walk - with the
# alarm restarting all the while
AMBUSH_HOLD = True
AMBUSH_HOLD_TEXT = "You have been ambushed. Press the button when it is safe"
AMBUSH_HOLD_BUTTON = "Resume"
AMBUSH_HOLD_HUE = 33
AMBUSH_HOLD_POLL = 0.5


# Ordered, not a dict: InJournalAny answers yes/no, so the buckets are polled in order and the first
# holding a match wins. Guesses for a RunUO-family shard - correct them against the real journal.
OUTCOME_TEXT = [
    ("chopped", ["You put", "You hack at the tree", "You chop some"]),
    # About the trunk: how much ground it speaks for depends on how the swing was aimed
    (
        "empty",
        [
            "There's not enough wood here to harvest",
            "There is not enough wood here to harvest",
            "There is no wood here to harvest",
            "There are no logs left",
        ],
    ),
    # About everything in reach, which is what a self-target asks: this one always parks the ground,
    # whichever way the swing was aimed. Confirmed on UOAlive - the run that found it read every one
    # of these as an unreadable outcome, because this bucket was folded into 'empty' and the wording
    # was lost on the way.
    (
        "nothingNearby",
        [
            "There are no harvestable resources nearby",
            "There is nothing here to harvest",
            "There are no resources here",
        ],
    ),
    # "You can't use an axe on that" is UOAlive's wording, seen on a live web-client run against an
    # 'o'hii tree' static (0xc9e) - the client calls it a tree, the shard will not harvest it
    (
        "notTree",
        [
            "You can't use an axe on that",
            "You can't chop that",
            "You can't use a bladed item on that",
            "You cannot chop",
        ],
    ),
    ("tooFar", TOO_FAR_TEXT),
    # Line of sight, not range: the tile is inside CHOP_RANGE and no amount of walking closer or
    # waiting fixes it
    ("notSeen", ["Target cannot be seen"]),
    # Answered by hauling rather than by consolidating: one log stack converts to one board stack,
    # so merging gives back almost nothing. What frees slots is boards leaving for the animal.
    ("packFull", ["Your backpack is full", "That container cannot hold more"]),
    ("wornOut", ["You have worn out your tool"]),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]
