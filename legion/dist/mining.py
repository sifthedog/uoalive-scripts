# Built from src/mining/index.py by build.py - do not edit.

import API
import time
import clr
import System


# src/uo/phrases.py
"""The shard's own wordings, as far as they are the same whatever the script is doing."""

SAVING_TEXT = ["The world is saving", "Saving world", "World save started"]
SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"]

# Ends in a bare 'You must wait', which longer refusals contain - so a bucket that has to be told
# apart from a throttle is ordered before this one
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

STOPPED = "stopped from the script manager"

# A fragment: the journal line is your own character's "You have been ambushed!" with the name first
AMBUSH_TEXT = ["been ambushed"]


# src/uo/timings.py
"""The constants the scripts agreed on. Every one is in seconds - API.Pause takes seconds."""

SAVE_WAIT = 60.0
SAVE_POLL = 1.0

THROTTLE_BACKOFF = 1.0
THROTTLE_BACKOFF_MAX = 8.0

LOG_EVERY = 25
HEARTBEAT_EVERY = 30.0

STALL_WARN = 60
STALL_STOP = 300

STEP_DELAY = 0.3

# The item cap is per container
PACK_LIMIT = 120


# src/mining/config.py
# Whole words and a list, so a plural still matches
PICKAXE_NAMES = ["pickaxe", "pickaxes"]

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

# 'No harvestable resources nearby' is about the 8x8 block the character stands in, on RunUO-family
# shards, so that is what it parks
HARVEST_BANK = 8
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

COMBINE_DELAY = 0.3
COMBINE_TIMEOUT = 2.0
COMBINE_POLL = 0.2
MAX_COMBINE_ATTEMPTS = 12

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

# A tooltip that answers with no metal line is plain iron, and it has to key the same as one saying
# 'Iron' or two piles of the one metal sit apart for the whole run
PLAIN_METAL = "iron"

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

IDLE_POLL = 10.0
IDLE_LOG_EVERY = 60.0

# A cycle this long says where its time went, so a slow run can be read off the journal
SLOW_CYCLE = 2.0

MAX_CYCLES = 5000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_CURSOR = 20
MAX_NO_TOOL = 10

# Spots in a row with nothing in them before the run says ORE_TILE_GRAPHICS is probably wrong
NOTHING_NEARBY_HINT = 5

WATCH_FOR_TROUBLE = True

THREAT_RANGE = 12
AMBUSH_WARNING = "AMBUSHED!"
AMBUSH_HUE = 33

# Run on this Mac, outside the game, so the client's sound setting does not matter. An empty list
# turns the one off. The alarm restarts while trouble lasts, up to AMBUSH_REPEATS starts
AMBUSH_ALARM = ["afplay", "/System/Library/Sounds/Sosumi.aiff"]
AMBUSH_NOTICES = [
    ["osascript", "-e", 'display notification "You have been ambushed!" with title "Ultima Online"'],
]
AMBUSH_REPEATS = 30

# The smelt refusal is mining's own; the rest are the shard's general wording
SMELT_UNSKILLED_TEXT = ["You have no idea how to smelt this strange ore"] + UNSKILLED_TEXT


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


# src/uo/journal.py
def said(texts):
    for text in texts:
        if API.InJournal(text, False):
            return True

    return False


# Line by line rather than the whole journal: a wholesale clear before every swing wiped the ambush
# warning before the threat watch got its once-a-cycle look at it
def forget(phrases):
    for text in phrases:
        API.ClearJournal(text)


def forget_outcomes(buckets):
    for _name, phrases in buckets:
        forget(phrases)


def matched_bucket(buckets):
    for name, phrases in buckets:
        # clearMatches, or a line already read answers the next wait as well
        if API.InJournalAny(phrases, True):
            return name

    return None


def read_outcome(buckets, budget, poll, between=None):
    waited = 0.0

    while not API.StopRequested:
        hit = matched_bucket(buckets)

        if hit is not None:
            return hit

        if waited >= budget:
            return None

        # Between the slices rather than around the wait: a mobile walks while its attempt resolves
        if between is not None:
            between()

        API.Pause(poll)
        waited += poll


# src/mining/dig.py
class Digger(object):
    def __init__(self, ore, buckets, config, log, cancel_pathfinding):
        self._ore = ore
        self._buckets = buckets
        self._config = config
        self._log = log
        self._cancel_pathfinding = cancel_pathfinding

    def _silent_outcome(self, serial, ore_before):
        if serial is not None and API.FindItem(serial) is None:
            return "wornOut"

        if self._ore.total() > ore_before:
            return "dug"

        return "unknown"

    # HasTarget alone was not enough on the web client: a measured swing had the shard's prompt in
    # the journal at 164ms and the cursor flag false for the whole six seconds after it
    def _cursor_opened(self):
        waited = 0.0

        while waited < self._config["cursor_timeout"]:
            if API.HasTarget() or said(self._config["prompt_text"]):
                return True

            API.Pause(self._config["cursor_poll"])
            waited += self._config["cursor_poll"]

        return False

    # No cursor is not the same as nothing having happened: the commonest reason a shard declines a
    # swing is that it refused the action outright and said so
    def _refused_outcome(self, serial, ore_before):
        matched = read_outcome(self._buckets, self._config["no_cursor_read"],
                               self._config["cursor_poll"])

        if matched is not None:
            return matched

        silent = self._silent_outcome(serial, ore_before)

        if silent != "unknown":
            return silent

        self._log("no target cursor - the shard never asked where to dig")

        return "noCursor"

    def dig_once(self, serial):
        # A pathfind still running would walk the character away mid-swing
        if self._cancel_pathfinding and API.Pathfinding():
            API.CancelPathfinding()

        # Cancelled only when there is one to cancel: an unconditional cancel a few hundred
        # milliseconds before the swing left the next cursor unusable in the run this was copied
        # from
        if API.HasTarget():
            API.CancelTarget()

        ore_before = self._ore.total()
        forget(self._config["prompt_text"])
        forget_outcomes(self._buckets)

        API.UseObject(serial)

        if not self._cursor_opened():
            return self._refused_outcome(serial, ore_before)

        # Answered with yourself rather than with the vein's coordinates: the shard takes that as
        # 'mine where I am' and picks the ore itself, so nothing has to guess land versus static
        API.TargetSelf()

        matched = read_outcome(self._buckets, self._config["dig_timeout"],
                               self._config["cursor_poll"])

        return matched if matched is not None else self._silent_outcome(serial, ore_before)


# src/uo/entity.py
# API.Player is None whenever the client is between world states - a recall, a server line change,
# the moment around a death - and reading through it threw a live restock away
def player():
    try:
        return API.Player
    except Exception:
        return None


def hex_of(value):
    return "0x%x" % (value & 0xFFFFFFFF)


# src/uo/weight.py
# Unknown is not overweight, the same call WeightMax == 0 gets: WeightMax reads 0 before the client
# has been told, against which every weight is overweight - a live mining run ended at 436/453 on it
def over_buffer(buffer):
    me = player()

    if me is None:
        return False

    ceiling = me.WeightMax

    return ceiling > 0 and me.Weight > ceiling - buffer


def too_heavy():
    return over_buffer(0)


# src/mining/relieve.py
class Relief(object):
    """Making room by turning the ore into ingots, and knowing when that has stopped working."""

    def __init__(self, ore, combiner, smelter, saves, reach, advice, log):
        self._ore = ore
        self._combiner = combiner
        self._smelter = smelter
        self._saves = saves
        self._reach = reach
        self._advice = advice
        self._log = log

    def smelt(self):
        return self._smelter.smelt_against(self._reach)

    def group_and_smelt(self):
        self._combiner.group()
        self.smelt()

    def smelt_for_room(self):
        if not too_heavy():
            return None

        before = self._ore.total()

        # Unconditional, because the decision has already been taken: a helper that asked too_heavy
        # a second time could disagree, and the run stopped for weight without ever having tried
        self.group_and_smelt()

        # Ore leaving the pack is the proof, not the weight going down: the client can still report
        # its pre-smelt figure over a conversion the pack diff has confirmed
        if self._ore.total() < before:
            return "smelting"

        # Before the retry rather than after it: a frozen shard converts nothing, and a retry spent
        # here is the run's only one gone
        if self._saves.is_saving():
            self._saves.wait_out()

            return "smelting"

        if self._smelter.retry_written_off():
            return "smelting"

        # The retry above has just reopened the hues written off, so this pass is the one that acts
        self.group_and_smelt()

        if self._ore.total() < before:
            return "smelting"

        if self._saves.is_saving():
            self._saves.wait_out()

            return "smelting"

        return {
            "stop": "overweight (%d/%d) with %d ore left, and smelting freed nothing%s"
            % (API.Player.Weight, API.Player.WeightMax, self._ore.total(), self._advice)
        }


