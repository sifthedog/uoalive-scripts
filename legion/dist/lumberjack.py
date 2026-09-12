# Built from src/lumberjacking/index.py by build.py - do not edit.

import API
import time
import clr
import System


# src/uo/log.py
# Every stamp make_log has handed out. The client puts a SysMsg in the journal beside the shard's
# own lines, so a script reading the journal back needs to know which of them it wrote itself -
# without this a report of an unreadable outcome quotes the last report of an unreadable outcome.
# Lowercase, because that is how the journal readers compare. One entry per script in practice.
STAMPS = []


def make_log(prefix):
    stamp = prefix + ": "

    if stamp.lower() not in STAMPS:
        STAMPS.append(stamp.lower())

    def log(message):
        API.SysMsg(stamp + message)

    return log


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
                return gained, lost

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

        changed = self._wait_for_change(before)

        if changed is not None:
            gained, lost = changed
            self._misses.pop(hue, None)
            self._progressed = True
            self._config["learn_product"](gained)
            self._config["converted"](gained, lost)

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


# src/uo/entity.py
# API.Player is None whenever the client is between world states - a recall, a server line change,
# the moment around a death - and reading through it threw a live restock away
def player():
    try:
        return API.Player
    except Exception:
        if API.StopRequested:
            raise

        return None


def hex_of(value):
    return "0x%x" % (value & 0xFFFFFFFF)


# src/lumberjacking/boards.py
class Boards(object):
    """The wood side of the converter: the axe is used and the log stack is the target."""

    def __init__(self, wood, tool, saves, config, log):
        self._wood = wood
        self._tool = tool
        self._config = config
        self._log = log
        self._reported_nothing = False

        self._converter = Converter({
            "noun": "logs",
            "attempts": config["attempts"],
            "passes": config["passes"],
            "delay": config["delay"],
            "timeout": config["timeout"],
            "poll": config["poll"],
            "throttled_text": config["throttled_text"],
            "unskilled_text": config["unskilled_text"],
            "wait_on_save": True,
            "saving_message": "the world is saving, leaving the logs for now",
            "next_source": self._next_log,
            "perform": self._perform,
            "blocked": self._no_axe_in_hand,
            "learn_product": self._learn_board,
            "converted": config["converted"],
            "nothing_to_do": self._say_nothing_to_convert,
            "about_to_convert": self._converting,
        }, log, saves)

    def _next_log(self, skip):
        for pile in self._wood.log_piles():
            if hue_of(pile) not in skip:
                return pile

        return None

    def _no_axe_in_hand(self):
        return "no axe in hand" if self._tool.serial() is None else None

    # The diff names the real board art, which is why the seed set can be wrong and corrects itself
    # on the first conversion
    def _learn_board(self, gained):
        for graphic, _hue in gained:
            if graphic in self._config["log_graphics"]:
                continue

            if graphic in self._config["board_graphics"]:
                continue

            self._config["board_graphics"].add(graphic)
            self._log("board graphic is %s" % hex_of(graphic))

    # Said once per stretch, not once a cycle: the haul fires at HAUL_BUFFER and stays true for a
    # long run of them
    def _say_nothing_to_convert(self, _written_off):
        piles = self._wood.log_piles()

        if len(piles) > 0 and not self._reported_nothing:
            self._reported_nothing = True
            self._log("nothing to convert in %d log pile(s)" % len(piles))

    # Logs become boards by using the axe and targeting the log stack - the inverse of smelting,
    # where the ore is used and the forge targeted
    def _perform(self, stack):
        serial = self._tool.serial()

        if serial is None:
            return False

        # No cancel unless there is one to cancel: an unconditional cancel shortly before the action
        # leaves the cursor that follows unusable
        if API.HasTarget():
            API.CancelTarget()

        forget(self._config["throttled_text"] + self._config["unskilled_text"])
        API.UseObject(serial)

        if not API.WaitForTarget("any", self._config["target_timeout"]):
            API.CancelTarget()
            self._log("no target cursor for the logs, nothing usable in hand?")

            return False

        # The one-argument overload: an item serial, not the tile form the chop uses
        API.Target(stack.Serial)

        return True

    def _converting(self):
        self._reported_nothing = False
        self._config["about_to_convert"]()

    def run(self):
        return self._converter.run()

    # Forced, unlike mining's progress-gated retry: only boards ever go onto an animal, so a log
    # given up on to a lost cursor or a broken axe would ride out the whole run as weight. The
    # verdict is a backstop for one pass, never for the run.
    def make_boards(self):
        self._converter.retry_written_off(True)

        return self._converter.run()


# src/lumberjacking/chop.py
class Chopper(object):
    def __init__(self, wood, tool, buckets, config, log):
        self._wood = wood
        self._tool = tool
        self._buckets = buckets
        self._config = config
        self._log = log

    def _silent_outcome(self, serial, logs_before):
        if serial is not None and API.FindItem(serial) is None:
            return "wornOut"

        if self._wood.log_total() > logs_before:
            return "chopped"

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
    def _refused_outcome(self, serial, logs_before):
        matched = read_outcome(self._buckets, self._config["no_cursor_read"],
                               self._config["cursor_poll"])

        if matched is not None:
            return matched

        silent = self._silent_outcome(serial, logs_before)

        if silent != "unknown":
            return silent

        held = self._tool.held()
        self._log("no target cursor - hand %s, the shard never asked where to chop"
                  % ((held.Name or hex_of(held.Graphic)) if held is not None else "empty"))

        return "noCursor"

    def chop_once(self, serial, tree):
        # A pathfind still running would walk the character away mid-swing
        if API.Pathfinding():
            API.CancelPathfinding()

        # Cancelled only when there is one to cancel: an unconditional cancel a few hundred
        # milliseconds before the swing left the next cursor unusable in the run this was copied
        # from
        if API.HasTarget():
            API.CancelTarget()

        logs_before = self._wood.log_total()
        forget(self._config["prompt_text"])
        forget_outcomes(self._buckets)

        API.UseObject(serial)

        if not self._cursor_opened():
            return self._refused_outcome(serial, logs_before)

        if self._config["aim_at_self"]:
            # This shard takes a self-target as 'harvest what is in reach' and picks the tree
            # itself, so nothing has to name a static. The scan still earns its place: it is what
            # decides where to stand, and 'in reach' is only ever the trunk you walked to.
            API.TargetSelf()
        else:
            # The four-argument overload, and the graphic is never left off: target.terrain with no
            # art hits the land tile, which the shard answers as mining rather than as chopping. A
            # static carries no serial, so naming the tile and its art is the only other way in.
            API.Target(tree["x"], tree["y"], tree["z"], tree["graphic"])

        matched = read_outcome(self._buckets, self._config["chop_timeout"],
                               self._config["cursor_poll"])

        return matched if matched is not None else self._silent_outcome(serial, logs_before)


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


