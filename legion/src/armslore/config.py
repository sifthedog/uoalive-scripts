from uo.phrases import SAVING_TEXT, THROTTLED_TEXT, UNSKILLED_TEXT

# Every success and failure is appended here, one JSON object per line, for legion/skilldb.py to
# turn into a table later. "" turns recording off. A bare name lands beside the script.
DATA_PATH = "skill-attempts.jsonl"

# API.Pause takes seconds where the ClassicUO port took ms
DELAY = 0.5

PICK_TIMEOUT = 30.0
TARGET_TIMEOUT = 1.0

# A reading answers within a tick or is not coming; the poll is short because the whole cycle is
READ_TIMEOUT = 1.5
READ_POLL = 0.1

SKILL = "Arms Lore"

# Polled in declaration order, first match wins - and the journal is cleared before every use, so
# what is in it belongs to this reading and nothing older.
#
# Every phrase here is a GUESS. Nothing in this repo has watched Arms Lore on this shard, and the
# stock RunUO wording is a localized message whose English this table is reconstructing. An outcome
# no bucket matches is counted and reported, never recorded - so a wrong table under-reports rather
# than writing something untrue. Watch one run and correct it.
OUTCOME_TEXT = [
    # The refusals are whole sentences, so they are asked first. `read` below is stems, which a
    # longer refusal could contain.
    (
        "missed",
        [
            "You are not certain",
            "You have no idea",
            "You are not sure",
            "You can not tell anything about",
            "You cannot tell anything about",
            "You can't tell anything about",
        ],
    ),
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
    # Stems the whole family of readings shares rather than any one wording: a shard reports the
    # weapon's damage, its durability, its quality or what it is made of, and no two phrase it the
    # same way. Last, because these are the loosest strings in the table.
    (
        "read",
        [
            "damage",
            "durability",
            "quality",
            "appears to be",
            "is made of",
        ],
    ),
]
