# Built from src/mining/index.py by build.py - do not edit.

import API
import time


# src/uo/notoriety.py
"""Passed through to the scans, never compared or OR-ed: the API.py stub lists every value as 1."""

# Innocent is out, or every blue NPC in the world is trouble
HOSTILE = [
    API.Notoriety.Gray,
    API.Notoriety.Criminal,
    API.Notoriety.Enemy,
    API.Notoriety.Murderer,
]

# Gray is out: the wildlife is gray, and a cat wandering past is not evidence of anything. A gray
# still draws the call the moment it damages you or the pet.
CALL_ON_SIGHT = [
    API.Notoriety.Criminal,
    API.Notoriety.Enemy,
    API.Notoriety.Murderer,
]


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

NO_GUARDS_TEXT = [
    "The guards can not be called here",
    "The guards cannot be called here",
    "Guards can not be called here",
    "Guards cannot be called here",
    "There are no guards here",
    "guards cannot be summoned here",
]

GUARD_ZONE_TEXT = ["under the protection of the town guards", "now under guard"]
UNGUARDED_TEXT = ["left the protection of the town guards", "no longer under guard"]

# Empty on purpose: nothing in stock RunUO announces being attacked, and a wrong guess calls the
# guards every cycle of a quiet run
ATTACK_TEXT = []


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

MAX_CYCLES = 5000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_CURSOR = 20
MAX_NO_TOOL = 10

# Spots in a row with nothing in them before the run says ORE_TILE_GRAPHICS is probably wrong
NOTHING_NEARBY_HINT = 5

WATCH_FOR_TROUBLE = True

THREAT_RANGE = 12
GUARD_CALL = "guards"
GUARD_CALLS = 3
GUARD_CALL_DELAY = 10.0
GUARD_REPLY_WAIT = 0.8

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


def matched_bucket(buckets):
    for name, phrases in buckets:
        # clearMatches, or a line already read answers the next wait as well
        if API.InJournalAny(phrases, True):
            return name

    return None


def read_outcome(buckets, budget, poll, between=None):
    waited = 0.0

    while True:
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
        API.ClearJournal()

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


# src/uo/clock.py
def now():
    return time.time()


# src/uo/scan.py
def chebyshev_to(tile):
    return max(abs(tile["x"] - API.Player.X), abs(tile["y"] - API.Player.Y))


def steps_to(tile, within):
    path = API.GetPath(tile["x"], tile["y"], tile["z"], within)

    return len(path) if path else None


# GetPath costs a call per candidate, where the web client's flood fill answered every tile at once,
# so only the nearest `probes` matches are asked for a route
def pick_nearest(candidates, memory, probes, within):
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
        steps = steps_to(tile, within)

        if steps is None:
            walled += 1
            continue

        if best_steps is None or steps < best_steps:
            best = tile
            best_steps = steps

    if best is not None:
        best = dict(best)
        best["distance"] = chebyshev_to(best)

    return best, cooling, walled


# src/mining/roam.py
class Roam(object):
    """Walking to the next vein, and waiting where there is nothing left but a clock."""

    def __init__(self, veins, memory, saves, threat, config, log, heartbeat, stop_reason):
        self._veins = veins
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
        self._log("everything in reach is worked out, waiting for a vein to come back")
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

    # One of ('target', vein), ('walked',), ('waited',), ('stop', reason)
    def approach(self):
        vein, respawns_at = self._veins.scan()

        if vein is None:
            if respawns_at is not None:
                self._idle_until(respawns_at)

                return ("waited",)

            # Ore that matched everything and had no way to walk to it is the one cause the survey
            # below cannot show
            if self._veins.skipped_unreachable() > 0:
                self._log("%d vein(s) matched but had no walkable route"
                          % self._veins.skipped_unreachable())

            self._log("nothing within %dz of %d matched, here is what is around"
                      % (self._config["z_range"], API.Player.Z))
            self._veins.survey(self._config["scan_radius"], self._config["survey_arts"])

            return ("stop", "no ore in range")

        if vein["distance"] <= self._config["range"]:
            self._walking_to = None
            self._walking_cycles = 0

            return ("target", vein)

        key = "%d,%d" % (vein["x"], vein["y"])

        if self._walking_to != key:
            self._walking_to = key
            self._walking_cycles = 0

        self._walking_cycles += 1

        if self._walking_cycles > self._config["max_walks"]:
            self._memory.mark_unreachable(vein)
            self._walking_to = None
            self._walking_cycles = 0

            return ("walked",)

        before = vein["distance"]
        API.Pathfind(vein["x"], vein["y"], vein["z"], self._config["range"], True,
                     self._config["pathfind_timeout"])
        API.CancelPathfinding()

        # A step that does not move during a save is not a wall
        if chebyshev_to(vein) >= before and not self._saves.is_saving():
            self._memory.mark_unreachable(vein)
            self._walking_to = None
            self._walking_cycles = 0

        return ("walked",)


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

        API.ClearJournal()

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
        self._opl_timeout = config["opl_timeout"]
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

        props = API.ItemNameAndProps(serial, True, self._opl_timeout) or ""
        name = (item.Name or "").strip()

        # A miss is an unanswered tooltip, which here is an empty string or one carrying only the
        # name - the structured OPL this was ported from reported it as an empty property list
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

        while True:
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