# src/lumberjacking/config.py
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

# How long a swing's logs are waited for, which land after the sentence announcing them
LOG_SETTLE_TIMEOUT = 1.5
LOG_SETTLE_POLL = 0.15

# Where each chop and each conversion is appended, while Lumberjacking is below its cap. A bare
# filename lands in TazUO's working directory; "" records nothing
DATA_PATH = "skill-attempts.jsonl"

SKILL_NAMES = ["Lumberjacking"]
SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25

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

# Boards a pack animal takes before it refuses the next one, seen on UOAlive. A stack bigger than
# what is left is refused whole, so the haul moves only the slice that still fits.
PACK_ANIMAL_BOARDS = 1600

PACK_OPEN_DELAY = 0.6

# Also what the shard says to a board dropped on an animal that walked off mid-load
TOO_FAR_TEXT = ["That is too far away", "You cannot reach that"]

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

IDLE_POLL = 10.0
IDLE_LOG_EVERY = 60.0

MAX_CYCLES = 5000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_CURSOR = 20
MAX_NO_TOOL = 10

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

# The run stands still behind a gump until its button is pressed - no swing, no walk - with the
# alarm restarting all the while
AMBUSH_HOLD = True
AMBUSH_HOLD_TEXT = "You have been ambushed. Press the button when it is safe"
AMBUSH_HOLD_BUTTON = "Resume"
AMBUSH_HOLD_HUE = 33
AMBUSH_HOLD_POLL = 0.5


