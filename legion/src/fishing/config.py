from uo.phrases import SAVING_TEXT, THROTTLED_TEXT

# One JSON object per cast, for legion/skilldb.py. "" turns recording off. A bare name lands
# beside the script, in LegionScripts.
DATA_PATH = "skill-attempts.jsonl"

SKILL_NAMES = ["Fishing"]

# Said once, before the cast. "" says nothing.
GUARD_PHRASE = "all guard"

POLE_GRAPHICS = set([0x0DBF])
POLE_NAME_WORDS = ["fishing", "pole"]

# Two-handed on stock shards; the other layer is for a reskinned one
HAND_LAYERS = ["twohanded", "onehanded"]

# Stock RunUO Fishing.cs bands, a hypothesis about this shard. Land and statics are numbered apart,
# and the static bands are RunUO's 0x4000-offset ids brought back down.
WATER_LAND_GRAPHICS = set()
for _low, _high in [(0x00A8, 0x00AB), (0x0136, 0x0137)]:
    for _water in range(_low, _high + 1):
        WATER_LAND_GRAPHICS.add(_water)

WATER_STATIC_GRAPHICS = set()
for _low, _high in [(0x1797, 0x179C), (0x346E, 0x3485), (0x3490, 0x34AB), (0x34B5, 0x35D5)]:
    for _water in range(_low, _high + 1):
        WATER_STATIC_GRAPHICS.add(_water)

# RunUO's fishing range: past it the shard says to stand closer to the water
FISH_RANGE = 4

# The cursor prompt is a guess; HasTarget is what the wait leans on
PROMPT_TEXT = ["Where do you want to fish"]

# Seconds throughout - API.Pause takes seconds
CURSOR_TIMEOUT = 2.0
CURSOR_POLL = 0.1
NO_CURSOR_READ = 1.0

# Has to outlast the cast animation, which plays before the shard answers
CAST_TIMEOUT = 12.0
CAST_POLL = 0.2

# The fish lands in the pack after the line that announced it
CATCH_SETTLE = 1.5
CATCH_POLL = 0.25

SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25

# The client applies a gain some time after the outcome
GAIN_SETTLE = 2.0
GAIN_POLL = 0.25

DISMOUNT_ATTEMPTS = 3
DISMOUNT_TIMEOUT = 2.0
DISMOUNT_POLL = 0.2

JOURNAL_TAIL_SECONDS = 20.0
JOURNAL_TAIL_LINES = 10

# The catch is named after the colon: 'You pull out an item: a fish'
CAUGHT_TEXT = ["You pull out an item"]

# Ordered: 'caught' first, and 'throttled' last because THROTTLED_TEXT ends in a bare 'You must wait'
OUTCOME_TEXT = [
    ("caught", CAUGHT_TEXT),
    ("failed", ["You fish a while, but fail to catch anything", "fail to catch anything"]),
    ("empty", ["The fish don't seem to be biting here", "don't seem to be biting"]),
    ("tooFar", ["You need to be closer to the water", "too far away"]),
    ("notWater", ["You can't fish there", "You cannot fish there", "Try fishing elsewhere"]),
    ("mounted", ["You can't fish while riding", "can't fish while riding"]),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]
