from uo.phrases import SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT, UNSKILLED_TEXT
from uo.timings import HEARTBEAT_EVERY, SAVE_POLL, SAVE_WAIT

# Every success and failure is appended here, one JSON object per line, for legion/skilldb.py to
# turn into a table later. "" turns recording off. A bare name lands beside the script.
DATA_PATH = "skill-attempts.jsonl"

# The whole pause between two uses, flat: a throttle is counted and the next use goes out anyway
DELAY = 0.5

PICK_TIMEOUT = 30.0
TARGET_TIMEOUT = 1.0

READ_TIMEOUT = 1.5
READ_POLL = 0.1

SKILL_CHOICE = {
    "text": "Which skill to train?",
    "hue": 996,
    "poll": 0.5,
    "timeout": 60.0,
    "rows": 6,
}

SHARED_OUTCOMES = [
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]

# One row per skill; `skills` is the client's name for it, first one found wins. `targets` asks for one target at the start and answers every cursor with it.
# `flag` proves an unread roll off the hidden flag, `gump` off a gump the use opened (closed after).
# `outcomes` is polled in order, first match wins, and a bucket that is neither the row's success
# nor its failure is counted and said, never recorded. Only Hiding and Arms Lore have been watched
# on UOAlive; every other phrase is a RunUO guess, so a wrong table under-reports rather than lies.
SKILLS = [
    {
        "key": "anatomy", "caption": "Anatomy", "skills": ["Anatomy"],
        "targets": True, "flag": False, "gump": False, "success": "read", "failure": "missed",
        "outcomes": [
            ("missed", ["You can not analyze", "You cannot analyze", "You can't analyze"]),
        ] + SHARED_OUTCOMES + [
            ("read", ["That being is", "looks", "appears to be"]),
        ],
    },
    {
        "key": "animalLore", "caption": "Animal Lore", "skills": ["Animal Lore"],
        "targets": True, "flag": False, "gump": True, "success": "read", "failure": "missed",
        "outcomes": [
            ("missed", ["You can't think of anything you know offhand",
                        "You cannot think of anything you know offhand"]),
            ("refused", ["That's not an animal", "At your skill level, you can only lore"]),
        ] + SHARED_OUTCOMES,
    },
    {
        "key": "armsLore", "caption": "Arms Lore", "skills": ["Arms Lore"],
        "targets": True, "flag": False, "gump": False, "success": "read", "failure": "missed",
        "outcomes": [
            ("missed", ["You are not certain", "You have no idea", "You are not sure",
                        "You can not tell anything about", "You cannot tell anything about",
                        "You can't tell anything about"]),
        ] + SHARED_OUTCOMES + [
            ("read", ["damage", "durability", "quality", "appears to be", "is made of"]),
        ],
    },
    {
        "key": "hiding", "caption": "Hiding", "skills": ["Hiding"],
        "targets": False, "flag": True, "gump": False, "success": "hidden", "failure": "failed",
        # `busy` before `failed`, which contains its stem. Neither hides you: fighting or casting
        "outcomes": [
            ("busy", ["You can't seem to hide right now", "You cannot seem to hide right now",
                      "You are busy doing something else and cannot hide"]),
            ("failed", ["You fail to hide", "You can't seem to hide here",
                        "You cannot seem to hide here"]),
            ("hidden", ["You have hidden yourself well"]),
        ] + SHARED_OUTCOMES,
    },
    {
        "key": "itemId", "caption": "Item ID", "skills": ["Item ID", "Item Identification"],
        "targets": True, "flag": False, "gump": False, "success": "read", "failure": "missed",
        "outcomes": [
            ("missed", ["You are not certain", "You have no idea", "You are not sure"]),
        ] + SHARED_OUTCOMES + [
            ("read", ["You identify", "appears to be", "is made of"]),
        ],
    },
    {
        "key": "tasteId", "caption": "Taste ID", "skills": ["Taste ID", "Taste Identification"],
        "targets": True, "flag": False, "gump": False, "success": "read", "failure": "missed",
        "outcomes": [
            ("missed", ["You cannot discern anything", "You can't discern anything",
                        "You are not sure"]),
        ] + SHARED_OUTCOMES + [
            ("read", ["is not poisoned", "It is a", "tastes like"]),
        ],
    },
    {
        "key": "begging", "caption": "Begging", "skills": ["Begging"],
        "targets": True, "flag": False, "gump": False, "success": "given", "failure": "refused",
        "outcomes": [
            ("refused", ["no gold for thee", "Thou dost not look trustworthy"]),
            ("broke", ["I have not enough money"]),
            ("tooFar", ["Thou art too far", "too far away"]),
            ("given", ["I feel sorry for thee", "Thou dost look hungry", "worthy fellow"]),
        ] + SHARED_OUTCOMES,
    },
]