# Ordered, not a dict: InJournalAny answers yes/no, so the buckets are polled in order and the first
# holding a match wins. Guesses for a RunUO-family shard - correct them against the real journal.
OUTCOME_TEXT = [
    ("chopped", ["You put", "You chop some"]),
    # RunUO's 'You hack at the tree for a while, but fail to produce any useable wood': a swing that
    # landed and delivered nothing
    ("failed", ["You hack at the tree"]),
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
    ("tooFar", TOO_FAR_TEXT),
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


# src/uo/weight.py
# Unknown is not overweight, the same call WeightMax == 0 gets: WeightMax reads 0 before the client
# has been told, against which every weight is overweight - a live mining run ended at 436/453 on it
def over_buffer(buffer):
    me = player()

    if me is None:
        return False

    ceiling = me.WeightMax

    return ceiling > 0 and me.Weight > ceiling - buffer


# src/lumberjacking/haul.py
class Haul(object):
    """Getting the boards onto the pack animals, and knowing when they will take no more."""

    def __init__(self, wood, boards, saves, config, log):
        self._wood = wood
        self._boards = boards
        self._saves = saves
        self._config = config
        self._log = log

        # A list chosen rather than guessed - from config or from the cursor - is the law, so an
        # animal out of sight for a moment is not a reason to go loading a stranger's mule
        self._pinned = list(config["serials"])
        self._reported_animals = False
        self._reported_no_animal = False

        # Kept from the last search so the trouble watch can re-resolve one mobile rather than
        # paying a GetAllMobiles per body every cycle
        self._last_serial = None

        # Never cleared: what empties a pack horse is a trip to the bank, and that ends the run
        self._overloaded = set()
        self._opened = set()
        self._said_all_full = False
        self._hauling = True
        self._empty_hauls = 0

    def hauling(self):
        return self._hauling

    def pick(self):
        if API.Player.IsMounted:
            self._log("you are mounted - dismount first if the animal you want is the one you "
                      "are riding")

        self._log("target the pack animals to load, ESC when done")

        picked = []

        for _pick in range(self._config["max_picks"]):
            if API.HasTarget():
                API.CancelTarget()

            serial = API.RequestTarget(self._config["pick_timeout"])

            # Falsy is ESC or a cursor that timed out, and either one ends the selection
            if not serial:
                break

            animal = API.FindMobile(serial)

            # Not an ending: a misclick on the ground should cost the click and nothing more
            if animal is None:
                self._log("%s is not a mobile" % hex_of(serial))
                continue

            if serial in picked:
                continue

            # Not a refusal either: the graphics table is a guess at this shard, so a body it has
            # never heard of is worth reporting and then using
            if animal.Graphic not in self._config["graphics"]:
                self._log("%s is not a body PACK_ANIMAL_GRAPHICS knows, using it anyway"
                          % hex_of(animal.Graphic))

            picked.append(serial)
            self._log("picked '%s' %s" % (animal.Name or "?", hex_of(serial)))

        if API.HasTarget():
            API.CancelTarget()

        if len(picked) == 0:
            self._log("nothing picked, looking for the animals instead")

            return []

        self._pinned = picked

        return picked

    def find(self):
        found = []

        if len(self._pinned) > 0:
            # A pinned serial can be hand-written, so check what came back rather than trusting it
            for serial in self._pinned:
                animal = API.FindMobile(serial)

                if animal is not None and not animal.IsDead:
                    found.append(animal)
        else:
            for graphic in self._config["graphics"]:
                for animal in API.GetAllMobiles(graphic, self._config["radius"]) or []:
                    if not animal.IsDead:
                        found.append(animal)

            # Only your own pets can be renamed, so this is what tells yours from a stranger's
            mine = [animal for animal in found if animal.IsRenamable]

            if len(mine) > 0:
                found = mine

        if len(found) == 0:
            return []

        if not self._reported_animals:
            self._reported_animals = True
            names = ", ".join("'%s'" % (animal.Name or "?") for animal in found)
            self._log("%d pack animal(s) - %s" % (len(found), names))

        # Nearest first, so the closest one fills before you walk past it to another
        found.sort(key=lambda animal: animal.Distance)
        self._last_serial = found[0].Serial

        return found

    def companion(self):
        return API.FindMobile(self._last_serial) if self._last_serial is not None else None

    # A pet's coordinates go stale within a cycle, so the serial is re-resolved rather than the
    # find result trusted
    def _walk_to(self, serial):
        here = API.FindMobile(serial)

        if here is None:
            self._log("lost track of %s" % hex_of(serial))

            return None

        if here.Distance <= self._config["unload_range"]:
            return here

        API.PathfindEntity(serial, self._config["unload_range"], True,
                           self._config["pathfind_timeout"])
        API.CancelPathfinding()

        here = API.FindMobile(serial)

        if here is None:
            self._log("lost track of %s" % hex_of(serial))

            return None

        if here.Distance > self._config["unload_range"]:
            self._log("could not get within %d of '%s', it is %d tiles off"
                      % (self._config["unload_range"], here.Name or "?", here.Distance))

            return None

        return here

    # Two independent reads, and no double-click fallback: the web client had only the layer, and
    # its fallback is a UseObject on a rideable giant beetle, which mounts you. Nothing in this file
    # dismounts, so a mount here would cost the rest of the run.
    def _animal_pack(self, animal):
        pack = getattr(animal, "Backpack", None)

        if pack is not None:
            return pack

        return API.FindLayer("backpack", animal.Serial)

    # Opened once a run: ItemsInContainer reads nothing out of a pack the client has never seen
    # inside, and the pack item is safe to double-click where the animal itself is not
    def _room_in(self, pack_serial):
        if pack_serial not in self._opened:
            self._opened.add(pack_serial)
            API.UseObject(pack_serial)
            API.Pause(self._config["open_delay"])

        items = API.ItemsInContainer(pack_serial, True)

        # Unreadable is not empty: moving whole stacks is what the shard's refusal already handles
        if items is None:
            return self._config["capacity"]

        return max(0, self._config["capacity"] - self._wood.board_amount(items))

    def _out_of_reach(self, serial):
        here = API.FindMobile(serial)

        return here is None or here.Distance > self._config["unload_range"]

    # Moves are asynchronous, so rescan between passes rather than trusting MoveItem's return value.
    # A pet that walked off mid-pass has every move refused and looks exactly as full.
    def _move_all(self, serial, pack_serial):
        previous = None

        while not API.StopRequested:
            stacks = self._wood.board_piles()
            total = self._wood.board_amount(stacks)

            if total == 0:
                return "clear"

            if previous is not None and total >= previous:
                if self._out_of_reach(serial) or said(self._config["too_far_text"]):
                    return "lost"

                return "full"

            if self._walk_to(serial) is None:
                return "lost"

            room = self._room_in(pack_serial)

            if room == 0:
                return "full"

            previous = total
            forget(self._config["too_far_text"])

            for stack in stacks:
                part = min(amount_of(stack), room)

                if part == 0:
                    break

                API.MoveItem(stack.Serial, pack_serial, part)
                API.Pause(self._config["move_delay"])
                room -= part

        return "lost"

    # Works down the animals until the pack is clear or every one has had a turn. An animal that
    # stops accepting is full rather than broken, so what is left goes to the next one and that
    # animal is remembered rather than walked to again.
    def _unload_to(self, animals):
        attempted = False
        reached = False

        for animal in animals:
            before = self._wood.board_total()

            if before == 0:
                break

            attempted = True
            here = self._walk_to(animal.Serial)

            if here is None:
                continue

            pack = self._animal_pack(here)

            if pack is None:
                reached = True
                self._log("'%s' has no reachable backpack" % (here.Name or "?"))
                continue

            verdict = self._move_all(animal.Serial, pack.Serial)

            moved = before - self._wood.board_total()
            name = here.Name or "?"

            if verdict == "lost":
                self._log("'%s' moved out of reach while loading, trying it again next haul" % name)
                continue

            reached = True

            if verdict != "full":
                continue

            # A save refuses every move at once, and the caller only asks afterwards - read as
            # this animal's verdict it would sit out the rest of the run over a five second wait
            if self._saves.is_saving():
                self._log("'%s' took nothing while the world is saving, trying the next" % name)
            elif moved == 0:
                self._overloaded.add(animal.Serial)
                self._log("'%s' took nothing, leaving it out of the rest of the run" % name)
            else:
                self._overloaded.add(animal.Serial)
                self._log("'%s' took %d of %d boards and is full, leaving it out of the rest of "
                          "the run" % (name, moved, before))

        # Nothing to load is not a failure to reach anyone
        return reached or not attempted

    # Answers whether an animal was found and reached, not whether anything moved: only a missing
    # animal is worth giving up the search for, and one that took nothing has already been dropped
    def unload(self):
        animals = self.find()

        if len(animals) == 0:
            if not self._reported_no_animal:
                self._reported_no_animal = True
                self._log("no pack animal nearby")

            return "none"

        self._reported_no_animal = False

        # Filtered here rather than in find, which also feeds the trouble watch its companion - an
        # animal that is full is still one worth watching
        spare = [animal for animal in animals if animal.Serial not in self._overloaded]
        reached = True

        if len(spare) == 0:
            if not self._said_all_full:
                self._said_all_full = True
                self._log("all %d pack animal(s) are full, nothing left to load" % len(animals))
        else:
            reached = self._unload_to(spare)

        # A log that leaves as a log never comes back as a board, so what would not convert waits
        # for the next haul to try it again. Asked once every animal has had its turn at the boards.
        if over_buffer(self._config["buffer"]):
            left = self._wood.log_total()

            if left > 0:
                self._log("%d logs would not convert, keeping them in the pack" % left)

        return "tried" if reached else "unreached"

    def haul_now(self):
        before = API.Player.Weight

        self._boards.make_boards()

        outcome = self.unload()

        # A save freezes every part of a haul at once - the conversion is silent, the animal takes
        # nothing, the weight does not move. Read as an ordinary result it latches hauling off.
        if self._saves.is_saving():
            self._saves.wait_out()

            return "hauling"

        if outcome == "none":
            self._hauling = False
            self._log("no pack animal found, carrying on until overweight")

            return "hauling"

        # Not counted against the animals: a haul that never got a pass in range says nothing about
        # whether they are full, and the pets do come back
        if outcome == "unreached":
            self._log("no pack animal in reach this haul, trying again next time")

            return "hauling"

        # Weight rather than stacks moved: what this decides is whether the haul relieved the pack,
        # and an animal that took a stack and refused the rest has not
        if not over_buffer(self._config["buffer"]) or API.Player.Weight < before:
            self._empty_hauls = 0

            return "hauling"

        self._empty_hauls += 1

        if self._empty_hauls >= self._config["max_empty_hauls"]:
            self._hauling = False
            self._log("%d hauls freed nothing - the animals are full. Carrying on until overweight"
                      % self._empty_hauls)

        return "hauling"

    def haul_for_room(self):
        if not over_buffer(self._config["buffer"]):
            return None

        # Once hauling has latched off there is nothing to walk to, so the cycle goes on to chop
        # rather than spending itself on a phase. The conversion still runs, because boards weigh
        # less than the logs they came from and that is worth having with no animal to put them on.
        # Unforced, unlike the one inside a real haul: this runs every cycle from here to the end of
        # the run, and re-trying a wood that has already refused three times would cost three
        # cursors a cycle for the rest of it.
        if not self._hauling:
            self._boards.run()

            return None

        return self.haul_now()


# src/uo/clock.py
def now():
    return time.time()


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


# src/lumberjacking/trees.py
def as_tile(static):
    return {
        "x": static.X,
        "y": static.Y,
        "z": static.Z,
        "graphic": static.Graphic,
        "is_land": False,
        "name": static.Name or "",
        "flagged": bool(getattr(static, "IsTree", False)),
        "vegetation": bool(getattr(static, "IsVegetation", False)),
    }


def tree_marks(tile):
    marks = []

    if tile.get("flagged"):
        marks.append("IsTree")

    if tile.get("vegetation"):
        marks.append("IsVegetation")

    return marks


class Trees(object):
    def __init__(self, memory, config, log):
        self._memory = memory
        self._config = config
        self._log = log
        self._current = None
        self._skipped_unreachable = 0

    def skipped_unreachable(self):
        return self._skipped_unreachable

    # Overrides first, which is the opposite order to mining's is_ore and deliberate: that one asks
    # the refusals first because its land table ships full and would outrank a ban learned on the
    # shard. Both sets here ship empty, so the override gets asked first.
    def is_tree(self, graphic, name, flagged):
        if graphic in self._config["graphics"]:
            return True

        if graphic in self._config["not_graphics"]:
            return False

        if self._memory.art_banned(graphic, False):
            return False

        if flagged:
            return True

        return any_in(name, self._config["names"])

    def matches(self, tile):
        return self.is_tree(tile["graphic"], tile.get("name", ""), tile.get("flagged", False))

    def within_z(self, z):
        return abs(z - API.Player.Z) <= self._config["z_range"]

    # One call for the whole box, where mining pays a pair of reads per coordinate. There is no
    # terrain cache behind it for the same reason: a sweep is one call, and a felled tree that
    # changes art would go stale in one.
    def _statics_in(self, radius):
        x = API.Player.X
        y = API.Player.Y

        return API.GetStaticsInArea(x - radius, y - radius, x + radius, y + radius) or []

    def _candidates(self, radius):
        for static in self._statics_in(radius):
            tile = as_tile(static)

            if self.matches(tile) and self.within_z(tile["z"]):
                yield tile

    def scan_box(self, radius):
        best, cooling, walled = pick_nearest(self._candidates(radius), self._memory,
                                             self._config["probes"], self._config["range"], True)
        self._skipped_unreachable = walled

        return best, cooling

    # The z and the art have to match as well as the coordinates: a tile carries several statics,
    # and only one of them is the trunk that was picked
    def _still_tree(self, tree):
        if self._memory.is_blocked(tree) or not self.within_z(tree["z"]):
            return None

        for static in API.GetStaticsAt(tree["x"], tree["y"]) or []:
            if static.Z == tree["z"] and static.Graphic == tree["graphic"]:
                if not self.matches(as_tile(static)):
                    return None

                found = dict(tree)
                found["distance"] = chebyshev_to(tree)

                return found

        return None

    # Widened rather than swept twice: the roam radius is 49 tiles a side, and walking that many
    # statics through interop is only worth paying for on the cycle that would otherwise stand still
    def scan(self):
        if self._current is not None:
            self._current = self._still_tree(self._current)

            if self._current is not None:
                return self._current, None

        near, near_cooling = self.scan_box(self._config["scan_radius"])

        if near is not None:
            self._current = near

            return near, None

        found, cooling = self.scan_box(self._config["roam_radius"])
        self._current = found

        return found, cooling if cooling is not None else near_cooling

    def forget_current(self):
        self._current = None

    # For the shard answering about what it can reach rather than about a tile, which is what a
    # self-target asks it. Parking only the trunk the scan picked left mining swinging at the
    # neighbour the shard had just written off, for the same sentence.
    def mark_area_depleted(self, reach):
        until = now() + self._config["regrow_delay"]
        parked = 0

        for tile in self._candidates(reach):
            self._memory.block(tile, until)
            parked += 1

        self._log("nothing to chop at %d,%d, parking %d tree(s) within %d for %dm"
                  % (API.Player.X, API.Player.Y, parked, reach,
                     max(1, int(round(self._config["regrow_delay"] / 60.0)))))

        return parked

    def survey(self, radius, limit):
        survey([as_tile(static) for static in self._statics_in(radius)], radius, limit,
               self.matches, self._log, tree_marks)


# src/lumberjacking/wood.py
class Wood(object):
    """What in the pack is a log and what is a board, learning both arts as it goes."""

    def __init__(self, log_graphics, log_words, board_graphics, board_words, log):
        self._log_graphics = log_graphics
        self._log_words = log_words
        self._board_graphics = board_graphics
        self._board_words = board_words
        self._log = log

    def _matches(self, item, graphics, words, noun):
        if item is None:
            return False

        if item.Graphic in graphics:
            return True

        if not word_in(item.Name, words):
            return False

        graphics.add(item.Graphic)
        self._log("%s '%s' is a %s too, remembering the art"
                  % (hex_of(item.Graphic), item.Name, noun))

        return True

    def is_log(self, item):
        return self._matches(item, self._log_graphics, self._log_words, "log")

    def is_board(self, item):
        return self._matches(item, self._board_graphics, self._board_words, "board")

    # Top level only, unlike log_total: the conversion acts by serial on loose items. Largest first,
    # so the biggest stack is the one turned into boards first.
    def log_piles(self):
        piles = [item for item in pack_top_level() if self.is_log(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def board_piles(self):
        return [item for item in pack_top_level() if self.is_board(item)]

    def board_total(self):
        return self.board_amount(pack_top_level())

    def board_amount(self, items):
        return sum(amount_of(item) for item in items if self.is_board(item))

    # Hue-blind on purpose: a shard with special woods hues its logs, and those still count, still
    # convert and still need hauling
    def log_total(self):
        return sum(amount_of(item) for item in pack_contents() if self.is_log(item))

    def wait_for_logs(self, before, timeout, poll):
        waited = 0.0

        while not API.StopRequested:
            if self.log_total() > before:
                return True

            if waited >= timeout:
                return False

            API.Pause(poll)
            waited += poll


# src/uo/gathered.py
class Gathered(object):
    """What a swing and a conversion each put in the pack, as attempt rows, while the skill can still gain."""

    def __init__(self, recorder, skill, capped, config, log):
        self._recorder = recorder
        self._skill = skill
        self._capped = capped
        self._config = config
        self._log = log
        self._names = {}
        self._from = None

    def recording(self):
        return self._recorder.recording() and self._capped() is None

    def read(self):
        return self._skill.read()

    def close(self):
        self._recorder.close(self._skill.read())

    def _resource_name(self, item):
        name = self._config["name_of"](item)

        if name is not None:
            return name

        return (getattr(item, "Name", "") or "").strip() or self._config["noun"]

    # By hue rather than by (graphic, hue): a stack's art changes with its size, so the merge after a
    # swing would read as one art lost and another gained
    def _resource_by_hue(self):
        counts = {}

        for item in pack_contents():
            if not self._config["is_resource"](item):
                continue

            hue = hue_of(item)
            counts[hue] = counts.get(hue, 0) + amount_of(item)

            # A name the caller vouches for is kept once seen: the pile carrying it is often merged away
            if hue not in self._names or self._config["name_of"](item) is not None:
                self._names[hue] = (self._resource_name(item), item.Graphic)

        return counts

    def before_swing(self):
        return self._resource_by_hue() if self.recording() else None

    def after_swing(self, skill_from, outcome, before):
        if before is None:
            return

        after = self._resource_by_hue()
        rows = []

        for hue in sorted(after):
            delta = after[hue] - before.get(hue, 0)

            if delta > 0:
                name, graphic = self._names[hue]
                rows.append((name, graphic, hue, delta))

        self._recorder.record(skill_from, outcome, self._config["tool"], gained=rows)

    def before_convert(self):
        self._from = self._skill.read() if self.recording() else None

    def _product_name(self, graphic, hue):
        for item in pack_contents():
            if item.Graphic == graphic and hue_of(item) == hue:
                name = (getattr(item, "Name", "") or "").strip()

                if name:
                    return name

        return hex_of(graphic)

    def after_convert(self, gained, lost):
        if self._from is None:
            return

        skill_from = self._from
        self._from = None
        graphics = self._config["resource_graphics"]
        spent = {}
        art = {}
        products = []

        for (graphic, hue), quantity in sorted(lost.items()):
            if graphic in graphics:
                spent[hue] = spent.get(hue, 0) + quantity
                art[hue] = graphic

        # A failed smelt halves the stack, and the smaller stack can wear another art
        for (graphic, hue), quantity in sorted(gained.items()):
            if graphic in graphics:
                spent[hue] = spent.get(hue, 0) - quantity
            else:
                products.append((self._product_name(graphic, hue), graphic, hue, quantity))

        consumed = []

        for hue in sorted(spent):
            if spent[hue] > 0:
                name = self._names.get(hue, (self._config["noun"], None))[0]
                consumed.append((name, art[hue], hue, spent[hue]))

        outcome = self._config["made"] if products else "failed"
        self._recorder.record(skill_from, outcome, self._config["converter_tool"], consumed, products)


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


def overweight(buffer):
    def clause():
        me = player()

        if me is None or not over_buffer(buffer):
            return None

        return "overweight at %d/%d" % (me.Weight, me.WeightMax)

    return clause


# The base, not Value: jewelry lifts Value past the cap while the skill is still gaining
def skill_capped(name):
    def clause():
        skill = API.GetSkill(name) if name is not None else None

        if skill is None:
            return None

        base = getattr(skill, "Base", None)
        value = base if base is not None else skill.Value

        if value > 0 and value >= skill.Cap:
            return "%s is capped at %.1f" % (name, value)

        return None

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


# src/uo/hold.py
WIDTH = 340
HEIGHT = 110


class Hold(object):
    """Standing still behind a gump the script drew, until its button is pressed."""

    def __init__(self, config, log, stop_reason, heartbeat):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason
        self._heartbeat = heartbeat

    def _show(self, on_press):
        gump = API.Gumps.CreateGump(True, True)

        if gump is None:
            return None

        gump.SetRect(0, 0, WIDTH, HEIGHT)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.85, "#1E1E1E")
        background.SetRect(0, 0, WIDTH, HEIGHT)
        gump.Add(background)

        label = API.Gumps.CreateGumpLabel(self._config["text"], self._config["hue"])
        label.SetPos(16, 16)
        gump.Add(label)

        button = API.Gumps.CreateSimpleButton(self._config["button"], 120, 26)
        button.SetPos(16, HEIGHT - 42)
        API.Gumps.AddControlOnClick(button, on_press)
        gump.Add(button)

        API.Gumps.AddGump(gump)

        return gump

    # each() runs once a slice, so the caller's alarm can keep restarting while the gump is up
    def wait(self, each):
        if API.Pathfinding():
            API.CancelPathfinding()

        if API.HasTarget():
            API.CancelTarget()

        pressed = [False]

        def on_press():
            pressed[0] = True

        gump = self._show(on_press)

        # API.Stop() only lands at the next Pause, and every client call before it answers nothing
        if gump is None:
            self._log("not holding - the run is being stopped")
            return False

        self._log("holding - %s" % self._config["text"])
        why = None

        # The click only arrives through ProcessCallbacks, and a stopped script's client calls all
        # answer with nothing, so the stop flag is the one read that still means something then
        while why is None:
            if API.StopRequested:
                why = "the run is being stopped"
                break

            each()
            API.ProcessCallbacks()

            if pressed[0]:
                why = "the button was pressed"
            elif gump.IsDisposed:
                why = "the gump was closed"
            elif self._stop_reason() is not None:
                why = "the run has a reason to stop"
            else:
                API.Pause(self._config["poll"])

        if not gump.IsDisposed:
            gump.Dispose()

        self._heartbeat.reset()
        self._log("%s, carrying on" % why)

        return why in ("the button was pressed", "the gump was closed")


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


# src/uo/record.py
# Written by hand rather than with json.dumps, so the key order stays the one the README shows
def quoted(text):
    out = ['"']

    for character in text:
        code = ord(character)

        if character == '"' or character == "\\":
            out.append("\\" + character)
        elif character == "\n":
            out.append("\\n")
        elif character == "\r":
            out.append("\\r")
        elif character == "\t":
            out.append("\\t")
        # Non-ASCII escaped rather than written through: a character name carrying an accent is
        # ordinary here, and what encoding the runtime picked for the file is not knowable from in
        # here
        elif code < 0x20 or code > 0x7E:
            out.append("\\u%04x" % code)
        else:
            out.append(character)

    out.append('"')

    return "".join(out)


def skill_json(value):
    return "null" if value is None else "%.1f" % value


def append_line(path, line):
    handle = open(path, "a")

    try:
        handle.write(line + "\n")
    finally:
        handle.close()


class AttemptLog(object):
    """One JSON object per attempt, appended as it happens.

    A row is buffered when the attempt resolves and written when the *next* attempt is recorded,
    carrying that attempt's starting value as its own end: the client applies a gain some time after
    the outcome, and a value read on the next cycle still misses one that lands during a pause,
    where the next attempt's read cannot. close() writes the last row at the end of the run. The
    cost is one row in the air at any moment, which a killed script loses; the alternative is a
    file that under-reports every gain it exists to measure.
    """

    def __init__(self, path, character, serial, skill, log, append=None):
        self._path = path or ""
        self._character = character or ""
        self._serial = serial
        self._skill = skill
        self._log = log
        self._append = append if append is not None else append_line
        self._off = not self._path
        # Milliseconds, not seconds: two runs started inside the same second would mint the
        # same ids, and the converter reads a repeated id as the same row arriving twice
        self._run = int(now() * 1000)
        self._seq = 0
        self._pending = None
        self._said = False

    # Asked before an attempt so a caller can skip the work of measuring what it spent
    def recording(self):
        return not self._off

    # used is what the attempt was made with: the spell, the product, the creature, the weapon.
    # consumed and gained are lists of (name, graphic, hue, quantity) - measured, so an attempt that
    # spent nothing passes nothing rather than a guess at what the recipe charges
    def record(self, skill_from, outcome, used, consumed=None, gained=None):
        if self._off or skill_from is None:
            return

        # The previous row ends where this attempt starts: the latest read there is
        self._flush(skill_from)

        self._seq += 1
        self._pending = {
            "id": "%s/%d/%d" % (hex_of(self._serial), self._run, self._seq),
            "at": now(),
            "from": skill_from,
            "used": used,
            "outcome": outcome,
            "consumed": list(consumed) if consumed else [],
            "gained": list(gained) if gained else [],
        }

    # The end of the run. skill_to is None where the client had stopped answering, and the row is
    # written all the same with its end unknown rather than lost with the run
    def close(self, skill_to):
        self._flush(skill_to)

    def _flush(self, skill_to):
        pending = self._pending
        self._pending = None

        if pending is None or self._off:
            return

        self._write(pending, skill_to)

    def _line(self, row, skill_to):
        fields = [
            '"v":1',
            '"id":%s' % quoted(row["id"]),
            '"t":%.3f' % row["at"],
            '"char":%s' % quoted(self._character),
            '"serial":%s' % quoted(hex_of(self._serial)),
            '"skill":%s' % quoted(self._skill),
            '"used":%s' % quoted(row["used"]),
            '"from":%s' % skill_json(row["from"]),
            '"to":%s' % skill_json(skill_to),
            '"outcome":%s' % quoted(row["outcome"]),
        ]

        for key in ("consumed", "gained"):
            if row[key]:
                fields.append('"%s":[%s]' % (key, ",".join(
                    '{"name":%s,"graphic":%s,"hue":%d,"qty":%d}'
                    % (quoted(name), quoted(hex_of(graphic)), hue, quantity)
                    for name, graphic, hue, quantity in row[key]
                )))

        return "{%s}" % ",".join(fields)

    # A run that cannot write its log is still a run: the recorder retires itself and says so once,
    # rather than ending the training over a file
    def _write(self, row, skill_to):
        try:
            self._append(self._path, self._line(row, skill_to))
        except Exception as error:
            self._off = True

            if not self._said:
                self._said = True
                self._log("cannot write %s (%s) - not recording this run" % (self._path, error))


# The character is read once, here, rather than on every row: it cannot change under a running
# script, and a client between world states answers None for the player without that meaning the
# run should stop recording.
def attempt_log(path, skill, log):
    me = player()

    if me is None and path:
        log("the client is not reporting the character - rows will not name it")

    return AttemptLog(path, getattr(me, "Name", ""), getattr(me, "Serial", 0), skill, log)


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
                if not self._config["wait"]:
                    return ("stop", "%s, the soonest is back in %dm" % (
                        self._config["worked_out"],
                        max(1, int(round((ready_at_or_none - now()) / 60.0)))))

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


# src/uo/skill.py
# A name the client does not carry throws on some builds rather than answering None
def find_skill_name(names):
    for name in names:
        try:
            if API.GetSkill(name) is not None:
                return name
        except Exception:
            if API.StopRequested:
                raise

            continue

    return None


def reading(value):
    return "unknown" if value is None else "%.1f" % value


class SkillReader(object):
    """Value reads 0.0 before the skill list arrives, which is also a real skill value."""

    def __init__(self, name):
        self._name = name
        self._seen = False

    def read(self):
        skill = API.GetSkill(self._name)

        if skill is None:
            return None

        value = skill.Value

        if value <= 0.0 and not self._seen:
            return None

        self._seen = True

        return value

    def name(self):
        skill = API.GetSkill(self._name)

        return skill.Name if skill is not None and skill.Name else self._name

    def cap(self):
        skill = API.GetSkill(self._name)

        return skill.Cap if skill is not None else None

    def wait(self, timeout, poll):
        waited = 0.0

        while not API.StopRequested:
            value = self.read()

            if value is not None:
                return value

            if waited >= timeout:
                return None

            API.Pause(poll)
            waited += poll


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
            # The stop button's interrupt can land inside Process.Start, and swallowed here it would
            # leave a detached thread restarting the alarm
            if API.StopRequested:
                raise

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
    def __init__(self, config, log, companion, friend_label, hold=None):
        self._config = config
        self._log = log
        self._companion = companion
        self._friend_label = friend_label
        self._hold = hold
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

    def _sound(self):
        if self._alarm_left > 0 and self._alert.play(self._config["ambush_alarm"]):
            self._alarm_left -= 1

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

            # The scan above is stale once the hold returns; the next look reads the fight afresh
            if self._hold is not None:
                self._hold.wait(self._sound)
                self._in_episode = False
                self._trouble_seen = False
                self._alarm_left = 0
                self._alert.stop()

                return

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

        self._sound()


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

    def __init__(self, respawn_delay, unreachable_delay, noun, verb, log, saver=None):
        self._respawn_delay = respawn_delay
        self._unreachable_delay = unreachable_delay
        self._noun = noun
        self._verb = verb
        self._log = log
        self._saver = saver
        self._blocked = {}
        self._banned_arts = set()

    def blocked_until(self, tile):
        return self._blocked.get(tile_key(tile))

    def is_blocked(self, tile):
        until = self.blocked_until(tile)

        return until is not None and now() < until

    def block(self, tile, until):
        self._blocked[tile_key(tile)] = until

        if self._saver is not None and until != float("inf"):
            self._saver(tile_key(tile), until)

    def restore(self, key, until):
        self._blocked[key] = until

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


# src/uo/retry.py
def settled(timeout, poll, landed):
    waited = 0.0

    while waited < timeout:
        API.Pause(poll)
        waited += poll

        if landed():
            return True

    return False


# src/uo/tool.py
# Books carry the client's container flag, so the flag alone opens every spellbook in the pack
NOT_BAG_GRAPHICS = set([
    0x0EFA,  # spellbook
    0x2253,  # necromancer spellbook
    0x2252,  # book of chivalry
    0x238C,  # book of bushido
    0x23A0,  # book of ninjitsu
    0x2D50,  # spellweaving spellbook
    0x2D9D,  # mysticism spellbook
    0x22C5,  # runebook
    0x9C16,  # runic atlas
    0x2259,  # bulk order book
])
NOT_BAG_NAMES = ["spellbook", "runebook", "book", "atlas"]


def is_bag(item):
    if not getattr(item, "IsContainer", False) or getattr(item, "Opened", False):
        return False

    if item.Graphic in NOT_BAG_GRAPHICS:
        return False

    return not word_in(item.Name, NOT_BAG_NAMES)


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
        bags = [item for item in pack_contents() if is_bag(item)]

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


# src/lumberjacking/index.py
log = make_log("lumberjack")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "chops", position_and_weight)
stall = StallWatch("cycles without a chop", STALL_WARN, STALL_STOP, heartbeat, log)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), overweight(WEIGHT_BUFFER),
                         pack_full(PACK_LIMIT)])


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)
hold = Hold({
    "text": AMBUSH_HOLD_TEXT,
    "button": AMBUSH_HOLD_BUTTON,
    "hue": AMBUSH_HOLD_HUE,
    "poll": AMBUSH_HOLD_POLL,
}, log, stop_reason, heartbeat)

