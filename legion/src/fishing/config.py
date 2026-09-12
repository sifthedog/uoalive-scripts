from uo.phrases import AMBUSH_TEXT, SAVE_DONE_TEXT, SAVING_TEXT, STOPPED, THROTTLED_TEXT
from uo.timings import (HEARTBEAT_EVERY, LOG_EVERY, SAVE_POLL, SAVE_WAIT, STEP_DELAY,
                        THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

# One JSON object per cast, for legion/skilldb.py. "" turns recording off. A bare name lands
# beside the script, in LegionScripts.
DATA_PATH = "skill-attempts.jsonl"

SKILL_NAMES = ["Fishing"]

# Said once, before the loop starts. "" says nothing
GUARD_PHRASE = "all guard"

POLE_GRAPHICS = set([0x0DBF])
POLE_NAME_WORDS = ["fishing", "pole"]

# Two-handed on stock shards; the other layer is for a reskinned one
HAND_LAYERS = ["twohanded", "onehanded"]

# Confirmed on this shard; HasTarget is what the wait actually leans on
PROMPT_TEXT = ["What water do you want to fish in"]

# Stock RunUO Fishing.cs bands, a hypothesis about this shard. Land and statics are numbered apart,
# and the static bands are RunUO's 0x4000-offset ids brought back down. A shoreline's water is
# commonly a static laid over plain grass, which is why the aimed-at tile checks statics first
WATER_LAND_GRAPHICS = set()
for _low, _high in [(0x00A8, 0x00AB), (0x0136, 0x0137)]:
    for _water in range(_low, _high + 1):
        WATER_LAND_GRAPHICS.add(_water)

WATER_STATIC_GRAPHICS = set()
for _low, _high in [(0x1797, 0x179C), (0x346E, 0x3485), (0x3490, 0x34AB), (0x34B5, 0x35D5)]:
    for _water in range(_low, _high + 1):
        WATER_STATIC_GRAPHICS.add(_water)

# Used only when the client has no land data at all for the computed tile (out of range, or the
# chunk never loaded) - normally the real tile there is read and used instead, static or land. An
# earlier version always passed 1337 outright, and later the land tile's own real graphic outright,
# and the shard silently dropped every cast either way - it needs to be a real water tile, not just
# a real tile
LAND_TILE_GRAPHIC = 1337

# Asked once, via a gump, before the loop starts. Uncapped - RunUO's own fishing range does not
# apply to a cast this run never scans the water for
TILES_AHEAD_PROMPT_TEXT = "How many tiles ahead should the cast land?"
TILES_AHEAD_DEFAULT = 4
TILES_AHEAD_HUE = 996
TILES_AHEAD_POLL = 0.5

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

MAX_CYCLES = 5000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20

WATCH_FOR_TROUBLE = True
THREAT_RANGE = 12

AMBUSH_WARNING = "AMBUSHED!"
AMBUSH_HUE = 33

# Run on this Mac, outside the game, so the client's sound setting does not matter. An empty list
# turns the one off. The alarm restarts while trouble lasts, up to AMBUSH_REPEATS starts. Shared
# by the boat-stopped watch below - the same mechanism, a different trigger phrase and wording
AMBUSH_ALARM = ["afplay", "/System/Library/Sounds/Sosumi.aiff"]
AMBUSH_NOTICES = [
    ["osascript", "-e", 'display notification "You have been ambushed!" with title "Ultima Online"'],
]
AMBUSH_REPEATS = 30

# The run stands still behind a gump until its button is pressed - no cast, no walk - with the
# alarm restarting all the while
AMBUSH_HOLD = True
AMBUSH_HOLD_TEXT = "You have been ambushed. Press the button when it is safe"
AMBUSH_HOLD_BUTTON = "Resume"
AMBUSH_HOLD_HUE = 33
AMBUSH_HOLD_POLL = 0.5

# The shard's boat auto-pilot-stopped line, handled exactly like an ambush (sound, HeadMsg,
# notices, an optional hold) - only the trigger text and the wording differ. Wording unconfirmed;
# see the README's Unverified section
BOAT_STOPPED_TEXT = ["Ar, we've stopped, sir"]
BOAT_STOPPED_WARNING = "THE BOAT HAS STOPPED!"
BOAT_STOPPED_HUE = 43
BOAT_STOPPED_HOLD = True
BOAT_STOPPED_HOLD_TEXT = "The boat has stopped. Press the button once it is safe to carry on"

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
