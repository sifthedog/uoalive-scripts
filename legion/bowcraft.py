import time

import API

# GetSkill answers None for a name it does not know, so the shard's wording is found rather than
# asserted - the gump calls it "Bowcraft/Fletching" and the skill list may not
SKILL_NAMES = ["Bowcraft", "Bowcraft/Fletching", "Fletching"]

MIN_SKILL = 30.0

# The two bands that offer a choice. Flip these to "fukiya darts" and "yumi" without touching BANDS.
LOW_BAND_ITEM = "bow"
HIGH_BAND_ITEM = "repeating crossbow"

# The first row whose ceiling the value is under wins, so the ceilings are exclusive. Value is a
# float percentage here - the src/training tables are in the client's tenths and would be 10x out.
BANDS = [
    (60.0, LOW_BAND_ITEM),
    (70.0, "crossbow"),
    (80.0, "composite bow"),
    (90.0, "heavy crossbow"),
    (None, HIGH_BAND_ITEM),
]

# The CATEGORIES rows, lowercased. Only used to find where the group block ends and the item rows
# begin in the gump text.
CATEGORY_NAMES = ["materials", "ammunition", "weapons"]

# Name as the SELECTIONS row spells it, and the graphics it arrives in the pack as. The graphics are
# what proves a craft landed on the right row, and what the sell counter counts.
PRODUCTS = {
    "bow": set([0x13B2]),
    "crossbow": set([0x0F50]),
    "composite bow": set([0x26C2]),
    "heavy crossbow": set([0x13FD]),
    "repeating crossbow": set([0x26C3]),
    "yumi": set([0x27A5]),
    "fukiya darts": set([0x2806]),
}

PRODUCT_GRAPHICS = set()

for _product in PRODUCTS:
    PRODUCT_GRAPHICS.update(PRODUCTS[_product])

TOOL_GRAPHICS = set([0x1022])
TOOL_NAME_WORDS = ["fletcher", "fletchers"]

# A stack's graphic changes with its size, so match a set rather than one graphic. Hue is
# deliberately not part of the match: a shard with special woods hues them, and those craft too.
LOG_GRAPHICS = set([0x1BDD, 0x1BE0, 0x1BDE, 0x1BDF])
LOG_NAME_WORDS = ["log", "logs"]

# Boards are wood as far as this run is concerned: the menu takes them, and the lumberjack run
# brings boards home rather than logs because they weigh less for the same craft.
BOARD_GRAPHICS = set([0x1BD7, 0x1BD9, 0x1BDA, 0x1BDB])
BOARD_NAME_WORDS = ["board", "boards"]

# Counted as one pool, reported apart. A shard that turns out to craft from only one of the two says
# which kind is sitting in the pack being refused, rather than stalling on a full pack.
WOOD_KINDS = [
    ("logs", LOG_GRAPHICS, LOG_NAME_WORDS),
    ("boards", BOARD_GRAPHICS, BOARD_NAME_WORDS),
]

REGULAR_WOOD = "regular"

# The named woods, read straight off the tooltip: '74 Oak Boards' is oak, and '1580 Boards' with no
# word in front of it is regular. Each is its own resource to the craft menu, which spends the one it
# is set to and refuses every other - a pack full of oak is a pack full of nothing, as far as a menu
# set to regular is concerned.
WOOD_TYPES = ["oak", "ash", "yew", "heartwood", "bloodwood", "frostwood"]

# What the menu is set to, and so what a restock pulls and what counts as stock. Set it to one of
# WOOD_TYPES to work that wood instead, and set the menu to match by hand.
WOOD_TYPE = REGULAR_WOOD

# Hue to wood, for the stack whose tooltip has not arrived - the name is the first thing read, and
# this is what answers when there is no name yet. Incomplete on purpose: these were read off this
# shard, and the log's 'the pack holds ... hue 0x...' line is where the missing ones come from. A
# colour that is in neither table is not treated as regular, whatever else it might be.
WOOD_HUES = {
    0: REGULAR_WOOD,
    1191: "ash",
    2010: "oak",
}

# Wood of the wrong type is weight and nothing else. Off leaves it in the pack.
RETURN_WRONG_WOOD = True

# Above the largest recipe, so a craft never refuses for wood the run thinks it still has. What is
# actually pulled is the smaller of this and what the weight has room for.
BATCH_SIZE = 300
RESTOCK_AT = 25

# What one wood weighs, and only a starting guess: it is learned from the first move that shifts any,
# because a board and a log do not weigh the same and a shard can change either. Pulling a batch
# without it is what put a run at 400/386 in one move.
WOOD_WEIGHT = 1.0

# Counted as amounts, so fukiya darts - which stack ten to a craft - reach this in three crafts.
# Raise it if you run the darts band.
SELL_AT = 20

# Matched against the name *and* the tooltip: a shopkeeper is named "Alger" and titled "the bowyer",
# and only the tooltip carries the title. Matching the name alone found no vendor to sell to.
BOWYER_TITLES = ["bowyer", "fletcher", "archer", "bowyers", "fletchers"]
# Tried before the phrase, and matched against the menu's own text so no entry index is guessed. The
# menu wants you next to the vendor, which is where the run should be standing anyway.
SELL_ENTRY = "sell"
SELL_PHRASE = "vendor sell"

VENDOR_SCAN_RADIUS = 18

# Adjacent. Two tiles away is heard on some shards and not on others, and the context menu is
# refused outright - a sell trip that stopped short is a sell trip that did nothing.
VENDOR_RANGE = 1

# Walks at the vendor before giving up on reaching it. More than one because a pathfind that ends
# early, a doorway and a vendor that stepped aside all look the same from here.
VENDOR_STEPS = 3

CONTEXT_TIMEOUT = 3.0

# Set this to a vendor's serial to skip the search entirely
VENDOR_SERIAL = None

# How long the tooltips have to arrive once they have been asked for
OPL_WAIT = 1.0

# A backstop only - the selection ends when you press ESC
MAX_PICKS = 8

CONTAINER_RANGE = 2

CRAFT_TITLE = "BOWCRAFT AND FLETCHING"

# Any one of them, matched case-insensitively, and only ever to *recognise* a gump - never to refuse
# one. The header is a cliloc the client resolves, and a build whose GetGumpContents answers nothing
# for it made every craft read as 'no craft menu'.
CRAFT_TITLE_TEXT = [CRAFT_TITLE, "BOWCRAFT", "FLETCHING"]
CRAFT_TITLE_FRAGMENTS = [phrase.lower() for phrase in CRAFT_TITLE_TEXT]

# Its own button rather than a group, so it does not count toward the category index
LAST_TEN_LABEL = "LAST TEN"

