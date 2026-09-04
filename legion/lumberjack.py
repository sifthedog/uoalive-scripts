import time

import API

# Whole words and a list, never a substring: "axe" is inside "pickaxe", so a substring match picks
# the mining tool out of the pack the moment the real axe breaks - and a pickaxe is a working tool,
# so it equips, swings, and digs. Every RunUO lumberjacking tool carries the word 'axe' except the
# hatchet. The exclusion is what the veto below rests on, so add to it rather than trimming the list.
AXE_NAMES = ["axe", "axes", "hatchet", "hatchets"]
NOT_AXE_NAMES = ["pickaxe", "pickaxes", "shovel", "shovels"]

# Worth setting only if the spares are somewhere ItemsInContainer's recursive read does not reach
SPARE_BAG_SERIAL = None

# The client flags trees itself, so there is no table of arts to keep. Both sets ship empty and are
# the override for a shard the flag and the name both get wrong - a dead-end run prints what it saw.
TREE_GRAPHICS = set()
NOT_TREE_GRAPHICS = set()

# The fallback behind ApiStatic.IsTree, for a build that leaves the flag unset
TREE_NAME = ["tree"]

CHOP_RANGE = 2

# A tree 40 z up passes the 2D distance test and the walk at it never closes
CHOP_Z_RANGE = 20

SCAN_RADIUS = 12

# Swept only on the cycle the SCAN_RADIUS box comes back dry, which is the one that would stand still
ROAM_RADIUS = 24

SURVEY_ARTS = 15

# Whole seconds: the API takes an int here where API.Pause takes a float
PATHFIND_TIMEOUT = 10

# Cycles spent walking to one tree before it is written off
MAX_TREE_WALKS = 4

# How many of the nearest matches a sweep pays an API.GetPath for
MAX_PATH_PROBES = 24

# A stump grows back, so a tile that ran out of wood is a cooldown and never a write-off
REGROW_DELAY = 25 * 60.0
UNREACHABLE_DELAY = 5 * 60.0

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms
# How the target cursor is answered. True answers with yourself and lets the shard pick whatever is
# in reach, which is how mining.py and mine-here.py swing and what this shard is known to accept.
# False names the scanned tree's tile and its art instead, the way the ClassicUO script does - keep
# that for a shard where a self-target harvests nothing, and read the two notes at the branches in
# the loop, because which one is used changes what an 'empty' and a 'notTree' are evidence about.
AIM_AT_SELF = True

# A swing plays its animation before the result arrives, so this has to outlast the animation
CHOP_TIMEOUT = 8.0

CHOP_TARGET_TIMEOUT = 4.0
CHOP_TARGET_POLL = 0.1

# Waited on as the cursor itself, because HasTarget cannot be relied on - get this wrong and every
# swing reports no target cursor
CHOP_PROMPT_TEXT = [
    "What do you want to use this on",
    "Select a tree",
    "Where do you wish to chop",
]

# A short window for a refusal worded a moment late; the journal was cleared just before the swing
NO_CURSOR_READ = 0.5

# A stack's graphic changes with its size, so match a set rather than one graphic. Hue is
# deliberately not part of the match: a shard with special woods hues its logs, and those still
# count, still convert and still need hauling.
LOG_GRAPHICS = set([0x1BDD, 0x1BE0, 0x1BDE, 0x1BDF])

# Whole words, or 'log' inside 'logic' would put something in the converter. Both numbers, because
# words_of("Oak Logs") answers 'logs' and nothing would ever match the singular.
LOG_NAME_WORDS = ["log", "logs"]

# A seed only: the real board graphic is learned by diffing the pack across the first conversion
BOARD_GRAPHICS = set([0x1BD7, 0x1BD9, 0x1BDA, 0x1BDB])

# So a haul still works on a run where no conversion has landed yet to name the art
BOARD_NAME_WORDS = ["board", "boards"]

# Pauses after each conversion and each move, to stay under the server's action throttle
CONVERT_DELAY = 0.7
MOVE_DELAY = 0.7

# Polled rather than slept through: the throttle can delay a conversion well past a fixed pause, and
# reading too early looks like a failure
CONVERT_TIMEOUT = 4.0
CONVERT_POLL = 0.2

# More than one, because a throttled or stale attempt also looks silent, and giving up on hue 0
# means hauling ordinary logs
CONVERT_ATTEMPTS = 3

# One pass converts one stack, so this caps a haul
MAX_CONVERT_PASSES = 60

# Empty spots in a row before it says the tree test is probably matching scenery
EMPTY_HINT = 5

# Pack horse, pack llama, giant beetle. Unverified on this shard; the search logs the body it finds.
PACK_ANIMAL_GRAPHICS = set([0x123, 0x124, 0x317])

# Optional: pin the animals instead of discovering them. Order does not matter - the haul walks to
# whichever is nearest first either way.
PACK_ANIMAL_SERIALS = []

# A cursor at startup to click the animals, ESC to fall back to PACK_ANIMAL_SERIALS or the search
PICK_PACK_ANIMALS = True

# A backstop only - the selection ends when you press ESC
MAX_PICKS = 8

# It waits on a person, not the shard
PICK_TIMEOUT = 60.0

ANIMAL_SCAN_RADIUS = 18

UNLOAD_RANGE = 2

# Deliberately wider than WEIGHT_BUFFER, so hauling always gets its turn before the overweight stop
HAUL_BUFFER = 120

# Hauls in a row that freed no weight before the animals are taken to be full. Without it a run
# whose animals fill up spends every remaining cycle walking to them and never swings again, and
# ends on the stall watch saying 'no progress' when the real answer is 'they are full'.
MAX_EMPTY_HAULS = 3

