import time

import API

PICKAXE_NAME = "pickaxe"

# Worth setting only if the spares are somewhere ItemsInContainer's recursive read does not reach
SPARE_BAG_SERIAL = None

# Land carries no name, so the table is the whole answer for it. Stock RunUO bands and a hypothesis
# about this shard - a dead-end run prints the arts it actually saw.
ORE_TILE_GRAPHICS = set()

for _first, _last in [(220, 251), (1339, 1359), (1361, 1383), (1386, 1394)]:
    for _art in range(_first, _last + 1):
        ORE_TILE_GRAPHICS.add(_art)

# A seed only - a refusal learned on the shard goes into the run's memory rather than back in here
NOT_ORE_GRAPHICS = set()

# Cave floors are statics, and those the client can name. 'rock' also names the pebbles scattered
# over half the world, which is the cheap direction to be wrong in: the first swing bans the art.
ORE_STATIC_NAME = ["cave", "rock", "mountain", "ore"]

# Where walking stops and swinging starts, not a range the shard enforces - the swing names no tile
MINE_RANGE = 2

# Distance is Chebyshev over x and y, so a mountain face 40 z up is 'one tile away' and the walk at
# it never closes
MINE_Z_RANGE = 20

SCAN_RADIUS = 12
SURVEY_ARTS = 15

# How long one blocking pathfind may take, in place of the web client's per-tile step budget
PATHFIND_TIMEOUT = 10

# Cycles spent walking to one vein before it is written off, where the web client counted single
# steps: a blocking pathfind covers the whole route in one
MAX_VEIN_WALKS = 4

# GetPath costs a call per candidate, where the web client's flood fill answered every tile at
# once, so only this many of the nearest matches are asked for a route
MAX_PATH_PROBES = 24

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms
RESPAWN_DELAY = 25 * 60.0
UNREACHABLE_DELAY = 5 * 60.0

# A swing plays its animation before the result arrives, so this has to outlast the animation
DIG_TIMEOUT = 8.0

DIG_TARGET_TIMEOUT = 4.0
DIG_TARGET_POLL = 0.1

# Waited on as the cursor itself, because HasTarget cannot be relied on - get this wrong and every
# swing reports no target cursor
DIG_PROMPT_TEXT = ["Where do you wish to dig"]

# A short window for a refusal worded a moment late; the journal was cleared just before the swing
NO_CURSOR_READ = 0.5

# A set to match against and nothing more: a pile of 33 arrives wearing the art the stock tables
# call a single, so a stack's size comes from item.Amount alone
ORE_GRAPHICS = set([0x19B7, 0x19BA, 0x19B9, 0x19B8])

# A whole word: 'ore' inside 'sycamore' would put something in the smelter
ORE_NAME_WORD = "ore"

INGOT_GRAPHICS = set([0x1BEF, 0x1BF0, 0x1BF1, 0x1BF2])

COMBINE_DELAY = 0.7
COMBINE_TIMEOUT = 2.0
COMBINE_POLL = 0.2
MAX_COMBINE_ATTEMPTS = 12

# ItemNameAndProps takes whole seconds
OPL_TIMEOUT = 1

ORE_METALS = set(
    [
        "iron",
        "dull copper",
        "shadow iron",
        "copper",
        "bronze",
        "gold",
        "agapite",
        "verite",
        "valorite",
    ]
)

# Letters only, so the divider the client draws between tooltip blocks is not read as a metal.
# The line must start with a letter and hold nothing but letters and these.
METAL_LINE_EXTRA = " '-"

# 'ore' because the name line is that word on its own
NOT_METAL_WORDS = set(
    [
        "blessed",
        "cursed",
        "insured",
        "exceptional",
        "newbie",
        "antique",
        "brittle",
        "unmovable",
        "weight",
        "contents",
        "ore",
    ]
)

METAL_MISSES = 3
METAL_ASKS = 3

DIFFERENT_ORE_TEXT = ["You cannot combine ores of different metals"]

# A swing's ore arrives after the sentence that announced it
ORE_SETTLE_TIMEOUT = 1.5
ORE_SETTLE_POLL = 0.15

FIRE_BEETLE_GRAPHICS = set([0xA9])
FIRE_BEETLE_SERIAL = None

# A cursor at startup, so the beetle is chosen rather than guessed at by body and renamability -
# which picks a stranger's pet if theirs is the nearer one. ESC falls back to that search.
PICK_BEETLE = True

BEETLE_SCAN_RADIUS = 18
SMELT_RANGE = 2

# Waiting on a person rather than on the shard, unlike TARGET_TIMEOUT
PICK_TIMEOUT = 60.0

SMELT_DELAY = 0.7
SMELT_TIMEOUT = 4.0
SMELT_POLL = 0.2

# Two ore make an ingot, so a stack of one is refused - silently, in a way the pack diff cannot tell
# from a throttled attempt
MIN_SMELT_AMOUNT = 2

SMELT_ATTEMPTS = 3
MAX_SMELT_PASSES = 60

DISMOUNT_TIMEOUT = 2.0
DISMOUNT_POLL = 0.2
DISMOUNT_ATTEMPTS = 3

EQUIP_TIMEOUT = 2.0
EQUIP_POLL = 0.2
EQUIP_ATTEMPTS = 3

TARGET_TIMEOUT = 2.0

STEP_DELAY = 0.3
IDLE_POLL = 10.0
IDLE_LOG_EVERY = 60.0

MAX_CYCLES = 5000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_CURSOR = 20
MAX_NO_TOOL = 10

THROTTLE_BACKOFF = 1.0
THROTTLE_BACKOFF_MAX = 8.0

LOG_EVERY = 25
HEARTBEAT_EVERY = 30.0
STALL_WARN = 60
STALL_STOP = 300

# The container's item cap. There is deliberately no weight guard: one would fire before the smelt
# ever ran, and what ends an overweight run is a smelt that freed nothing.
PACK_LIMIT = 120

# Spots in a row with nothing in them before the run says ORE_TILE_GRAPHICS is probably wrong
NOTHING_NEARBY_HINT = 5

SAVE_WAIT = 60.0
SAVE_POLL = 1.0
SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"]
SAVING_TEXT = ["The world is saving", "Saving world", "World save started"]

# Full wordings first, bare prefix last: reading an unrelated 'You must wait N seconds' as a refusal
# costs a pass, where missing a real one writes off a hue
THROTTLED_TEXT = [
    "You must wait to perform another action",
    "You must wait a moment",
    "You must wait",
]

UNSKILLED_TEXT = [
    "You have no idea how to smelt this strange ore",
    "You are not skilled enough",
    "You lack the required skill",
    "You do not have enough skill",
]

WATCH_FOR_TROUBLE = True

# Innocent is out, or every blue NPC in the world is trouble. Passed through as enum members: the
# API.py stub lists every Notoriety value as 1, so an int written against it is wrong at runtime.
HOSTILE_NOTORIETY = [
    API.Notoriety.Gray,
    API.Notoriety.Criminal,
    API.Notoriety.Enemy,
    API.Notoriety.Murderer,
]

# Gray is out: the wildlife is gray, and a cat wandering past is not evidence of anything. A gray
# still draws the call the moment it damages you or the pet.
CALL_ON_SIGHT_NOTORIETY = [
    API.Notoriety.Criminal,
    API.Notoriety.Enemy,
    API.Notoriety.Murderer,
]

