from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT, UNSKILLED_TEXT
from uo.timings import HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STALL_STOP, STALL_WARN
from uo.timings import THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX

PET_NAME = "sifinha"

# What becomes of the animal once it is yours: 'kill' keeps it and puts it to work, 'release' hands
# the follower slot back, 'keep' does neither.
AFTER_TAME = "kill"

SKILL_NAME = "Animal Taming"

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms.
TAME_START_TIMEOUT = 3.0
TAME_RESOLVE_TIMEOUT = 15.0

# Both waits are taken in slices this long, because the animal walks while the attempt resolves and
# a script sat in one long wait cannot follow it
TAME_WAIT_SLICE = 0.5

TAME_RANGE = 2

# How far the run looks for the next animal of the type you picked. 0 turns the hunt off and asks
# for every animal.
HUNT_RADIUS = 12

CHASE_TIMEOUT = 10

# A floor, not the cadence: the shard's skill timer is not something the client can be asked for, so
# the pace below raises this until the refusals stop.
TAME_DELAY = 1.5
PACE_STEP = 0.4
PACE_MAX = 8.0

# Easing after a single success oscillates between an attempt and a refusal
PACE_EASE_AFTER = 5

ANGRY_DELAY = 10.0

MAX_CYCLES = 5000
MAX_AWAY = 10
MAX_CONTESTED = 20
MAX_ANGRY = 10
MAX_PENDING = 10
MAX_THROTTLED = 20

# A failed tame turns the animal on you, so this run has a health floor
HEALTH_FLOOR = 0.5

SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25

OPL_TIMEOUT = 1

# Waiting on a person rather than on the shard - and unlike the web client's cursor, this one
# has a timeout, which expires into the same "nothing picked" that ESC does
TARGET_TIMEOUT = 60.0


CONTEXT_TIMEOUT = 2.0

KILL_MENU_TEXT = ["Kill", "Attack"]
KILL_CURSOR_TIMEOUT = 2.0

# Long, because this one is waiting on a person rather than on the shard
KILL_PICK_TIMEOUT = 60.0
KILL_PICK_POLL = 0.25

RELEASE_MENU_TEXT = ["Release"]

# The shard asks before it lets a pet go. Which button is 'yes' is not something the client reports,
# so the release is retried with each of these until the animal is actually let go.
RELEASE_CONFIRM_BUTTONS = [1, 2, 0]
RELEASE_CONFIRM_TEXT = ["release this creature", "release this", "Are you sure"]
RELEASE_CONFIRM_TIMEOUT = 3.0
RELEASE_CONFIRM_POLL = 0.15

# Goes each candidate button gets, and separately how many early menus are tolerated: a confirm that
# arrives late loses a press, and a menu asked for too early comes back without the entry
RELEASE_ATTEMPTS = 3

RELEASE_TIMEOUT = 3.0
RELEASE_POLL = 0.25

RENAME_TIMEOUT = 3.0
RENAME_POLL = 0.25
RENAME_ATTEMPTS = 3

# A tame lands in the journal before the shard has finished making the animal yours, and both the
# rename packet and the Release entry are refused until it has
PET_SETTLE_TIMEOUT = 5.0
PET_SETTLE_POLL = 0.25

MENU_RETRY_DELAY = 0.5

# Guesses for a RunUO-family shard, apart from `tamed` and `failed` which are read off this one.
# Ordered, not a dict: the first bucket holding a match wins, which is why `unskilled`, `saving` and
# `throttled` sit last.
OUTCOME_TEXT = [
    ("tamed", ["It seems to accept you as master"]),
    ("failed", ["You fail to tame the creature"]),
    # Not a result: the attempt has been accepted and will answer in a few seconds
    (
        "starting",
        [
            "You start to tame the creature",
            "You continue to tame the creature",
            "You are already taming this creature",
        ],
    ),
    ("angry", ["is too angry to continue taming", "You have been interrupted"]),
    ("contested", ["Someone else is already taming this creature"]),
    ("alreadyTame", ["That animal looks tame already"]),
    ("hopeless", ["You have no chance of taming this creature"]),
    (
        "notAnimal",
        ["That creature cannot be tamed", "You can't tame that", "That wasn't a valid target"],
    ),
    (
        "tooFar",
        [
            "You must be closer to attempt to tame this creature",
            "You are too far away to continue taming",
            "That is too far away",
            "You cannot see that",
        ],
    ),
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]

RESOLUTION_TEXT = [pair for pair in OUTCOME_TEXT if pair[0] != "starting"]

# The outcomes no amount of retrying gets past, and what the run says about each
STOP_REASON = {
    "hopeless": "the shard says this creature cannot be tamed by you",
    "notAnimal": "that is not something Animal Taming works on",
    "alreadyTame": "that animal is already tame",
    "unskilled": "not skilled enough to tame this creature",
}
