from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT, UNSKILLED_TEXT
from uo.timings import HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT
from uo.timings import THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX

# Cast in this order within a pass. `buff` is a BuffIconType member name, matched against
# str(buff.Type); `title` is the localized fallback. `mana` is a ceiling - the shard charges a
# paladin less as Chivalry rises - and the client's own Chivalry table says 10 for both.
KEEP = [
    {
        "spell": "Consecrate Weapon",
        "buff": "ConsecrateWeapon",
        "title": "Consecrate Weapon",
        "mana": 10,
        "tithing": 10,
        "needs_weapon": True,
    },
    {
        "spell": "Divine Fury",
        "buff": "DivineFury",
        "title": "Divine Fury",
        "mana": 15,
        "tithing": 10,
    },
]

# Off is a keeper that puts the buffs up and stops. On it keeps them up until you stop the script.
KEEP_UP = True

# Between passes. The buff bar is fed by server packets, so this is how stale the run's picture of
# it can be, and roughly how long a lapsed buff stays down.
POLL = 1.0

# Long enough for the buff packet to land after the incantation, which is what a shard that words
# these differently is read by
CAST_TIMEOUT = 1.0
CAST_WAIT_SLICE = 0.2

# Between two casts inside one pass, to stay under the action throttle
CAST_DELAY = 0.6

# Consecutive casts the shard said nothing readable about, and that put no buff up and spent no
# mana, before the entry is set aside
MAX_MISSES = 5

# How long an entry refused for something a pass cannot fix is left alone before it is tried again
SET_ASIDE = 60.0

# Runs for a day at POLL. A keeper standing over a character with both buffs up is working, so
# nothing here counts cycles against it.
MAX_CYCLES = 100000

MAX_THROTTLED = 20

# Guesses, apart from the tithing wording. Ordered, not a dict: the first bucket holding a match
# wins, which is why alreadyCasting sits before throttled - THROTTLED_TEXT ends in a bare
# 'You must wait' that the longer sentence contains.
OUTCOME_TEXT = [
    # Not depended on: the buff arriving and the mana leaving the pool are the proof
    ("cast", ["Your weapon is consecrated", "You are filled with divine fury"]),
    ("fizzled", ["You fail to cast the spell", "The spell fizzles"]),
    (
        "noTithing",
        [
            "You do not have enough tithing points",
            "You must have at least",
            "You need to make an offering",
        ],
    ),
    ("noMana", ["You do not have enough mana", "Insufficient mana"]),
    ("alreadyUp", ["You are already under the effect"]),
    (
        "noWeapon",
        [
            "You cannot consecrate your fists",
            "You must have a weapon",
            "You must be wielding a weapon",
        ],
    ),
    ("unskilled", ["You are not pious enough", "Your karma is not high enough"] + UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("alreadyCasting", ["You are already casting a spell", "You are already casting"]),
    ("throttled", THROTTLED_TEXT),
]