axe = Tool("axe", AXE_NAMES, NOT_AXE_NAMES, ["twohanded", "onehanded"], SPARE_BAG_SERIAL,
           EQUIP_ATTEMPTS, EQUIP_TIMEOUT, EQUIP_POLL, log)
wood = Wood(LOG_GRAPHICS, LOG_NAME_WORDS, BOARD_GRAPHICS, BOARD_NAME_WORDS, log)

skill_name = find_skill_name(SKILL_NAMES)

if skill_name is None and DATA_PATH:
    log("the client reports none of %s - not recording" % ", ".join(SKILL_NAMES))

skill = SkillReader(skill_name or SKILL_NAMES[0])
recorder = attempt_log(DATA_PATH if skill_name else "", skill.name(), log)
gathered = Gathered(recorder, skill, skill_capped(skill_name), {
    "is_resource": wood.is_log,
    "name_of": lambda item: None,
    "resource_graphics": LOG_GRAPHICS,
    "noun": "logs",
    "tool": "axe",
    "converter_tool": "axe",
    "made": "converted",
}, log)
boards = Boards(wood, axe, saves, {
    "attempts": CONVERT_ATTEMPTS,
    "passes": MAX_CONVERT_PASSES,
    "delay": CONVERT_DELAY,
    "timeout": CONVERT_TIMEOUT,
    "poll": CONVERT_POLL,
    "target_timeout": TARGET_TIMEOUT,
    "log_graphics": LOG_GRAPHICS,
    "board_graphics": BOARD_GRAPHICS,
    "throttled_text": THROTTLED_TEXT,
    "unskilled_text": UNSKILLED_TEXT,
    "about_to_convert": gathered.before_convert,
    "converted": gathered.after_convert,
}, log)
haul = Haul(wood, boards, saves, {
    "serials": PACK_ANIMAL_SERIALS,
    "graphics": PACK_ANIMAL_GRAPHICS,
    "radius": ANIMAL_SCAN_RADIUS,
    "unload_range": UNLOAD_RANGE,
    "too_far_text": TOO_FAR_TEXT,
    "capacity": PACK_ANIMAL_BOARDS,
    "open_delay": PACK_OPEN_DELAY,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "move_delay": MOVE_DELAY,
    "max_picks": MAX_PICKS,
    "pick_timeout": PICK_TIMEOUT,
    "buffer": HAUL_BUFFER,
    "max_empty_hauls": MAX_EMPTY_HAULS,
}, log)
memory = TileMemory(REGROW_DELAY, UNREACHABLE_DELAY, "tree", "chopped", log)
trees = Trees(memory, {
    "graphics": TREE_GRAPHICS,
    "not_graphics": NOT_TREE_GRAPHICS,
    "names": TREE_NAME,
    "z_range": CHOP_Z_RANGE,
    "range": CHOP_RANGE,
    "scan_radius": SCAN_RADIUS,
    "roam_radius": ROAM_RADIUS,
    "probes": MAX_PATH_PROBES,
    "regrow_delay": REGROW_DELAY,
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
}, log, haul.companion, lambda friend: "'%s'" % (friend.Name or "?"),
    hold if AMBUSH_HOLD else None)