THREAT_RANGE = 12
GUARD_CALL = "guards"
GUARD_CALLS = 3
GUARD_CALL_DELAY = 10.0
GUARD_REPLY_WAIT = 0.8

NO_GUARDS_TEXT = [
    "The guards can not be called here",
    "The guards cannot be called here",
    "Guards can not be called here",
    "Guards cannot be called here",
    "There are no guards here",
]

# Empty on purpose: nothing in stock RunUO announces being attacked, and a wrong guess calls the
# guards every cycle of a quiet run
ATTACK_TEXT = []

GUARD_ZONE_TEXT = ["under the protection of the town guards", "now under guard"]
UNGUARDED_TEXT = ["left the protection of the town guards", "no longer under guard"]

# Ordered, not a dict: InJournalAny answers yes/no, so the buckets are polled in order and the first
# holding a match wins. Guesses for a RunUO-family shard - correct them against the real journal.
OUTCOME_TEXT = [
    ("dug", ["You dig some", "You put", "You loosen some rocks"]),
    # Both wordings are in the wild: RunUO says metal, some shards say ore
    (
        "empty",
        [
            "There is no metal here to mine",
            "There is no ore here to mine",
            "You cannot mine there",
        ],
    ),
    # The shard answering about everything in reach rather than about a tile, which is what parks
    # the whole area and walks the character off
    (
        "nothingNearby",
        ["There are no harvestable resources nearby", "There is nothing here to harvest"],
    ),
    ("notOre", ["You can't mine that", "Try mining in rock", "You can only mine"]),
    ("tooFar", ["That is too far away", "You cannot reach that"]),
    ("notSeen", ["Target cannot be seen"]),
    # The ore is destroyed rather than dropped when this fires, so it triggers a consolidation
    ("packFull", ["Your backpack is full", "That container cannot hold more"]),
    ("wornOut", ["You have worn out your tool"]),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]


def log(message):
    API.SysMsg("mining: " + message)


def hex_of(value):
    return "0x%x" % (value & 0xFFFFFFFF)


def words_of(text):
    letters = []

    for char in (text or "").lower():
        letters.append(char if char.isalnum() else " ")

    return "".join(letters).split()


def word_in(text, word):
    return word in words_of(text)


def any_in(text, fragments):
    low = (text or "").lower()

    for fragment in fragments:
        if fragment in low:
            return True

    return False


def looks_like_metal(line):
    if not line or not line[0].isalpha():
        return False

    for char in line:
        if not char.isalpha() and char not in METAL_LINE_EXTRA:
            return False

    for word in words_of(line):
        if word in NOT_METAL_WORDS:
            return False

    return True


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
            "still here - %s, cycle %d, at %d,%d, %d/%d, %d swings"
            % (
                phase,
                cycle,
                API.Player.X,
                API.Player.Y,
                API.Player.Weight,
                API.Player.WeightMax,
                tally,
            )
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
stall = StallWatch("cycles without a swing landing", STALL_WARN, STALL_STOP, heartbeat)


def said(texts):
    for text in texts:
        if API.InJournal(text, False):
            return True

    return False


def pack_contents():
    items = API.ItemsInContainer(API.Backpack, True)

    return items if items else []


# The item cap is per container, so the guard and the combine both count the top level only
def pack_top_level():
    items = API.ItemsInContainer(API.Backpack, False)

    return items if items else []


def stop_reason():
    if API.StopRequested:
        return "stopped from the script manager"

    if API.Player.IsDead:
        return "you are dead"

    if len(pack_top_level()) >= PACK_LIMIT:
        return "the pack is at its item cap"

    return None


def is_saving():
    return said(SAVING_TEXT)


def wait_out_save():
    log("the world is saving, waiting it out")

    # Read before the clear: a save can start and finish inside one swing, and clearing first threw
    # the completion away and then stood still for the whole of SAVE_WAIT
    ended = "the shard had already finished" if said(SAVE_DONE_TEXT) else None

    API.ClearJournal()

    waited = 0.0

    while ended is None and waited < SAVE_WAIT:
        API.Pause(SAVE_POLL)
        waited += SAVE_POLL

        if said(SAVE_DONE_TEXT):
            ended = "the shard says it is done"
        elif stop_reason() is not None:
            ended = "the run has a reason to stop"

    log("%s, carrying on" % (ended or "nothing said in %ds" % int(SAVE_WAIT)))

    heartbeat.reset()


def matched_bucket(buckets):
    for name, phrases in buckets:
        # clearMatches, or a line already read answers the next wait as well
        if API.InJournalAny(phrases, True):
            return name

    return None


def read_outcome(buckets, budget, poll):
    waited = 0.0

    while True:
        hit = matched_bucket(buckets)

        if hit is not None:
            return hit

        if waited >= budget:
            return None

        API.Pause(poll)
        waited += poll


pickaxe_graphic = None
reported_empty_pack = False


def is_pickaxe(item):
    if item is None:
        return False

    if pickaxe_graphic is not None and item.Graphic == pickaxe_graphic:
        return True

    return PICKAXE_NAME in (item.Name or "").lower()


def held_tool():
    return API.FindLayer("onehanded")


def remember_pickaxe(item):
    global pickaxe_graphic

    if item is not None and pickaxe_graphic is None:
        pickaxe_graphic = item.Graphic
        log("pickaxe graphic is %s" % hex_of(item.Graphic))


def pickaxe_serial():
    item = held_tool()

    return item.Serial if item is not None else None


def find_pickaxe():
    global reported_empty_pack

    for item in pack_contents():
        if is_pickaxe(item):
            reported_empty_pack = False
            remember_pickaxe(item)

            return item

    if SPARE_BAG_SERIAL is not None:
        for item in API.ItemsInContainer(SPARE_BAG_SERIAL, True) or []:
            if is_pickaxe(item):
                reported_empty_pack = False
                remember_pickaxe(item)

                return item

    if not reported_empty_pack:
        reported_empty_pack = True
        arts = []

        for item in pack_contents():
            arts.append(hex_of(item.Graphic))

        log("no pickaxe found. Pack holds: %s" % (", ".join(arts) or "nothing"))

    return None


# A broken tool can linger on the layer, and is_pickaxe would match it by graphic, so the world is
# asked rather than the layer
def still_holding():
    item = held_tool()

    return item is not None and is_pickaxe(item) and API.FindItem(item.Serial) is not None


def equip_pickaxe():
    if still_holding():
        return True

    found = find_pickaxe()

    if found is None:
        return False

    # A cursor left open by the swing that broke the tool would swallow the equip
    if API.HasTarget():
        API.CancelTarget()

    serial = found.Serial

    for _attempt in range(EQUIP_ATTEMPTS):
        API.EquipItem(serial)

        if settled(EQUIP_TIMEOUT, EQUIP_POLL, lambda: pickaxe_serial() == serial):
            return True

    log("could not get the pickaxe %s onto the hand" % hex_of(serial))

    return False


def dismount():
    if not API.Player.IsMounted:
        return True

    for _attempt in range(DISMOUNT_ATTEMPTS):
        API.Dismount()

        if settled(DISMOUNT_TIMEOUT, DISMOUNT_POLL, lambda: not API.Player.IsMounted):
            return True

    return False


