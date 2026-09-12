from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT, UNSKILLED_TEXT
from uo.timings import HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STEP_DELAY
from uo.timings import THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX

# Every success and failure is appended here, one JSON object per line, for legion/skilldb.py to
# turn into a table later. "" turns recording off. A bare name lands beside the script.
DATA_PATH = "skill-attempts.jsonl"

# up_to is the skill value the row trains to, exclusive, so the bands butt together. These are the
# spells the guides name as gaining without a victim: a punchbag has to be found, kept alive and in
# range. `buff` is a BuffIconType member name matched against str(buff.Type); `title` is the
# localized fallback. cast_timeout and cast_delay are per row because the circles are seconds
# apart - a 3rd-circle cast answered at 1.8s here, and each timeout is that time with a margin.
STAGES = [
    # 3rd circle. Below about 30 the sensible thing is to buy the skill from an NPC trainer.
    {
        "up_to": 45.0,
        "spell": "Bless",
        "buff": "Bless",
        "title": "Bless",
        "mana": 9,
        "target": "self",
        "cast_timeout": 3.0,
        "cast_delay": 0.3,
    },
    # 4th circle
    {
        "up_to": 60.0,
        "spell": "Arch Protection",
        "buff": "ArchProtection",
        "title": "Arch Protection",
        "mana": 11,
        "target": "self",
        "cast_timeout": 3.5,
        "cast_delay": 0.35,
    },
    # 6th. The 5th and 7th circles are skipped because their spells want a cursor over ground or a
    # gump answered, and neither is something this loop can do.
    {
        "up_to": 80.0,
        "spell": "Invisibility",
        "buff": "Invisibility",
        "title": "Invisibility",
        "mana": 20,
        "target": "self",
        "cast_timeout": 4.0,
        "cast_delay": 0.4,
    },
    # 8th. An area attack that hits everything nearby, so this band belongs somewhere empty. The
    # only row with no buff to prove itself by - the mana falling is the whole proof.
    {
        "up_to": 120.0,
        "spell": "Earthquake",
        "mana": 50,
        "cast_timeout": 5.0,
        "cast_delay": 0.6,
    },
]

SKILL = "Magery"
MEDITATION = "Meditation"

# The BuffIconType the client publishes while a trance is running
MEDITATION_BUFF = "ActiveMeditation"

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms.

SKILL_TIMEOUT = 1.0
SKILL_POLL = 0.5

# Consecutive cycles the client answered nothing for the skill before the run gives up
MAX_BLIND_READS = 5

# The fallback for a row that names neither, and every row in STAGES names both
CAST_TIMEOUT = 2.0
CAST_DELAY = 0.75

CAST_WAIT_SLICE = 0.2

# How long the cursor is given to go down once it has been answered, which is what says whether the
# shard took that answer
SELF_TARGET_TIMEOUT = 1.0
SELF_TARGET_POLL = 0.1

# Fallbacks for a cursor the pre-target did not take, tried in this order until one brings it down
SELF_ANSWERS = ["Target(player)", "TargetSelf", "Target(serial)"]

# The mana leaves the pool a beat after the incantation ends, so IsCasting falling is not the end of
# the read - it was measured landing 0.2s behind the flag
PROOF_GRACE = 0.6

# What a cast issued before the last one finished costs. Flat, and never counted towards a stop:
# this is the pacing finding the shard's real cast time rather than anything going wrong. Short
# because the refusal itself is read in one slice, so overshooting costs another cheap retry.
CASTING_WAIT = 0.5

BUFF_WAIT = 2.0

# Gating on the buff would cap the run at one cast per buff duration
SKIP_WHEN_BUFFED = False

# A toggle the shard turned back off was still a cast it charged for and rolled the skill on
DISABLED_IS_PROGRESS = True

# Off waits for natural regeneration instead: slower, always available
MEDITATE = True

# The last band charges 50 a cast, so a pool topped right up pays for several
MEDITATE_TO_FULL = True

MEDITATE_TIMEOUT = 20.0
MEDITATE_ATTEMPTS = 4
MEDITATE_START_TIMEOUT = 2.0

MANA_POLL = 0.5
MANA_LOG_EVERY = 10.0

REGEN_TIMEOUT = 120.0

# Cycles that produced neither a readable cast nor any movement in the skill before the run gives
# up. A dry mana stretch is charged what it cost in cycles, so this ceiling covers that case too.
MAX_STALE = 500

MAX_CYCLES = 5000

MAX_THROTTLED = 20
# Guesses - correct them against the real journal after the first run. Ordered, not a dict: the
# first bucket holding a match wins, which is why alreadyCasting sits before throttled: the latter
# ends in a bare 'You must wait' that the longer sentence contains.
OUTCOME_TEXT = [
    # Not depended on: the mana leaving the pool and the buff arriving are the proof
    ("cast", ["You feel a surge of magic", "You are now protected"]),
    ("fizzled", ["The spell fizzles", "You have failed to cast the spell"]),
    (
        "noReagents",
        [
            "You do not have enough reagents",
            "More reagents are needed",
            "You lack the required reagents",
        ],
    ),
    ("noMana", ["You do not have enough mana", "Insufficient mana"]),
    ("alreadyUp", ["You are already under the effect"]),
    ("disabled", ["You are no longer", "You have dispelled"]),
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    # The recovery wording is this shard's own, read off a live run; the other two are guesses
    (
        "alreadyCasting",
        [
            "You have not yet recovered from casting a spell",
            "You are already casting a spell",
            "You are already casting",
        ],
    ),
    ("throttled", THROTTLED_TEXT),
]

# trance is the only wording here that is not a guess: it is the client's own documented example.
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