# Buffer, so the stop lands before the shard starts refusing to move the new logs
WEIGHT_BUFFER = 40

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

# The container's item cap, counted top level only because the cap is per container
PACK_LIMIT = 120

SAVE_WAIT = 60.0
SAVE_POLL = 1.0
SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"]
SAVING_TEXT = ["The world is saving", "Saving world", "World save started"]

# Full wordings first: the bare prefix also catches sentences from systems that have nothing to do
# with harvesting. Kept last as a fallback all the same - a phrase this list misses reads as an
# unreadable outcome, which is worse.
THROTTLED_TEXT = [
    "You must wait to perform another action",
    "You must wait a moment",
    "You must wait",
]

UNSKILLED_TEXT = [
    "You are not skilled enough",
    "You lack the required skill",
    "You do not have enough skill",
]

WATCH_FOR_TROUBLE = True

# Innocent is out, or every blue NPC in the world is trouble
HOSTILE_NOTORIETY = [
    API.Notoriety.Gray,
    API.Notoriety.Criminal,
    API.Notoriety.Enemy,
    API.Notoriety.Murderer,
]

# Gray is out: the wildlife is gray, and a cat wandering past is not evidence of anything. A gray
# still draws the call the moment it damages you or the animal.
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
    "The guards cannot be called here",
    "The guards can not be called here",
    "There are no guards here",
    "guards cannot be summoned here",
    "You are not in a guarded area",
]

ATTACK_TEXT = []

GUARD_ZONE_TEXT = ["under the protection of the town guards", "now under guard"]
UNGUARDED_TEXT = ["left the protection of the town guards", "no longer under guard"]

# Ordered, not a dict: InJournalAny answers yes/no, so the buckets are polled in order and the first
# holding a match wins. Guesses for a RunUO-family shard - correct them against the real journal.
OUTCOME_TEXT = [
    ("chopped", ["You put", "You hack at the tree", "You chop some"]),
    # About the trunk: how much ground it speaks for depends on how the swing was aimed
    (
        "empty",
        [
            "There's not enough wood here to harvest",
            "There is not enough wood here to harvest",
            "There is no wood here to harvest",
            "There are no logs left",
        ],
    ),
    # About everything in reach, which is what a self-target asks: this one always parks the ground,
    # whichever way the swing was aimed. Confirmed on UOAlive - the run that found it read every one
    # of these as an unreadable outcome, because this bucket was folded into 'empty' and the wording
    # was lost on the way.
    (
        "nothingNearby",
        [
            "There are no harvestable resources nearby",
            "There is nothing here to harvest",
            "There are no resources here",
        ],
    ),
    # "You can't use an axe on that" is UOAlive's wording, seen on a live web-client run against an
    # 'o'hii tree' static (0xc9e) - the client calls it a tree, the shard will not harvest it
    (
        "notTree",
        [
            "You can't use an axe on that",
            "You can't chop that",
            "You can't use a bladed item on that",
            "You cannot chop",
        ],
    ),
    ("tooFar", ["That is too far away", "You cannot reach that"]),
    # Line of sight, not range: the tile is inside CHOP_RANGE and no amount of walking closer or
    # waiting fixes it
    ("notSeen", ["Target cannot be seen"]),
    # Answered by hauling rather than by consolidating: one log stack converts to one board stack,
    # so merging gives back almost nothing. What frees slots is boards leaving for the animal.
    ("packFull", ["Your backpack is full", "That container cannot hold more"]),
    ("wornOut", ["You have worn out your tool"]),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]


def log(message):
    API.SysMsg("lumberjack: " + message)


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
            "still here - %s, cycle %d, at %d,%d, %d/%d, %d chops"
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
stall = StallWatch("cycles without a chop", STALL_WARN, STALL_STOP, heartbeat)


def said(texts):
    for text in texts:
        if API.InJournal(text, False):
            return True

    return False


def pack_contents():
    items = API.ItemsInContainer(API.Backpack, True)

    return items if items else []


# The item cap is per container, so the guard counts the top level only
def pack_top_level():
    items = API.ItemsInContainer(API.Backpack, False)

    return items if items else []


# WeightMax reads 0 before the client has been told, against which every weight is overweight - a
# live mining run ended at 436/453 on exactly that
def over_buffer(buffer):
    ceiling = API.Player.WeightMax

    return ceiling > 0 and API.Player.Weight > ceiling - buffer


def too_heavy():
    return over_buffer(0)


# mining.py has no weight guard at all, on the grounds that one would fire before the smelt could
# run. It cannot here: HAUL_BUFFER is three times WEIGHT_BUFFER, so the haul gets its turn some
# forty logs before this does, and the prologue hauls once before the first cycle.
def stop_reason():
    if API.StopRequested:
        return "stopped from the script manager"

    if API.Player.IsDead:
        return "you are dead"

    if over_buffer(WEIGHT_BUFFER):
        return "overweight at %d/%d" % (API.Player.Weight, API.Player.WeightMax)

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


axe_graphic = None
reported_empty_pack = False


def is_axe(item):
    if item is None:
        return False

    name = item.Name or ""

    # The veto is asked before the graphic, not after it. The name test below can no longer match a
    # pickaxe, but one already learned as the axe graphic - off a shard that names nothing, or off a
    # hand that held it at startup - would go on matching every cycle without this.
    if word_in(name, NOT_AXE_NAMES):
        return False

    if axe_graphic is not None and item.Graphic == axe_graphic:
        return True

    return word_in(name, AXE_NAMES)


