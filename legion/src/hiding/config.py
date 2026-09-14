from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT, UNSKILLED_TEXT
from uo.timings import HEARTBEAT_EVERY, SAVE_POLL, SAVE_WAIT, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX

# Every success and failure is appended here, one JSON object per line. "" turns recording off.
DATA_PATH = "skill-attempts.jsonl"

SKILL = "Hiding"

READ_TIMEOUT = 1.5
READ_POLL = 0.1

# ServUO's Hiding holds the skill timer for 10s after a roll and 1s after a refusal; the pace
# climbs from the floor by PACE_STEP per throttle and eases back after PACE_EASE_AFTER rolls
PACE_FLOOR = 1.0
PACE_STEP = 1.0
PACE_MAX = 12.0
PACE_EASE_AFTER = 5

MAX_THROTTLED = 20

# Polled in declaration order, first match wins. `hidden` and the first `failed` phrase were watched
# on UOAlive; the rest are ServUO guesses. `busy` sits before `failed`, which contains its stem.
OUTCOME_TEXT = [
    (
        "busy",
        [
            "You can't seem to hide right now",
            "You cannot seem to hide right now",
            "You are busy doing something else and cannot hide",
        ],
    ),
    ("failed", ["You fail to hide", "You can't seem to hide here", "You cannot seem to hide here"]),
    ("hidden", ["You have hidden yourself well"]),
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]