# src/mining/beetle.py
class Beetle(object):
    """The fire beetle the ore is smelted against."""

    def __init__(self, graphics, serial, radius, smelt_range, pathfind_timeout, pick_timeout, log):
        self._graphics = graphics
        self._radius = radius
        self._smelt_range = smelt_range
        self._pathfind_timeout = pathfind_timeout
        self._pick_timeout = pick_timeout
        self._log = log

        self._serial = serial
        # A serial chosen rather than guessed - from config or from the cursor - is the law, so a
        # moment out of sight is not a reason to go looking for someone else's beetle
        self._pinned = serial is not None
        self._reported = False

    def pick(self):
        # A cursor left open by whatever ran last would swallow this query
        if API.HasTarget():
            API.CancelTarget()

        self._log("target your fire beetle, ESC to let the script find it")

        serial = API.RequestTarget(self._pick_timeout)

        if not serial:
            # A cancelled pick can still leave the cursor up, and a live one would spend the
            # double-clicks that follow as target clicks instead
            if API.HasTarget():
                API.CancelTarget()

            self._log("nothing picked, looking for one instead")

            return None

        picked = API.FindMobile(serial)

        if picked is None:
            self._log("%s is not a mobile, looking for one instead" % hex_of(serial))

            return None

        # Not a refusal: the graphics table is a guess at this shard, so a body it has never heard
        # of is worth reporting and then using
        if picked.Graphic not in self._graphics:
            self._log("%s is not a body FIRE_BEETLE_GRAPHICS knows, using it anyway"
                      % hex_of(picked.Graphic))

        self._serial = serial
        self._pinned = True
        self._reported = True
        self._log("using '%s' %s as the forge" % (picked.Name or hex_of(serial),
                                                  hex_of(picked.Graphic)))

        return picked

    def find(self):
        if self._serial is not None:
            resolved = API.FindMobile(self._serial)

            if resolved is not None:
                return resolved

            # Out of range, dead, or a hand-written serial that was never a mobile
            if self._pinned:
                return None

            self._serial = None

        found = []

        for graphic in self._graphics:
            for mobile in API.GetAllMobiles(graphic, self._radius) or []:
                found.append(mobile)

        if not found:
            return None

        # Only your own pets can be renamed, so this is what tells yours from a stranger's
        mine = [mobile for mobile in found if mobile.IsRenamable]
        candidates = mine if mine else found
        candidates.sort(key=lambda mobile: mobile.Distance)

        beetle = candidates[0]

        if not self._reported:
            self._reported = True
            self._log("using '%s' %s as the forge" % (beetle.Name or hex_of(beetle.Serial),
                                                      hex_of(beetle.Graphic)))

        self._serial = beetle.Serial

        return beetle

    # A pet's coordinates go stale within a cycle, so the serial is re-resolved rather than the
    # find result trusted
    def walk_to(self, serial):
        here = API.FindMobile(serial)

        if here is None:
            self._log("lost track of %s" % hex_of(serial))

            return None

        if here.Distance <= self._smelt_range:
            return here

        API.PathfindEntity(serial, self._smelt_range, True, self._pathfind_timeout)
        API.CancelPathfinding()

        here = API.FindMobile(serial)

        if here is None or here.Distance > self._smelt_range:
            self._log("could not get within %d of the beetle" % self._smelt_range)

            return None

        return here

    # The stationary counterpart: a beetle not already next to you is not a forge this run can use
    def in_range(self, serial):
        found = API.FindMobile(serial)

        if found is None:
            self._log("lost track of %s" % hex_of(serial))

            return None

        if found.Distance > self._smelt_range:
            self._log("the beetle is %d tiles off and this run does not walk" % found.Distance)

            return None

        return found


# src/uo/pack.py
def pack_contents():
    items = API.ItemsInContainer(API.Backpack, True)

    return items if items else []


# The item cap is per container, so the guard and the combine both count the top level only
def pack_top_level():
    items = API.ItemsInContainer(API.Backpack, False)

    return items if items else []


# None is an unreported stack, not an empty one: counted as 0 it would hide the ore a swing just
# delivered, which is the proof that the swing landed
def amount_of(item):
    amount = getattr(item, "Amount", None)

    return amount if amount is not None else 1


def hue_of(item):
    return getattr(item, "Hue", 0) or 0


def counts_by_graphic(items):
    counts = {}

    for item in items:
        key = (item.Graphic, hue_of(item))
        counts[key] = counts.get(key, 0) + amount_of(item)

    return counts


def diff_counts(before, after):
    gained = {}
    lost = {}

    for key in set(list(before.keys()) + list(after.keys())):
        change = after.get(key, 0) - before.get(key, 0)

        if change > 0:
            gained[key] = change
        elif change < 0:
            lost[key] = -change

    return gained, lost


# src/mining/combine.py
def serial_key(a, b):
    if a.Serial < b.Serial:
        return "s%d:%d" % (a.Serial, b.Serial)

    return "s%d:%d" % (b.Serial, a.Serial)


def hue_key(a, b):
    low, high = sorted([hue_of(a), hue_of(b)])

    return "h%d:%d" % (low, high)


# Never for hue 0, which is both iron and 'the client has not said yet'
def hue_tells_apart(a, b):
    return hue_of(a) != 0 and hue_of(b) != 0 and hue_of(a) != hue_of(b)


class Combiner(object):
    def __init__(self, ore, metals, config, log):
        self._ore = ore
        self._metals = metals
        self._config = config
        self._log = log

        # The backstop for the piles no tooltip named. Remembered by serial, which is why it cannot
        # carry a run alone: every swing delivers a pile wearing a serial nothing is known about.
        self._differing = set()

        # This call only: a silent miss is as likely to be a busy moment as a verdict, and
        # remembering it for the run would split two piles of one metal for good
        self._skipped = set()

    def _describe(self, item):
        metal = self._metals.of(item)

        return "%d %s" % (amount_of(item), metal if metal is not None else "hue %d" % hue_of(item))

    # Only ever forbids: one pile the tooltip could not name must not split its own metal
    def _metal_tells_apart(self, a, b):
        mine = self._metals.of(a)
        theirs = self._metals.of(b)

        return mine is not None and theirs is not None and mine != theirs

    def _differs(self, a, b):
        # A pile whose tooltip is still in flight is paired with nothing at all - guessing at it
        # earned a refusal every cycle, and one more swing loose costs the pack nothing
        return (
            self._metals.pending(a)
            or self._metals.pending(b)
            or self._metal_tells_apart(a, b)
            or serial_key(a, b) in self._differing
            or serial_key(a, b) in self._skipped
            or (hue_tells_apart(a, b) and hue_key(a, b) in self._differing)
        )

    def _same_metal(self, a, b):
        mine = self._metals.of(a)

        return mine is not None and mine == self._metals.of(b)

    # A merge is silent either way, so the pack is the evidence: the consumed pile gone, or the pile
    # it went into grown. The refusal cuts the wait short, or a pack holding two metals spends the
    # whole timeout on every swing.
    def _merged(self, primary, dup, before):
        waited = 0.0

        while waited < self._config["timeout"]:
            grown = None
            dup_here = False

            for item in pack_contents():
                if item.Serial == primary.Serial:
                    grown = item
                elif item.Serial == dup.Serial:
                    dup_here = True

            if not dup_here or (grown is not None and amount_of(grown) > before):
                return True

            if said(self._config["different_text"]):
                return False

            API.Pause(self._config["poll"])
            waited += self._config["poll"]

        return False

    def _combine(self, primary, dup):
        before = amount_of(primary)

        forget(self._config["different_text"] + self._config["throttled_text"])

        # No cancel before the use: a cursor cancelled shortly before an action has been measured
        # costing that action its own cursor
        API.UseObject(dup.Serial)

        if not API.WaitForTarget("any", self._config["target_timeout"]):
            API.CancelTarget()
            self._skipped.add(serial_key(primary, dup))
            self._log("no target cursor for %s" % self._describe(dup))

            return

        API.Target(primary.Serial)

        if self._merged(primary, dup, before):
            return

        # Nothing was attempted, so nothing has been learned about the metals
        if said(self._config["throttled_text"]):
            self._log("the shard says wait, leaving the two of them paired")

            return

        if said(self._config["different_text"]):
            metal = self._metals.of(primary)

            if metal is not None and metal == self._metals.of(dup):
                self._metals.doubt(metal)

            self._differing.add(serial_key(primary, dup))

            if hue_tells_apart(primary, dup):
                self._differing.add(hue_key(primary, dup))

            return

        self._skipped.add(serial_key(primary, dup))
        self._log("%s and %s did not merge and nothing was said"
                  % (self._describe(primary), self._describe(dup)))

    # The first pile that can join one already seen. Everything ahead of it is a family of its own,
    # so returning nothing means every pile in the pack is a metal of its own.
    def _next_pair(self, piles):
        primaries = []

        for pile in piles:
            home = None

            # The tooltip's metal first, then hue: hue is right nearly always, and wrong costs a
            # refusal
            for primary in primaries:
                if self._same_metal(primary, pile) and not self._differs(primary, pile):
                    home = primary
                    break

            if home is None:
                for primary in primaries:
                    if hue_of(primary) == hue_of(pile) and not self._differs(primary, pile):
                        home = primary
                        break

            if home is None:
                for primary in primaries:
                    if not self._differs(primary, pile):
                        home = primary
                        break

            if home is not None:
                return home, pile

            primaries.append(pile)

        return None

    def group(self):
        self._skipped.clear()
        self._metals.start_pass()

        for _attempt in range(self._config["attempts"]):
            piles = self._ore.piles()
            self._metals.forget_missing(piles)

            pair = self._next_pair(piles)

            if pair is None:
                if len(self._skipped) > 0 and len(piles) > 1:
                    self._log("left %d piles - %s"
                              % (len(piles), ", ".join(map(self._describe, piles))))

                return

            self._combine(pair[0], pair[1])
            API.Pause(self._config["delay"])

        self._log("hit the %d combine attempt backstop" % self._config["attempts"])