# Axes are two-handed and hatchets one-handed, so the two-hand layer is read first - the same order
# axe.ts reads equippedItems.twoHanded ?? equippedItems.oneHanded in
def held_tool():
    return API.FindLayer("twohanded") or API.FindLayer("onehanded")


def remember_axe(item):
    global axe_graphic

    if item is None or axe_graphic is not None:
        return

    name = item.Name or ""

    # Refused only on positive evidence. A name reads empty until the client has tooltip data, and
    # an axe in hand is the documented precondition, so an unnamed tool is taken at its word - but a
    # pickaxe learned here would be the axe for the whole run, and every swing would dig.
    if word_in(name, NOT_AXE_NAMES):
        log("you are holding a '%s', which is not an axe - not learning its graphic" % name)

        return

    axe_graphic = item.Graphic
    log("axe graphic is %s ('%s')" % (hex_of(item.Graphic), name or "unnamed"))


def axe_serial():
    item = held_tool()

    return item.Serial if item is not None else None


def find_axe():
    global reported_empty_pack

    for item in pack_contents():
        if is_axe(item):
            reported_empty_pack = False
            remember_axe(item)

            return item

    if SPARE_BAG_SERIAL is not None:
        for item in API.ItemsInContainer(SPARE_BAG_SERIAL, True) or []:
            if is_axe(item):
                reported_empty_pack = False
                remember_axe(item)

                return item

    if not reported_empty_pack:
        reported_empty_pack = True
        arts = []

        for item in pack_contents():
            arts.append(hex_of(item.Graphic))

        log(
            "no axe found - nothing named %s in the pack. It holds: %s"
            % ("/".join(AXE_NAMES), ", ".join(arts) or "nothing")
        )

    return None


# A broken tool can linger on the layer, and is_axe would match it by graphic, so the world is asked
# rather than the layer
def still_holding():
    item = held_tool()

    return item is not None and is_axe(item) and API.FindItem(item.Serial) is not None


def equip_axe():
    if still_holding():
        return True

    found = find_axe()

    if found is None:
        return False

    # A cursor left open by the swing that broke the tool would swallow the equip
    if API.HasTarget():
        API.CancelTarget()

    serial = found.Serial

    for _attempt in range(EQUIP_ATTEMPTS):
        API.EquipItem(serial)

        if settled(EQUIP_TIMEOUT, EQUIP_POLL, lambda: axe_serial() == serial):
            return True

    log("could not get the axe %s onto the hand" % hex_of(serial))

    return False


def amount_of(item):
    return item.Amount if item.Amount is not None else 1


def hue_of(item):
    return item.Hue or 0


# Graphic first, name second: names are empty until the client has tooltip data. An art learned by
# name joins the set, so it costs one name read and no more.
def is_log_pile(item):
    if item is None:
        return False

    if item.Graphic in LOG_GRAPHICS:
        return True

    if not word_in(item.Name, LOG_NAME_WORDS):
        return False

    LOG_GRAPHICS.add(item.Graphic)
    log("%s '%s' is a log too, remembering the art" % (hex_of(item.Graphic), item.Name))

    return True


def is_board(item):
    if item is None:
        return False

    if item.Graphic in BOARD_GRAPHICS:
        return True

    if not word_in(item.Name, BOARD_NAME_WORDS):
        return False

    BOARD_GRAPHICS.add(item.Graphic)
    log("%s '%s' is a board too, remembering the art" % (hex_of(item.Graphic), item.Name))

    return True


# Top level only, unlike log_total: the conversion acts by serial on loose items. Largest first, so
# the biggest stack is the one turned into boards first.
def log_piles():
    piles = []

    for item in pack_top_level():
        if is_log_pile(item):
            piles.append(item)

    piles.sort(key=amount_of, reverse=True)

    return piles


def board_piles():
    piles = []

    for item in pack_top_level():
        if is_board(item):
            piles.append(item)

    return piles


# Hue-blind on purpose: a shard with special woods hues its logs, and those still count, still
# convert and still need hauling
def log_total():
    total = 0

    for item in pack_contents():
        if is_log_pile(item):
            total += amount_of(item)

    return total


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
convert_misses = {}
reported_nothing = False

# Whether anything has converted since the last retry. Without it a retry granted unconditionally
# answers true again next cycle and the caller loops until the stall watchdog ends the run.
convert_progressed = True


# Every failing path comes through here: one that returns without counting leaves the candidate set
# unchanged, so the next pass picks the same stack and the loop runs to its backstop
def convert_missed(hue):
    count = convert_misses.get(hue, 0) + 1
    convert_misses[hue] = count

    if count >= CONVERT_ATTEMPTS:
        written_off.add(hue)
        log("hue %d failed %d times, leaving it as logs" % (hue, count))


# The diff names the real board art, which is why BOARD_GRAPHICS is only a seed and a wrong guess
# corrects itself on the first conversion
def learn_board(changes):
    for key, delta in changes:
        if delta <= 0:
            continue

        graphic = int(key.split("/")[0])

        if graphic in LOG_GRAPHICS or graphic in BOARD_GRAPHICS:
            continue

        BOARD_GRAPHICS.add(graphic)
        log("board graphic is %s" % hex_of(graphic))


# The action throttle can hold a conversion well past any pause worth taking, and reading too early
# is indistinguishable from a wood that cannot be worked
def wait_for_change(before):
    waited = 0.0

    while waited < CONVERT_TIMEOUT:
        API.Pause(CONVERT_POLL)
        waited += CONVERT_POLL

        changes = diff_counts(before, counts_by_graphic())

        if changes:
            return changes

    return []


# The journal is cleared to perform the conversion, so a save that starts mid-attempt is past the
# check at the top of the pass
def convert_saving(hue):
    if not is_saving():
        return False

    log("the world is saving, not counting it against hue %d" % hue)
    wait_out_save()

    return True