# A tooltip that answers with no metal line is plain iron, and it has to key the same as one saying
# 'Iron' or two piles of the one metal sit apart for the whole run
PLAIN_METAL = "iron"

metals = {}
metal_asks = {}
missed_this_pass = set()
doubted_metals = set()

opl_names_metals = True
opl_answered = False
metal_misses = 0


def read_metal(props, name):
    lines = []

    for raw in (props or "").splitlines():
        line = raw.strip()

        if line and line != name:
            lines.append(line)

    for line in lines:
        if line.lower() in ORE_METALS:
            return line.lower()

    for line in lines:
        if looks_like_metal(line):
            ORE_METALS.add(line.lower())
            log("'%s' is a metal too, remembering it" % line)

            return line.lower()

    return PLAIN_METAL


def worth_asking(serial):
    return (
        opl_names_metals
        and serial not in missed_this_pass
        and metal_asks.get(serial, 0) < METAL_ASKS
    )


def look_up_metal(item):
    global opl_names_metals, opl_answered, metal_misses

    serial = item.Serial

    if serial in metals or not worth_asking(serial):
        return

    metal_asks[serial] = metal_asks.get(serial, 0) + 1

    props = API.ItemNameAndProps(serial, True, OPL_TIMEOUT) or ""
    name = (item.Name or "").strip()

    # A miss is an unanswered tooltip, which here is an empty string or one carrying only the name -
    # the structured OPL this was ported from reported it as an empty property list
    body = []

    for raw in props.splitlines():
        line = raw.strip()

        if line and line != name:
            body.append(line)

    if not body:
        missed_this_pass.add(serial)
        metal_misses += 1

        if metal_misses >= METAL_MISSES:
            opl_names_metals = False
            log("tooltips are not naming the metal here, so a pair has to be refused to be split")

        return

    metal_misses = 0
    opl_answered = True
    metals[serial] = read_metal(props, name)


# None is 'the tooltip did not say', which is not a metal of its own: callers fall back to the hue
# and the shard's refusal for those
def metal_of(item):
    look_up_metal(item)

    metal = metals.get(item.Serial)

    return None if metal is not None and metal in doubted_metals else metal


def metal_pending(item):
    look_up_metal(item)

    # Not worth_asking: a pile that missed this pass is still pending, or it would be paired on a
    # guess the moment its lookup came back empty
    return (
        opl_answered
        and opl_names_metals
        and item.Serial not in metals
        and metal_asks.get(item.Serial, 0) < METAL_ASKS
    )


def start_metal_pass():
    missed_this_pass.clear()


def doubt_metal(metal):
    if metal in doubted_metals:
        return

    doubted_metals.add(metal)
    log("the shard refused two piles both read as '%s', so that line is not the metal" % metal)


# The shard reissues the serial of a pile a combine or a smelt consumed, so a stale entry would name
# the wrong metal for whatever turns up wearing it next
def forget_missing_metals(piles):
    here = set()

    for pile in piles:
        here.add(pile.Serial)

    for serial in list(metals.keys()):
        if serial not in here:
            del metals[serial]

    for serial in list(metal_asks.keys()):
        if serial not in here:
            del metal_asks[serial]


# Graphic first, name second: names are empty until the client has tooltip data. An art learned by
# name joins the set, so it costs one tooltip and no more.
def is_ore_pile(item):
    if item.Graphic in ORE_GRAPHICS:
        return True

    if not word_in(item.Name, ORE_NAME_WORD):
        return False

    ORE_GRAPHICS.add(item.Graphic)
    log("%s '%s' is ore too, remembering the art" % (hex_of(item.Graphic), item.Name))

    return True


def amount_of(item):
    return item.Amount if item.Amount is not None else 1


def hue_of(item):
    return item.Hue or 0


def describe_pile(item):
    metal = metal_of(item)

    return "%d %s" % (amount_of(item), metal if metal is not None else "hue %d" % hue_of(item))


# Top level only, unlike ore_total: the combine and the smelt both act by serial on loose items.
# Largest first, so the pile a combine consumes is always the smaller one.
def ore_piles():
    piles = []

    for item in pack_top_level():
        if is_ore_pile(item):
            piles.append(item)

    piles.sort(key=amount_of, reverse=True)

    return piles


# Hue-blind on purpose: every ore type counts toward the pack, whatever it smelts into
def ore_total():
    total = 0

    for item in pack_contents():
        if is_ore_pile(item):
            total += amount_of(item)

    return total


# Reads the total rather than the number of piles, so a shard that does merge ore on arrival is
# satisfied immediately instead of waiting out the timeout on every swing
def wait_for_ore(before):
    waited = 0.0

    while True:
        # Read before the first pause: the delivery has usually already happened by the time the
        # journal line announcing it is read
        if ore_total() > before:
            return True

        if waited >= ORE_SETTLE_TIMEOUT:
            return False

        API.Pause(ORE_SETTLE_POLL)
        waited += ORE_SETTLE_POLL


# The backstop for the piles no tooltip named. Remembered by serial, which is why it cannot carry a
# run alone: every swing delivers a pile wearing a serial nothing has been learned about.
differing_pairs = set()

# This call only: a silent miss is as likely to be a busy moment as a verdict, and remembering it for
# the run would split two piles of one metal for good
skipped_pairs = set()


def serial_key(a, b):
    return "s%d:%d" % (a.Serial, b.Serial) if a.Serial < b.Serial else "s%d:%d" % (b.Serial, a.Serial)


def hue_key(a, b):
    low, high = sorted([hue_of(a), hue_of(b)])

    return "h%d:%d" % (low, high)


# Never for hue 0, which is both iron and 'the client has not said yet'
def hue_tells_apart(a, b):
    return hue_of(a) != 0 and hue_of(b) != 0 and hue_of(a) != hue_of(b)


# Only ever forbids: one pile the tooltip could not name must not split its own metal
def metal_tells_apart(a, b):
    mine = metal_of(a)
    theirs = metal_of(b)

    return mine is not None and theirs is not None and mine != theirs


def differs(a, b):
    # A pile whose tooltip is still in flight is paired with nothing at all - guessing at it earned
    # a refusal every cycle, and one more swing loose costs the pack nothing
    return (
        metal_pending(a)
        or metal_pending(b)
        or metal_tells_apart(a, b)
        or serial_key(a, b) in differing_pairs
        or serial_key(a, b) in skipped_pairs
        or (hue_tells_apart(a, b) and hue_key(a, b) in differing_pairs)
    )


def same_metal(a, b):
    mine = metal_of(a)

    return mine is not None and mine == metal_of(b)


# A merge is silent either way, so the pack is the evidence: the consumed pile gone, or the pile it
# went into grown. The refusal cuts the wait short, or a pack holding two metals spends the whole
# timeout on every swing.
def merged(primary, dup, before):
    waited = 0.0

    while waited < COMBINE_TIMEOUT:
        piles = pack_contents()
        grown = None
        dup_here = False

        for item in piles:
            if item.Serial == primary.Serial:
                grown = item
            elif item.Serial == dup.Serial:
                dup_here = True

        if not dup_here or (grown is not None and amount_of(grown) > before):
            return True

        if said(DIFFERENT_ORE_TEXT):
            return False

        API.Pause(COMBINE_POLL)
        waited += COMBINE_POLL

    return False