# src/mining/smelt.py
class Smelter(object):
    def __init__(self, ore, beetle, combiner, saves, config, log):
        self._ore = ore
        self._beetle = beetle
        self._combiner = combiner
        self._saves = saves
        self._config = config
        self._log = log

        self._written_off = set()
        self._misses = {}
        # Whether anything has converted since the last retry. Without it a retry granted
        # unconditionally answers true again next cycle and the caller loops until the watchdog ends
        self._progressed = True
        self._forge = None
        self._reported_no_beetle = False

    def written_off(self):
        return self._written_off

    def _counts(self):
        return counts_by_graphic(pack_contents())

    # Every failing path comes through here: one that returns without counting leaves the candidate
    # set unchanged, so the next pass picks the same stack and the loop runs to its backstop
    def _missed(self, hue):
        count = self._misses.get(hue, 0) + 1
        self._misses[hue] = count

        if count >= self._config["attempts"]:
            self._written_off.add(hue)
            self._log("hue %d failed %d times, leaving it as ore" % (hue, count))

    def _learn_ingot(self, gained):
        for graphic, _hue in gained:
            if graphic in self._config["ore_graphics"]:
                continue

            if graphic in self._config["ingot_graphics"]:
                continue

            self._config["ingot_graphics"].add(graphic)
            self._log("ingot graphic is %s" % hex_of(graphic))

    # The action throttle can hold a conversion well past any pause worth taking, and reading too
    # early is indistinguishable from a resource that cannot be worked
    def _wait_for_change(self, before):
        waited = 0.0

        while waited < self._config["timeout"]:
            API.Pause(self._config["poll"])
            waited += self._config["poll"]

            gained, lost = diff_counts(before, self._counts())

            if gained or lost:
                return gained

        return None

    # The journal is cleared to perform the smelt, so a save that starts mid-attempt is past the
    # check at the top of the pass: one cost three hues and ended a live run overweight beside a
    # working beetle
    def _saving(self, hue):
        if not self._saves.is_saving():
            return False

        self._log("the world is saving, not counting it against hue %d" % hue)

        return True

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

        API.ClearJournal()
        API.UseObject(stack.Serial)

        if not API.WaitForTarget("any", self._config["target_timeout"]):
            API.CancelTarget()
            self._log("no target cursor for the beetle")

            return False

        API.Target(self._forge.Serial)

        return True

    def _convert_one(self, stack):
        hue = hue_of(stack)
        before = self._counts()

        if not self._perform(stack):
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
            self._learn_ingot(gained)

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
            self._log("not skilled enough for hue %d, leaving it as ore" % hue)

            return

        # Otherwise it was silent, which is also what a throttled or stale attempt looks like
        self._missed(hue)

    def _run(self):
        for _pass in range(self._config["passes"]):
            # A frozen shard answers a conversion the same way an unworkable material does, so
            # without this a world save costs the attempts and writes the hue off for the run
            if self._saves.is_saving():
                self._log("the world is saving, leaving it for now")

                return False

            stack = self._ore.next_ore(self._written_off)

            if stack is None:
                piles = self._ore.piles()

                if len(piles) > 0:
                    described = [self._ore.describe_skipped(pile, self._written_off)
                                 for pile in piles]
                    self._log("nothing to smelt in %d pile(s) - %s"
                              % (len(piles), ", ".join(described)))

                return True

            # Asked only once there is something that needs it, which is what makes smelting on
            # every dry vein affordable
            blocked = self._forge_gone()

            if blocked is not None:
                self._log("%s, leaving it for now" % blocked)

                return False

            self._convert_one(stack)
            API.Pause(self._config["delay"])

        self._log("hit the %d smelt pass backstop" % self._config["passes"])

        return False

    def retry_written_off(self, force=False):
        if len(self._written_off) == 0 or (not self._progressed and not force):
            return False

        self._progressed = False
        self._log("giving %d hue(s) written off earlier another go" % len(self._written_off))
        self._written_off.clear()
        self._misses.clear()

        return True

    def smelt_against(self, reach):
        # Asked before the beetle is looked for, so a pack with nothing eligible costs neither a
        # search nor a walk
        if self._ore.next_ore(self._written_off) is None:
            return self._run()

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

        return self._run()


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

        API.ClearJournal()

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
    def __init__(self, config, log, companion, friend_noun):
        self._config = config
        self._log = log
        self._companion = companion
        self._friend_noun = friend_noun
        self._last_hits = 0
        self._last_companion_hits = 0
        self._last_call = 0.0
        self._calls = 0
        self._in_episode = False
        self._no_guards = False
        self._said_protection = False
        self._zone = None

    def _read_zone(self):
        if said(self._config["zone_text"]):
            self._zone = "guarded"
        elif said(self._config["unguarded_text"]):
            self._zone = "unguarded"

    # Nothing in the API answers this. A yellow human is a guard or a vendor, and either one means a
    # town, which is the best the client can be asked.
    def _protection(self):
        if self._zone is not None:
            return "the journal says %s" % self._zone

        seen = API.GetAllMobiles(None, self._config["range"], [API.Notoriety.Invulnerable]) or []

        for mobile in seen:
            if mobile.IsHuman and not mobile.IsDead:
                return "an invulnerable '%s' in sight, so probably a town" % (mobile.Name or "?")

        return "nothing in sight to say either way"

    def _call_guards(self):
        limit = self._config["calls"]

        if self._no_guards or (limit > 0 and self._calls >= limit):
            return

        at = now()

        if self._calls > 0 and at - self._last_call < self._config["call_delay"]:
            return

        self._last_call = at
        self._calls += 1

        if not self._said_protection:
            self._said_protection = True
            self._log("guard protection - %s" % self._protection())

        self._log("calling the guards (%d%s)" % (self._calls, "/%d" % limit if limit > 0 else ""))
        API.Msg(self._config["call"])

        refusals = self._config["no_guards_text"]

        if not refusals:
            return

        wait = self._config["reply_wait"]

        if read_outcome([("refused", refusals)], wait, wait) is not None:
            self._no_guards = True
            self._log("the shard says the guards cannot be called here - not calling again this run")

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
            theirs = ", %s %d/%s" % (self._friend_noun, friend.Hits, friend.HitsMax or "?")

        return "%s, %s%s" % (who, mine, theirs)

    def look(self):
        if not self._config["watch"]:
            return

        self._read_zone()

        hits = API.Player.Hits
        hurt = dropped(self._last_hits, hits)

        if hits > 0:
            self._last_hits = hits

        friend = self._companion()
        friend_hits = friend.Hits if friend is not None else 0
        friend_hurt = dropped(self._last_companion_hits, friend_hits)

        if friend_hits > 0:
            self._last_companion_hits = friend_hits

        attack_text = self._config["attack_text"]
        attacked = said(attack_text) if attack_text else False
        hostile = hostiles_near(HOSTILE, self._config["range"])

        if hostile is None and not hurt and not friend_hurt and not attacked:
            if self._in_episode:
                self._in_episode = False
                self._calls = 0
                self._log("clear")

            return

        if not self._in_episode:
            self._in_episode = True
            self._log("trouble - %s" % self._describe(hostile, friend))

        # Blood drawn is evidence whatever its notoriety; being in sight is only evidence for the
        # notorieties CALL_ON_SIGHT names
        on_sight = hostile is not None and hostile.Notoriety in CALL_ON_SIGHT

        if hurt or friend_hurt or attacked or on_sight:
            self._call_guards()