# Logs become boards by using the axe and targeting the log stack - the inverse of smelting, where
# the ore is used and the forge targeted
def perform_convert(stack):
    serial = axe_serial()

    if serial is None:
        return False

    # No cancel unless there is one to cancel: an unconditional cancel shortly before the action
    # leaves the cursor that follows unusable
    if API.HasTarget():
        API.CancelTarget()

    API.ClearJournal()
    API.UseObject(serial)

    if not API.WaitForTarget("any", TARGET_TIMEOUT):
        API.CancelTarget()
        log("no target cursor for the logs, nothing usable in hand?")

        return False

    # The one-argument overload: an item serial, not the tile form the chop uses
    API.Target(stack.Serial)

    return True


def next_log(skip):
    for pile in log_piles():
        if hue_of(pile) not in skip:
            return pile

    return None


def convert_one(stack):
    global convert_progressed

    hue = hue_of(stack)
    before = counts_by_graphic()

    if not perform_convert(stack):
        if convert_saving(hue):
            return

        # Counted like any other failure: without this an empty hand spends every pass waiting on a
        # cursor that is never going to come
        convert_missed(hue)

        return

    changes = wait_for_change(before)

    if changes:
        convert_misses.pop(hue, None)
        convert_progressed = True
        learn_board(changes)

        return

    # Asked before either wording, because a frozen shard's verdict on the material is worthless
    if convert_saving(hue):
        return

    # Nothing was attempted, so this is not a verdict on the wood
    if said(THROTTLED_TEXT):
        log("the shard says wait, not counting it against hue %d" % hue)

        return

    if said(UNSKILLED_TEXT):
        written_off.add(hue)
        log("not skilled enough for hue %d, leaving it as logs" % hue)

        return

    # Otherwise it was silent, which is also what a throttled or stale attempt looks like
    convert_missed(hue)


def no_axe_in_hand():
    return axe_serial() is None


def run_converter():
    global reported_nothing

    for _pass in range(MAX_CONVERT_PASSES):
        # A frozen shard answers a conversion the same way an unworkable wood does, so without this
        # a world save costs CONVERT_ATTEMPTS and writes the hue off for the rest of the run
        if is_saving():
            log("the world is saving, leaving the logs for now")

            return False

        stack = next_log(written_off)

        if stack is None:
            piles = log_piles()

            # Said once per stretch, not once a cycle: haul_for_room fires at HAUL_BUFFER and stays
            # true for a long run of them
            if len(piles) > 0 and not reported_nothing:
                reported_nothing = True
                log("nothing to convert in %d log pile(s)" % len(piles))

            return True

        if no_axe_in_hand():
            log("no axe in hand, leaving the logs for now")

            return False

        reported_nothing = False
        convert_one(stack)
        API.Pause(CONVERT_DELAY)

    log("hit the %d conversion pass backstop" % MAX_CONVERT_PASSES)

    return False


def retry_unconverted(force=False):
    global convert_progressed

    if len(written_off) == 0 or (not convert_progressed and not force):
        return False

    convert_progressed = False
    log("giving %d hue(s) written off earlier another go" % len(written_off))
    written_off.clear()
    convert_misses.clear()

    return True


# Forced, unlike mining's progress-gated retry: only boards ever go onto an animal, so a log given
# up on to a lost cursor or a broken axe would ride out the whole run as weight. The verdict is a
# backstop for one pass, never for the run.
def make_boards():
    retry_unconverted(True)

    return run_converter()


# A list chosen rather than guessed - from config or from the cursor - is the law, so an animal out
# of sight for a moment is not a reason to go loading a stranger's mule
pinned_serials = list(PACK_ANIMAL_SERIALS)
reported_animals = False
reported_no_animal = False

# Kept from the last search so the trouble watch can re-resolve one mobile rather than paying a
# GetAllMobiles per body every cycle
last_animal_serial = None

# Never cleared: what empties a pack horse is a trip to the bank, and that ends the run
overloaded = set()
said_all_full = False

hauling = True


def pick_pack_animals():
    global pinned_serials

    if API.Player.IsMounted:
        log("you are mounted - dismount first if the animal you want is the one you are riding")

    log("target the pack animals to load, ESC when done")

    picked = []

    for _pick in range(MAX_PICKS):
        if API.HasTarget():
            API.CancelTarget()

        serial = API.RequestTarget(PICK_TIMEOUT)

        # Falsy is ESC or a cursor that timed out, and either one ends the selection
        if not serial:
            break

        animal = API.FindMobile(serial)

        # Not an ending: a misclick on the ground should cost the click and nothing more
        if animal is None:
            log("%s is not a mobile" % hex_of(serial))
            continue

        if serial in picked:
            continue

        # Not a refusal either: PACK_ANIMAL_GRAPHICS is a guess at this shard, so a body it has
        # never heard of is worth reporting and then using
        if animal.Graphic not in PACK_ANIMAL_GRAPHICS:
            log("%s is not a body PACK_ANIMAL_GRAPHICS knows, using it anyway" % hex_of(animal.Graphic))

        picked.append(serial)
        log("picked '%s' %s" % (animal.Name or "?", hex_of(serial)))

    if API.HasTarget():
        API.CancelTarget()

    if len(picked) == 0:
        log("nothing picked, looking for the animals instead")

        return []

    pinned_serials = picked

    return picked