def combine(primary, dup):
    before = amount_of(primary)

    API.ClearJournal()

    # No cancel before the use: a cursor cancelled shortly before an action has been measured
    # costing that action its own cursor
    API.UseObject(dup.Serial)

    if not API.WaitForTarget("any", TARGET_TIMEOUT):
        API.CancelTarget()
        skipped_pairs.add(serial_key(primary, dup))
        log("no target cursor for %s" % describe_pile(dup))

        return

    API.Target(primary.Serial)

    if merged(primary, dup, before):
        return

    # Nothing was attempted, so nothing has been learned about the metals
    if said(THROTTLED_TEXT):
        log("the shard says wait, leaving the two of them paired")

        return

    if said(DIFFERENT_ORE_TEXT):
        metal = metal_of(primary)

        if metal is not None and metal == metal_of(dup):
            doubt_metal(metal)

        differing_pairs.add(serial_key(primary, dup))

        if hue_tells_apart(primary, dup):
            differing_pairs.add(hue_key(primary, dup))

        return

    skipped_pairs.add(serial_key(primary, dup))
    log("%s and %s did not merge and nothing was said" % (describe_pile(primary), describe_pile(dup)))


# The first pile that can join one already seen. Everything ahead of it is a family of its own, so
# returning nothing means every pile in the pack is a metal of its own.
def next_pair(piles):
    primaries = []

    for pile in piles:
        home = None

        # The tooltip's metal first, then hue: hue is right nearly always, and wrong costs a refusal
        for primary in primaries:
            if same_metal(primary, pile) and not differs(primary, pile):
                home = primary
                break

        if home is None:
            for primary in primaries:
                if hue_of(primary) == hue_of(pile) and not differs(primary, pile):
                    home = primary
                    break

        if home is None:
            for primary in primaries:
                if not differs(primary, pile):
                    home = primary
                    break

        if home is not None:
            return home, pile

        primaries.append(pile)

    return None


def group_ores():
    skipped_pairs.clear()
    start_metal_pass()

    for _attempt in range(MAX_COMBINE_ATTEMPTS):
        piles = ore_piles()
        forget_missing_metals(piles)

        pair = next_pair(piles)

        if pair is None:
            if len(skipped_pairs) > 0 and len(piles) > 1:
                log("left %d piles - %s" % (len(piles), ", ".join(map(describe_pile, piles))))

            return

        combine(pair[0], pair[1])
        API.Pause(COMBINE_DELAY)

    log("hit the %d combine attempt backstop" % MAX_COMBINE_ATTEMPTS)


beetle_serial = FIRE_BEETLE_SERIAL

# A serial chosen rather than guessed - from config or from the cursor - is the law, so a moment out
# of sight is not a reason to go looking for someone else's beetle
beetle_pinned = FIRE_BEETLE_SERIAL is not None

reported_beetle = False
reported_no_beetle = False


def pick_beetle():
    global beetle_serial, beetle_pinned, reported_beetle

    # A cursor left open by whatever ran last would swallow this query
    if API.HasTarget():
        API.CancelTarget()

    log("target your fire beetle, ESC to let the script find it")

    serial = API.RequestTarget(PICK_TIMEOUT)

    if not serial:
        # A cancelled pick can still leave the cursor up, and a live one would spend the
        # double-clicks that follow as target clicks instead
        if API.HasTarget():
            API.CancelTarget()

        log("nothing picked, looking for one instead")

        return None

    picked = API.FindMobile(serial)

    if picked is None:
        log("%s is not a mobile, looking for one instead" % hex_of(serial))

        return None

    # Not a refusal: FIRE_BEETLE_GRAPHICS is a guess at this shard, so a body it has never heard of
    # is worth reporting and then using
    if picked.Graphic not in FIRE_BEETLE_GRAPHICS:
        log("%s is not a body FIRE_BEETLE_GRAPHICS knows, using it anyway" % hex_of(picked.Graphic))

    beetle_serial = serial
    beetle_pinned = True
    reported_beetle = True
    log("using '%s' %s as the forge" % (picked.Name or hex_of(serial), hex_of(picked.Graphic)))

    return picked


def find_beetle():
    global beetle_serial, reported_beetle

    if beetle_serial is not None:
        resolved = API.FindMobile(beetle_serial)

        if resolved is not None:
            return resolved

        # Out of range, dead, or a hand-written serial that was never a mobile
        if beetle_pinned:
            return None

        beetle_serial = None

    found = []

    for graphic in FIRE_BEETLE_GRAPHICS:
        for mobile in API.GetAllMobiles(graphic, BEETLE_SCAN_RADIUS) or []:
            found.append(mobile)

    if not found:
        return None

    # Only your own pets can be renamed, so this is what tells yours from a stranger's
    mine = [mobile for mobile in found if mobile.IsRenamable]
    candidates = mine if mine else found
    candidates.sort(key=lambda mobile: mobile.Distance)

    beetle = candidates[0]

    if not reported_beetle:
        reported_beetle = True
        log("using '%s' %s as the forge" % (beetle.Name or hex_of(beetle.Serial), hex_of(beetle.Graphic)))

    beetle_serial = beetle.Serial

    return beetle


# item.Amount reads 0 for a stack the client has no data for, so 'amount >= 2' skips every pile in
# the pack. An unknown size is worth one attempt; only a size reported as one is skipped.
def big_enough(item):
    amount = item.Amount or 0

    return amount == 0 or amount >= MIN_SMELT_AMOUNT


def next_ore(written_off):
    for item in ore_piles():
        if hue_of(item) not in written_off and big_enough(item):
            return item

    return None


def describe_skipped_pile(item, written_off):
    amount = item.Amount or 0
    hue = hue_of(item)

    if hue in written_off:
        return "%d hue %d (written off)" % (amount, hue)

    if not big_enough(item):
        return "%d hue %d (too small)" % (amount, hue)

    return "%d hue %d" % (amount, hue)


forge = None


# A smelt aimed at a beetle that has drifted out of range fails exactly the way ore that cannot be
# worked does: silently. Three of those wrote off 86 ore of one colour on a live run.
def forge_gone():
    if forge is None:
        return "no beetle to smelt against"

    here = API.FindMobile(forge.Serial)

    if here is None:
        return "the beetle %s is out of sight" % hex_of(forge.Serial)

    if here.Distance > SMELT_RANGE:
        return "the beetle has wandered %d tiles off" % here.Distance

    return None


def counts_by_graphic():
    counts = {}

    for item in pack_contents():
        key = "%d/%d" % (item.Graphic, hue_of(item))
        counts[key] = counts.get(key, 0) + amount_of(item)

    return counts


def diff_counts(before, after):
    changes = []

    for key in set(list(before.keys()) + list(after.keys())):
        delta = after.get(key, 0) - before.get(key, 0)

        if delta != 0:
            changes.append((key, delta))

    return changes


written_off = set()
smelt_misses = {}

# Whether anything has converted since the last retry. Without it a retry granted unconditionally
# answers true again next cycle and the caller loops until the stall watchdog ends the run.
smelt_progressed = True


# Every failing path comes through here: one that returns without counting leaves the candidate set
# unchanged, so the next pass picks the same stack and the loop runs to its backstop
def smelt_missed(hue):
    count = smelt_misses.get(hue, 0) + 1
    smelt_misses[hue] = count

    if count >= SMELT_ATTEMPTS:
        written_off.add(hue)
        log("hue %d failed %d times, leaving it as ore" % (hue, count))