# This gump numbers its buttons 1 + type + index * 20: categories are type 0 (1, 21, 41), the arrow
# on a SELECTIONS row is type 1 (2, 22, 42, ...), and the fixed buttons sit where this shard puts
# them. Read off a working script for this shard. The stock 7-step numbering this file used to
# assume put MAKE LAST on 21, which is the Ammunition category - so every craft pressed a category.
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MAKE_LAST_BUTTON = 47

# (category button, row button) for the rows this menu is known to carry, so the common products
# cost no probing at all. A product that is not here, or a row this table gets wrong, is found by
# walking the categories exactly as before - the pack is what settles it either way.
RECIPES = {
    "bow": (41, 2),
    "crossbow": (41, 22),
    "heavy crossbow": (41, 42),
    "composite bow": (41, 62),
    "repeating crossbow": (41, 82),
    "yumi": (41, 102),
    "arrow": (21, 2),
    "crossbow bolt": (21, 22),
    "fukiya darts": (21, 42),
    "kindling": (1, 22),
    "shaft": (1, 42),
}

MAX_CATEGORIES = 6
MAX_ITEM_ROWS = 12

# Crafts spent finding the right SELECTIONS row when the gump text does not name it. Each miss costs
# one item's worth of wood, which is why the text is read first.
MAX_ITEM_PROBES = 8

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms
PICK_TIMEOUT = 60.0

# Whole seconds: the API takes an int here where API.Pause takes a float
PATHFIND_TIMEOUT = 10

GUMP_TIMEOUT = 5.0
GUMP_POLL = 0.15

# A craft plays its animation before the shard answers, so this has to outlast the animation
CRAFT_TIMEOUT = 10.0
CRAFT_POLL = 0.2

# How long the pack has to show the new item once the shard has answered
CRAFT_SETTLE = 1.5

OPEN_DELAY = 0.6
MOVE_DELAY = 0.7

SELL_TIMEOUT = 15.0
SELL_POLL = 0.5

SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25

STEP_DELAY = 0.3

MAX_CYCLES = 20000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_TOOL = 10
MAX_EMPTY_MOVES = 3

# Sell trips in a row that bought nothing before the run stops trying for a while. It never ends the
# run: crafting is what takes weight off a pack nothing will buy from.
MAX_SELL_MISSES = 3
SELL_RETRY_AFTER = 25

# The largest recipe in BANDS. Under this there is nothing the run can make, which is the only thing
# that makes a short pack worth another restock cycle rather than a craft.
MIN_CRAFT_WOOD = 10

# Refusals for material while the pack still holds wood a restock cannot add to. One is the shard
# and the run disagreeing about a stack; this many in a row is the wrong kind of wood.
MAX_NO_MATERIAL = 3

THROTTLE_BACKOFF = 1.0
THROTTLE_BACKOFF_MAX = 8.0

# What an unreadable outcome reports before it goes quiet again, and how much of it. Without this
# the one wording that would fix OUTCOME_TEXT is the one thing nothing ever prints.
MAX_UNREADABLE_REPORTS = 2
UNREADABLE_TEXT_LIMIT = 160
JOURNAL_TAIL_SECONDS = 20.0
JOURNAL_TAIL_LINES = 4

# The shard's own pacing, counted rather than narrated: a line per throttle would outnumber the
# progress lines, and a wait nobody can see is what makes a working run look hung.
SAY_THROTTLE_ONCE = True

LOG_EVERY = 25
HEARTBEAT_EVERY = 30.0
STALL_WARN = 60
STALL_STOP = 300

# The container's item cap, counted top level only because the cap is per container
PACK_LIMIT = 120

# Buffer, so the sell trip lands before the shard starts refusing to move the next batch of wood
WEIGHT_BUFFER = 40

SAVE_WAIT = 60.0
SAVE_POLL = 1.0
SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"]
SAVING_TEXT = ["The world is saving", "Saving world", "World save started"]

# Full wordings first: the bare prefix also catches sentences from systems that have nothing to do
# with crafting. Kept last as a fallback all the same - a phrase this list misses reads as an
# unreadable outcome, which is worse.
THROTTLED_TEXT = [
    "You must wait to perform another action",
    "You must wait a moment",
    "You must wait",
]

# Ordered, not a dict: the buckets are polled in order and the first holding a match wins. 'failed'
# is declared before 'made' because "You failed to create the item" contains "create the item".
OUTCOME_TEXT = [
    (
        "failed",
        [
            "You failed to create the item",
            "You fail to create",
            "You have failed to create",
            "lost some of the raw material",
        ],
    ),
    (
        "made",
        [
            "You create the item",
            "You put the",
            "You have worked the wood",
        ],
    ),
    # The gump says this in its NOTICES panel and the journal may never carry it, which is why the
    # outcome is read from both
    (
        "noMaterial",
        [
            "You do not have sufficient wood",
            "You don't have the resources",
            "You do not have the resources",
            "There is not enough wood",
        ],
    ),
    (
        "skillTooLow",
        [
            "You have no idea how to make that",
            "You do not have enough skill",
            "You are not skilled enough",
            "lack the skill",
        ],
    ),
    ("toolWorn", ["You have worn out your tool", "worn out your tool"]),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]


def log(message):
    API.SysMsg("bowcraft: " + message)


def hex_of(value):
    return "0x%x" % (value & 0xFFFFFFFF)


def words_of(text):
    letters = []

    for char in (text or "").lower():
        letters.append(char if char.isalnum() else " ")

    return "".join(letters).split()


def word_in(text, words):
    found = words_of(text)

    for word in words:
        if word in found:
            return True

    return False


def any_in(text, fragments):
    low = (text or "").lower()

    for fragment in fragments:
        if fragment in low:
            return True

    return False


def backoff_for(count, step, cap):
    return min(step * count, cap)


def settled(timeout, poll, landed):
    waited = 0.0

    while waited < timeout:
        API.Pause(poll)
        waited += poll

        if landed():
            return True

    return False


class Heartbeat(object):
    """Proof of life: a loop standing still in silence looks exactly like a hung one."""

    def __init__(self, every):
        self._every = every
        self._last = None

    # The clock, not the cycle counter: a cycle can be 300ms or 8s depending on which waits it hit
    def beat(self, phase, cycle, tally):
        moment = time.time()

        if self._last is None:
            self._last = moment
            return

        if moment - self._last < self._every:
            return

        self._last = moment
        log(
            "still here - %s, cycle %d, %s, %d made"
            % (phase, cycle, weight_reading(), tally)
        )

    def reset(self):
        self._last = time.time()


class StallWatch(object):
    def __init__(self, without, warn_at, stop_at, heartbeat):
        self._without = without
        self._warn_at = warn_at
        self._stop_at = stop_at
        self._heartbeat = heartbeat
        self._since = 0
        self._reason = None

    def end_cycle(self, phase, cycle, tally):
        self._heartbeat.beat(phase, cycle, tally)
        self._since += 1

        if self._since == self._warn_at:
            log("%d %s, last was '%s'" % (self._warn_at, self._without, phase))

        if self._since >= self._stop_at:
            self._reason = "no progress in %d cycles, last was '%s'" % (self._stop_at, phase)

    def progressed(self):
        self._since = 0

    def reason(self):
        return self._reason