# src/uo/tool.py
class Tool(object):
    """Find it, learn its graphic, get it onto the hand, and notice when it breaks."""

    def __init__(self, name, layers, spare_bag, attempts, timeout, poll, log):
        self._name = name
        self._layers = layers
        self._spare_bag = spare_bag
        self._attempts = attempts
        self._timeout = timeout
        self._poll = poll
        self._log = log
        self._graphic = None
        self._reported_empty_pack = False

    def learn(self, item):
        if item is not None and self._graphic is None:
            self._graphic = item.Graphic
            self._log("%s graphic is %s" % (self._name, hex_of(item.Graphic)))

    def is_tool(self, item):
        if item is None:
            return False

        if self._graphic is not None and item.Graphic == self._graphic:
            return True

        return self._name in (item.Name or "").lower()

    def held(self):
        for layer in self._layers:
            found = API.FindLayer(layer)

            if found is not None:
                return found

        return None

    def serial(self):
        item = self.held()

        return item.Serial if item is not None else None

    def find(self):
        for item in pack_contents():
            if self.is_tool(item):
                self._reported_empty_pack = False
                self.learn(item)

                return item

        if self._spare_bag is not None:
            for item in API.ItemsInContainer(self._spare_bag, True) or []:
                if self.is_tool(item):
                    self._reported_empty_pack = False
                    self.learn(item)

                    return item

        if not self._reported_empty_pack:
            self._reported_empty_pack = True
            arts = [hex_of(item.Graphic) for item in pack_contents()]
            self._log("no %s found. Pack holds: %s" % (self._name, ", ".join(arts) or "nothing"))

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

        self._log("could not get the %s %s onto the hand" % (self._name, hex_of(serial)))

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
log = make_log("mining")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "swings", position_and_weight)
stall = StallWatch("cycles without a swing landing", STALL_WARN, STALL_STOP, heartbeat, log)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), pack_full(PACK_LIMIT)])


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