def learn_ingot(changes):
    for key, delta in changes:
        if delta <= 0:
            continue

        graphic = int(key.split("/")[0])

        if graphic in ORE_GRAPHICS or graphic in INGOT_GRAPHICS:
            continue

        INGOT_GRAPHICS.add(graphic)
        log("ingot graphic is %s" % hex_of(graphic))


# The action throttle can hold a conversion well past any pause worth taking, and reading too early
# is indistinguishable from a resource that cannot be worked
def wait_for_change(before):
    waited = 0.0

    while waited < SMELT_TIMEOUT:
        API.Pause(SMELT_POLL)
        waited += SMELT_POLL

        changes = diff_counts(before, counts_by_graphic())

        if changes:
            return changes

    return []


# The journal is cleared to perform the smelt, so a save that starts mid-attempt is past the check at
# the top of the pass: one cost three hues and ended a live run overweight beside a working beetle
def smelt_saving(hue):
    if not is_saving():
        return False

    log("the world is saving, not counting it against hue %d" % hue)

    return True


# The inverse of making boards: the ore is double-clicked and the beetle is the target. The beetle is
# never double-clicked itself - it is rideable, so that mounts you.
def perform_smelt(stack):
    if forge is None:
        return False

    # Cancelled only when there is one to cancel: a cursor cancelled shortly before an action has
    # been measured costing that action its own
    if API.HasTarget():
        API.CancelTarget()

    API.ClearJournal()
    API.UseObject(stack.Serial)

    if not API.WaitForTarget("any", TARGET_TIMEOUT):
        API.CancelTarget()
        log("no target cursor for the beetle")

        return False

    API.Target(forge.Serial)

    return True


def convert_one(stack):
    global smelt_progressed

    hue = hue_of(stack)
    before = counts_by_graphic()

    if not perform_smelt(stack):
        if smelt_saving(hue):
            return

        # Counted like any other failure: without this an empty hand spends every pass waiting on a
        # cursor that is never going to come
        smelt_missed(hue)

        return

    changes = wait_for_change(before)

    if changes:
        smelt_misses.pop(hue, None)
        smelt_progressed = True
        learn_ingot(changes)

        return

    # Asked before either wording, because a frozen shard's verdict on the material is worthless
    if smelt_saving(hue):
        return

    # Nothing was attempted, so this is not a verdict on the material
    if said(THROTTLED_TEXT):
        log("the shard says wait, not counting it against hue %d" % hue)

        return

    if said(UNSKILLED_TEXT):
        written_off.add(hue)
        log("not skilled enough for hue %d, leaving it as ore" % hue)

        return

    # Otherwise it was silent, which is also what a throttled or stale attempt looks like
    smelt_missed(hue)


def run_converter():
    for _pass in range(MAX_SMELT_PASSES):
        # A frozen shard answers a conversion the same way an unworkable material does, so without
        # this a world save costs SMELT_ATTEMPTS and writes the hue off for the rest of the run
        if is_saving():
            log("the world is saving, leaving it for now")

            return False

        stack = next_ore(written_off)

        if stack is None:
            piles = ore_piles()

            if len(piles) > 0:
                described = [describe_skipped_pile(pile, written_off) for pile in piles]
                log("nothing to smelt in %d pile(s) - %s" % (len(piles), ", ".join(described)))

            return True

        # Asked only once there is something that needs it, which is what makes smelting on every
        # dry vein affordable
        blocked = forge_gone()

        if blocked is not None:
            log("%s, leaving it for now" % blocked)

            return False

        convert_one(stack)
        API.Pause(SMELT_DELAY)

    log("hit the %d smelt pass backstop" % MAX_SMELT_PASSES)

    return False


def retry_unsmeltable(force=False):
    global smelt_progressed

    if len(written_off) == 0 or (not smelt_progressed and not force):
        return False

    smelt_progressed = False
    log("giving %d hue(s) written off earlier another go" % len(written_off))
    written_off.clear()
    smelt_misses.clear()

    return True


# A pet's coordinates go stale within a cycle, so the serial is re-resolved rather than the
# find_beetle result trusted
def walk_to_beetle(serial):
    here = API.FindMobile(serial)

    if here is None:
        log("lost track of %s" % hex_of(serial))

        return None

    if here.Distance <= SMELT_RANGE:
        return here

    API.PathfindEntity(serial, SMELT_RANGE, True, PATHFIND_TIMEOUT)
    API.CancelPathfinding()

    here = API.FindMobile(serial)

    if here is None or here.Distance > SMELT_RANGE:
        log("could not get within %d of the beetle" % SMELT_RANGE)

        return None

    return here


# The stationary counterpart: a beetle not already next to you is not a forge this run can use
def beetle_in_range(serial):
    found = API.FindMobile(serial)

    if found is None:
        log("lost track of %s" % hex_of(serial))

        return None

    if found.Distance > SMELT_RANGE:
        log("the beetle is %d tiles off and this run does not walk" % found.Distance)

        return None

    return found


def smelt_against(reach):
    global forge, reported_no_beetle

    # Asked before the beetle is looked for, so a pack with nothing eligible costs neither a search
    # nor a walk
    if next_ore(written_off) is None:
        return run_converter()

    found = find_beetle()

    if found is None:
        # Said once rather than every pass: a missing beetle is not fatal, the ore travels unsmelted
        if not reported_no_beetle:
            reported_no_beetle = True
            log("no fire beetle nearby, keeping the ore as it is")

        return False

    reported_no_beetle = False
    forge = reach(found.Serial)

    if forge is None:
        return False

    return run_converter()


def smelt_all():
    return smelt_against(walk_to_beetle)


# WeightMax reads 0 before the client has been told, against which every weight is overweight - a
# run ended at 436/453 on exactly that. No buffer: ore travels as ore until it cannot travel at all.
def too_heavy():
    ceiling = API.Player.WeightMax

    return ceiling > 0 and API.Player.Weight > ceiling


def group_and_smelt():
    group_ores()
    smelt_all()


def smelt_for_room():
    if not too_heavy():
        return None

    before = ore_total()

    # Unconditional, because the decision has already been taken: a helper that asked too_heavy() a
    # second time could disagree, and the run stopped for weight without ever having tried
    group_ores()
    smelt_all()

    # Ore leaving the pack is the proof, not the weight going down: the client can still report its
    # pre-smelt figure over a conversion the pack diff has confirmed
    if ore_total() < before:
        return "smelting"

    # Before the retry rather than after it: a frozen shard converts nothing, and a retry spent here
    # is the run's only one gone
    if is_saving():
        wait_out_save()

        return "smelting"

    if retry_unsmeltable():
        return "smelting"

    # The retry above has just reopened the hues written off, so this pass is the one that can act
    group_ores()
    smelt_all()

    if ore_total() < before:
        return "smelting"

    if is_saving():
        wait_out_save()

        return "smelting"

    return {
        "stop": "overweight (%d/%d) with %d ore left, and smelting freed nothing"
        % (API.Player.Weight, API.Player.WeightMax, ore_total())
    }


def silent_outcome(serial, ore_before):
    if serial is not None and API.FindItem(serial) is None:
        return "wornOut"

    if ore_total() > ore_before:
        return "dug"

    return "unknown"