heartbeat = Heartbeat(HEARTBEAT_EVERY)
stall = StallWatch("cycles without a craft", STALL_WARN, STALL_STOP, heartbeat)


def said(texts):
    for text in texts:
        if API.InJournal(text, False):
            return True

    return False


def clipped(text, limit):
    flat = " ".join((text or "").split())

    return flat if len(flat) <= limit else flat[:limit] + "..."


# matchingText is left off on purpose: the client only applies it as a regex, so a plain string
# there filters everything out
def journal_tail(seconds, limit):
    try:
        entries = API.GetJournalEntries(seconds)
    except Exception:
        return []

    texts = []

    for entry in entries if entries else []:
        text = getattr(entry, "Text", None)

        if text and text.strip():
            texts.append(text.strip())

    return texts[-limit:]


def matched_bucket(buckets):
    for name, phrases in buckets:
        # clearMatches, or a line already read answers the next wait as well
        if API.InJournalAny(phrases, True):
            return name

    return None


def pack_contents():
    items = API.ItemsInContainer(API.Backpack, True)

    return items if items else []


# The item cap is per container, so the guard counts the top level only
def pack_top_level():
    items = API.ItemsInContainer(API.Backpack, False)

    return items if items else []


def amount_of(item):
    return item.Amount if item.Amount is not None else 1


# API.Player is None whenever the client is between world states - a recall, a server line change,
# the moment around a death - and reading through it threw the run away mid-restock. Every read of
# the player goes through here, and one that finds nothing reads as unknown rather than as a throw.
def player():
    try:
        return API.Player
    except Exception:
        return None


# Unknown is not overweight, the same call WeightMax == 0 gets: the sell trip and the restock ceiling
# are for a weight the client has actually reported. WeightMax reads 0 before the client has been
# told, against which every weight is overweight - a live mining run ended at 436/453 on exactly that.
def over_buffer(buffer):
    me = player()

    if me is None:
        return False

    ceiling = me.WeightMax

    return ceiling > 0 and me.Weight > ceiling - buffer


# For the log lines, which want the numbers whatever state the client is in
def weight_reading():
    me = player()

    return "?/?" if me is None else "%d/%d" % (me.Weight, me.WeightMax)


# Out of range when the position is unknown, so the caller pathfinds and asks again rather than
# treating a client that has not answered as arm's length
def chebyshev(x, y):
    me = player()

    if me is None:
        return CONTAINER_RANGE + 1

    return max(abs(me.X - x), abs(me.Y - y))


def is_saving():
    return said(SAVING_TEXT)


def wait_out_save():
    log("the world is saving, waiting it out")

    # Read before the clear: a save can start and finish inside one craft, and clearing first threw
    # the completion away and then stood still for the whole of SAVE_WAIT
    ended = "the shard had already finished" if said(SAVE_DONE_TEXT) else None

    API.ClearJournal()

    waited = 0.0

    while ended is None and waited < SAVE_WAIT:
        API.Pause(SAVE_POLL)
        waited += SAVE_POLL

        if said(SAVE_DONE_TEXT):
            ended = "the shard says it is done"

    log("%s, carrying on" % (ended or "nothing said in %ds" % int(SAVE_WAIT)))

    heartbeat.reset()


skill_name = None


# A name the client does not carry throws rather than answering None on some builds, and the
# prologue has nothing above it to report the throw
def find_skill_name():
    for name in SKILL_NAMES:
        try:
            if API.GetSkill(name) is not None:
                return name
        except Exception:
            continue

    return None


def skill_value():
    if skill_name is None:
        return None

    skill = API.GetSkill(skill_name)

    # Value reads 0.0 until the skill list arrives, which is a real value too, so it is reported as
    # unknown rather than coerced
    if skill is None or skill.Value <= 0:
        return None

    return skill.Value


def wait_for_skill():
    waited = 0.0

    while waited < SKILL_TIMEOUT:
        value = skill_value()

        if value is not None:
            return value

        API.Pause(SKILL_POLL)
        waited += SKILL_POLL

    return skill_value()


def reading(value):
    return "unknown" if value is None else "%.1f" % value


def band_for(value):
    if value is None:
        return None

    for ceiling, product in BANDS:
        if ceiling is None or value < ceiling:
            return product

    return None


tool_graphic = None


def is_tool(item):
    if item is None:
        return False

    if item.Graphic in TOOL_GRAPHICS:
        return True

    if not word_in(item.Name, TOOL_NAME_WORDS):
        return False

    TOOL_GRAPHICS.add(item.Graphic)
    log("%s '%s' is a fletcher's tool too, remembering the art" % (hex_of(item.Graphic), item.Name))

    return True


def tool_serial():
    for item in pack_contents():
        if is_tool(item):
            return item.Serial

    return None


# Graphic first across every kind, name second: names are empty until the client has tooltip data,
# and an art learned by name joins its kind's set, so it costs one name read and no more.
def wood_kind(item):
    if item is None:
        return None

    for kind, graphics, _words in WOOD_KINDS:
        if item.Graphic in graphics:
            return kind

    for kind, graphics, words in WOOD_KINDS:
        if word_in(item.Name, words):
            graphics.add(item.Graphic)
            log(
                "%s '%s' counts as %s, remembering the art"
                % (hex_of(item.Graphic), item.Name, kind)
            )

            return kind

    return None


def is_wood(item):
    return wood_kind(item) is not None


def hue_of(item):
    return getattr(item, "Hue", 0) or 0


# The name first, because that is where the shard writes it. A name that has not arrived leaves the
# hue: plain is regular, coloured is a wood this table has no word for, and neither is guessed at.
def type_of_wood(item):
    for wood in WOOD_TYPES:
        if word_in(item.Name, [wood]):
            return wood

    return WOOD_HUES.get(hue_of(item))


def usable_wood(item):
    return is_wood(item) and type_of_wood(item) == WOOD_TYPE


def wrong_wood(item):
    return is_wood(item) and type_of_wood(item) != WOOD_TYPE


# Only what the menu will spend. Wood of another type is not stock, however much of it there is -
# counting it is what let a run sit on 300 oak boards reporting a full pack and crafting nothing.
def wood_counts(items):
    counts = {}

    for item in items:
        if not usable_wood(item):
            continue

        kind = wood_kind(item)
        counts[kind] = counts.get(kind, 0) + amount_of(item)

    return counts


# The rest of the wood, by the name the shard gives it, so a pack that reads as empty says why
def other_counts(items):
    counts = {}

    for item in items:
        if not wrong_wood(item):
            continue

        wood = type_of_wood(item) or "unknown"
        counts[wood] = counts.get(wood, 0) + amount_of(item)

    return counts