# src/uo/text.py
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


# src/mining/metal.py
class MetalBook(object):
    """What the tooltip says each pile is made of, and how much that answer is trusted."""

    def __init__(self, config, log):
        self._metals = config["metals"]
        self._plain = config["plain"]
        self._line_extra = config["line_extra"]
        self._not_metal_words = config["not_metal_words"]
        self._asks = config["asks"]
        self._miss_limit = config["misses"]
        self._log = log

        self._known = {}
        self._asked = {}
        self._missed_this_pass = set()
        self._doubted = set()
        self._opl_names_metals = True
        self._opl_answered = False
        self._misses = 0

    def _looks_like_metal(self, line):
        if not line or not line[0].isalpha():
            return False

        for char in line:
            if not char.isalpha() and char not in self._line_extra:
                return False

        for word in words_of(line):
            if word in self._not_metal_words:
                return False

        return True

    def _body(self, props, name):
        lines = []

        for raw in (props or "").splitlines():
            line = raw.strip()

            if line and line != name:
                lines.append(line)

        return lines

    def _read_metal(self, props, name):
        lines = self._body(props, name)

        for line in lines:
            if line.lower() in self._metals:
                return line.lower()

        for line in lines:
            if self._looks_like_metal(line):
                self._metals.add(line.lower())
                self._log("'%s' is a metal too, remembering it" % line)

                return line.lower()

        return self._plain

    def _worth_asking(self, serial):
        return (
            self._opl_names_metals
            and serial not in self._missed_this_pass
            and self._asked.get(serial, 0) < self._asks
        )

    def _look_up(self, item):
        serial = item.Serial

        if serial in self._known or not self._worth_asking(serial):
            return

        self._asked[serial] = self._asked.get(serial, 0) + 1

        # Never waited for: a wait is a second of nothing else, and the pile is still there next pass
        props = API.ItemNameAndProps(serial, False) or ""

        if not props:
            self._missed_this_pass.add(serial)
            API.RequestOPLData([serial])

            return

        name = (item.Name or "").strip()

        # A miss is a tooltip that arrived carrying only the name
        if not self._body(props, name):
            self._missed_this_pass.add(serial)
            self._misses += 1

            if self._misses >= self._miss_limit:
                self._opl_names_metals = False
                self._log("tooltips are not naming the metal here, so a pair has to be refused "
                          "to be split")

            return

        self._misses = 0
        self._opl_answered = True
        self._known[serial] = self._read_metal(props, name)

    # None is 'the tooltip did not say', which is not a metal of its own: callers fall back to the
    # hue and the shard's refusal for those
    def of(self, item):
        self._look_up(item)

        metal = self._known.get(item.Serial)

        return None if metal is not None and metal in self._doubted else metal

    def pending(self, item):
        self._look_up(item)

        # Not _worth_asking: a pile that missed this pass is still pending, or it would be paired on
        # a guess the moment its lookup came back empty
        return (
            self._opl_answered
            and self._opl_names_metals
            and item.Serial not in self._known
            and self._asked.get(item.Serial, 0) < self._asks
        )

    def start_pass(self):
        self._missed_this_pass.clear()

    def doubt(self, metal):
        if metal in self._doubted:
            return

        self._doubted.add(metal)
        self._log("the shard refused two piles both read as '%s', so that line is not the metal"
                  % metal)

    # The shard reissues the serial of a pile a combine or a smelt consumed, so a stale entry would
    # name the wrong metal for whatever turns up wearing it next
    def forget_missing(self, piles):
        here = set(pile.Serial for pile in piles)

        for serial in list(self._known.keys()):
            if serial not in here:
                del self._known[serial]

        for serial in list(self._asked.keys()):
            if serial not in here:
                del self._asked[serial]