# HasTarget alone was not enough on the web client: a measured swing had the shard's prompt in the
# journal at 164ms and the cursor flag false for the whole six seconds after it
def cursor_opened():
    waited = 0.0

    while waited < DIG_TARGET_TIMEOUT:
        if API.HasTarget() or said(DIG_PROMPT_TEXT):
            return True

        API.Pause(DIG_TARGET_POLL)
        waited += DIG_TARGET_POLL

    return False


# No cursor is not the same as nothing having happened: the commonest reason a shard declines a swing
# is that it refused the action outright and said so
def refused_outcome(serial, ore_before):
    matched = read_outcome(OUTCOME_TEXT, NO_CURSOR_READ, DIG_TARGET_POLL)

    if matched is not None:
        return matched

    silent = silent_outcome(serial, ore_before)

    if silent != "unknown":
        return silent

    log("no target cursor - the shard never asked where to dig")

    return "noCursor"


def dig_once(serial):
    # A pathfind still running would walk the character away mid-swing
    if API.Pathfinding():
        API.CancelPathfinding()

    # Cancelled only when there is one to cancel: an unconditional cancel a few hundred milliseconds
    # before the swing left the next cursor unusable in the run this was copied from
    if API.HasTarget():
        API.CancelTarget()

    ore_before = ore_total()
    API.ClearJournal()

    API.UseObject(serial)

    if not cursor_opened():
        return refused_outcome(serial, ore_before)

    # Answered with yourself rather than with the vein's coordinates: the shard takes that as 'mine
    # where I am' and picks the ore itself, so nothing has to guess land versus static
    API.TargetSelf()

    matched = read_outcome(OUTCOME_TEXT, DIG_TIMEOUT, DIG_TARGET_POLL)

    return matched if matched is not None else silent_outcome(serial, ore_before)


last_hits = 0
last_companion_hits = 0
last_call = 0.0
guard_calls = 0
in_episode = False
no_guards = False
said_protection = False
guard_zone = None


# 0 is what the client reports while it is refreshing stats, and for a mobile it has lost track of,
# so a fall to 0 is no news at all
def dropped(was, is_now):
    return was > 0 and is_now > 0 and is_now < was


def hostiles_near(notoriety):
    found = API.GetAllMobiles(None, THREAT_RANGE, notoriety) or []

    for mobile in found:
        # IsRenamable is how the rest of this repo tells your own pet from a stranger's, and a pet
        # flagged gray by whatever it was fighting would otherwise read as the thing attacking you
        if mobile.Serial != API.Player.Serial and not mobile.IsDead and not mobile.IsRenamable:
            return mobile

    return None


def read_zone():
    global guard_zone

    if said(GUARD_ZONE_TEXT):
        guard_zone = "guarded"
    elif said(UNGUARDED_TEXT):
        guard_zone = "unguarded"


# Nothing in the API answers this. A yellow human is a guard or a vendor, and either one means a
# town, which is the best the client can be asked.
def protection():
    if guard_zone is not None:
        return "the journal says %s" % guard_zone

    for mobile in API.GetAllMobiles(None, THREAT_RANGE, [API.Notoriety.Invulnerable]) or []:
        if mobile.IsHuman and not mobile.IsDead:
            return "an invulnerable '%s' in sight, so probably a town" % (mobile.Name or "?")

    return "nothing in sight to say either way"


def call_guards():
    global last_call, guard_calls, said_protection, no_guards

    if no_guards or (GUARD_CALLS > 0 and guard_calls >= GUARD_CALLS):
        return

    at = time.time()

    if guard_calls > 0 and at - last_call < GUARD_CALL_DELAY:
        return

    last_call = at
    guard_calls += 1

    if not said_protection:
        said_protection = True
        log("guard protection - %s" % protection())

    log("calling the guards (%d%s)" % (guard_calls, "/%d" % GUARD_CALLS if GUARD_CALLS > 0 else ""))
    API.Msg(GUARD_CALL)

    if not NO_GUARDS_TEXT:
        return

    if read_outcome([("refused", NO_GUARDS_TEXT)], GUARD_REPLY_WAIT, GUARD_REPLY_WAIT) is not None:
        no_guards = True
        log("the shard says the guards cannot be called here - not calling again this run")


def describe_trouble(hostile, friend):
    if hostile is not None:
        who = "'%s' %s %d tiles off" % (
            hostile.Name or "?",
            hex_of(hostile.Graphic),
            hostile.Distance,
        )
    else:
        who = "nothing in sight"

    ceiling = API.Player.HitsMax
    mine = "you %d/%s" % (API.Player.Hits, ceiling if ceiling > 0 else "?")
    theirs = ""

    if friend is not None:
        theirs = ", beetle %d/%s" % (friend.Hits, friend.HitsMax or "?")

    return "%s, %s%s" % (who, mine, theirs)


def watch_for_trouble():
    global last_hits, last_companion_hits, in_episode, guard_calls

    if not WATCH_FOR_TROUBLE:
        return

    read_zone()

    hits = API.Player.Hits
    hurt = dropped(last_hits, hits)

    if hits > 0:
        last_hits = hits

    friend = find_beetle()
    friend_hits = friend.Hits if friend is not None else 0
    friend_hurt = dropped(last_companion_hits, friend_hits)

    if friend_hits > 0:
        last_companion_hits = friend_hits

    attacked = said(ATTACK_TEXT) if ATTACK_TEXT else False
    hostile = hostiles_near(HOSTILE_NOTORIETY)

    if hostile is None and not hurt and not friend_hurt and not attacked:
        if in_episode:
            in_episode = False
            guard_calls = 0
            log("clear")

        return

    if not in_episode:
        in_episode = True
        log("trouble - %s" % describe_trouble(hostile, friend))

    # Blood drawn is evidence whatever its notoriety; being in sight is only evidence for the
    # notorieties CALL_ON_SIGHT_NOTORIETY names
    on_sight = hostile is not None and hostile.Notoriety in CALL_ON_SIGHT_NOTORIETY

    if hurt or friend_hurt or attacked or on_sight:
        call_guards()


terrain_cache = {}

# Land and static tiledata are numbered in separate tables, so 1339 is a mountain band as land and a
# cave floor as a static. Everything keyed on an art keys on the kind too.
blocked_tiles = {}
not_ore_arts = set()


def art_key(graphic, is_land):
    return "%s:%d" % ("land" if is_land else "static", graphic)


def tile_key(tile):
    return "%d,%d,%d,%s" % (tile["x"], tile["y"], tile["z"], art_key(tile["graphic"], tile["is_land"]))


# Land and statics do not change during a session, so a coordinate costs one pair of calls for the
# whole run
def terrain_at(x, y):
    key = (x, y)
    cached = terrain_cache.get(key)

    if cached is not None:
        return cached

    tiles = []
    land = API.GetTile(x, y)

    if land is not None:
        tiles.append(
            {"x": x, "y": y, "z": land.Z, "graphic": land.Graphic, "is_land": True, "name": ""}
        )

    for static in API.GetStaticsAt(x, y) or []:
        tiles.append(
            {
                "x": x,
                "y": y,
                "z": static.Z,
                "graphic": static.Graphic,
                "is_land": False,
                "name": static.Name or "",
            }
        )

    terrain_cache[key] = tiles

    return tiles


