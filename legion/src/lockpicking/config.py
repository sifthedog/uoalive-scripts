from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT, UNSKILLED_TEXT
from uo.timings import HEARTBEAT_EVERY, SAVE_POLL, SAVE_WAIT, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX

# Every success and failure is appended here, one JSON object per line, for legion/skilldb.py to
# turn into a table later. "" turns recording off. A bare name lands beside the script.
DATA_PATH = "skill-attempts.jsonl"

SKILL = "Lockpicking"

# The shard's training chest. It re-rolls its own difficulty to your skill on every double-click,
# which is what makes the loop worth running at all.
BOX_GRAPHIC = 2474
BOX_HUE = 33

# Tiles. A lockpick reaches two, and the run stands still
BOX_RANGE = 2

# Read off a stack in the pack, and the same art the tinkering table makes
LOCKPICK_GRAPHIC = 0x14FC

# API.Pause takes seconds where the ClassicUO port took ms
DELAY = 0.5

TARGET_TIMEOUT = 1.0
SET_TIMEOUT = 1.0

READ_TIMEOUT = 2.0
READ_POLL = 0.1

# Refusals in a row before the run stops. The pace should get there first
MAX_THROTTLED = 20

# The double-click's own answer, waited on so the pick goes against a level that has been re-rolled
SET_TEXT = ["This chest has been set for"]

# Polled in declaration order, first match wins - and the journal is cleared before every pick, so
# what is in it belongs to this attempt and nothing older.
#
# `failed` and `picked` were given by whoever runs this shard; the rest are the shared tables. There
# is deliberately no bucket for a broken pick, an unlocked box or one out of reach: an outcome no
# bucket matches is counted and reported, never recorded, and that report is what hands you the
# wording to add.
OUTCOME_TEXT = [
    ("failed", ["You are unable to pick the lock"]),
    ("picked", ["The lock quickly yields to your skill"]),
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]