roam = Roam(trees, memory, saves, threat, {
    "noun": "tree",
    "idle_message": "everything in reach is regrowing, waiting for the soonest one",
    "none_left": "no tree in range",
    "wait": True,
    "worked_out": "",
    "range": CHOP_RANGE,
    "scan_radius": SCAN_RADIUS,
    "z_range": CHOP_Z_RANGE,
    "survey_arts": SURVEY_ARTS,
    "max_walks": MAX_TREE_WALKS,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "idle_poll": IDLE_POLL,
    "idle_log_every": IDLE_LOG_EVERY,
}, log, heartbeat, stop_reason)
chopper = Chopper(wood, axe, OUTCOME_TEXT, {
    "cursor_timeout": CHOP_TARGET_TIMEOUT,
    "cursor_poll": CHOP_TARGET_POLL,
    "prompt_text": CHOP_PROMPT_TEXT,
    "no_cursor_read": NO_CURSOR_READ,
    "chop_timeout": CHOP_TIMEOUT,
    "aim_at_self": AIM_AT_SELF,
}, log)

axe.learn(axe.held())

log("%d logs in the pack to start, at %d,%d" % (wood.log_total(), API.Player.X, API.Player.Y))

if recorder.recording():
    start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)
    cap = skill.cap()
    log("%s at %s%s%s" % (
        skill.name(), reading(start),
        "/%.1f" % cap if cap is not None and cap > 0 else "",
        "" if gathered.recording() else ", capped - not recording"))