def other_report(counts):
    parts = []

    for wood in sorted(counts, key=lambda name: -counts[name]):
        parts.append("%d %s" % (counts[wood], wood))

    return ", ".join(parts)


def total_of(counts):
    total = 0

    for kind in counts:
        total += counts[kind]

    return total


# In WOOD_KINDS order, so two runs of the same pack read the same
def wood_report(counts):
    parts = []

    for kind, _graphics, _words in WOOD_KINDS:
        if counts.get(kind, 0) > 0:
            parts.append("%d %s" % (counts[kind], kind))

    return ", ".join(parts) if parts else "no wood"


def pack_wood():
    return wood_counts(pack_contents())


# What the pack holds, in one phrase: what the menu will spend, and what it will not
def pack_report():
    text = wood_report(pack_wood())
    other = other_report(pack_other())

    return text if not other else "%s (%s set aside)" % (text, other)


# Wood in a bag inside the pack is wood the craft may not reach, and it is nearer than the animals
def nested_wood():
    top = set()

    for item in pack_top_level():
        top.add(item.Serial)

    piles = []

    for item in pack_contents():
        if item.Serial not in top and usable_wood(item):
            piles.append(item)

    piles.sort(key=amount_of, reverse=True)

    return piles


# Moves inside the pack cost no weight, so this is free and always worth doing first
def lift_wood_from_bags():
    moved = 0

    for pile in nested_wood():
        before = total_of(wood_counts(pack_top_level()))

        API.MoveItem(pile.Serial, API.Backpack, amount_of(pile))
        API.Pause(MOVE_DELAY)

        gained = total_of(wood_counts(pack_top_level())) - before

        if gained > 0:
            moved += gained

    if moved > 0:
        log("brought %d wood up out of the bags in your pack" % moved)

    return moved


# Hue is what tells one wood from another - oak, ash, yew and heartwood are all 'boards' by name and
# graphic, and the menu spends only the one it is set to. A refusal over a pack full of wood is
# nearly always this, so the log says which hues are actually in there.
def wood_by_hue():
    counts = {}

    for item in pack_contents():
        kind = wood_kind(item)

        if kind is None:
            continue

        key = (kind, hue_of(item), type_of_wood(item) or "unknown")
        counts[key] = counts.get(key, 0) + amount_of(item)

    return counts


def hue_report():
    counts = wood_by_hue()
    parts = []

    for key in sorted(counts, key=lambda pair: -counts[pair]):
        parts.append("%d %s %s hue %s" % (counts[key], key[2], key[0], hex_of(key[1])))

    return ", ".join(parts) if parts else "no wood"


def wood_in_pack():
    return total_of(pack_wood())


def products_in_pack():
    total = 0

    for item in pack_contents():
        if item.Graphic in PRODUCT_GRAPHICS:
            total += amount_of(item)

    return total


# One picked source each: a container item, whose world spot is remembered because a chest does not
# move, or a pack animal, whose backpack is resolved afresh every time because a pet does.
sources = []


def source_name(entry):
    return entry["name"] or hex_of(entry["serial"])


# The animal holds nothing itself - what is read and drawn from is the backpack it wears. Never
# UseObject the animal to open that: on a rideable body a double-click mounts you, and nothing in
# this script dismounts.
def animal_pack(serial):
    animal = API.FindMobile(serial)

    if animal is None:
        return None

    pack = getattr(animal, "Backpack", None)

    if pack is None:
        pack = API.FindLayer("backpack", serial)

    if pack is None:
        return None

    # A build that answers with the serial itself rather than the item is fine too
    return getattr(pack, "Serial", pack)


def source_container(entry):
    if entry["kind"] == "mobile":
        return animal_pack(entry["serial"])

    return entry["serial"]


def source_for(serial):
    item = API.FindItem(serial)

    if item is not None:
        return {
            "kind": "item",
            "serial": serial,
            "name": item.Name or "?",
            "spot": (item.X, item.Y, item.Z),
        }

    animal = API.FindMobile(serial)

    if animal is None:
        return None

    return {"kind": "mobile", "serial": serial, "name": animal.Name or "?", "spot": None}


# ItemsInContainer reads nothing out of a container the client has never seen inside, so a source is
# opened before it is counted or drawn from
def open_source(entry):
    container = source_container(entry)

    if container is None:
        return None

    API.UseObject(container)
    API.Pause(OPEN_DELAY)

    return container


def pick_sources():
    log("target every container or pack animal holding logs or boards, ESC when done")

    me = player()
    mine = me.Serial if me is not None else None

    for _pick in range(MAX_PICKS):
        if API.HasTarget():
            API.CancelTarget()

        serial = API.RequestTarget(PICK_TIMEOUT)

        # Falsy is ESC or a cursor that timed out, and either one ends the selection
        if not serial:
            break

        # Your own pack is where the wood is being counted from in the first place
        if serial == API.Backpack or (mine is not None and serial == mine):
            log("your own pack is always counted, no need to pick it")
            continue

        if serial in [entry["serial"] for entry in sources]:
            continue

        entry = source_for(serial)

        # Not an ending: a misclick on the ground should cost the click and nothing more
        if entry is None:
            log("%s is neither a container nor a creature" % hex_of(serial))
            continue

        # Opened here, and the spot recorded now, because this is the one moment it is in reach
        if open_source(entry) is None:
            log("'%s' has no backpack to draw from" % source_name(entry))
            continue

        sources.append(entry)

        other = other_report(other_counts(source_wood_all(entry)))

        log(
            "picked '%s' %s, %s in it%s"
            % (
                source_name(entry),
                hex_of(serial),
                wood_report(source_counts(entry)),
                "" if not other else " (%s it will not use)" % other,
            )
        )

    if API.HasTarget():
        API.CancelTarget()

    return sources


# Only the type the menu is set to: pulling a pile of oak into a pack a regular menu will not spend
# it from is the whole of what went wrong before
def container_wood(serial):
    items = API.ItemsInContainer(serial, True)
    piles = []

    for item in items if items else []:
        if usable_wood(item):
            piles.append(item)

    piles.sort(key=amount_of, reverse=True)

    return piles


def source_wood(entry):
    container = source_container(entry)

    return [] if container is None else container_wood(container)


# Every wood in there, wrong type included, for the lines that report what a source is holding
def source_wood_all(entry):
    container = source_container(entry)
    items = API.ItemsInContainer(container, True) if container else None

    return [item for item in items if is_wood(item)] if items else []


def source_counts(entry):
    return wood_counts(source_wood(entry))


def source_total(entry):
    return total_of(source_counts(entry))


def stock_left():
    total = 0

    for entry in sources:
        total += source_total(entry)

    return total


def stock_line():
    if len(sources) == 0:
        return "nothing picked to restock from"

    return "%d in the %d you picked" % (stock_left(), len(sources))


