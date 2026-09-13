from uo.phrases import STOPPED

SKILL_NAMES = ["Alchemy"]

# Mortar and pestle, 3739
TOOL_GRAPHICS = set([0x0E9B])
TOOL_NAME_WORDS = ["mortar"]

TOOL_MODES = [("stop", "Stop the run"), ("fetch", "Fetch from a container")]
OUTPUT_OPTIONS = [("unload", "Unload into a container"), ("keep", "Keep")]

# Products in the pack, counted as amounts, before they are unloaded
DUMP_AT = 10

# name -> graphics, filled in once the run crafts
PRODUCTS = {}

# The form the run is set up on. Closing it, Cancel, or no OK in the timeout ends the run.
SETUP = {
    "title": "Alchemy",
    "tool_noun": "mortars and pestles",
    "material": "reagents",
    "tool_modes": TOOL_MODES,
    "outputs": OUTPUT_OPTIONS,
    "unsold_hint": None,
    "dump_at": DUMP_AT,
    "hue": 996,
    "poll": 0.25,
    "timeout": 600.0,
}

# Bounds Sources.pick only; the form adds sources one cursor at a time and never calls it
MAX_PICKS = 8

CONTAINER_RANGE = 2

# One tool is fetched at a time from the container the form picked; how long the pack has to show it
FETCH_TIMEOUT = 3.0
FETCH_POLL = 0.25

# Seconds throughout - API.Pause takes seconds
PICK_TIMEOUT = 60.0

# Whole seconds: the API takes an int here
PATHFIND_TIMEOUT = 10

OPEN_DELAY = 0.6
MOVE_DELAY = 0.7

SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25

# ALCHEMY MENU, read off the menu on 2026-09-13
CATEGORY_NAMES = [
    "healing and curative",
    "enhancement",
    "toxic",
    "explosive",
    "strange brew",
    "ingredients",
    "skill tinctures",
]

RECIPES = {
    # Healing and Curative (button 1)
    "refresh": (1, 2),
    "greater refreshment": (1, 22),
    "lesser heal": (1, 42),
    "heal": (1, 62),
    "greater heal": (1, 82),
    "lesser cure": (1, 102),
    "cure": (1, 122),
    "greater cure": (1, 142),
    "elixir of rebirth": (1, 162),
    "barrab hemolymph concentrate": (1, 182),
    # Enhancement (button 21)
    "agility": (21, 2),
    "greater agility": (21, 22),
    "night sight": (21, 42),
    "strength": (21, 62),
    "greater strength": (21, 82),
    "invisibility": (21, 102),
    "jukari burn poultice": (21, 122),
    "kurak ambusher's essence": (21, 142),
    "barako draft of might": (21, 162),
    "urali trance tonic": (21, 182),
    "sakkhra prophylaxis potion": (21, 202),
    # Toxic (button 41)
    "lesser poison": (41, 2),
    "poison": (41, 22),
    "greater poison": (41, 42),
    "deadly poison": (41, 62),
    "parasitic": (41, 82),
    "darkglow": (41, 102),
    "scouring toxin": (41, 122),
    # Explosive (button 61)
    "lesser explosion": (61, 2),
    "explosion": (61, 22),
    "greater explosion": (61, 42),
    "conflagration": (61, 62),
    "greater conflagration": (61, 82),
    "confusion blast": (61, 102),
    "greater confusion blast": (61, 122),
    "black powder": (61, 142),
    "fuse cord": (61, 162),
    # Strange Brew (button 81)
    "smoke bomb": (81, 2),
    "hovering wisp": (81, 22),
    "natural dye": (81, 42),
    "nexus core": (81, 62),
    # Ingredients (button 101)
    "plant pigment": (101, 2),
    "color fixative": (101, 22),
    "crystal granules": (101, 42),
    "crystal dust": (101, 62),
    "softened reeds": (101, 82),
    "vial of vitriol": (101, 102),
    "bottle of ichor": (101, 122),
    "potash": (101, 142),
    "gold dust": (101, 162),
    # Skill Tinctures (button 121)
    "tincture of shadows": (121, 2),
    "tincture of the minstrel": (121, 22),
}