pickaxe = Tool(PICKAXE_NAME, ["onehanded"], SPARE_BAG_SERIAL, EQUIP_ATTEMPTS, EQUIP_TIMEOUT,
               EQUIP_POLL, log)
ore = OrePack(ORE_GRAPHICS, ORE_NAME_WORD, MIN_SMELT_AMOUNT, log)
metals = MetalBook({
    "metals": ORE_METALS,
    "plain": PLAIN_METAL,
    "line_extra": METAL_LINE_EXTRA,
    "not_metal_words": NOT_METAL_WORDS,
    "asks": METAL_ASKS,
    "misses": METAL_MISSES,
    "opl_timeout": OPL_TIMEOUT,
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
smelter = Smelter(ore, beetle, combiner, saves, {
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
    "call": GUARD_CALL,
    "calls": GUARD_CALLS,
    "call_delay": GUARD_CALL_DELAY,
    "reply_wait": GUARD_REPLY_WAIT,
    "no_guards_text": NO_GUARDS_TEXT,
    "zone_text": GUARD_ZONE_TEXT,
    "unguarded_text": UNGUARDED_TEXT,
    "attack_text": ATTACK_TEXT,
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


# src/uo/survey.py
# The dead-end report: what the run actually saw, so a wrong art table can be corrected from it
def survey(tiles, radius, limit, matches, log):
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

    def _candidates(self, radius):
        for tile in self._terrain.box(radius):
            if self.matches(tile) and self.within_z(tile["z"]):
                yield tile

    def scan_box(self, radius):
        best, cooling, walled = pick_nearest(self._candidates(radius), self._memory,
                                             self._config["probes"], self._config["range"])
        self._skipped_unreachable = walled

        return best, cooling

    # One pair of reads against the (2 * radius + 1) squared the box costs. The z and the art have
    # to match as well as the coordinates: a tile carries several, and only one of them is the vein.
    def _still_ore(self, vein):
        if self._memory.is_blocked(vein):
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

    # Widened rather than swept: a mountain face is wall-to-wall ore, so the tile that replaces a
    # worked out one is almost always within reach
    def scan(self):
        if self._current is not None:
            self._current = self._still_ore(self._current)

            if self._current is not None:
                return self._current, None

        near, _cooling = self.scan_box(self._config["range"])

        if near is not None:
            self._current = near

            return near, None

        found, cooling = self.scan_box(self._config["scan_radius"])
        self._current = found

        return found, cooling

    def forget_current(self):
        self._current = None

    # For the shard answering about where you stand rather than about a tile. Parking a single tile
    # left the character swinging at the spot the shard had just written off, for the same sentence.
    def mark_area_depleted(self, reach):
        until = now() + self._config["respawn_delay"]
        parked = 0

        for tile in self._terrain.box(reach):
            # The shard's sentence is about what it can reach, so parking a tile 60 z up would
            # record a claim it never made
            if not self.within_z(tile["z"]) or not self.matches(tile):
                continue

            self._memory.block(tile, until)
            parked += 1

        self._log("nothing harvestable at %d,%d, parking %d tile(s) within %d for %dm"
                  % (API.Player.X, API.Player.Y, parked, reach,
                     max(1, int(round(self._config["respawn_delay"] / 60.0)))))

        return parked

    def survey(self, radius, limit):
        survey(self._terrain.box(radius), radius, limit, self.matches, self._log)


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

    def __init__(self, respawn_delay, unreachable_delay, noun, log):
        self._respawn_delay = respawn_delay
        self._unreachable_delay = unreachable_delay
        self._noun = noun
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
        self._log("%s cannot be worked, skipping that art from here on" % hex_of(tile["graphic"]))


# src/uo/terrain.py
class Terrain(object):
    """Land and statics do not change during a session, so a coordinate costs one pair of calls."""

    def __init__(self):
        self._cache = {}

    def at(self, x, y):
        cached = self._cache.get((x, y))

        if cached is not None:
            return cached

        tiles = []
        land = API.GetTile(x, y)

        if land is not None:
            tiles.append({"x": x, "y": y, "z": land.Z, "graphic": land.Graphic,
                          "is_land": True, "name": ""})

        for static in API.GetStaticsAt(x, y) or []:
            tiles.append({"x": x, "y": y, "z": static.Z, "graphic": static.Graphic,
                          "is_land": False, "name": static.Name or ""})

        self._cache[(x, y)] = tiles

        return tiles

    def box(self, radius):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                for tile in self.at(API.Player.X + dx, API.Player.Y + dy):
                    yield tile


# src/mining/index.py
memory = TileMemory(RESPAWN_DELAY, UNREACHABLE_DELAY, "vein", log)
veins = Veins(Terrain(), memory, {
    "tile_graphics": ORE_TILE_GRAPHICS,
    "not_ore_graphics": NOT_ORE_GRAPHICS,
    "static_names": ORE_STATIC_NAME,
    "z_range": MINE_Z_RANGE,
    "range": MINE_RANGE,
    "scan_radius": SCAN_RADIUS,
    "probes": MAX_PATH_PROBES,
    "respawn_delay": RESPAWN_DELAY,
}, log)
roam = Roam(veins, memory, saves, threat, {
    "range": MINE_RANGE,
    "scan_radius": SCAN_RADIUS,
    "z_range": MINE_Z_RANGE,
    "survey_arts": SURVEY_ARTS,
    "max_walks": MAX_VEIN_WALKS,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "idle_poll": IDLE_POLL,
    "idle_log_every": IDLE_LOG_EVERY,
}, log, heartbeat, stop_reason)
digger = Digger(ore, OUTCOME_TEXT, DIG_CONFIG, log, True)
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

        relieved = relief.smelt_for_room()

        if relieved is not None:
            if isinstance(relieved, dict):
                stop = relieved["stop"]
                break

            end_cycle(relieved)
            API.Pause(STEP_DELAY)
            continue

        found = roam.approach()

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
        outcome = digger.dig_once(pickaxe.serial())

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

        if tally >= reported + LOG_EVERY:
            reported = tally
            log(
                "%d swings, %d ore, %d/%d"
                % (tally, ore.total(), API.Player.Weight, API.Player.WeightMax)
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
combiner.group()

if too_heavy():
    relief.smelt()

# Swings rather than an ore delta: smelted ore has left the pack, so the pack cannot total the run
log("%d swings, %d ore still in the pack" % (tally, ore.total()))
log("stopping - %s" % reason)
API.Stop()