def wrong_wood_piles():
    piles = []

    for item in pack_contents():
        if wrong_wood(item):
            piles.append(item)

    return piles


def pack_other():
    return other_counts(pack_contents())


# Wood of another type is weight and nothing else, and the container it came out of is open and in
# reach at exactly this moment - which is the only moment putting it back costs nothing
def put_back(container):
    before = total_of(pack_other())

    if before == 0:
        return 0

    for pile in wrong_wood_piles():
        API.MoveItem(pile.Serial, container, amount_of(pile))
        API.Pause(MOVE_DELAY)

    moved = before - total_of(pack_other())

    if moved > 0:
        log("put %d wood the menu will not spend back" % moved)

    return moved


wood_weight = WOOD_WEIGHT


def carried():
    me = player()

    return None if me is None else me.Weight


# None when the client has not said, which reads as no limit - the same call over_buffer makes
def room_for_wood():
    me = player()

    if me is None or me.WeightMax <= 0:
        return None

    return int((me.WeightMax - WEIGHT_BUFFER - me.Weight) / max(wood_weight, 0.1))


def learn_wood_weight(each):
    global wood_weight

    # Sanity: a move the client mis-timed can read as any weight at all
    if each < 0.1 or each > 50 or abs(each - wood_weight) < 0.05:
        return

    wood_weight = each
    log("one wood weighs %.1f here, pulling to fit" % each)


def reach_source(entry):
    if entry["kind"] == "mobile":
        animal = API.FindMobile(entry["serial"])

        if animal is None:
            return False

        if animal.Distance <= CONTAINER_RANGE:
            return True

        API.PathfindEntity(entry["serial"], CONTAINER_RANGE, True, PATHFIND_TIMEOUT)
        API.CancelPathfinding()

        animal = API.FindMobile(entry["serial"])

        return animal is not None and animal.Distance <= CONTAINER_RANGE

    spot = entry["spot"]

    # A container picked inside the pack has no world position worth walking to
    if spot is None or (spot[0] == 0 and spot[1] == 0):
        return True

    if chebyshev(spot[0], spot[1]) <= CONTAINER_RANGE:
        return True

    API.Pathfind(spot[0], spot[1], spot[2], CONTAINER_RANGE, True, PATHFIND_TIMEOUT)

    return chebyshev(spot[0], spot[1]) <= CONTAINER_RANGE


# Moves are asynchronous, so the pack is re-counted between them rather than MoveItem's return value
# being trusted. A move that gains nothing MAX_EMPTY_MOVES times running is a container that is done.
def restock():
    # The pack is read before anything is fetched: what is already here, bags included, counts
    moved = lift_wood_from_bags()

    wanted = BATCH_SIZE - wood_in_pack()

    if wanted <= 0:
        return moved

    for entry in sources:
        if moved >= wanted or over_buffer(WEIGHT_BUFFER):
            break

        if not reach_source(entry):
            log("cannot reach '%s', trying the next" % source_name(entry))
            continue

        container = open_source(entry)

        if container is None:
            log("'%s' has no backpack to draw from" % source_name(entry))
            continue

        if RETURN_WRONG_WOOD:
            put_back(container)

        stalled = 0

        while moved < wanted and stalled < MAX_EMPTY_MOVES and not over_buffer(WEIGHT_BUFFER):
            piles = container_wood(container)

            if len(piles) == 0:
                break

            room = room_for_wood()
            take = min(wanted - moved, amount_of(piles[0]))

            if room is not None:
                take = min(take, room)

            # Not a stall: there is wood there and no room for it, which the caller reports
            if take <= 0:
                break

            before = wood_in_pack()
            heavy = carried()

            API.MoveItem(piles[0].Serial, API.Backpack, take)
            API.Pause(MOVE_DELAY)

            gained = wood_in_pack() - before

            if gained <= 0:
                stalled += 1
            else:
                stalled = 0
                moved += gained

                now = carried()

                if heavy is not None and now is not None and now > heavy:
                    learn_wood_weight((now - heavy) / float(gained))

    if moved > 0:
        log(
            "pulled %d wood, %s in the pack, %d left in what you picked"
            % (moved, pack_report(), stock_left())
        )

    if over_buffer(WEIGHT_BUFFER) and moved < wanted:
        log("stopped short of the batch at %s" % weight_reading())

    return moved


# HasGump answers the gump's *type* id, which every page of one craft menu shares, and ReplyGump
# disposes the gump it answers before the shard sends the next page. So the wait is for the menu to
# be back, never for a different id: waiting for the id to change is what this used to do, and it
# could not come true - every press timed out and reported 'no craft menu' for a menu that was
# reopening correctly each time.
def await_gump(timeout):
    waited = 0.0

    while waited < timeout:
        found = API.HasGump()

        if found:
            return found

        API.Pause(GUMP_POLL)
        waited += GUMP_POLL

    return 0


craft_gump_id = 0
said_gump_text = False


# The craft menu is the gump id *changing*. WaitForGump with no id resolves to whatever LastGumpID
# already is, so it answers a stale gump when one is open and times out when none is.
def press(button, gump, timeout):
    global craft_gump_id

    # False is the client saying the gump was gone before the button was pressed, which is a
    # different fact from the page not coming back and is worth not waiting out the timeout for
    if not API.ReplyGump(button, gump):
        return 0

    found = await_gump(timeout)

    # Only ever the craft menu presses buttons here, so whatever answered is the menu's next page
    if found:
        craft_gump_id = found

    return found


def is_craft_gump(ident):
    if not ident:
        return False

    if any_in(API.GetGumpContents(ident) or "", CRAFT_TITLE_FRAGMENTS):
        return True

    # The client's own search gets a turn: it reads controls GetGumpContents may not put in the text
    for phrase in CRAFT_TITLE_TEXT:
        if API.GumpContains(phrase, ident):
            return True

    return False


def craft_gump():
    global craft_gump_id, said_gump_text

    found = API.HasGump()

    # The one already being driven, or one that names itself
    if found and (found == craft_gump_id or is_craft_gump(found)):
        craft_gump_id = found

        return found

    serial = tool_serial()

    if serial is None:
        return None

    # Any other server gump has to go first: the wait below is for a gump to be *there*, and a
    # vendor's or a status gump standing open answers it before the tools have opened anything
    if found:
        log("closing the gump that is in the way %s" % hex_of(found))
        API.CloseGump(found)
        API.Pause(GUMP_POLL)

    API.UseObject(serial)

    found = await_gump(GUMP_TIMEOUT)

    if not found:
        return None

    # Whatever the tools opened is the menu. The title is not a gate - it is a cliloc the client
    # resolves, and refusing a gump over it is what made a working craft menu read as no menu at
    # all. A gump that does not name itself is reported once and then used.
    if not said_gump_text and not is_craft_gump(found):
        said_gump_text = True
        lines = gump_lines(found)
        log(
            "the tools opened a gump that does not name %s - it starts '%s'"
            % (CRAFT_TITLE, lines[0] if lines else "(no text)")
        )

    craft_gump_id = found

    return found