# Refusals first, seeds second: ORE_TILE_GRAPHICS ships full, so asking it first made
# mark_not_mineable silently do nothing - the ban was recorded and ignored on the next scan
def is_ore(graphic, is_land, name):
    if graphic in NOT_ORE_GRAPHICS or art_key(graphic, is_land) in not_ore_arts:
        return False

    # No name to fall back on, so the table is the whole answer for land
    if is_land:
        return graphic in ORE_TILE_GRAPHICS

    return any_in(name, ORE_STATIC_NAME)


def tile_is_ore(tile):
    return is_ore(tile["graphic"], tile["is_land"], tile.get("name"))


def within_z(z):
    return abs(z - API.Player.Z) <= MINE_Z_RANGE


def blocked_until(tile):
    return blocked_tiles.get(tile_key(tile))


def is_blocked(tile):
    until = blocked_until(tile)

    return until is not None and time.time() < until


def block_tile(tile, until):
    blocked_tiles[tile_key(tile)] = until


def mark_depleted(tile):
    block_tile(tile, time.time() + RESPAWN_DELAY)


def mark_unreachable(tile):
    block_tile(tile, time.time() + UNREACHABLE_DELAY)


def mark_unusable(tile, why):
    block_tile(tile, float("inf"))
    log("the vein at %d,%d %s" % (tile["x"], tile["y"], why))


# For the shard answering about where you stand rather than about a tile. Parking a single tile left
# the character swinging at the spot the shard had just written off, for the same sentence.
def mark_area_depleted(reach):
    until = time.time() + RESPAWN_DELAY
    parked = 0

    for dx in range(-reach, reach + 1):
        for dy in range(-reach, reach + 1):
            for tile in terrain_at(API.Player.X + dx, API.Player.Y + dy):
                # The shard's sentence is about what it can reach, so parking a tile 60 z up would
                # record a claim it never made
                if not within_z(tile["z"]) or not tile_is_ore(tile):
                    continue

                block_tile(tile, until)
                parked += 1

    log(
        "nothing harvestable at %d,%d, parking %d tile(s) within %d for %dm"
        % (API.Player.X, API.Player.Y, parked, reach, max(1, int(round(RESPAWN_DELAY / 60.0))))
    )

    return parked


# About the art, not the tile: a wrong entry in ORE_TILE_GRAPHICS is a whole band of the mountain
def mark_not_mineable(tile):
    key = art_key(tile["graphic"], tile["is_land"])

    if key in not_ore_arts:
        return

    not_ore_arts.add(key)
    log("%s cannot be mined, skipping that art from here on" % hex_of(tile["graphic"]))


def chebyshev(tile):
    return max(abs(tile["x"] - API.Player.X), abs(tile["y"] - API.Player.Y))


def steps_to(tile):
    path = API.GetPath(tile["x"], tile["y"], tile["z"], MINE_RANGE)

    return len(path) if path else None


skipped_unreachable = 0


def scan_box(radius):
    global skipped_unreachable

    candidates = []
    cooling = None

    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            for tile in terrain_at(API.Player.X + dx, API.Player.Y + dy):
                if not tile_is_ore(tile) or not within_z(tile["z"]):
                    continue

                until = blocked_until(tile)

                if until is not None and time.time() < until:
                    if until != float("inf") and (cooling is None or until < cooling):
                        cooling = until

                    continue

                candidates.append(tile)

    candidates.sort(key=chebyshev)

    best = None
    best_steps = None
    walled = 0

    for tile in candidates[:MAX_PATH_PROBES]:
        steps = steps_to(tile)

        if steps is None:
            walled += 1
            continue

        if best_steps is None or steps < best_steps:
            best = tile
            best_steps = steps

    skipped_unreachable = walled

    if best is not None:
        best = dict(best)
        best["distance"] = chebyshev(best)

    return best, cooling


current_vein = None


# One pair of reads against the (2 * SCAN_RADIUS + 1) squared the box costs. The z and the art have
# to match as well as the coordinates: a tile carries several, and only one of them is the vein.
def still_ore(vein):
    if is_blocked(vein):
        return None

    # The character has walked since this was picked, and the vein is now up a cliff
    if not within_z(vein["z"]):
        return None

    for tile in terrain_at(vein["x"], vein["y"]):
        if (
            tile["z"] == vein["z"]
            and tile["graphic"] == vein["graphic"]
            and tile["is_land"] == vein["is_land"]
        ):
            if not tile_is_ore(tile):
                return None

            found = dict(vein)
            found["distance"] = chebyshev(vein)

            return found

    return None


# Widened rather than swept: a mountain face is wall-to-wall ore, so the tile that replaces a worked
# out one is almost always within reach
def scan_for_vein():
    global current_vein

    if current_vein is not None:
        current_vein = still_ore(current_vein)

        if current_vein is not None:
            return current_vein, None

    near, _cooling = scan_box(MINE_RANGE)

    if near is not None:
        current_vein = near

        return near, None

    found, cooling = scan_box(SCAN_RADIUS)
    current_vein = found

    return found, cooling


def survey_terrain(radius, limit):
    seen = {}

    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            for tile in terrain_at(API.Player.X + dx, API.Player.Y + dy):
                key = art_key(tile["graphic"], tile["is_land"])
                entry = seen.get(key)

                if entry is None:
                    seen[key] = [1, tile]
                else:
                    entry[0] += 1

    ranked = sorted(seen.values(), key=lambda entry: entry[0], reverse=True)

    log("the arts within %d, commonest first:" % radius)

    for count, tile in ranked[:limit]:
        marks = []

        if tile_is_ore(tile):
            marks.append("MATCHES")

        if not tile["is_land"]:
            marks.append("'%s'" % (tile["name"] or "?"))

        # Decimal as well as hex: the RunUO tables ORE_TILE_GRAPHICS is seeded from are decimal
        log(
            "  %s %s (%d) x%d z%d %s"
            % (
                "land" if tile["is_land"] else "static",
                hex_of(tile["graphic"]),
                tile["graphic"],
                count,
                tile["z"],
                " ".join(marks),
            )
        )


walking_to = None
walking_cycles = 0


def idle_until(ready_at):
    log("everything in reach is worked out, waiting for a vein to come back")
    said_at = time.time()

    while time.time() < ready_at:
        if stop_reason() is not None:
            return

        watch_for_trouble()

        if time.time() - said_at >= IDLE_LOG_EVERY:
            said_at = time.time()
            log("%dm to go" % max(1, int(round((ready_at - time.time()) / 60.0))))

        API.Pause(IDLE_POLL)

    heartbeat.reset()


# One of ('target', vein), ('walked',), ('waited',), ('stop', reason)
def approach():
    global walking_to, walking_cycles

    vein, respawns_at = scan_for_vein()

    if vein is None:
        if respawns_at is not None:
            idle_until(respawns_at)

            return ("waited",)

        # Ore that matched everything and had no way to walk to it is the one cause the survey
        # below cannot show
        if skipped_unreachable > 0:
            log("%d vein(s) matched but had no walkable route" % skipped_unreachable)

        log("nothing within %dz of %d matched, here is what is around" % (MINE_Z_RANGE, API.Player.Z))
        survey_terrain(SCAN_RADIUS, SURVEY_ARTS)

        return ("stop", "no ore in range")

    if vein["distance"] <= MINE_RANGE:
        walking_to = None
        walking_cycles = 0

        return ("target", vein)

    key = "%d,%d" % (vein["x"], vein["y"])

    if walking_to != key:
        walking_to = key
        walking_cycles = 0

    walking_cycles += 1

    if walking_cycles > MAX_VEIN_WALKS:
        mark_unreachable(vein)
        walking_to = None
        walking_cycles = 0

        return ("walked",)

    before = vein["distance"]
    API.Pathfind(vein["x"], vein["y"], vein["z"], MINE_RANGE, True, PATHFIND_TIMEOUT)
    API.CancelPathfinding()

    # A step that does not move during a save is not a wall
    if chebyshev(vein) >= before and not is_saving():
        mark_unreachable(vein)
        walking_to = None
        walking_cycles = 0

    return ("walked",)


