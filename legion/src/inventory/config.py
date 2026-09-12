# One JSON object per item is appended here. "" turns recording off. A bare name lands beside the
# script, in LegionScripts; a path with a folder in it is used as written.
DATA_PATH = "bag-items.jsonl"

# Whether a bag inside the bag is opened and read too
RECURSIVE = True

PICK_TIMEOUT = 30.0

# After UseObject on each container, so the client has seen inside before it is listed
OPEN_DELAY = 0.6

# One RequestOPLData per batch of this many serials, then this long for the tooltips to land
OPL_BATCH = 25
OPL_WAIT = 1.0

# Whole seconds: the API takes an int here
OPL_TIMEOUT = 1

# Further ask-and-read rounds for the tooltips that did not come. What still has none is written
# anyway, with the client's name and no lines.
RETRIES = 2

MAX_CONTAINERS = 50

# The whole line, matched without regard to case, kept as the shard wrote it. Stock ServUO
# ItemPower wording; "Minor" is here for a shard that says it instead of "Lesser".
TIER_TEXT = [
    "Minor Magic Item",
    "Lesser Magic Item",
    "Greater Magic Item",
    "Major Magic Item",
    "Lesser Artifact",
    "Greater Artifact",
    "Major Artifact",
    "Legendary Artifact",
]

# Line starts, matched without regard to case
DURABILITY_TEXT = ["durability"]
WEIGHT_TEXT = ["weight"]

# Line starts whose remainder is text rather than a number or a flag
PREFIX_TEXT = ["crafted by"]