def gump_lines(gump):
    text = API.GetGumpContents(gump)
    lines = []

    for line in (text or "").split("\n"):
        stripped = line.strip()

        if stripped:
            lines.append(stripped)

    return lines


# The stock gump emits the group rows before the item rows, so everything past the last group name
# is this page's SELECTIONS. A shard that emits them the other way round leaves this empty.
def item_rows(gump):
    lines = gump_lines(gump)
    start = None

    for index in range(len(lines)):
        if lines[index].lower() in CATEGORY_NAMES or lines[index].upper() == LAST_TEN_LABEL:
            start = index + 1

    return [] if start is None else lines[start:]


# A whole row, never a substring: "crossbow" is inside "crossbow bolt", so a substring match finds
# the wanted item in the Ammunition category and never reaches Weapons at all
def page_has(product, gump):
    rows = item_rows(gump)

    for row in rows:
        if row.lower() == product:
            return True

    return len(rows) == 0 and API.GumpContains(product, gump)


def button_id(kind, index):
    return 1 + kind + index * BUTTON_STRIDE


category_buttons = {}
category_rejects = {}
said_no_category = False


# Pressing a category only redraws the SELECTIONS panel, so walking them costs nothing - which is
# why the category is found this way and the row below is not
def find_category(product, gump):
    global said_no_category

    known = category_buttons.get(product)

    if known is not None:
        return (press(known, gump, GUMP_TIMEOUT), known)

    rejected = category_rejects.get(product, set())

    for index in range(MAX_CATEGORIES):
        button = button_id(CATEGORY_BUTTON_TYPE, index)

        if button in rejected:
            continue

        opened = press(button, gump, GUMP_TIMEOUT)

        # A category that answered nothing says nothing about the category, so the caller retries
        # rather than ending the run over it
        if not opened:
            return (0, 0)

        if page_has(product, opened):
            category_buttons[product] = button
            log("'%s' is in the category on button %d" % (product, button))

            return (opened, button)

        gump = opened

    if not said_no_category:
        said_no_category = True
        log("no category lists '%s' - check the name against the SELECTIONS rows" % product)

    return (gump, None)


item_buttons = {}
item_probes = {}
said_no_row = set()

# Products RECIPES got wrong on this shard, which the walk owns from then on
walked_products = set()


# The text is read first and only falls back to walking the rows, because unlike a category a wrong
# row here crafts the wrong item and spends the wood for it
def candidate_buttons(product, gump):
    rows = item_rows(gump)
    order = []

    for index in range(len(rows)):
        if rows[index].lower() == product:
            order.append(button_id(ITEM_BUTTON_TYPE, index))

    if len(order) == 0 and product not in said_no_row:
        said_no_row.add(product)
        log("the gump text does not name '%s' on a row of its own, walking the rows" % product)
        log("rows seen: %s" % (", ".join(rows) if rows else "none"))

    for index in range(MAX_ITEM_ROWS):
        button = button_id(ITEM_BUTTON_TYPE, index)

        if button not in order:
            order.append(button)

    return order


def counts_of(graphics):
    total = 0

    for item in pack_contents():
        if item.Graphic in graphics:
            total += amount_of(item)

    return total


def notice_bucket(gump):
    if not gump:
        return None

    for name, phrases in OUTCOME_TEXT:
        for phrase in phrases:
            if API.GumpContains(phrase, gump):
                return name

    return None


# Three things every pass, and the pack is one of them. The journal is not read first because the
# shard writes its refusals into the NOTICES panel; the pack is not read *last* because a success
# whose wording this table has not got is still a success - and waiting out CRAFT_TIMEOUT for a line
# that was never coming is a silent ten-second stall on a craft that worked.
def read_outcome(opened, landed):
    waited = 0.0

    while True:
        if landed():
            return "made"

        hit = matched_bucket(OUTCOME_TEXT)

        if hit is None:
            hit = notice_bucket(opened)

        if hit is not None:
            return hit

        if waited >= CRAFT_TIMEOUT:
            return None

        API.Pause(CRAFT_POLL)
        waited += CRAFT_POLL


make_last = False
said_unreadable = 0


# The shard's own words for an outcome this script cannot act on - the gump's panel and the journal
# it cleared before the press, so what comes back belongs to this craft and nothing older. A refusal
# nobody can read is the one thing that cannot be fixed from the log.
def report_outcome(why, gump):
    global said_unreadable

    if said_unreadable >= MAX_UNREADABLE_REPORTS:
        return

    said_unreadable += 1

    text = clipped(" ".join(gump_lines(gump)), UNREADABLE_TEXT_LIMIT) if gump else ""
    lines = journal_tail(JOURNAL_TAIL_SECONDS, JOURNAL_TAIL_LINES)

    log("%s - the gump says '%s'" % (why, text or "(nothing)"))
    log("the journal says '%s'" % (" | ".join(lines) or "(nothing)"))
    log("the pack holds %s, and the menu is set to %s here" % (hue_report(), WOOD_TYPE))


def forget_row(product):
    global make_last

    make_last = False

    if product in item_buttons:
        del item_buttons[product]

    item_probes[product] = item_probes.get(product, 0) + 1


