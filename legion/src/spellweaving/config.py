from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT, UNSKILLED_TEXT
from uo.timings import HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STEP_DELAY
from uo.timings import THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX

# Every success and failure is appended here, one JSON object per line, for legion/skilldb.py to
# turn into a table later. "" turns recording off. A bare name lands beside the script.
DATA_PATH = "skill-attempts.jsonl"

# up_to is the skill value the row trains to, exclusive, so the bands butt together. `buff` is a
# BuffIconType member name matched against str(buff.Type); `title` is the localized fallback.
# target_kind is the cursor the shard raises - the two area rows are harmful, and a pre-target set
# to the wrong kind does not fire at all. cast_timeout is the book's own casting delay with a
# margin; cast_delay is the floor between casts. The spell names are the strings handed to
# API.CastSpell, so they have to read the way your spellbook does.
#
# How the rows were picked, because the book is bigger than the table. A spell the loop can grind
# has to be castable twice running, which rules out most of it:
#
#   - anything that leaves a timed buff on the caster answers the recast with "This spell is already
#     in effect" and can be cast once a duration. That is Arcane Empowerment (20 seconds), Ethereal
#     Voyage, Gift of Life, and on top of their own cooldowns Gift of Renewal and Attunement.
#   - Dryad Allure wants a humanoid to charm, Nature's Fury leaves a swarm, the two summons leave a
#     creature in your follower slots.
#
# What is left recasts freely: an enchant that renews (Arcane Circle, Immolating Weapon), a form
# that toggles (Reaper Form), and the three that resolve and are gone. Of those, each band takes the
# hardest it can cast: min_skill first, because that is the book's own difficulty ranking, then mana
# where two spells share a minimum.
# The top three bands open on their spell's minimum exactly, with no margin: a spell the shard has
# only just allowed fizzles more, and a fizzle is still a roll. The two below them carry a margin
# because nothing harder was available to move up to. min_skill is the shard's figure and nothing
# reads it but the test that holds the order.
#
# Every mana figure is the unfocused one; an arcane focus takes roughly a third off each.
STAGES = [
    # Casts solo on this shard - it renews the arcane focus and gains, which is what the cast
    # wordings below are read off. The focus it lights is what makes every row under it cheaper,
    # and the journal put its life at 7199 seconds.
    {
        "up_to": 20.0,
        "spell": "Arcane Circle",
        "min_skill": 0,
        "mana": 24,
        "cast_timeout": 3.5,
        "cast_delay": 0.4,
    },
    # Enchants what is in hand, so the run stows and redraws the weapon around every trance. The
    # fastest cast in the book at 1.0s, and Thunderstorm's equal on mana without the aggravation.
    {
        "up_to": 35.0,
        "spell": "Immolating Weapon",
        "min_skill": 10,
        "buff": "Immolating",
        "title": "Immolating Weapon",
        "mana": 32,
        "needs_weapon": True,
        "cast_timeout": 3.5,
        "cast_delay": 0.4,
    },
    # A transformation, and a toggle: every other cast takes it back off, which is still a cast the
    # shard charged for and rolled - see DISABLED_IS_PROGRESS. The only spell at its minimum that
    # can be cast twice running, so it holds the band until Essence of Wind's minimum lands.
    {
        "up_to": 52.0,
        "spell": "Reaper Form",
        "min_skill": 24,
        "buff": "ReaperForm",
        "title": "Reaper Form",
        "mana": 34,
        "cast_timeout": 4.0,
        "cast_delay": 0.5,
    },
    # Frost damage to everything hostile in six tiles, so this band and the two above it belong
    # somewhere empty. Centred on the caster, so no cursor.
    {
        "up_to": 66.0,
        "spell": "Essence of Wind",
        "min_skill": 52,
        "mana": 40,
        "cast_timeout": 4.5,
        "cast_delay": 0.5,
    },
    # Laid on the ground rather than on anything, so the cursor is answered at the caster the way
    # mysticism.py answers Hail Storm's
    {
        "up_to": 90.0,
        "spell": "Wildfire",
        "min_skill": 66,
        "mana": 50,
        "target": "self",
        "target_kind": "harmful",
        "cast_timeout": 4.0,
        "cast_delay": 0.5,
    },
    # Cast at the caster, who is a player: the book says it slays creatures and only chips players,
    # so this is chip damage in a loop rather than a way to die. HURT_FLOOR ends it either way.
    {
        "up_to": 120.0,
        "spell": "Word of Death",
        "min_skill": 83,
        "mana": 50,
        "target": "self",
        "target_kind": "harmful",
        "cast_timeout": 5.0,
        "cast_delay": 0.6,
    },
]