# src/mining/ore.py
class OrePack(object):
    def __init__(self, graphics, name_word, min_smelt, log):
        self._graphics = graphics
        self._name_word = name_word
        self._min_smelt = min_smelt
        self._log = log

    # Graphic first, name second: names are empty until the client has tooltip data. An art learned
    # by name joins the set, so it costs one tooltip and no more.
    def is_ore(self, item):
        if item.Graphic in self._graphics:
            return True

        if not word_in(item.Name, [self._name_word]):
            return False

        self._graphics.add(item.Graphic)
        self._log("%s '%s' is ore too, remembering the art" % (hex_of(item.Graphic), item.Name))

        return True

    # Top level only, unlike total: the combine and the smelt both act by serial on loose items.
    # Largest first, so the pile a combine consumes is always the smaller one.
    def piles(self):
        piles = [item for item in pack_top_level() if self.is_ore(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    # Hue-blind on purpose: every ore type counts toward the pack, whatever it smelts into
    def total(self):
        return sum(amount_of(item) for item in pack_contents() if self.is_ore(item))

    # Reads the total rather than the number of piles, so a shard that does merge ore on arrival is
    # satisfied immediately instead of waiting out the timeout on every swing
    def wait_for_ore(self, before, timeout, poll):
        waited = 0.0

        while not API.StopRequested:
            # Read before the first pause: the delivery has usually already happened by the time the
            # journal line announcing it is read
            if self.total() > before:
                return True

            if waited >= timeout:
                return False

            API.Pause(poll)
            waited += poll

    # item.Amount reads 0 for a stack the client has no data for, so 'amount >= 2' skips every pile
    # in the pack. An unknown size is worth one attempt; only a size reported as one is skipped.
    def big_enough(self, item):
        amount = item.Amount or 0

        return amount == 0 or amount >= self._min_smelt

    def next_ore(self, written_off):
        for item in self.piles():
            if hue_of(item) not in written_off and self.big_enough(item):
                return item

        return None

    def describe_skipped(self, item, written_off):
        amount = item.Amount or 0
        hue = hue_of(item)

        if hue in written_off:
            return "%d hue %d (written off)" % (amount, hue)

        if not self.big_enough(item):
            return "%d hue %d (too small)" % (amount, hue)

        return "%d hue %d" % (amount, hue)


# src/uo/convert.py
class Converter(object):
    """One resource into another, judged by the pack diff, with a per-hue write-off."""

    def __init__(self, config, log, saves):
        self._config = config
        self._log = log
        self._saves = saves
        self._written_off = set()
        self._misses = {}
        # Whether anything has converted since the last retry. Without it a retry granted
        # unconditionally answers true again next cycle and the caller loops until the watchdog ends
        self._progressed = True

    def written_off(self):
        return self._written_off

    # Every failing path comes through here: one that returns without counting leaves the candidate
    # set unchanged, so the next pass picks the same stack and the loop runs to its backstop
    def _missed(self, hue):
        count = self._misses.get(hue, 0) + 1
        self._misses[hue] = count

        if count >= self._config["attempts"]:
            self._written_off.add(hue)
            self._log("hue %d failed %d times, leaving it as %s"
                      % (hue, count, self._config["noun"]))

    # The journal is cleared to perform the conversion, so a save that starts mid-attempt is past
    # the check at the top of the pass
    def _saving(self, hue):
        if not self._saves.is_saving():
            return False

        self._log("the world is saving, not counting it against hue %d" % hue)

        if self._config["wait_on_save"]:
            self._saves.wait_out()

        return True

    # The action throttle can hold a conversion well past any pause worth taking, and reading too
    # early is indistinguishable from a resource that cannot be worked
    def _wait_for_change(self, before):
        waited = 0.0

        while waited < self._config["timeout"]:
            API.Pause(self._config["poll"])
            waited += self._config["poll"]

            gained, lost = diff_counts(before, counts_by_graphic(pack_contents()))

            if gained or lost:
                return gained

        return None

    def _convert_one(self, stack):
        hue = hue_of(stack)
        before = counts_by_graphic(pack_contents())

        if not self._config["perform"](stack):
            if self._saving(hue):
                return

            # Counted like any other failure: without this an empty hand spends every pass waiting
            # on a cursor that is never going to come
            self._missed(hue)

            return

        gained = self._wait_for_change(before)

        if gained is not None:
            self._misses.pop(hue, None)
            self._progressed = True
            self._config["learn_product"](gained)

            return

        # Asked before either wording, because a frozen shard's verdict on the material is worthless
        if self._saving(hue):
            return

        # Nothing was attempted, so this is not a verdict on the material
        if said(self._config["throttled_text"]):
            self._log("the shard says wait, not counting it against hue %d" % hue)

            return

        if said(self._config["unskilled_text"]):
            self._written_off.add(hue)
            self._log("not skilled enough for hue %d, leaving it as %s"
                      % (hue, self._config["noun"]))

            return

        # Otherwise it was silent, which is also what a throttled or stale attempt looks like
        self._missed(hue)

    def run(self):
        for _pass in range(self._config["passes"]):
            # A frozen shard answers a conversion the same way an unworkable material does, so
            # without this a world save costs the attempts and writes the hue off for the run
            if self._saves.is_saving():
                self._log(self._config["saving_message"])

                return False

            stack = self._config["next_source"](self._written_off)

            if stack is None:
                self._config["nothing_to_do"](self._written_off)

                return True

            # Asked only once there is something that needs it, which is what makes converting on
            # every dry spot affordable
            blocked = self._config["blocked"]()

            if blocked is not None:
                self._log("%s, leaving it for now" % blocked)

                return False

            self._config["about_to_convert"]()
            self._convert_one(stack)
            API.Pause(self._config["delay"])

        self._log("hit the %d conversion pass backstop" % self._config["passes"])

        return False

    def retry_written_off(self, force=False):
        if len(self._written_off) == 0 or (not self._progressed and not force):
            return False

        self._progressed = False
        self._log("giving %d hue(s) written off earlier another go" % len(self._written_off))
        self._written_off.clear()
        self._misses.clear()

        return True


# src/mining/smelt.py
class Smelter(object):
    """The ore side of the converter: a fire beetle is the forge, and the ore is what is used."""

    def __init__(self, ore, beetle, saves, config, log):
        self._ore = ore
        self._beetle = beetle
        self._config = config
        self._log = log
        self._forge = None
        self._reported_no_beetle = False

        self._converter = Converter({
            "noun": "ore",
            "attempts": config["attempts"],
            "passes": config["passes"],
            "delay": config["delay"],
            "timeout": config["timeout"],
            "poll": config["poll"],
            "throttled_text": config["throttled_text"],
            "unskilled_text": config["unskilled_text"],
            "wait_on_save": False,
            "saving_message": "the world is saving, leaving it for now",
            "next_source": ore.next_ore,
            "perform": self._perform,
            "blocked": self._forge_gone,
            "learn_product": self._learn_ingot,
            "nothing_to_do": self._say_what_is_left,
            "about_to_convert": self._nothing_to_note,
        }, log, saves)

    def written_off(self):
        return self._converter.written_off()

    def retry_written_off(self, force=False):
        return self._converter.retry_written_off(force)

    def _learn_ingot(self, gained):
        for graphic, _hue in gained:
            if graphic in self._config["ore_graphics"]:
                continue

            if graphic in self._config["ingot_graphics"]:
                continue

            self._config["ingot_graphics"].add(graphic)
            self._log("ingot graphic is %s" % hex_of(graphic))

    def _nothing_to_note(self):
        pass

    def _say_what_is_left(self, written_off):
        piles = self._ore.piles()

        if len(piles) > 0:
            described = [self._ore.describe_skipped(pile, written_off) for pile in piles]
            self._log("nothing to smelt in %d pile(s) - %s" % (len(piles), ", ".join(described)))

    # A smelt aimed at a beetle that has drifted out of range fails exactly the way ore that cannot
    # be worked does: silently. Three of those wrote off 86 ore of one colour on a live run.
    def _forge_gone(self):
        if self._forge is None:
            return "no beetle to smelt against"

        here = API.FindMobile(self._forge.Serial)

        if here is None:
            return "the beetle %s is out of sight" % hex_of(self._forge.Serial)

        if here.Distance > self._config["range"]:
            return "the beetle has wandered %d tiles off" % here.Distance

        return None

    # The inverse of making boards: the ore is double-clicked and the beetle is the target. The
    # beetle is never double-clicked itself - it is rideable, so that mounts you.
    def _perform(self, stack):
        if self._forge is None:
            return False

        # Cancelled only when there is one to cancel: a cursor cancelled shortly before an action
        # has been measured costing that action its own
        if API.HasTarget():
            API.CancelTarget()

        forget(self._config["throttled_text"] + self._config["unskilled_text"])
        API.UseObject(stack.Serial)

        if not API.WaitForTarget("any", self._config["target_timeout"]):
            API.CancelTarget()
            self._log("no target cursor for the beetle")

            return False

        API.Target(self._forge.Serial)

        return True

    def smelt_against(self, reach):
        # Asked before the beetle is looked for, so a pack with nothing eligible costs neither a
        # search nor a walk
        if self._ore.next_ore(self.written_off()) is None:
            return self._converter.run()

        found = self._beetle.find()

        if found is None:
            # Said once rather than every pass: a missing beetle is not fatal, the ore travels on
            if not self._reported_no_beetle:
                self._reported_no_beetle = True
                self._log("no fire beetle nearby, keeping the ore as it is")

            return False

        self._reported_no_beetle = False
        self._forge = reach(found.Serial)

        if self._forge is None:
            return False

        return self._converter.run()


# src/uo/guards.py
def first_reason(clauses):
    for clause in clauses:
        reason = clause()

        if reason is not None:
            return reason

    return None


def stopped(text):
    def clause():
        return text if API.StopRequested else None

    return clause


def dead():
    def clause():
        me = player()

        return "you are dead" if me is not None and me.IsDead else None

    return clause


def pack_full(limit):
    def clause():
        return "the pack is at its item cap" if len(pack_top_level()) >= limit else None

    return clause


def hurt(floor):
    def clause():
        me = player()

        if me is None:
            return None

        # HitsMax reads 0 before the client has been told, the way ManaMax does
        ceiling = me.HitsMax

        if ceiling > 0 and me.Hits < ceiling * floor:
            return "hurt (%d/%d)" % (me.Hits, ceiling)

        return None

    return clause


# src/uo/clock.py
def now():
    return time.time()


# src/uo/heartbeat.py
class Heartbeat(object):
    """Proof of life: a loop standing still in silence looks exactly like a hung one."""

    def __init__(self, every, log, noun, vitals):
        self._every = every
        self._log = log
        self._noun = noun
        self._vitals = vitals
        self._last = None

    # The clock, not the cycle counter: a cycle can be 300ms or 8s depending on which waits it hit
    def beat(self, phase, cycle, tally):
        moment = now()

        # The first call sets the clock rather than logging: the run has just said what it is doing
        if self._last is None:
            self._last = moment
            return

        if moment - self._last < self._every:
            return

        self._last = moment
        self._log("still here - %s, cycle %d, %s, %d %s"
                  % (phase, cycle, self._vitals(), tally, self._noun))

    def reset(self):
        self._last = now()


# src/uo/log.py
def make_log(prefix):
    def log(message):
        API.SysMsg(prefix + ": " + message)

    return log


# src/uo/loop.py
def backoff_for(count, step, cap):
    return min(step * count, cap)


class StallWatch(object):
    def __init__(self, without, warn_at, stop_at, heartbeat, log):
        self._without = without
        self._warn_at = warn_at
        self._stop_at = stop_at
        self._heartbeat = heartbeat
        self._log = log
        self._since = 0
        self._reason = None

    def end_cycle(self, phase, cycle, tally):
        self._heartbeat.beat(phase, cycle, tally)
        self._since += 1

        if self._since == self._warn_at:
            self._log("%d %s, last was '%s'" % (self._warn_at, self._without, phase))

        if self._since >= self._stop_at:
            self._reason = "no progress in %d cycles, last was '%s'" % (self._stop_at, phase)

    def progressed(self):
        self._since = 0

    def reason(self):
        return self._reason


# src/uo/retry.py
def settled(timeout, poll, landed):
    waited = 0.0

    while waited < timeout:
        API.Pause(poll)
        waited += poll

        if landed():
            return True

    return False


# src/uo/mount.py
def dismount(attempts, timeout, poll):
    if not API.Player.IsMounted:
        return True

    for _attempt in range(attempts):
        API.Dismount()

        if settled(timeout, poll, lambda: not API.Player.IsMounted):
            return True

    return False


# src/uo/save.py
class SaveWatch(object):
    def __init__(self, saving_text, done_text, wait, poll, log, heartbeat, stop_reason):
        self._saving_text = saving_text
        self._done_text = done_text
        self._wait = wait
        self._poll = poll
        self._log = log
        self._heartbeat = heartbeat
        self._stop_reason = stop_reason

    def is_saving(self):
        return said(self._saving_text)

    def wait_out(self):
        self._log("the world is saving, waiting it out")

        # Read before the clear: a save can start and finish inside one cycle, and clearing first
        # threw the completion away and then stood still for the whole of the wait
        ended = "the shard had already finished" if said(self._done_text) else None

        forget(self._saving_text + self._done_text)

        waited = 0.0

        while ended is None and waited < self._wait:
            API.Pause(self._poll)
            waited += self._poll

            if said(self._done_text):
                ended = "the shard says it is done"
            elif self._stop_reason() is not None:
                ended = "the run has a reason to stop"

        self._log("%s, carrying on" % (ended or "nothing said in %ds" % int(self._wait)))
        self._heartbeat.reset()


# src/uo/alert.py
class Launcher(object):
    def __init__(self, log):
        self._log = log
        self._playing = None
        self._referenced = False
        self._failed = set()

    def _start(self, command):
        if not self._referenced:
            self._referenced = True
            # Process is in its own assembly on .NET Core, and IronPython does not load it unasked
            clr.AddReference("System.Diagnostics.Process")

        info = System.Diagnostics.ProcessStartInfo()
        info.FileName = command[0]
        info.UseShellExecute = False
        info.CreateNoWindow = True

        for argument in command[1:]:
            info.ArgumentList.Add(argument)

        return System.Diagnostics.Process.Start(info)

    def _try(self, command):
        try:
            return self._start(command)
        except Exception as error:
            if command[0] not in self._failed:
                self._failed.add(command[0])
                self._log("could not run %s - %s" % (command[0], error))

            return None

    def run(self, command):
        if command:
            self._try(command)

    # One at a time, so a long file is not layered over itself every cycle. True means a start
    # was attempted, which is what the caller counts
    def play(self, command):
        if not command:
            return False

        if self._playing is not None and not self._playing.HasExited:
            return False

        self._playing = self._try(command)

        return True

    def stop(self):
        playing, self._playing = self._playing, None

        if playing is not None and not playing.HasExited:
            try:
                playing.Kill()
            except Exception:
                pass


# src/uo/notoriety.py
"""Passed through to the scans, never compared or OR-ed: the API.py stub lists every value as 1."""

# Innocent is out, or every blue NPC in the world is trouble
HOSTILE = [
    API.Notoriety.Gray,
    API.Notoriety.Criminal,
    API.Notoriety.Enemy,
    API.Notoriety.Murderer,
]


# src/uo/threat.py
# 0 is what the client reports while it is refreshing stats, and for a mobile it has lost track of,
# so a fall to 0 is no news at all
def dropped(was, is_now):
    return was > 0 and is_now > 0 and is_now < was


def hostiles_near(notoriety, within):
    found = API.GetAllMobiles(None, within, notoriety) or []

    for mobile in found:
        # IsRenamable is how the rest of this repo tells your own pet from a stranger's, and a pet
        # flagged gray by whatever it was fighting would otherwise read as the thing attacking you
        if mobile.Serial != API.Player.Serial and not mobile.IsDead and not mobile.IsRenamable:
            return mobile

    return None


class ThreatWatch(object):
    def __init__(self, config, log, companion, friend_label):
        self._config = config
        self._log = log
        self._companion = companion
        self._friend_label = friend_label
        self._alert = Launcher(log)
        self._last_hits = 0
        self._last_companion_hits = 0
        self._in_episode = False
        self._trouble_seen = False
        self._alarm_left = 0

    # Consuming: the roam idle loop never clears the journal, so said() would re-arm this every poll
    def _ambushed(self):
        text = self._config["ambush_text"]
        return bool(text) and matched_bucket([("ambushed", text)]) is not None

    def _describe(self, hostile, friend):
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
            theirs = ", %s %d/%s" % (self._friend_label(friend), friend.Hits,
                                     friend.HitsMax or "?")

        return "%s, %s%s" % (who, mine, theirs)

    def look(self):
        if not self._config["watch"]:
            return

        hits = API.Player.Hits
        hurt = dropped(self._last_hits, hits)

        if hits > 0:
            self._last_hits = hits

        friend = self._companion()
        friend_hits = friend.Hits if friend is not None else 0
        friend_hurt = dropped(self._last_companion_hits, friend_hits)

        if friend_hits > 0:
            self._last_companion_hits = friend_hits

        hostile = hostiles_near(HOSTILE, self._config["range"])
        trouble = hostile is not None or hurt or friend_hurt

        if self._ambushed():
            self._in_episode = True
            self._trouble_seen = False
            self._alarm_left = self._config["ambush_repeats"] if self._config["ambush_alarm"] else 0
            self._log("ambushed - %s" % self._describe(hostile, friend))
            API.HeadMsg(self._config["ambush_warning"], API.Player.Serial,
                        self._config["ambush_hue"])

            for command in self._config["ambush_notices"]:
                self._alert.run(command)

        if trouble:
            if not self._in_episode:
                self._in_episode = True
                self._log("trouble - %s" % self._describe(hostile, friend))

            self._trouble_seen = True
        # An ambush announces monsters that take a cycle to appear, so the alarm outlives an empty
        # scan until a fight has come and gone or the repeats run out
        elif self._in_episode and (self._trouble_seen or self._alarm_left == 0):
            self._in_episode = False
            self._trouble_seen = False
            self._alarm_left = 0
            self._alert.stop()
            self._log("clear")

        if self._alarm_left > 0 and self._alert.play(self._config["ambush_alarm"]):
            self._alarm_left -= 1


# src/uo/tool.py
class Tool(object):
    """Find it, learn its graphic, get it onto the hand, and notice when it breaks."""

    def __init__(self, noun, names, veto, layers, spare_bag, attempts, timeout, poll, log):
        self._noun = noun
        self._names = names
        self._veto = veto
        self._layers = layers
        self._spare_bag = spare_bag
        self._attempts = attempts
        self._timeout = timeout
        self._poll = poll
        self._log = log
        self._graphic = None
        self._reported_empty_pack = False
        self._opened = set()

    # Refused only on positive evidence. A name reads empty until the client has tooltip data, and
    # a tool in hand is the documented precondition, so an unnamed one is taken at its word - but a
    # vetoed tool learned here would be the tool for the whole run, and every swing would be wrong.
    def learn(self, item):
        if item is None or self._graphic is not None:
            return

        name = item.Name or ""

        if word_in(name, self._veto):
            self._log("you are holding a '%s', which this run does not use as its %s - "
                      "not learning its graphic" % (name, self._noun))

            return

        self._graphic = item.Graphic
        self._log("%s graphic is %s ('%s')" % (self._noun, hex_of(item.Graphic), name or "unnamed"))

    def is_tool(self, item):
        if item is None:
            return False

        name = item.Name or ""

        # The veto is asked before the graphic, not after it: one already learned off a shard that
        # names nothing, or off a hand that held it at startup, would go on matching every cycle
        if word_in(name, self._veto):
            return False

        if self._graphic is not None and item.Graphic == self._graphic:
            return True

        return word_in(name, self._names)

    def held(self):
        for layer in self._layers:
            found = API.FindLayer(layer)

            if found is not None:
                return found

        return None

    def serial(self):
        item = self.held()

        return item.Serial if item is not None else None

    def _search(self):
        for item in pack_contents():
            if self.is_tool(item):
                return item

        if self._spare_bag is not None:
            for item in API.ItemsInContainer(self._spare_bag, True) or []:
                if self.is_tool(item):
                    return item

        return None

    # A bag the client has not opened this session reads as empty, whatever is in it
    def _open_bags(self):
        bags = [item for item in pack_contents()
                if getattr(item, "IsContainer", False) and not getattr(item, "Opened", False)]

        if self._spare_bag is not None:
            spare = API.FindItem(self._spare_bag)

            if spare is not None and not getattr(spare, "Opened", False):
                bags.append(spare)

        bags = [bag for bag in bags if bag.Serial not in self._opened]

        if not bags:
            return False

        # A cursor left up would take the double-click as its answer
        if API.HasTarget():
            API.CancelTarget()

        self._log("opening %d bag(s) to look inside for a %s" % (len(bags), self._noun))

        for bag in bags:
            self._opened.add(bag.Serial)
            API.UseObject(bag.Serial)

        return True

    def find(self):
        found = self._search()

        if found is None and self._open_bags():
            settled(self._timeout, self._poll, lambda: self._search() is not None)
            found = self._search()

        if found is not None:
            self._reported_empty_pack = False
            self.learn(found)

            return found

        if not self._reported_empty_pack:
            self._reported_empty_pack = True
            arts = [hex_of(item.Graphic) for item in pack_contents()]
            self._log("no %s found - nothing named %s in the pack. It holds: %s"
                      % (self._noun, "/".join(self._names), ", ".join(arts) or "nothing"))

        return None

    # A broken tool can linger on the layer, and is_tool would match it by graphic, so the world is
    # asked rather than the layer
    def still_holding(self):
        item = self.held()

        return item is not None and self.is_tool(item) and API.FindItem(item.Serial) is not None

    def equip(self):
        if self.still_holding():
            return True

        found = self.find()

        if found is None:
            return False

        # A cursor left open by the swing that broke the tool would swallow the equip
        if API.HasTarget():
            API.CancelTarget()

        serial = found.Serial

        for _attempt in range(self._attempts):
            API.EquipItem(serial)

            if settled(self._timeout, self._poll, lambda: self.serial() == serial):
                return True

        self._log("could not get the %s %s onto the hand" % (self._noun, hex_of(serial)))

        return False


# src/uo/vitals.py
def weight_reading():
    me = player()

    return "?/?" if me is None else "%d/%d" % (me.Weight, me.WeightMax)


def where():
    me = player()

    return "somewhere" if me is None else "at %d,%d" % (me.X, me.Y)


def position_and_weight():
    return "%s, %s" % (where(), weight_reading())


# src/mining/run.py
class Run(object):
    """Everything both mining entries wire up alike. The prefix is what they differ on."""

    def __init__(self, prefix):
        log = make_log(prefix)
        heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "swings", position_and_weight)
        stall = StallWatch("cycles without a swing landing", STALL_WARN, STALL_STOP, heartbeat, log)


        def stop_reason():
            return first_reason([stopped(STOPPED), dead(), pack_full(PACK_LIMIT)])


        saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

        pickaxe = Tool("pickaxe", PICKAXE_NAMES, [], ["onehanded"], SPARE_BAG_SERIAL,
                       EQUIP_ATTEMPTS, EQUIP_TIMEOUT, EQUIP_POLL, log)
        ore = OrePack(ORE_GRAPHICS, ORE_NAME_WORD, MIN_SMELT_AMOUNT, log)
        metals = MetalBook({
            "metals": ORE_METALS,
            "plain": PLAIN_METAL,
            "line_extra": METAL_LINE_EXTRA,
            "not_metal_words": NOT_METAL_WORDS,
            "asks": METAL_ASKS,
            "misses": METAL_MISSES,
        }, log)
        combiner = Combiner(ore, metals, {
            "attempts": MAX_COMBINE_ATTEMPTS,
            "delay": COMBINE_DELAY,
            "timeout": COMBINE_TIMEOUT,
            "poll": COMBINE_POLL,
            "target_timeout": TARGET_TIMEOUT,
            "different_text": DIFFERENT_ORE_TEXT,
            "throttled_text": THROTTLED_TEXT,
        }, log)
        beetle = Beetle(FIRE_BEETLE_GRAPHICS, FIRE_BEETLE_SERIAL, BEETLE_SCAN_RADIUS, SMELT_RANGE,
                        PATHFIND_TIMEOUT, PICK_TIMEOUT, log)
        smelter = Smelter(ore, beetle, saves, {
            "attempts": SMELT_ATTEMPTS,
            "passes": MAX_SMELT_PASSES,
            "delay": SMELT_DELAY,
            "timeout": SMELT_TIMEOUT,
            "poll": SMELT_POLL,
            "range": SMELT_RANGE,
            "target_timeout": TARGET_TIMEOUT,
            "ore_graphics": ORE_GRAPHICS,
            "ingot_graphics": INGOT_GRAPHICS,
            "throttled_text": THROTTLED_TEXT,
            "unskilled_text": SMELT_UNSKILLED_TEXT,
        }, log)
        threat = ThreatWatch({
            "watch": WATCH_FOR_TROUBLE,
            "range": THREAT_RANGE,
            "ambush_text": AMBUSH_TEXT,
            "ambush_alarm": AMBUSH_ALARM,
            "ambush_notices": AMBUSH_NOTICES,
            "ambush_warning": AMBUSH_WARNING,
            "ambush_hue": AMBUSH_HUE,
            "ambush_repeats": AMBUSH_REPEATS,
        }, log, beetle.find, "beetle")

        DIG_CONFIG = {
            "cursor_timeout": DIG_TARGET_TIMEOUT,
            "cursor_poll": DIG_TARGET_POLL,
            "prompt_text": DIG_PROMPT_TEXT,
            "no_cursor_read": NO_CURSOR_READ,
            "dig_timeout": DIG_TIMEOUT,
        }


        def get_off_the_mount():
            return dismount(DISMOUNT_ATTEMPTS, DISMOUNT_TIMEOUT, DISMOUNT_POLL)


        # Read before the dismount, or the mounted half of it always answers no. A run that stops on its
        # first cycle otherwise looks exactly like a script that never started.
        def say_where_we_stand():
            pickaxe.learn(pickaxe.held())
            log("%d ore in the pack to start, at %d,%d" % (ore.total(), API.Player.X, API.Player.Y))
            held = pickaxe.held()
            log(
                "mounted %s, hand %s, weight %d/%d"
                % (
                    "yes" if API.Player.IsMounted else "no",
                    (held.Name or hex_of(held.Graphic)) if held is not None else "empty",
                    API.Player.Weight,
                    API.Player.WeightMax,
                )
            )

        self.log = log
        self.heartbeat = heartbeat
        self.stall = stall
        self.stop_reason = stop_reason
        self.saves = saves
        self.pickaxe = pickaxe
        self.ore = ore
        self.combiner = combiner
        self.beetle = beetle
        self.smelter = smelter
        self.threat = threat
        self.dig_config = DIG_CONFIG
        self.get_off_the_mount = get_off_the_mount
        self.say_where_we_stand = say_where_we_stand


# src/uo/scan.py
def chebyshev_to(tile):
    return max(abs(tile["x"] - API.Player.X), abs(tile["y"] - API.Player.Y))


# Moves, not points: the route the client returns starts with the tile you stand on
def steps_to(tile, within):
    path = API.GetPath(tile["x"], tile["y"], tile["z"], within)

    return len(path) - 1 if path else None


# GetPath costs a call per candidate, where the web client's flood fill answered every tile at once,
# so only the nearest `probes` matches are asked for a route
def pick_nearest(candidates, memory, probes, within, in_reach_is_free=False, stats=None):
    """(the shortest route in reach, when the soonest cooling tile is back, how many were walled)"""
    live = []
    cooling = None

    for tile in candidates:
        until = memory.blocked_until(tile)

        if until is not None and now() < until:
            if until != float("inf") and (cooling is None or until < cooling):
                cooling = until

            continue

        live.append(tile)

    live.sort(key=chebyshev_to)

    best = None
    best_steps = None
    walled = 0

    for tile in live[:probes]:
        # Sorted by crow flight, so once the best is at most this far nothing later can beat it
        if best_steps is not None and best_steps <= max(0, chebyshev_to(tile) - within):
            break

        # Already in reach, so there is nothing to route and no probe worth paying for
        if in_reach_is_free and chebyshev_to(tile) <= within:
            steps = 0
        else:
            steps = steps_to(tile, within)

            if stats is not None:
                stats["probes"] = stats.get("probes", 0) + 1

        # A refused route is a full A* on the client, so it is not asked for again for a while
        if steps is None:
            memory.mark_unreachable(tile)
            walled += 1
            continue

        if best_steps is None or steps < best_steps:
            best = tile
            best_steps = steps

    if best is not None:
        best = dict(best)
        best["distance"] = chebyshev_to(best)

    return best, cooling, walled


# src/uo/survey.py
# The dead-end report: what the run actually saw, so a wrong art table can be corrected from it
def survey(tiles, radius, limit, matches, log, extra_marks=None):
    seen = {}

    for tile in tiles:
        key = "%s:%d" % ("land" if tile["is_land"] else "static", tile["graphic"])
        entry = seen.get(key)

        if entry is None:
            seen[key] = [1, tile]
        else:
            entry[0] += 1

    ranked = sorted(seen.values(), key=lambda entry: entry[0], reverse=True)

    log("the arts within %d, commonest first:" % radius)

    for count, tile in ranked[:limit]:
        marks = []

        if matches(tile):
            marks.append("MATCHES")

        if not tile["is_land"]:
            marks.append("'%s'" % (tile["name"] or "?"))

        if extra_marks is not None:
            marks.extend(extra_marks(tile))

        # Decimal as well as hex: the RunUO tables the art sets are seeded from are decimal
        log("  %s %s (%d) x%d z%d %s"
            % ("land" if tile["is_land"] else "static", hex_of(tile["graphic"]), tile["graphic"],
               count, tile["z"], " ".join(marks)))


# src/mining/vein.py
class Veins(object):
    def __init__(self, terrain, memory, config, log):
        self._terrain = terrain
        self._memory = memory
        self._config = config
        self._log = log
        self._current = None
        self._skipped_unreachable = 0
        self._banks = {}
        self._bank_cooling = None
        self.stats = {}

    def skipped_unreachable(self):
        return self._skipped_unreachable

    # Refusals first, seeds second: the land table ships full, so asking it first made the ban
    # silently do nothing - it was recorded and ignored on the next scan
    def is_ore(self, graphic, is_land, name):
        if graphic in self._config["not_ore_graphics"]:
            return False

        if self._memory.art_banned(graphic, is_land):
            return False

        # No name to fall back on, so the table is the whole answer for land
        if is_land:
            return graphic in self._config["tile_graphics"]

        return any_in(name, self._config["static_names"])

    def matches(self, tile):
        return self.is_ore(tile["graphic"], tile["is_land"], tile.get("name"))

    def within_z(self, z):
        return abs(z - API.Player.Z) <= self._config["z_range"]

    def _bank_key(self, x, y):
        bank = self._config["bank"]

        return (x // bank, y // bank)

    def _bank_parked_until(self, tile):
        until = self._banks.get(self._bank_key(tile["x"], tile["y"]))

        if until is None:
            return None

        if now() >= until:
            return None

        return until

    def is_parked(self, tile):
        return self._memory.is_blocked(tile) or self._bank_parked_until(tile) is not None

    def _candidates(self, radius, statics_only):
        box = self._terrain.statics_box if statics_only else self._terrain.box

        for tile in box(radius):
            if not self.matches(tile) or not self.within_z(tile["z"]):
                continue

            until = self._bank_parked_until(tile)

            if until is not None:
                if self._bank_cooling is None or until < self._bank_cooling:
                    self._bank_cooling = until

                continue

            yield tile

    def scan_box(self, radius, statics_only=False):
        self._bank_cooling = None
        # The swing names no tile, so one already in reach needs no route
        best, cooling, walled = pick_nearest(self._candidates(radius, statics_only), self._memory,
                                             self._config["probes"], self._config["range"], True,
                                             self.stats)
        self._skipped_unreachable = walled
        self.stats["walled"] = self.stats.get("walled", 0) + walled

        if self._bank_cooling is not None and (cooling is None or self._bank_cooling < cooling):
            cooling = self._bank_cooling

        return best, cooling

    # One pair of reads against the (2 * radius + 1) squared the box costs. The z and the art have
    # to match as well as the coordinates: a tile carries several, and only one of them is the vein.
    def _still_ore(self, vein):
        if self.is_parked(vein):
            return None

        # The character has walked since this was picked, and the vein is now up a cliff
        if not self.within_z(vein["z"]):
            return None

        for tile in self._terrain.at(vein["x"], vein["y"]):
            if (
                tile["z"] == vein["z"]
                and tile["graphic"] == vein["graphic"]
                and tile["is_land"] == vein["is_land"]
            ):
                if not self.matches(tile):
                    return None

                found = dict(vein)
                found["distance"] = chebyshev_to(vein)

                return found

        return None

    def _radii(self):
        return range(self._config["range"], self._config["scan_radius"] + 1)

    # Widened a ring at a time rather than swept, statics before land in each: the next vein is
    # almost always close, a ring's statics are one read, and each land tile is a read of its own
    def scan(self):
        started = now()
        reads = self._terrain.reads
        self.stats = {}

        try:
            return self._scan()
        finally:
            self.stats["seconds"] = now() - started
            self.stats["reads"] = self._terrain.reads - reads

    def _scan(self):
        if self._current is not None:
            self._current = self._still_ore(self._current)

            if self._current is not None:
                return self._current, None

        cooling = None

        for radius in self._radii():
            for statics_only in [True, False]:
                found, cooling = self.scan_box(radius, statics_only)

                if found is not None:
                    self._current = found

                    return found, None

        self._current = None

        return None, cooling

    def forget_current(self):
        self._current = None

    # The sentence is about the bank the character stands in. The reach circle as well: a walk stops
    # short of its target, which can leave the character in the bank swinging at a tile past its edge
    def mark_area_depleted(self, reach):
        until = now() + self._config["respawn_delay"]
        bank = self._config["bank"]
        self._banks[self._bank_key(API.Player.X, API.Player.Y)] = until
        parked = 0

        for tile in self._terrain.box(reach):
            # The sentence is about what the shard can reach, so a tile 60 z up is not its claim
            if not self.within_z(tile["z"]) or not self.matches(tile):
                continue

            self._memory.block(tile, until)
            parked += 1

        self._log("nothing harvestable at %d,%d, parking the %dx%d bank and %d tile(s) within %d "
                  "for %dm"
                  % (API.Player.X, API.Player.Y, bank, bank, parked, reach,
                     max(1, int(round(self._config["respawn_delay"] / 60.0)))))

        return parked

    def survey(self, radius, limit):
        survey(self._terrain.box(radius), radius, limit, self.matches, self._log)


# src/uo/roam.py
class Roam(object):
    """Walking to the next spot, and waiting where there is nothing left but a clock."""

    def __init__(self, source, memory, saves, threat, config, log, heartbeat, stop_reason):
        self._source = source
        self._memory = memory
        self._saves = saves
        self._threat = threat
        self._config = config
        self._log = log
        self._heartbeat = heartbeat
        self._stop_reason = stop_reason
        self._walking_to = None
        self._walking_cycles = 0

    def _idle_until(self, ready_at):
        self._log(self._config["idle_message"])
        said_at = now()

        while now() < ready_at:
            if self._stop_reason() is not None:
                return

            self._threat.look()

            if now() - said_at >= self._config["idle_log_every"]:
                said_at = now()
                self._log("%dm to go" % max(1, int(round((ready_at - now()) / 60.0))))

            API.Pause(self._config["idle_poll"])

        self._heartbeat.reset()

    # One of ('target', spot), ('walked',), ('waited',), ('stop', reason)
    def approach(self):
        spot, ready_at_or_none = self._source.scan()

        if spot is None:
            if ready_at_or_none is not None:
                self._idle_until(ready_at_or_none)

                return ("waited",)

            # A match with no way to walk to it is the one cause the survey below cannot show
            if self._source.skipped_unreachable() > 0:
                self._log("%d %s(s) matched but had no walkable route"
                          % (self._source.skipped_unreachable(), self._config["noun"]))

            self._log("nothing within %dz of %d matched, here is what is around"
                      % (self._config["z_range"], API.Player.Z))
            self._source.survey(self._config["scan_radius"], self._config["survey_arts"])

            return ("stop", self._config["none_left"])

        if spot["distance"] <= self._config["range"]:
            self._walking_to = None
            self._walking_cycles = 0

            return ("target", spot)

        key = "%d,%d" % (spot["x"], spot["y"])

        if self._walking_to != key:
            self._walking_to = key
            self._walking_cycles = 0

        self._walking_cycles += 1

        if self._walking_cycles > self._config["max_walks"]:
            self._memory.mark_unreachable(spot)
            self._walking_to = None
            self._walking_cycles = 0

            return ("walked",)

        before = spot["distance"]
        API.Pathfind(spot["x"], spot["y"], spot["z"], self._config["range"], True,
                     self._config["pathfind_timeout"])
        API.CancelPathfinding()

        # A step that does not move during a save is not a wall
        if chebyshev_to(spot) >= before and not self._saves.is_saving():
            self._memory.mark_unreachable(spot)
            self._walking_to = None
            self._walking_cycles = 0

        return ("walked",)


# src/uo/tiles.py
# Land and static tiledata are numbered in separate tables, so 1339 is a mountain band as land and a
# cave floor as a static. Everything keyed on an art keys on the kind too.
def art_key(graphic, is_land):
    return "%s:%d" % ("land" if is_land else "static", graphic)


def tile_key(tile):
    return "%d,%d,%d,%s" % (tile["x"], tile["y"], tile["z"],
                            art_key(tile["graphic"], tile["is_land"]))


class TileMemory(object):
    """What is worked out, what could not be reached, and which art is not the resource at all."""

    def __init__(self, respawn_delay, unreachable_delay, noun, verb, log):
        self._respawn_delay = respawn_delay
        self._unreachable_delay = unreachable_delay
        self._noun = noun
        self._verb = verb
        self._log = log
        self._blocked = {}
        self._banned_arts = set()

    def blocked_until(self, tile):
        return self._blocked.get(tile_key(tile))

    def is_blocked(self, tile):
        until = self.blocked_until(tile)

        return until is not None and now() < until

    def block(self, tile, until):
        self._blocked[tile_key(tile)] = until

    def mark_depleted(self, tile):
        self.block(tile, now() + self._respawn_delay)

    def mark_unreachable(self, tile):
        self.block(tile, now() + self._unreachable_delay)

    def mark_unusable(self, tile, why):
        self.block(tile, float("inf"))
        self._log("the %s at %d,%d %s" % (self._noun, tile["x"], tile["y"], why))

    def art_banned(self, graphic, is_land):
        return art_key(graphic, is_land) in self._banned_arts

    # About the art, not the tile: a wrong entry in the table is a whole band of the mountain
    def ban_art(self, tile):
        key = art_key(tile["graphic"], tile["is_land"])

        if key in self._banned_arts:
            return

        self._banned_arts.add(key)
        self._log("%s cannot be %s, skipping that art from here on"
                  % (hex_of(tile["graphic"]), self._verb))


# src/uo/terrain.py
def land_tile(x, y, land):
    return {"x": x, "y": y, "z": land.Z, "graphic": land.Graphic, "is_land": True, "name": ""}


def static_tile(x, y, static):
    return {"x": x, "y": y, "z": static.Z, "graphic": static.Graphic, "is_land": False,
            "name": static.Name or ""}


class Terrain(object):
    """Land and statics do not change during a session, so a coordinate is read once. Every read is
    a client frame, which is why the statics of a box come in one call and the land only on demand."""

    def __init__(self):
        self._land = {}
        self._statics = {}
        self.reads = 0

    def _land_at(self, x, y):
        cached = self._land.get((x, y))

        if cached is None:
            self.reads += 1
            land = API.GetTile(x, y)
            cached = [land_tile(x, y, land)] if land is not None else []
            self._land[(x, y)] = cached

        return cached

    def _statics_at(self, x, y):
        cached = self._statics.get((x, y))

        if cached is None:
            self.reads += 1
            cached = [static_tile(x, y, static) for static in API.GetStaticsAt(x, y) or []]
            self._statics[(x, y)] = cached

        return cached

    def _fill_statics(self, x1, y1, x2, y2):
        missing = [(x, y) for x in range(x1, x2 + 1) for y in range(y1, y2 + 1)
                   if (x, y) not in self._statics]

        if not missing:
            return

        self.reads += 1
        by_coord = {}

        for static in API.GetStaticsInArea(x1, y1, x2, y2) or []:
            by_coord.setdefault((static.X, static.Y), []).append(static)

        for x, y in missing:
            self._statics[(x, y)] = [static_tile(x, y, static)
                                     for static in by_coord.get((x, y), [])]

    def at(self, x, y):
        return self._land_at(x, y) + self._statics_at(x, y)

    def _bounds(self, radius):
        return (API.Player.X - radius, API.Player.Y - radius,
                API.Player.X + radius, API.Player.Y + radius)

    def statics_box(self, radius):
        x1, y1, x2, y2 = self._bounds(radius)
        self._fill_statics(x1, y1, x2, y2)

        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                for tile in self._statics[(x, y)]:
                    yield tile

    def box(self, radius):
        x1, y1, x2, y2 = self._bounds(radius)
        self._fill_statics(x1, y1, x2, y2)

        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                for tile in self._land_at(x, y):
                    yield tile

                for tile in self._statics[(x, y)]:
                    yield tile


# src/mining/index.py
run = Run("mining")

log = run.log
heartbeat = run.heartbeat
stall = run.stall
stop_reason = run.stop_reason
saves = run.saves
pickaxe = run.pickaxe
ore = run.ore
combiner = run.combiner
beetle = run.beetle
smelter = run.smelter
threat = run.threat
get_off_the_mount = run.get_off_the_mount
say_where_we_stand = run.say_where_we_stand

memory = TileMemory(RESPAWN_DELAY, UNREACHABLE_DELAY, "vein", "mined", log)
veins = Veins(Terrain(), memory, {
    "tile_graphics": ORE_TILE_GRAPHICS,
    "not_ore_graphics": NOT_ORE_GRAPHICS,
    "static_names": ORE_STATIC_NAME,
    "z_range": MINE_Z_RANGE,
    "range": MINE_RANGE,
    "scan_radius": SCAN_RADIUS,
    "probes": MAX_PATH_PROBES,
    "respawn_delay": RESPAWN_DELAY,
    "bank": HARVEST_BANK,
}, log)
roam = Roam(veins, memory, saves, threat, {
    "noun": "vein",
    "idle_message": "everything in reach is worked out, waiting for a vein to come back",
    "none_left": "no ore in range",
    "range": MINE_RANGE,
    "scan_radius": SCAN_RADIUS,
    "z_range": MINE_Z_RANGE,
    "survey_arts": SURVEY_ARTS,
    "max_walks": MAX_VEIN_WALKS,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "idle_poll": IDLE_POLL,
    "idle_log_every": IDLE_LOG_EVERY,
}, log, heartbeat, stop_reason)
digger = Digger(ore, OUTCOME_TEXT, run.dig_config, log, True)
relief = Relief(ore, combiner, smelter, saves, beetle.walk_to, "", log)

say_where_we_stand()

# Before the cursor, so the beetle you click is one standing next to you rather than the one you are
# sitting on
afoot = get_off_the_mount()

if PICK_BEETLE:
    beetle.pick()

# A pack that arrives full has no room for the first swing's ore. Smelting only once off the mount:
# a smelt aimed at the beetle you ride is silent, and three silent passes write the hue off.
combiner.group()

if afoot and too_heavy():
    relief.smelt()

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
cycle_started = now()
spent = {}


def describe_spent():
    parts = []

    if "walk" in spent:
        scan = veins.stats
        parts.append("scan %.1fs (%d reads, %d probes, %d walled), walk %.1fs"
                     % (scan.get("seconds", 0.0), scan.get("reads", 0), scan.get("probes", 0),
                        scan.get("walled", 0), spent["walk"]))

    for name in ["smelt", "dig", "after"]:
        if spent.get(name, 0.0) >= 0.1:
            parts.append("%s %.1fs" % (name, spent[name]))

    return ", ".join(parts) or "nothing timed"


def end_cycle(phase):
    global stop

    stall.end_cycle(phase, cycle, tally)
    total = now() - cycle_started

    if total >= SLOW_CYCLE:
        log("slow cycle, %.1fs - %s" % (total, describe_spent()))

    if stop is None:
        stop = stall.reason()


try:
    while stop is None and cycle - idled < MAX_CYCLES:
        cycle += 1
        cycle_started = now()
        spent.clear()

        stop = stop_reason()

        if stop is not None:
            break

        # Everything below reads a frozen shard as its own failure: a step that does not move is a
        # wall, a smelt that converts nothing is ore that cannot be worked
        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        threat.look()

        # Asked every cycle, so a remount costs a single cycle instead of the rest of the run
        if not get_off_the_mount():
            stop = "could not get off the mount"
            break

        if not pickaxe.equip():
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = "no pickaxe"
                break

            log("no pickaxe (%d/%d), looking again" % (no_tool, MAX_NO_TOOL))
            end_cycle("no tool")
            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
            continue

        no_tool = 0

        started = now()
        relieved = relief.smelt_for_room()
        spent["smelt"] = now() - started

        if relieved is not None:
            if isinstance(relieved, dict):
                stop = relieved["stop"]
                break

            end_cycle(relieved)
            API.Pause(STEP_DELAY)
            continue

        started = now()
        found = roam.approach()
        spent["walk"] = now() - started - veins.stats.get("seconds", 0.0)

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

        ore_before = ore.total()
        started = now()
        outcome = digger.dig_once(pickaxe.serial())
        spent["dig"] = now() - started
        started = now()

        if outcome == "dug":
            tally += 1
            unknown = 0
            throttled = 0
            barren = 0
            stall.progressed()

            # Ore arrives as a new pile after the sentence that announced it, so grouping every
            # swing keeps the pack at one pile per metal and the item cap out of reach
            ore.wait_for_ore(ore_before, ORE_SETTLE_TIMEOUT, ORE_SETTLE_POLL)
            combiner.group()

        elif outcome == "wornOut":
            log("pickaxe worn out, swapping")
            unknown = 0

        elif outcome == "saving":
            saves.wait_out()
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
            memory.mark_depleted(vein)
            relief.group_and_smelt()

        # The shard answering about where you stand rather than about a tile
        elif outcome == "nothingNearby":
            unknown = 0
            veins.mark_area_depleted(MINE_RANGE)
            barren += 1

            # Said once, at the point it stops looking like bad luck
            if barren == NOTHING_NEARBY_HINT:
                log(
                    "%d spots in a row had nothing to harvest - ORE_TILE_GRAPHICS is probably "
                    "matching ground that carries no ore" % NOTHING_NEARBY_HINT
                )
                veins.survey(MINE_RANGE, SURVEY_ARTS)

            relief.group_and_smelt()

        # A wrong band in ORE_TILE_GRAPHICS is a whole stretch of mountain, so ban the art rather
        # than walking to its copies one at a time
        elif outcome == "notOre":
            unknown = 0
            memory.ban_art(vein)
            memory.mark_unusable(vein, "cannot be mined")

        elif outcome == "tooFar":
            unknown = 0
            memory.mark_unusable(vein, "is out of reach at %d tiles" % vein["distance"])

        elif outcome == "notSeen":
            unknown = 0
            memory.mark_unusable(vein, "is not in line of sight")

        # The ore this swing produced was destroyed rather than dropped, so a full pack is answered
        # by consolidating: forty piles of one become one pile of forty
        elif outcome == "packFull":
            unknown = 0
            log("pack is full, consolidating before the next swing")
            combiner.group()

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

        spent["after"] = now() - started

        if tally >= reported + LOG_EVERY:
            reported = tally
            log(
                "%d swings, %d ore, %d/%d"
                % (tally, ore.total(), API.Player.Weight, API.Player.WeightMax)
            )

        end_cycle(outcome if outcome is not None else "unknown")
        API.Pause(STEP_DELAY)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error

if API.Pathfinding():
    API.CancelPathfinding()

reason = stop or "hit the %d working cycle backstop" % MAX_CYCLES

# Smelted only if the run is ending over the limit: what is in the pack is a few swings' worth
combiner.group()

if too_heavy():
    relief.smelt()

# Swings rather than an ore delta: smelted ore has left the pack, so the pack cannot total the run
log("%d swings, %d ore still in the pack" % (tally, ore.total()))
log("stopping - %s" % reason)
API.Stop()