# Read before anything acts, or a run that stops on its first cycle looks exactly like a script that
# never started
held = axe.held()
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
    haul.pick()

# A pack pasted in already over the buffer would otherwise be stopped on cycle zero by the weight
# guard, before a haul had ever had its turn
haul.haul_for_room()

stop = None
tally = 0
fails = 0
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
        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        threat.look()

        if not axe.equip():
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = "no axe"
                break

            log("no axe (%d/%d), looking again" % (no_tool, MAX_NO_TOOL))
            end_cycle("no tool")
            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
            continue

        no_tool = 0

        relieved = haul.haul_for_room()

        if relieved is not None:
            end_cycle(relieved)
            API.Pause(STEP_DELAY)
            continue

        found = roam.approach()

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

        value = gathered.read()
        before = gathered.before_swing()
        logs_before = wood.log_total()
        outcome = chopper.chop_once(axe.serial(), tree)

        if outcome == "chopped":
            tally += 1
            unknown = 0
            throttled = 0
            barren = 0
            stall.progressed()

            if before is not None:
                wood.wait_for_logs(logs_before, LOG_SETTLE_TIMEOUT, LOG_SETTLE_POLL)
                gathered.after_swing(value, "chopped", before)

        elif outcome == "failed":
            tally += 1
            fails += 1
            unknown = 0
            throttled = 0
            barren = 0
            stall.progressed()
            gathered.after_swing(value, "failed", before)

        elif outcome == "wornOut":
            log("axe worn out, swapping")
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

        # A stump, not a dead tile. The two outcomes differ only in scope: nothingNearby is the
        # shard answering about everything it can reach, so it always parks the ground, while empty
        # is about the trunk - unless a self-target let the shard pick, in which case it is about
        # the spot as well.
        elif outcome == "empty" or outcome == "nothingNearby":
            unknown = 0
            barren += 1

            if outcome == "nothingNearby" or AIM_AT_SELF:
                trees.mark_area_depleted(CHOP_RANGE)
                trees.forget_current()
            else:
                memory.mark_depleted(tree)

            # Said once, at the point it stops looking like bad luck
            if barren == EMPTY_HINT:
                log(
                    "%d spots in a row had nothing to chop - either the stand is worked out, or "
                    "the tree test is matching scenery the shard will not harvest" % EMPTY_HINT
                )
                trees.survey(CHOP_RANGE, SURVEY_ARTS)

        # The art ban is only sound when the swing named the tile: aimed at yourself the shard chose
        # what to refuse, and banning the art of the trunk the scan happened to pick would write off
        # a perfectly good tree. Aimed that way the tile is set aside one at a time instead.
        elif outcome == "notTree":
            unknown = 0

            if not AIM_AT_SELF:
                memory.ban_art(tree)

            memory.mark_unusable(tree, "is not harvestable")

        elif outcome == "tooFar":
            unknown = 0
            memory.mark_unusable(tree, "is out of reach at %d tiles" % tree["distance"])

        elif outcome == "notSeen":
            unknown = 0
            memory.mark_unusable(tree, "is not in line of sight")

        # Consolidating would give back almost nothing here - one log stack converts to one board
        # stack - so what frees slots is the boards leaving for the animal
        elif outcome == "packFull":
            unknown = 0
            log("pack is full, hauling before the next swing")
            haul.haul_now()

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
                % (tally, wood.log_total(), API.Player.Weight, API.Player.WeightMax)
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
finally:
    gathered.close()

if API.Pathfinding():
    API.CancelPathfinding()

reason = stop or "hit the %d working cycle backstop" % MAX_CYCLES

# However the run ended, it finishes with boards on the animal rather than logs in the pack
boards.make_boards()

if haul.hauling():
    haul.unload()

# Closed again: a conversion after the loop records a row the close above did not see
gathered.close()

# Chops rather than a log delta: hauled wood has left the pack, so the pack cannot total the run
log("%d chops, %d failed, %d logs still in the pack" % (tally, fails, wood.log_total()))
log("stopping - %s" % reason)
API.Stop()