SKILL = "Spellweaving"
MEDITATION = "Meditation"

# The BuffIconType the client publishes while a trance is running
MEDITATION_BUFF = "ActiveMeditation"

# The ceiling of the Arcane Circle band, and the only band a shard reading the table strictly would
# refuse solo. The start-up line says so; the run tries it either way.
FIRST_BAND = 20.0

# The layers a trance wants empty, and where Immolating Weapon's weapon comes back to. A shield sits
# on onehanded too.
HAND_LAYERS = ["onehanded", "twohanded"]

EQUIP_ATTEMPTS = 3
EQUIP_TIMEOUT = 2.0
EQUIP_POLL = 0.2

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
# the read. 1.4 and not magery.py's 0.6: this shard posts the arcane focus lines well after the
# incantation, and the next cycle's ClearJournal destroys anything the window closed on - which is
# what every unreadable outcome on the first run turned out to be. It only costs wall clock on a
# cast nothing has proved yet; a mana drop or a matched line still leaves in the same slice.
PROOF_GRACE = 1.4

# What a cast issued before the last one finished costs. Flat, and never counted towards a stop:
# this is the pacing finding the shard's real cast time rather than anything going wrong.
CASTING_WAIT = 0.5

BUFF_WAIT = 2.0

# Gating on the buff would cap the run at one cast per Immolating Weapon
SKIP_WHEN_BUFFED = False

# A toggle the shard turned back off was still a cast it charged for and rolled the skill on
DISABLED_IS_PROGRESS = True

# The top two bands are cast at the caster's feet and nothing here heals, so a health floor is a
# stop rather than a pause
HURT_FLOOR = 0.5

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
    # Read off a live run. The focus lines are Arcane Circle's own receipt, and the band needs one:
    # it puts up no buff this loop reads, so without them a cast the client had not yet refreshed
    # the mana for went down as unreadable.
    (
        "cast",
        [
            "Your arcane focus is renewed",
            "Arcane Focus will expire",
            "You have gained an arcane focus",
        ],
    ),
    ("fizzled", ["The spell fizzles", "You have failed to cast the spell"]),
    ("noMana", ["You do not have enough mana", "Insufficient mana"]),
    # The first is this shard's own, off a live run: what every timed self-buff in the book answers
    # a recast with. A row that hits it belongs out of STAGES, not waited on.
    (
        "alreadyUp",
        ["This spell is already in effect", "You are already under the effect"],
    ),
    # The layers said the weapon was there, so this is the shard disagreeing rather than a missing
    # weapon: the run draws it again and carries on
    (
        "noWeapon",
        [
            "You must have a weapon",
            "You must be wielding a weapon",
            "You must have a weapon equipped",
        ],
    ),
    (
        "disabled",
        ["You are no longer in reaper form", "You are no longer", "You have dispelled"],
    ),
    # Reaper Form shuts the rest of the book on some shards, which strands the bands above it
    ("formLocked", ["You cannot cast this spell while in", "while in this form"]),
    # The first band, every time, unless a second spellweaver is standing on the circle with you
    (
        "noCircle",
        [
            "You must be in an arcane circle",
            "You need to be standing on an arcane circle",
            "Arcane Circle requires",
            "There are not enough spellweavers",
        ],
    ),
    ("unskilled", UNSKILLED_TEXT),
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