def find_pack_animals():
    global reported_animals, last_animal_serial

    found = []

    if len(pinned_serials) > 0:
        # A pinned serial can be hand-written, so check what came back rather than trusting it
        for serial in pinned_serials:
            animal = API.FindMobile(serial)

            if animal is not None and not animal.IsDead:
                found.append(animal)
    else:
        for graphic in PACK_ANIMAL_GRAPHICS:
            for animal in API.GetAllMobiles(graphic, ANIMAL_SCAN_RADIUS) or []:
                if not animal.IsDead:
                    found.append(animal)

        # Only your own pets can be renamed, so this is what tells yours from a stranger's
        mine = [animal for animal in found if animal.IsRenamable]

        if len(mine) > 0:
            found = mine

    if len(found) == 0:
        return []

    if not reported_animals:
        reported_animals = True
        names = ", ".join("'%s'" % (animal.Name or "?") for animal in found)
        log("%d pack animal(s) - %s" % (len(found), names))

    # Nearest first, so the closest one fills before you walk past it to another
    found.sort(key=lambda animal: animal.Distance)
    last_animal_serial = found[0].Serial

    return found


# A pet's coordinates go stale within a cycle, so the serial is re-resolved rather than the
# find_pack_animals result trusted
def walk_to_animal(serial):
    here = API.FindMobile(serial)

    if here is None:
        log("lost track of %s" % hex_of(serial))

        return None

    if here.Distance <= UNLOAD_RANGE:
        return here

    API.PathfindEntity(serial, UNLOAD_RANGE, True, PATHFIND_TIMEOUT)
    API.CancelPathfinding()

    here = API.FindMobile(serial)

    if here is None or here.Distance > UNLOAD_RANGE:
        return None

    return here


# Two independent reads, and no double-click fallback: the web client had only the layer, and its
# fallback is a UseObject on a rideable giant beetle, which mounts you. Nothing in this file
# dismounts, so a mount here would cost the rest of the run.
def animal_pack(animal):
    pack = getattr(animal, "Backpack", None)

    if pack is not None:
        return pack

    return API.FindLayer("backpack", animal.Serial)


# Moves are asynchronous, so rescan between passes rather than trusting MoveItem's return value.
# A pass that shifts nothing means this animal is full, which the caller reports.
def move_all(pack_serial):
    previous = None

    while True:
        stacks = board_piles()

        if len(stacks) == 0 or (previous is not None and len(stacks) >= previous):
            return

        previous = len(stacks)

        for stack in stacks:
            API.MoveItem(stack.Serial, pack_serial)
            API.Pause(MOVE_DELAY)


# Works down the animals until the pack is clear or every one of them has had a turn. An animal that
# stops accepting is full rather than broken, so what is left over goes to the next one and the one
# that took nothing at all is remembered rather than walked to again.
def unload_to(animals):
    for animal in animals:
        before = len(board_piles())

        if before == 0:
            break

        here = walk_to_animal(animal.Serial)

        if here is None:
            continue

        pack = animal_pack(here)

        if pack is None:
            log("'%s' has no reachable backpack" % (here.Name or "?"))
            continue

        move_all(pack.Serial)

        after = len(board_piles())
        moved = before - after
        name = here.Name or "?"

        if moved == 0:
            # A save refuses every move at once, and haul_now only asks afterwards - read as this
            # animal's verdict it would sit out the rest of the run over a five second pause
            if is_saving():
                log("'%s' took nothing while the world is saving, trying the next" % name)
            else:
                overloaded.add(animal.Serial)
                log("'%s' took nothing, leaving it out of the rest of the run" % name)
        elif after > 0:
            log("'%s' took %d of %d stack(s), trying the next" % (name, moved, before))


# Answers whether an animal was found, not whether anything moved: only a missing animal is worth
# giving up the search for, and one that took nothing has already been dropped from the list.
def unload():
    global reported_no_animal, said_all_full

    animals = find_pack_animals()

    if len(animals) == 0:
        if not reported_no_animal:
            reported_no_animal = True
            log("no pack animal nearby")

        return False

    reported_no_animal = False

    # Filtered here rather than in find_pack_animals, which also feeds the trouble watch its
    # companion - an animal that is full is still one worth watching
    spare = [animal for animal in animals if animal.Serial not in overloaded]

    if len(spare) == 0:
        if not said_all_full:
            said_all_full = True
            log("all %d pack animal(s) are full, nothing left to load" % len(animals))
    else:
        unload_to(spare)

    # A log that leaves as a log never comes back as a board, so what would not convert waits for
    # the next haul to try it again. Asked once every animal has had its turn at the boards.
    if over_buffer(HAUL_BUFFER):
        left = log_total()

        if left > 0:
            log("%d logs would not convert, keeping them in the pack" % left)

    return True


empty_hauls = 0


def haul_now():
    global hauling, empty_hauls

    before = API.Player.Weight

    make_boards()

    saw_animal = unload()

    # A save freezes every part of a haul at once - the conversion is silent, the animal takes
    # nothing, the weight does not move. Read as an ordinary result it latches hauling off for good.
    if is_saving():
        wait_out_save()

        return "hauling"

    if not saw_animal:
        hauling = False
        log("no pack animal found, carrying on until overweight")

        return "hauling"

    # Weight rather than stacks moved: what this is deciding is whether the haul relieved the pack,
    # and an animal that took a stack and refused the rest has not
    if not over_buffer(HAUL_BUFFER) or API.Player.Weight < before:
        empty_hauls = 0

        return "hauling"

    empty_hauls += 1

    if empty_hauls >= MAX_EMPTY_HAULS:
        hauling = False
        log(
            "%d hauls freed nothing - the animals are full. Carrying on until overweight"
            % empty_hauls
        )

    return "hauling"


