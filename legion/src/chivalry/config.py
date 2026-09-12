from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT, UNSKILLED_TEXT
from uo.timings import HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STEP_DELAY
from uo.timings import THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX

# Every success and failure is appended here, one JSON object per line, for legion/skilldb.py to
# turn into a table later. "" turns recording off. A bare name lands in TazUO's working directory
# rather than beside the script - set an absolute path to put it somewhere you will find it.
DATA_PATH = "skill-attempts.jsonl"

# up_to is the skill value the row trains to, exclusive. `buff` is a BuffIconType member name matched
# against str(buff.Type); `title` is the localized fallback. `mana` is a ceiling - the shard charges
# less as Chivalry rises. `tithing` is the other currency, gated before the cast because nothing a
# script does refills it. No row raises a cursor. The shard's own minimums are Consecrate Weapon 15,
# Divine Fury 25, Enemy of One 45, Holy Light 55, Noble Sacrifice 65, and every band opens above its own.
STAGES = [
    # Enchants what is in hand, so the run stows and redraws the weapon around every trance
    {
        "up_to": 45.0,
        "spell": "Consecrate Weapon",
        "buff": "ConsecrateWeapon",
        "title": "Consecrate Weapon",
        "mana": 10,
        "tithing": 10,
        "needs_weapon": True,
        "cast_timeout": 2.0,
        "cast_delay": 0.5,
    },
    {
        "up_to": 60.0,
        "spell": "Divine Fury",
        "buff": "DivineFury",
        "title": "Divine Fury",
        "mana": 15,
        "tithing": 10,
        "cast_timeout": 2.0,
        "cast_delay": 0.5,
    },
    # A toggle: cast while standing it comes off, which is still a cast the shard charged for
    {
        "up_to": 70.0,
        "spell": "Enemy of One",
        "buff": "EnemyOfOne",
        "title": "Enemy of One",
        "mana": 20,
        "tithing": 10,
        "cast_timeout": 2.0,
        "cast_delay": 0.5,
    },
    # An area attack on everything non-blue nearby, and the client publishes no buff for it
    {
        "up_to": 90.0,
        "spell": "Holy Light",
        "mana": 10,
        "tithing": 10,
        "cast_timeout": 2.0,
        "cast_delay": 0.5,
    },
    # Where it finds anything to heal it sets the caster's hits, mana and stamina to 1
    {
        "up_to": 120.0,
        "spell": "Noble Sacrifice",
        "mana": 20,
        "tithing": 30,
        "cast_timeout": 2.0,
        "cast_delay": 0.5,
    },
]

SKILL = "Chivalry"
MEDITATION = "Meditation"

# The BuffIconType the client publishes while a trance is running
MEDITATION_BUFF = "ActiveMeditation"

# Under it the first band is mostly fizzles, and a trainer sells the skill faster
FIRST_BAND = 40.0

# The layers a trance wants empty. A shield sits on onehanded too.
HAND_LAYERS = ["onehanded", "twohanded"]

EQUIP_ATTEMPTS = 3
EQUIP_TIMEOUT = 2.0
EQUIP_POLL = 0.2

# Fraction of max hits under which the run bandages itself, and stops if that cannot get it back
HURT_FLOOR = 0.5

# Off is a run that simply stops when it is hurt
BANDAGE = True

# Clean bandages; the bloodied ones are a different item
BANDAGE_GRAPHIC = 0x0E21

BANDAGE_ATTEMPTS = 4
BANDAGE_TIMEOUT = 8.0
BANDAGE_CURSOR_TIMEOUT = 1.0

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms.

SKILL_TIMEOUT = 1.0
SKILL_POLL = 0.5

# Consecutive cycles the client answered nothing for the skill before the run gives up
MAX_BLIND_READS = 5

# The fallback for a row that names neither, and every row in STAGES names both
CAST_TIMEOUT = 2.0
CAST_DELAY = 0.5

CAST_WAIT_SLICE = 0.2

# How long the cursor is given to go down once it has been answered, which is what says whether the
# shard took that answer
SELF_TARGET_TIMEOUT = 1.0
SELF_TARGET_POLL = 0.1

# Fallbacks for a cursor the pre-target did not take, tried in this order until one brings it down
SELF_ANSWERS = ["Target(player)", "TargetSelf", "Target(serial)"]

# The mana leaves the pool a beat after the incantation ends, so IsCasting falling is not the end of
# the read - it was measured landing 0.2s behind the flag. The tithing point the fizzle proof reads
# arrives on the same packets, so this covers both.
PROOF_GRACE = 0.6

# What an outcome neither the journal nor the two currencies could name reports before it goes quiet,
# and how much of the journal it shows. A run's worth of these means OUTCOME_TEXT is missing a line.
MAX_UNREAD_REPORTS = 5
JOURNAL_TAIL_SECONDS = 20.0
JOURNAL_TAIL_LINES = 10

# What a cast issued before the last one finished costs. Flat, and never counted towards a stop.
CASTING_WAIT = 0.5

BUFF_WAIT = 2.0

# Gating on the buff would cap the run at one cast per buff duration
SKIP_WHEN_BUFFED = False

# Enemy of One coming off was still a cast the shard charged for and rolled the skill on
DISABLED_IS_PROGRESS = True

# Off waits for natural regeneration instead: slower, always available
MEDITATE = True

# Every trance costs a stow and a draw, so a pool topped right up pays for several casts
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

# Guesses apart from the tithing and recovery wordings, which are UOAlive's own. Ordered, not a
# dict: the first bucket holding a match wins, which is why alreadyCasting sits before throttled -
# THROTTLED_TEXT ends in a bare 'You must wait' that the longer sentence contains.
OUTCOME_TEXT = [
    # Not depended on: the buff arriving and the mana leaving the pool are the proof
    (
        "cast",
        ["Your weapon is consecrated", "You are filled with divine fury", "You are now"],
    ),
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
    ("disabled", ["You are no longer", "You lose your focus"]),
    # Karma refusals mean the same thing as unskilled: this character cannot cast it, so stop
    (
        "unskilled",
        ["You are not pious enough", "Your karma is not high enough", "You must have proper karma"]
        + UNSKILLED_TEXT,
    ),
    ("saving", SAVING_TEXT),
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

# Guesses. A heal is proved by the hits going up, so these only explain the failures.
HEAL_OUTCOME_TEXT = [
    ("healed", ["You finish applying the bandages", "You heal", "You apply the bandages"]),
    (
        "noBandages",
        ["You do not have a bandage", "You must have bandages", "You do not have any bandages"],
    ),
    ("busy", ["You are already applying bandages"]),
    ("interrupted", ["You have been interrupted"]),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]