# MAKE LAST is the only path that skips the category: an item button indexes whichever SELECTIONS
# page is showing, so a remembered one crafts whatever sits on that row of the wrong page
def craft_once(product):
    global make_last, said_unreadable

    # Asked apart from the gump, so an empty pack and a menu that will not open are not one message
    if tool_serial() is None:
        return "noTool"

    gump = craft_gump()

    if gump is None:
        return "noGump"

    button = item_buttons.get(product)

    known = None if product in walked_products else RECIPES.get(product)

    if make_last and button is not None:
        button = MAKE_LAST_BUTTON
    elif known is not None:
        # Remembered too, so a walk that starts later - after a worn tool, say - starts in the right
        # category rather than from the first one
        category_buttons[product] = known[0]

        gump = press(known[0], gump, GUMP_TIMEOUT)

        if not gump:
            return "noGump"

        button = known[1]
    else:
        gump, category = find_category(product, gump)

        if category is None:
            return "noRow"

        if not gump:
            return "noGump"

        if button is None:
            order = candidate_buttons(product, gump)
            probe = item_probes.get(product, 0)

            if probe >= min(MAX_ITEM_PROBES, len(order)):
                rejected = category_rejects.setdefault(product, set())
                rejected.add(category)
                del category_buttons[product]

                if len(rejected) >= MAX_CATEGORIES:
                    return "noRow"

                item_probes[product] = 0
                log("no row on button %d's page made a '%s', trying another category" % (category, product))

                return "wrongRow"

            button = order[probe]

    before = counts_of(PRODUCTS[product])

    def made_one():
        return counts_of(PRODUCTS[product]) > before

    API.ClearJournal()

    opened = press(button, gump, CRAFT_TIMEOUT)
    outcome = read_outcome(opened, made_one)

    # The one proof no wording can argue with, and it is checked before the wordings are trusted: a
    # shard that says nothing on a success still puts the bow in the pack
    if outcome == "made" or outcome is None:
        if made_one() or settled(CRAFT_SETTLE, CRAFT_POLL, made_one):
            if item_buttons.get(product) is None:
                item_buttons[product] = button
                log("'%s' is the row on button %d" % (product, button))

            make_last = True
            said_unreadable = 0

            return "made"

    if outcome != "made":
        # Nothing was made and nothing was said. MAKE LAST is the first thing to doubt - the shard
        # forgets what was last made for reasons this script cannot see - so the next craft goes
        # back through the category and the row, which is the path that proved itself.
        if outcome == "noMaterial":
            report_outcome("refused for materials", opened)

        if outcome is None:
            report_outcome("nothing readable came back", opened)

            if button == MAKE_LAST_BUTTON:
                make_last = False
                log("MAKE LAST made nothing, pressing the row itself next time")

        return outcome

    # It said it made something and none of it was the wanted product, so the row was the wrong one
    log("button %d did not make a '%s', trying the next row" % (button, product))

    # A row RECIPES named is a row this shard has moved, so the walk takes the product over for good
    if product in RECIPES and product not in walked_products:
        walked_products.add(product)
        log("the button table is out of date for '%s', walking the categories for it instead" % product)

    forget_row(product)

    return "wrongRow"


said_overweight = False


# Weight stops nothing here. It is reported when it starts and when it clears, and that is all: the
# run has no way to put the pack down that is not selling it, and it is already trying to sell.
def warn_overweight():
    global said_overweight

    if over_buffer(0):
        if not said_overweight:
            said_overweight = True
            log("overweight at %s - carrying on, crafting is what takes it off" % weight_reading())
    elif said_overweight:
        said_overweight = False
        log("no longer overweight, at %s" % weight_reading())


said_no_vendor = False


def tooltip_of(mobile):
    try:
        return mobile.NameAndProps(False) or ""
    except Exception:
        return ""


def vendor_candidates():
    me = player()
    mine = me.Serial if me is not None else None
    found = []

    for mobile in API.GetAllMobiles(None, VENDOR_SCAN_RADIUS) or []:
        # Your own pets are the bulk of what is standing around a crafter, and only yours rename
        if mobile.IsDead or mobile.Serial == mine or mobile.IsRenamable:
            continue

        found.append(mobile)

    return found


# Name first because it costs nothing, tooltips second because they cost a round trip each: a
# shopkeeper is "Alger" by name and "the bowyer" only in the tooltip, which is why the name pass
# alone kept answering that there was no bowyer in sight.
def find_bowyer():
    if VENDOR_SERIAL:
        return API.FindMobile(VENDOR_SERIAL)

    candidates = vendor_candidates()

    for mobile in candidates:
        if any_in(mobile.Name, BOWYER_TITLES):
            return mobile

    if len(candidates) == 0:
        return None

    API.RequestOPLData([mobile.Serial for mobile in candidates])
    API.Pause(OPL_WAIT)

    for mobile in candidates:
        if any_in(tooltip_of(mobile), BOWYER_TITLES):
            return mobile

    return None


# Re-resolved every pass rather than the found mobile trusted: a pathfind that ends early leaves you
# short, and the only way to know is to ask where the vendor is now.
def walk_to_vendor(serial):
    for _step in range(VENDOR_STEPS):
        here = API.FindMobile(serial)

        if here is None:
            return None

        if here.Distance <= VENDOR_RANGE:
            return here

        API.PathfindEntity(serial, VENDOR_RANGE, True, PATHFIND_TIMEOUT, True)
        API.CancelPathfinding()
        API.Pause(STEP_DELAY)

    here = API.FindMobile(serial)

    return here if here is not None and here.Distance <= VENDOR_RANGE else None


said_sell_how = False


# The context menu first: it is the vendor's own 'Sell', matched by its text, and it does not depend
# on the shard hearing a phrase. The phrase is still there for a menu that has no such entry.
def ask_to_sell(serial):
    global said_sell_how

    asked = False

    try:
        asked = API.ContextMenu(serial, SELL_ENTRY, CONTEXT_TIMEOUT)
    except Exception:
        asked = False

    if not asked:
        API.Msg(SELL_PHRASE)

    if not said_sell_how:
        said_sell_how = True
        log("selling by %s" % ("the vendor's own Sell menu" if asked else "saying '%s'" % SELL_PHRASE))

    return asked


def sell_trip():
    global said_no_vendor

    vendor = find_bowyer()

    if vendor is None:
        if not said_no_vendor:
            said_no_vendor = True
            names = [mobile.Name or "?" for mobile in vendor_candidates()]
            log(
                "no bowyer within %d - looked at %d: %s"
                % (VENDOR_SCAN_RADIUS, len(names), clipped(", ".join(names), UNREADABLE_TEXT_LIMIT) or "nobody")
            )

        return False

    said_no_vendor = False

    name = vendor.Name or hex_of(vendor.Serial)
    here = walk_to_vendor(vendor.Serial)

    if here is None:
        log("could not get next to '%s', trying again next time" % name)

        return False

    before = products_in_pack()
    log("selling %d to '%s'" % (before, name))

    ask_to_sell(vendor.Serial)

    sold = settled(SELL_TIMEOUT, SELL_POLL, lambda: products_in_pack() < before)

    # Never the bare form: it closes the last gump, which is as likely to be the craft menu
    found = API.HasGump()

    if found and found != craft_gump_id and not is_craft_gump(found):
        API.CloseGump(found)

    if not sold:
        log("the vendor bought nothing - is the auto-sell agent on?")
    else:
        log("sold, %d left in the pack" % products_in_pack())

    heartbeat.reset()

    return sold


def stop_reason():
    if API.StopRequested:
        return "stopped from the script manager"

    me = player()

    if me is not None and me.IsDead:
        return "you are dead"

    skill = API.GetSkill(skill_name) if skill_name is not None else None

    if skill is not None and skill.Value > 0 and skill.Value >= skill.Cap:
        return "%s is capped at %.1f" % (skill_name, skill.Value)

    return None


if API.HasTarget():
    API.CancelTarget()

skill_name = find_skill_name()

if skill_name is None:
    log("the client reports none of %s - check SKILL_NAMES" % ", ".join(SKILL_NAMES))
    API.Stop()

start = wait_for_skill()

if start is None:
    log("%s is not reading yet - start it again once the skill list has arrived" % skill_name)
    API.Stop()