remember_pickaxe(held_tool())

log("%d ore in the pack to start, at %d,%d" % (ore_total(), API.Player.X, API.Player.Y))

# Read before the dismount below, or the mounted half of it always answers no. A run that stops on
# its first cycle otherwise looks exactly like a script that never started.
held = held_tool()
log(
    "mounted %s, hand %s, weight %d/%d"
    % (
        "yes" if API.Player.IsMounted else "no",
        (held.Name or hex_of(held.Graphic)) if held is not None else "empty",
        API.Player.Weight,
        API.Player.WeightMax,
    )
)

# Before the cursor, so the beetle you click is one standing next to you rather than the one you are
# sitting on
afoot = dismount()

if PICK_BEETLE:
    pick_beetle()

# A pack that arrives full has no room for the first swing's ore. Smelting only once off the mount:
# a smelt aimed at the beetle you ride is silent, and three silent passes write the hue off.
group_ores()

if afoot and too_heavy():
    smelt_all()

stop = None
tally = 0
unknown = 0
throttled = 0
no_cursor = 0
no_tool = 0
idled = 0
reported = 0
barren = 0
cycle = 0
ore_before = 0


def end_cycle(phase):
    global stop

    stall.end_cycle(phase, cycle, tally)

    if stop is None:
        stop = stall.reason()


try:
    while stop is None and cycle - idled < MAX_CYCLES:
        cycle += 1

        stop = stop_reason()

        if stop is not None:
            break

        # Everything below reads a frozen shard as its own failure: a step that does not move is a
        # wall, a smelt that converts nothing is ore that cannot be worked
        if is_saving():
            wait_out_save()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        watch_for_trouble()

        # Asked every cycle, so a remount costs a single cycle instead of the rest of the run
        if not dismount():
            stop = "could not get off the mount"
            break

        if not equip_pickaxe():
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = "no pickaxe"
                break

            log("no pickaxe (%d/%d), looking again" % (no_tool, MAX_NO_TOOL))
            end_cycle("no tool")
            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
            continue

        no_tool = 0

        relieved = smelt_for_room()

        if relieved is not None:
            if isinstance(relieved, dict):
                stop = relieved["stop"]
                break

            end_cycle(relieved)
            API.Pause(STEP_DELAY)
            continue

        found = approach()

        if found[0] == "stop":
            stop = found[1]
            break

        # No pause: a resource coming back has already waited out its own clock, and a wait is the
        # script working rather than stalling
        if found[0] == "waited":
            idled += 1
            stall.progressed()
            continue

        if found[0] == "walked":
            end_cycle("walking")
            continue

        vein = found[1]

        ore_before = ore_total()
        outcome = dig_once(pickaxe_serial())

        if outcome == "dug":
            tally += 1
            unknown = 0
            throttled = 0
            barren = 0
            stall.progressed()

            # Ore arrives as a new pile after the sentence that announced it, so grouping every
            # swing keeps the pack at one pile per metal and the item cap out of reach
            wait_for_ore(ore_before)
            group_ores()

        elif outcome == "wornOut":
            log("pickaxe worn out, swapping")
            unknown = 0

        elif outcome == "saving":
            wait_out_save()
            unknown = 0
            throttled = 0
            stall.progressed()

        elif outcome == "throttled":
            throttled += 1

            # A refusal is a read outcome, so it clears the unreadable count: left standing, a shard
            # alternating refusals with silence ends the run on MAX_UNKNOWN
            unknown = 0
            log("shard says wait (%d/%d), backing off" % (throttled, MAX_THROTTLED))
            API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

            if throttled >= MAX_THROTTLED:
                stop = "the shard kept refusing the swing"

        elif outcome == "noCursor":
            no_cursor += 1
            log("no target cursor (%d/%d), backing off" % (no_cursor, MAX_NO_CURSOR))
            API.Pause(backoff_for(no_cursor, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

            if no_cursor >= MAX_NO_CURSOR:
                stop = "the shard never opened a target cursor"

        # Worked out, not dead: mark_depleted times it out and the scan picks it up again
        elif outcome == "empty":
            unknown = 0
            mark_depleted(vein)
            group_and_smelt()

        # The shard answering about where you stand rather than about a tile
        elif outcome == "nothingNearby":
            unknown = 0
            mark_area_depleted(MINE_RANGE)
            barren += 1

            # Said once, at the point it stops looking like bad luck
            if barren == NOTHING_NEARBY_HINT:
                log(
                    "%d spots in a row had nothing to harvest - ORE_TILE_GRAPHICS is probably "
                    "matching ground that carries no ore" % NOTHING_NEARBY_HINT
                )
                survey_terrain(MINE_RANGE, SURVEY_ARTS)

            group_and_smelt()

        # A wrong band in ORE_TILE_GRAPHICS is a whole stretch of mountain, so ban the art rather
        # than walking to its copies one at a time
        elif outcome == "notOre":
            unknown = 0
            mark_not_mineable(vein)
            mark_unusable(vein, "cannot be mined")

        elif outcome == "tooFar":
            unknown = 0
            mark_unusable(vein, "is out of reach at %d tiles" % vein["distance"])

        elif outcome == "notSeen":
            unknown = 0
            mark_unusable(vein, "is not in line of sight")

        # The ore this swing produced was destroyed rather than dropped, so a full pack is answered
        # by consolidating: forty piles of one become one pile of forty
        elif outcome == "packFull":
            unknown = 0
            log("pack is full, consolidating before the next swing")
            group_ores()

        else:
            unknown += 1
            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        # Done here rather than inside each branch the way unknown is: every branch but one clears
        # it, and one added later would have to remember to
        if outcome != "noCursor":
            no_cursor = 0

        if unknown >= MAX_UNKNOWN:
            stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
            break

        if tally >= reported + LOG_EVERY:
            reported = tally
            log(
                "%d swings, %d ore, %d/%d"
                % (tally, ore_total(), API.Player.Weight, API.Player.WeightMax)
            )

        end_cycle(outcome if outcome is not None else "unknown")
        API.Pause(STEP_DELAY)
except Exception as error:
    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error

if API.Pathfinding():
    API.CancelPathfinding()

reason = stop or "hit the %d working cycle backstop" % MAX_CYCLES

# Smelted only if the run is ending over the limit: what is in the pack is a few swings' worth
group_ores()

if too_heavy():
    smelt_all()

# Swings rather than an ore delta: smelted ore has left the pack, so the pack cannot total the run
log("%d swings, %d ore still in the pack" % (tally, ore_total()))
log("stopping - %s" % reason)
API.Stop()