def haul_for_room():
    if not over_buffer(HAUL_BUFFER):
        return None

    # Once hauling has latched off there is nothing to walk to, so the cycle goes on to chop rather
    # than spending itself on a phase - index.ts returns undefined here for the same reason. The
    # conversion still runs, because boards weigh less than the logs they came from and that is
    # worth having with no animal to put them on. Unforced, unlike the one inside a real haul: this
    # runs every cycle from here to the end of the run, and re-trying a wood that has already
    # refused three times would cost three cursors a cycle for the rest of it.
    if not hauling:
        run_converter()

        return None

    return haul_now()


def silent_outcome(serial, logs_before):
    if serial is not None and API.FindItem(serial) is None:
        return "wornOut"

    if log_total() > logs_before:
        return "chopped"

    return "unknown"


# HasTarget alone was not enough on the web client: a measured swing had the shard's prompt in the
# journal at 164ms and the cursor flag false for the whole six seconds after it
def cursor_opened():
    waited = 0.0

    while waited < CHOP_TARGET_TIMEOUT:
        if API.HasTarget() or said(CHOP_PROMPT_TEXT):
            return True

        API.Pause(CHOP_TARGET_POLL)
        waited += CHOP_TARGET_POLL

    return False


# No cursor is not the same as nothing having happened: the commonest reason a shard declines a
# swing is that it refused the action outright and said so
def refused_outcome(serial, logs_before):
    matched = read_outcome(OUTCOME_TEXT, NO_CURSOR_READ, CHOP_TARGET_POLL)

    if matched is not None:
        return matched

    silent = silent_outcome(serial, logs_before)

    if silent != "unknown":
        return silent

    held = held_tool()
    log(
        "no target cursor - hand %s, the shard never asked where to chop"
        % ((held.Name or hex_of(held.Graphic)) if held is not None else "empty")
    )

    return "noCursor"


def chop_once(serial, tree):
    # A pathfind still running would walk the character away mid-swing
    if API.Pathfinding():
        API.CancelPathfinding()

    # Cancelled only when there is one to cancel: an unconditional cancel a few hundred milliseconds
    # before the swing left the next cursor unusable in the run this was copied from
    if API.HasTarget():
        API.CancelTarget()

    logs_before = log_total()
    API.ClearJournal()

    API.UseObject(serial)

    if not cursor_opened():
        return refused_outcome(serial, logs_before)

    if AIM_AT_SELF:
        # This shard takes a self-target as 'harvest what is in reach' and picks the tree itself,
        # so nothing has to name a static. The scan still earns its place: it is what decides where
        # to stand, and 'in reach' is only ever the trunk you walked to.
        API.TargetSelf()
    else:
        # The four-argument overload, and the graphic is never left off: target.terrain with no art
        # hits the land tile, which the shard answers as mining rather than as chopping. A static
        # carries no serial, so naming the tile and its art is the only other way to aim at one.
        API.Target(tree["x"], tree["y"], tree["z"], tree["graphic"])

    matched = read_outcome(OUTCOME_TEXT, CHOP_TIMEOUT, CHOP_TARGET_POLL)

    return matched if matched is not None else silent_outcome(serial, logs_before)


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
        # IsRenamable is how the rest of this repo tells your own pet from a stranger's, and a pack
        # animal flagged gray by whatever it was fighting would otherwise read as the attacker
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
        theirs = ", '%s' %d/%s" % (friend.Name or "?", friend.Hits, friend.HitsMax or "?")

    return "%s, %s%s" % (who, mine, theirs)


# The nearest animal the last search found, re-resolved. mining.py calls find_beetle here; searching
# by body every cycle would cost a GetAllMobiles per graphic, and would keep searching for animals
# after the haul had latched itself off.
def companion():
    if last_animal_serial is None:
        return None

    return API.FindMobile(last_animal_serial)


def watch_for_trouble():
    global last_hits, last_companion_hits, in_episode, guard_calls

    if not WATCH_FOR_TROUBLE:
        return

    read_zone()

    hits = API.Player.Hits
    hurt = dropped(last_hits, hits)

    if hits > 0:
        last_hits = hits

    friend = companion()
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


# Trees are statics only, so unlike mining there is no land tiledata table to keep apart from the
# static one - the key is the coordinate and the art, and nothing else
blocked_tiles = {}
not_tree_arts = set()


def tile_key(tile):
    return "%d,%d,%d,%d" % (tile["x"], tile["y"], tile["z"], tile["graphic"])


# Overrides first, which is the opposite order to mining's is_ore and deliberate: that one asks the
# refusals first because ORE_TILE_GRAPHICS ships full and would outrank a ban learned on the shard.
# Both sets here ship empty, so TREE_GRAPHICS is an override and gets asked first, as tree.ts does.
def is_tree(graphic, name, flagged):
    if graphic in TREE_GRAPHICS:
        return True

    if graphic in NOT_TREE_GRAPHICS or graphic in not_tree_arts:
        return False

    if flagged:
        return True

    return any_in(name, TREE_NAME)


def static_is_tree(static):
    return is_tree(static.Graphic, static.Name or "", getattr(static, "IsTree", False))


def as_tile(static):
    return {
        "x": static.X,
        "y": static.Y,
        "z": static.Z,
        "graphic": static.Graphic,
        "name": static.Name or "",
    }


def within_z(z):
    return abs(z - API.Player.Z) <= CHOP_Z_RANGE


def blocked_until(tile):
    return blocked_tiles.get(tile_key(tile))


def is_blocked(tile):
    until = blocked_until(tile)

    return until is not None and time.time() < until


def block_tile(tile, until):
    blocked_tiles[tile_key(tile)] = until


# A stump, not a dead tile: this times out and the scan picks the trunk up again later. Written off
# permanently it would ban every tree the run ever chopped and stop in the middle of a forest.
def mark_depleted(tile):
    block_tile(tile, time.time() + REGROW_DELAY)