elif start < MIN_SKILL:
    log("%s is at %.1f and the table starts at %.1f - train it up by hand first" % (skill_name, start, MIN_SKILL))
    API.Stop()

if tool_serial() is None:
    log("no fletcher's tools in the pack")
    API.Stop()

pick_sources()

# Nothing picked is only an ending when the pack is empty too: a run that starts on the wood it is
# already carrying is a run that needed no cursor at all
if len(sources) == 0 and wood_in_pack() == 0:
    log("nothing picked and no wood in the pack")
    API.Stop()

log(
    "%s at %.1f, %s in the pack, %s"
    % (skill_name, start, pack_report(), stock_line())
)

if wood_in_pack() < RESTOCK_AT:
    restock()

stop = None
tally = 0
fails = 0
unknown = 0
throttled = 0
no_tool = 0
no_material = 0
throttle_tally = 0
said_throttle = False
sell_misses = 0
sell_paused_until = 0
reported = 0
cycle = 0
product = None
last_skill = start


def end_cycle(phase):
    global stop

    stall.end_cycle(phase, cycle, tally)

    if stop is None:
        stop = stall.reason()


try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1

        stop = stop_reason()

        if stop is not None:
            break

        # Everything below reads a frozen shard as its own failure: a craft that answers nothing is
        # an unreadable outcome, a move that gains nothing is an empty container
        if is_saving():
            wait_out_save()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        value = skill_value()

        if value is not None and value != last_skill:
            last_skill = value
            stall.progressed()

        wanted = band_for(value if value is not None else last_skill)

        if wanted is None:
            stop = "%s reads %s and no band covers it" % (skill_name, reading(value))
            break

        if wanted != product:
            log("%s at %s, making %s" % (skill_name, reading(value), wanted))
            product = wanted
            make_last = False

        # Weight is never an ending. Said once a stretch, because a run that cannot sell can still
        # craft, and every craft turns wood the pack is carrying into one lighter item.
        warn_overweight()

        wants_sale = (
            products_in_pack() >= SELL_AT
            or over_buffer(WEIGHT_BUFFER)
            or len(pack_top_level()) >= PACK_LIMIT
        )

        if wants_sale and cycle >= sell_paused_until:
            if sell_trip():
                sell_misses = 0

                end_cycle("selling")
                continue

            sell_misses += 1

            # The trip is worth retrying, but not every cycle for ever: without this it walks to the
            # vendor and back on each pass and the crafting never gets a turn
            if sell_misses >= MAX_SELL_MISSES:
                sell_misses = 0
                sell_paused_until = cycle + SELL_RETRY_AFTER
                log(
                    "%d sell trips bought nothing - crafting on, and asking again in %d cycles"
                    % (MAX_SELL_MISSES, SELL_RETRY_AFTER)
                )

        if wood_in_pack() < RESTOCK_AT:
            # Weight and an unreachable container also pull nothing, and neither is an empty
            # container - the stall watch is what ends those
            pulled = restock()

            if pulled == 0 and stock_left() == 0 and wood_in_pack() < MIN_CRAFT_WOOD:
                stop = (
                    "out of %s wood - %s in the pack, none left in what you picked"
                    % (WOOD_TYPE, pack_report())
                )
                break

            # Only a pack with nothing makeable in it is worth spending the cycle on: a short pack
            # that can still make something crafts, which is also what takes weight off
            if wood_in_pack() < MIN_CRAFT_WOOD:
                end_cycle("restocking")
                continue

        outcome = craft_once(product)

        if outcome == "made":
            tally += 1
            unknown = 0
            throttled = 0
            no_material = 0
            stall.progressed()
        elif outcome == "failed":
            # Still a gain and still spends the wood, so it counts as the loop getting somewhere
            fails += 1
            unknown = 0
            throttled = 0
            no_material = 0
            stall.progressed()
        elif outcome == "noMaterial":
            unknown = 0
            pulled = restock()

            if pulled > 0:
                no_material = 0
                stall.progressed()
            elif wood_in_pack() < RESTOCK_AT and stock_left() == 0:
                stop = "the shard says there is not enough wood and there is none left to pull"
                break
            else:
                # Wood in the pack that a restock cannot add to, refused all the same: what a shard
                # that crafts from only one of logs and boards looks like from in here
                no_material += 1

                if no_material >= MAX_NO_MATERIAL:
                    stop = (
                        "the shard refused %s in the pack %d times - read the gump's own words "
                        "above; if it wants another wood, set WOOD_TYPE and the menu to match"
                        % (pack_report(), no_material)
                    )
                    break
        elif outcome == "wrongRow":
            unknown = 0
            stall.progressed()
        elif outcome == "toolWorn":
            make_last = False
            unknown = 0
            stall.progressed()
            log("the tools wore out, looking for another pair")
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s at %s" % (product, reading(value))
            break
        elif outcome == "noRow":
            stop = "could not find the SELECTIONS row for '%s'" % product
            break
        elif outcome == "noTool" or outcome == "noGump":
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = "no fletcher's tools left" if outcome == "noTool" else "the craft menu will not open"
                break

            log(
                "%s (%d/%d), trying again"
                % (
                    "no fletcher's tools in the pack"
                    if outcome == "noTool"
                    else "the tools opened no craft menu",
                    no_tool,
                    MAX_NO_TOOL,
                )
            )
            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
        elif outcome == "throttled":
            throttled += 1
            throttle_tally += 1

            if throttled >= MAX_THROTTLED:
                stop = "%d throttled crafts in a row" % MAX_THROTTLED
                break

            waiting = backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

            # Said once, then only tallied: the pause itself is the shard's, and it is normal
            if SAY_THROTTLE_ONCE and not said_throttle:
                said_throttle = True
                log(
                    "the shard is pacing the crafts - waiting %.1fs, and counting these from here on"
                    % waiting
                )

            API.Pause(waiting)
        elif outcome == "saving":
            unknown = 0
            stall.progressed()
        else:
            unknown += 1
            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        if outcome != "noTool" and outcome != "noGump":
            no_tool = 0

        if unknown >= MAX_UNKNOWN:
            stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
            break

        if tally >= reported + LOG_EVERY:
            reported = tally
            log(
                "%d made, %d failed, %d throttled, %s at %s, %s left"
                % (
                    tally,
                    fails,
                    throttle_tally,
                    skill_name,
                    reading(value),
                    wood_report(pack_wood()),
                )
            )

        end_cycle(outcome if outcome is not None else "unknown")
        API.Pause(STEP_DELAY)
except Exception as error:
    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error

if API.Pathfinding():
    API.CancelPathfinding()

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES
ended = skill_value()

log(
    "%d made, %d failed, %d throttled, %s %.1f -> %s"
    % (tally, fails, throttle_tally, skill_name, start, reading(ended))
)
log("stopping - %s" % reason)
API.Stop()