def mark_unreachable(tile):
    block_tile(tile, time.time() + UNREACHABLE_DELAY)


def mark_unusable(tile, why):
    block_tile(tile, float("inf"))
    log("the tree at %d,%d %s" % (tile["x"], tile["y"], why))


# About the art, not the tile: the client's own IsTree over-reaches - a live run matched 0xc9e,
# named 'o'hii tree', and the shard answered that an axe cannot be used on it. That answer is about
# the graphic, so one refusal drops every copy of the art out of the scan at once.
def mark_not_choppable(graphic):
    if graphic in not_tree_arts:
        return

    not_tree_arts.add(graphic)
    log("%s cannot be chopped, skipping that art from here on" % hex_of(graphic))


# For the shard answering about what it can reach rather than about a tile, which is what a
# self-target asks it. Parking only the trunk the scan picked left mining swinging at the neighbour
# the shard had just written off, for the same sentence.
def mark_area_depleted(reach):
    until = time.time() + REGROW_DELAY
    parked = 0

    for static in statics_in(reach):
        if not static_is_tree(static) or not within_z(static.Z):
            continue

        block_tile(as_tile(static), until)
        parked += 1

    log(
        "nothing to chop at %d,%d, parking %d tree(s) within %d for %dm"
        % (API.Player.X, API.Player.Y, parked, reach, max(1, int(round(REGROW_DELAY / 60.0))))
    )

    return parked


def chebyshev(tile):
    return max(abs(tile["x"] - API.Player.X), abs(tile["y"] - API.Player.Y))


def steps_to(tile):
    path = API.GetPath(tile["x"], tile["y"], tile["z"], CHOP_RANGE)

    return len(path) if path else None


# One call for the whole box, where mining pays a pair of reads per coordinate. There is no terrain
# cache behind it for the same reason: a sweep is one call, and a felled tree that changes art would
# go stale in one.
def statics_in(radius):
    x = API.Player.X
    y = API.Player.Y

    return API.GetStaticsInArea(x - radius, y - radius, x + radius, y + radius) or []


skipped_unreachable = 0


def scan_box(radius):
    global skipped_unreachable

    candidates = []
    cooling = None

    for static in statics_in(radius):
        if not static_is_tree(static) or not within_z(static.Z):
            continue

        tile = as_tile(static)
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
        # Already in reach, so there is nothing to route and no probe worth paying for
        if chebyshev(tile) <= CHOP_RANGE:
            steps = 0
        else:
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


current_tree = None


# The z and the art have to match as well as the coordinates: a tile carries several statics, and
# only one of them is the trunk that was picked
def still_tree(tree):
    if is_blocked(tree) or not within_z(tree["z"]):
        return None

    for static in API.GetStaticsAt(tree["x"], tree["y"]) or []:
        if static.Z == tree["z"] and static.Graphic == tree["graphic"]:
            if not static_is_tree(static):
                return None

            found = dict(tree)
            found["distance"] = chebyshev(tree)

            return found

    return None


# Widened rather than swept twice: ROAM_RADIUS is 49 tiles a side, and walking that many statics
# through interop is only worth paying for on the cycle that would otherwise stand still
def scan_for_tree():
    global current_tree

    if current_tree is not None:
        current_tree = still_tree(current_tree)

        if current_tree is not None:
            return current_tree, None

    near, near_cooling = scan_box(SCAN_RADIUS)

    if near is not None:
        current_tree = near

        return near, None

    found, cooling = scan_box(ROAM_RADIUS)
    current_tree = found

    return found, cooling if cooling is not None else near_cooling


def survey_statics(radius, limit):
    seen = {}

    for static in statics_in(radius):
        entry = seen.get(static.Graphic)

        if entry is None:
            seen[static.Graphic] = [1, static]
        else:
            entry[0] += 1

    ranked = sorted(seen.values(), key=lambda entry: entry[0], reverse=True)

    log("the statics within %d, commonest first:" % radius)

    for count, static in ranked[:limit]:
        marks = []

        if static_is_tree(static):
            marks.append("MATCHES")

        if getattr(static, "IsTree", False):
            marks.append("IsTree")

        if getattr(static, "IsVegetation", False):
            marks.append("IsVegetation")

        # Decimal as well as hex, because that is the form TREE_GRAPHICS wants
        log(
            "  %s (%d) x%d z%d '%s' %s"
            % (
                hex_of(static.Graphic),
                static.Graphic,
                count,
                static.Z,
                static.Name or "?",
                " ".join(marks),
            )
        )


walking_to = None
walking_cycles = 0


def idle_until(ready_at):
    log("everything in reach is regrowing, waiting for the soonest one")
    said_at = time.time()

    # Sliced rather than slept through: one blocking sleep of twenty minutes leaves the client
    # unresponsive with no way to stop the script, and nothing would watch for trouble meanwhile
    while time.time() < ready_at:
        if stop_reason() is not None:
            return

        watch_for_trouble()

        if time.time() - said_at >= IDLE_LOG_EVERY:
            said_at = time.time()
            log("%dm to go" % max(1, int(round((ready_at - time.time()) / 60.0))))

        API.Pause(IDLE_POLL)

    heartbeat.reset()


# One of ('target', tree), ('walked',), ('waited',), ('stop', reason)
def approach():
    global walking_to, walking_cycles

    tree, regrows_at = scan_for_tree()

    if tree is None:
        if regrows_at is not None:
            idle_until(regrows_at)

            return ("waited",)

        # Trees that matched everything and had no way to walk to them are the one cause the survey
        # below cannot show
        if skipped_unreachable > 0:
            log("%d tree(s) matched but had no walkable route" % skipped_unreachable)

        log("nothing within %dz of %d matched, here is what is around" % (CHOP_Z_RANGE, API.Player.Z))
        survey_statics(SCAN_RADIUS, SURVEY_ARTS)

        return ("stop", "no tree in range")

    if tree["distance"] <= CHOP_RANGE:
        walking_to = None
        walking_cycles = 0

        return ("target", tree)

    key = "%d,%d" % (tree["x"], tree["y"])

    if walking_to != key:
        walking_to = key
        walking_cycles = 0

    walking_cycles += 1

    if walking_cycles > MAX_TREE_WALKS:
        mark_unreachable(tree)
        walking_to = None
        walking_cycles = 0

        return ("walked",)

    before = tree["distance"]
    API.Pathfind(tree["x"], tree["y"], tree["z"], CHOP_RANGE, True, PATHFIND_TIMEOUT)
    API.CancelPathfinding()

    # A step that does not move during a save is not a wall
    if chebyshev(tree) >= before and not is_saving():
        mark_unreachable(tree)
        walking_to = None
        walking_cycles = 0

    return ("walked",)


remember_axe(held_tool())

log("%d logs in the pack to start, at %d,%d" % (log_total(), API.Player.X, API.Player.Y))

# Read before anything acts, or a run that stops on its first cycle looks exactly like a script that
# never started
held = held_tool()
log(
    "mounted %s, hand %s, weight %d/%d, aiming %s"
    % (
        "yes" if API.Player.IsMounted else "no",
        (held.Name or hex_of(held.Graphic)) if held is not None else "empty",
        API.Player.Weight,
        API.Player.WeightMax,
        "at yourself" if AIM_AT_SELF else "at the tree",
    )
)

if PICK_PACK_ANIMALS:
    pick_pack_animals()

# A pack pasted in already over the buffer would otherwise be stopped on cycle zero by the weight
# guard, before a haul had ever had its turn
if over_buffer(HAUL_BUFFER):
    haul_now()

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

        # Everything below reads a frozen shard as its own failure: a walk that does not move is a
        # wall, a conversion that changes nothing is wood that cannot be worked
        if is_saving():
            wait_out_save()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        watch_for_trouble()

        if not equip_axe():
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = "no axe"
                break

            log("no axe (%d/%d), looking again" % (no_tool, MAX_NO_TOOL))
            end_cycle("no tool")
            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
            continue

        no_tool = 0

        relieved = haul_for_room()

        if relieved is not None:
            end_cycle(relieved)
            API.Pause(STEP_DELAY)
            continue

        found = approach()

        if found[0] == "stop":
            stop = found[1]
            break

        # No pause: a tree coming back has already waited out its own clock, and a wait is the
        # script working rather than stalling
        if found[0] == "waited":
            idled += 1
            stall.progressed()
            continue

        if found[0] == "walked":
            end_cycle("walking")
            continue

        tree = found[1]

        outcome = chop_once(axe_serial(), tree)

        if outcome == "chopped":
            tally += 1
            unknown = 0
            throttled = 0
            barren = 0
            stall.progressed()

        elif outcome == "wornOut":
            log("axe worn out, swapping")
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

        # A stump, not a dead tile. The two outcomes differ only in scope: nothingNearby is the shard
        # answering about everything it can reach, so it always parks the ground, while empty is
        # about the trunk - unless a self-target let the shard pick, in which case it is about the
        # spot as well. Parking one tile for an answer about the area left mining.py swinging at the
        # neighbour the shard had just written off, for the same sentence.
        elif outcome == "empty" or outcome == "nothingNearby":
            unknown = 0
            barren += 1

            if outcome == "nothingNearby" or AIM_AT_SELF:
                mark_area_depleted(CHOP_RANGE)
                current_tree = None
            else:
                mark_depleted(tree)

            # Said once, at the point it stops looking like bad luck
            if barren == EMPTY_HINT:
                log(
                    "%d spots in a row had nothing to chop - either the stand is worked out, or the "
                    "tree test is matching scenery the shard will not harvest" % EMPTY_HINT
                )
                survey_statics(CHOP_RANGE, SURVEY_ARTS)

        # The art ban is only sound when the swing named the tile: aimed at yourself the shard chose
        # what to refuse, and banning the art of the trunk the scan happened to pick would write off
        # a perfectly good tree. Aimed that way the tile is set aside one at a time instead - slower
        # across a stand of scenery, but never wrong about which art it was.
        elif outcome == "notTree":
            unknown = 0

            if not AIM_AT_SELF:
                mark_not_choppable(tree["graphic"])

            mark_unusable(tree, "is not harvestable")

        elif outcome == "tooFar":
            unknown = 0
            mark_unusable(tree, "is out of reach at %d tiles" % tree["distance"])

        elif outcome == "notSeen":
            unknown = 0
            mark_unusable(tree, "is not in line of sight")

        # Consolidating would give back almost nothing here - one log stack converts to one board
        # stack - so what frees slots is the boards leaving for the animal
        elif outcome == "packFull":
            unknown = 0
            log("pack is full, hauling before the next swing")
            haul_now()

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
                "%d chops, %d logs, %d/%d"
                % (tally, log_total(), API.Player.Weight, API.Player.WeightMax)
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

# However the run ended, it finishes with boards on the animal rather than logs in the pack
make_boards()

if hauling:
    unload()

# Chops rather than a log delta: hauled wood has left the pack, so the pack cannot total the run
log("%d chops, %d logs still in the pack" % (tally, log_total()))
log("stopping - %s" % reason)
API.Stop()
