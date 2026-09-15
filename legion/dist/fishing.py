# Built from src/fishing/index.py by build.py - do not edit.

import API
import time
import clr
import System


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


# A craft's mana coming back gains Meditation and Focus, which buries the one line that matters
SKILL_GAIN_TEXT = ["your skill in", "has changed by"]


# matchingText is left off on purpose: the client only applies it as a regex, so a plain string
# there filters everything out
def journal_entries(seconds, stamp=None):
    try:
        entries = API.GetJournalEntries(seconds)
    except Exception:
        if API.StopRequested:
            raise

        return []

    kept = []
    stamps = [stamp] if stamp else []

    for entry in entries if entries else []:
        text = getattr(entry, "Text", None)

        if (text and text.strip() and not any_in(text, SKILL_GAIN_TEXT)
                and not any_in(text, stamps)):
            kept.append(((getattr(entry, "Name", None) or "").strip(), text.strip()))

    return kept


# The text alone: fishing reads the catch off the end of the line it returns
def journal_tail(seconds, limit, stamp=None):
    return [text for _name, text in journal_entries(seconds, stamp)][-limit:]


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


# src/fishing/angler.py
def caught_name(lines, fragments):
    for line in reversed(lines):
        if any_in(line, fragments):
            return line.partition(":")[2].strip()

    return None


class Angler(object):
    """One cast: the pole, the cursor, the water tile, the shard's answer."""

    def __init__(self, buckets, config, log, stamp=None):
        self._buckets = buckets
        self._config = config
        self._log = log
        self._stamp = stamp
        self._caught_fragments = [phrase.lower() for phrase in config["caught_text"]]

    # HasTarget alone was not enough on the web client: the prompt was in the journal well before
    # the cursor flag rose
    def _cursor_opened(self):
        waited = 0.0

        while waited < self._config["cursor_timeout"]:
            if API.HasTarget() or said(self._config["prompt_text"]):
                return True

            API.Pause(self._config["cursor_poll"])
            waited += self._config["cursor_poll"]

        return False

    # Read off the tail rather than through InJournalAny: that clears the line, and the name is on it
    def _caught(self):
        return caught_name(journal_tail(self._config["tail_seconds"], self._config["tail_lines"],
                                         self._stamp),
                           self._caught_fragments)

    # In declaration order, the way read_outcome does, with the catch bucket answered by the tail
    def _matched(self):
        for name, phrases in self._buckets:
            if name == "caught":
                caught = self._caught()

                if caught is not None:
                    return name, caught
            elif API.InJournalAny(phrases, True):
                return name, ""

        return None, ""

    def _read(self, budget, poll):
        waited = 0.0

        while not API.StopRequested:
            name, caught = self._matched()

            if name is not None:
                return name, caught

            if waited >= budget:
                return None, ""

            API.Pause(poll)
            waited += poll

        return None, ""

    # No cursor is not the same as nothing having happened: a shard that refused the cast says so
    def _refused_outcome(self):
        name, caught = self._read(self._config["no_cursor_read"], self._config["cursor_poll"])

        if name is not None:
            return name, caught

        self._log("no target cursor - the shard never asked where to fish")

        return "noCursor", ""

    def cast_once(self, serial, tile):
        # Cancelled only when there is one to cancel: an unconditional cancel a few hundred
        # milliseconds before the use left the next cursor unusable in the run this was copied from
        if API.HasTarget():
            API.CancelTarget()

        forget(self._config["prompt_text"])
        forget_outcomes(self._buckets)

        API.UseObject(serial)

        if not self._cursor_opened():
            return self._refused_outcome()

        # The four-argument overload: a static carries no serial, so the tile and its art are the
        # only way to name it, and a self-target is refused for fishing on this shard
        API.Target(tile["x"], tile["y"], tile["z"], tile["graphic"])

        name, caught = self._read(self._config["cast_timeout"], self._config["cast_poll"])

        return (name, caught) if name is not None else ("unknown", "")


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

STEP_DELAY = 0.3

GAIN_PATH_TIMEOUT = 5.0
GAIN_PATH_POLL = 0.25


# src/fishing/config.py
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

# How long a turn (API.Turn) needs before the client's own Direction reflects it
TURN_DELAY = 0.5

# Matched against the caught item's own name text (the part after the colon in "You pull out an
# item: ..."), not its graphic - there is no confirmed graphic ID for any of these on this shard
JUNK_TEXT = ["fish", "boots", "sandals", "shoes", "thigh boots"]

# Asked on the same start-up gump as the tiles-ahead question. Discard preserves the run's old
# always-drop behavior as the default
CATCH_MODE_TEXT = "What should happen to junk catches (fish, boots, sandals, shoes, thigh boots)?"
CATCH_MODE_OPTIONS = [("container", "Container"), ("keep", "Keep"), ("discard", "Discard")]
CATCH_MODE_DEFAULT = "discard"
CATCH_MODE_HUE = 996

PICK_TIMEOUT = 60.0
MOVE_DELAY = 0.7

# x/y are an offset from your own position (confirmed off TazUO's own LegionAPI.cs) - one of the
# eight adjacent tiles is picked instead of always your own, so catches do not all stack underfoot
DROP_OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# Seconds throughout - API.Pause takes seconds
CURSOR_TIMEOUT = 2.0
CURSOR_POLL = 0.1
NO_CURSOR_READ = 1.0

# Has to outlast the cast animation, which plays before the shard answers
CAST_TIMEOUT = 2.0
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

# What an unreadable outcome reports before it goes quiet - a short CAST_TIMEOUT means this shard
# hits it often as a matter of course, not just on a genuinely unrecognized wording. Reset once a
# catch lands clean, so a run that goes quiet still gets a fresh look if the wording changes later
MAX_UNREADABLE_REPORTS = 2

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
    # A short CAST_TIMEOUT recasts before the shard is done resolving the last one - harmless
    ("busy", ["You are already fishing"]),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]


# src/fishing/direction.py
# API.Player.Direction is a string, not a bitmask - confirmed live, after an earlier version of
# this tried "& 0x07" on it and threw. These are ClassicUO's own Direction enum names, matched
# case-insensitively; a running character may report an extra word (e.g. "North, Running"), so the
# match looks at each word rather than the whole string. Falls back to North if nothing matches.
NAMES = ["North", "Right", "East", "Down", "South", "Left", "West", "Up"]

# Index order matches NAMES: N, NE, E, SE, S, SW, W, NW
DELTAS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]


def facing():
    text = (API.Player.Direction or "").replace(",", " ")

    for word in text.split():
        for index, name in enumerate(NAMES):
            if word.lower() == name.lower():
                return index

    return 0


# A shoreline's water is commonly a static laid over plain grass, not a change to the land tile
# underneath - an earlier version read only the land tile there, named the grass, and the shard
# silently ignored every cast. A static match wins over the land tile it sits on; failing that, the
# plain land tile is used as given - that is what open ocean off a boat looks like, with no static
# to name at all - and fallback_graphic only covers a coordinate the client has no land data for.
# "source" is not read by the cast itself; it is there so a run can log which path a tile came from
def tile_ahead(tiles_ahead, land_graphics, static_graphics, fallback_graphic):
    dx, dy = DELTAS[facing()]
    x = API.Player.X + dx * tiles_ahead
    y = API.Player.Y + dy * tiles_ahead

    for static in API.GetStaticsAt(x, y) or []:
        if static.Graphic in static_graphics:
            return {"x": x, "y": y, "z": static.Z, "graphic": static.Graphic, "source": "static"}

    land = API.GetTile(x, y)

    if land is not None:
        source = "land" if land.Graphic in land_graphics else "land (unrecognized)"

        return {"x": x, "y": y, "z": land.Z, "graphic": land.Graphic, "source": source}

    return {"x": x, "y": y, "z": API.Player.Z, "graphic": fallback_graphic, "source": "fallback"}


def _is_water(x, y, land_graphics, static_graphics):
    for static in API.GetStaticsAt(x, y) or []:
        if static.Graphic in static_graphics:
            return True

    land = API.GetTile(x, y)

    return land is not None and land.Graphic in land_graphics


# The DELTAS/NAMES index of the nearest direction whose tile at tiles_ahead is recognized water -
# current facing checked first, so an already-good facing is never turned away from. None when none
# of the eight match; the water tables are a hypothesis, same as tile_ahead's own fallback
def water_direction(tiles_ahead, land_graphics, static_graphics):
    current = facing()
    order = [current] + [index for index in range(len(DELTAS)) if index != current]

    for index in order:
        dx, dy = DELTAS[index]
        x = API.Player.X + dx * tiles_ahead
        y = API.Player.Y + dy * tiles_ahead

        if _is_water(x, y, land_graphics, static_graphics):
            return index

    return None


# API.Turn only turns, the way a single directional key press does when you are not already facing
# that way - it never steps forward. Does nothing when already facing water, or when none of the
# eight directions match anything in the water tables
def turn_toward_water(tiles_ahead, land_graphics, static_graphics, turn_delay):
    current = facing()
    direction = water_direction(tiles_ahead, land_graphics, static_graphics)

    if direction is not None and direction != current:
        API.Turn(NAMES[direction].lower())
        API.Pause(turn_delay)

    return direction


# src/uo/pack.py
def pack_contents():
    items = API.ItemsInContainer(API.Backpack, True)

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


# A bag the client has not opened this session reads as empty, whatever is in it. extra_serial, a
# spare bag outside the pack, joins the search if it is not open yet either. opened is mutated:
# every bag this call sends a double-click to is remembered so a later call leaves it alone.
def open_unopened_bags(noun, log, opened, extra_serial=None):
    bags = [item for item in pack_contents() if is_bag(item)]

    if extra_serial is not None:
        spare = API.FindItem(extra_serial)

        if spare is not None and not getattr(spare, "Opened", False):
            bags.append(spare)

    bags = [bag for bag in bags if bag.Serial not in opened]

    if not bags:
        return False

    # A cursor left up would take the double-click as its answer
    if API.HasTarget():
        API.CancelTarget()

    log("opening %d bag(s) to look inside for a %s" % (len(bags), noun))

    for bag in bags:
        opened.add(bag.Serial)
        API.UseObject(bag.Serial)

    return True


# search is called fresh each time: opening the bags is asynchronous, so what it finds only
# improves after settled() gives the pack a chance to catch up
def find_after_opening_bags(search, noun, log, opened, timeout, poll, extra_serial=None):
    found = search()

    if found is None and open_unopened_bags(noun, log, opened, extra_serial):
        settled(timeout, poll, lambda: search() is not None)
        found = search()

    return found


# src/uo/crafttool.py
class CraftTool(object):
    """A crafting tool, used out of the pack rather than equipped."""

    def __init__(self, noun, graphics, name_words, log, prefer=None):
        self._noun = noun
        self._graphics = graphics
        self._name_words = name_words
        self._log = log
        self._prefer = prefer or set()
        self._opened = set()

    def is_tool(self, item):
        if item is None:
            return False

        if item.Graphic in self._graphics:
            return True

        if not word_in(item.Name, self._name_words):
            return False

        self._graphics.add(item.Graphic)
        self._log("%s '%s' is a %s too, remembering the art"
                  % (hex_of(item.Graphic), item.Name, self._noun))

        return True

    def serials(self):
        return [item.Serial for item in pack_contents() if self.is_tool(item)]

    def serial(self):
        found = None

        for item in pack_contents():
            if not self.is_tool(item):
                continue

            if item.Graphic in self._prefer:
                return item.Serial

            if found is None:
                found = item.Serial

        return found

    def find(self, timeout, poll):
        return find_after_opening_bags(self.serial, self._noun, self._log, self._opened,
                                       timeout, poll)


# src/fishing/pole.py
def pole_in_hand(graphics, name_words, layers):
    for layer in layers:
        held = API.FindLayer(layer)

        if held is None:
            continue

        if held.Graphic in graphics or word_in(held.Name, name_words):
            return held.Serial

    return None


# The shard takes the pole from the pack as well, so nothing is equipped; a held one is preferred
# because it is the one you meant
def find_pole(graphics, name_words, layers, log):
    held = pole_in_hand(graphics, name_words, layers)

    if held is not None:
        return held

    return CraftTool("fishing pole", graphics, name_words, log).serial()


# src/uo/gumpwait.py
# Waits behind a gump the script drew, one poll slice at a time, until resolve() answers a reason
# to stop (checked first, so a click wins over the gump closing), the gump is disposed, stop_reason
# gives one, or timeout seconds pass - timeout=None means no ceiling. each(), when given, runs once
# a slice before resolve(), so an alarm or a heartbeat keeps going while the gump is up. Disposes
# the gump before returning why. The click only arrives through ProcessCallbacks, and a stopped
# script's client calls all answer with nothing, so the stop flag is the one read that still means
# something then.
def wait_for_gump(gump, stop_reason, poll, resolve, closed_message="the gump was closed",
                  timeout=None, each=None):
    waited = 0.0
    why = None

    while why is None:
        if API.StopRequested:
            why = "the run is being stopped"
            break

        if each is not None:
            each()

        API.ProcessCallbacks()

        why = resolve()

        if why is not None:
            pass
        elif gump.IsDisposed:
            why = closed_message
        elif stop_reason() is not None:
            why = "the run has a reason to stop"
        elif timeout is not None and waited >= timeout:
            why = "nothing was pressed in %.0fs" % timeout
        else:
            API.Pause(poll)
            waited += poll

    if not gump.IsDisposed:
        gump.Dispose()

    return why


# src/uo/setup.py
RADIO_CHAR = 8
RADIO_GAP = 40


# src/fishing/prompt.py
PROMPT_WIDTH = 380
PROMPT_HEIGHT = 202
PROMPT_BUTTON_HEIGHT = 26
PROMPT_BOX_WIDTH = 60
RADIO_ROW_Y = 16
TILES_LABEL_Y = 62
TILES_BOX_Y = 92
DEBUG_LOGS_Y = 126


class StartPrompt(object):
    """Asked once, before the loop starts: how many tiles ahead to cast, and what to do with a
    junk catch (fish, boots, sandals, shoes, thigh boots) - a container, the pack, or the ground."""

    def __init__(self, config, log, stop_reason):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason
        self._radios = []

    # A blank, zero, negative or non-numeric box answers the default rather than refusing to start
    def _tiles_ahead(self, box):
        text = (box.Text or "").strip()

        return int(text) if text.isdigit() and int(text) > 0 else self._config["tiles_default"]

    # Falls back to catch_default, not the first option - a radio's isChecked at creation is not
    # always something GetIsChecked reflects back until something has actually clicked one
    def _catch_mode(self):
        options = self._config["catch_options"]

        for index in range(len(self._radios)):
            if self._radios[index].GetIsChecked():
                return options[index][0]

        return self._config["catch_default"]

    def _debug_logs(self, checkbox):
        return checkbox.GetIsChecked()

    def _show(self, on_press):
        gump = API.Gumps.CreateGump(True, True)

        if gump is None:
            return None, None, None

        gump.SetRect(0, 0, PROMPT_WIDTH, PROMPT_HEIGHT)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.85, "#1E1E1E")
        background.SetRect(0, 0, PROMPT_WIDTH, PROMPT_HEIGHT)
        gump.Add(background)

        catch_label = API.Gumps.CreateGumpLabel(self._config["catch_text"],
                                                self._config["catch_hue"])
        catch_label.SetPos(16, RADIO_ROW_Y)
        gump.Add(catch_label)

        options = self._config["catch_options"]
        default = self._config["catch_default"]
        x = 16

        # Spaced by caption: the classic font runs about RADIO_CHAR pixels a letter
        for index in range(len(options)):
            key, caption = options[index]
            radio = API.Gumps.CreateGumpRadioButton(caption, 1, 0x00D0, 0x00D1,
                                                     self._config["catch_hue"], key == default)
            radio.SetPos(x, RADIO_ROW_Y + 24)
            gump.Add(radio)
            self._radios.append(radio)
            x += RADIO_GAP + RADIO_CHAR * len(caption)

        label = API.Gumps.CreateGumpLabel(self._config["tiles_text"], self._config["tiles_hue"])
        label.SetPos(16, TILES_LABEL_Y)
        gump.Add(label)

        box = API.Gumps.CreateGumpTextBox(str(self._config["tiles_default"]), PROMPT_BOX_WIDTH,
                                          PROMPT_BUTTON_HEIGHT, False, 20)
        box.SetPos(16, TILES_BOX_Y)
        gump.Add(box)

        checkbox = API.Gumps.CreateGumpCheckbox("Debug logs", self._config["tiles_hue"], True)
        checkbox.SetPos(16, DEBUG_LOGS_Y)
        gump.Add(checkbox)

        ok = API.Gumps.CreateSimpleButton("OK", 90, PROMPT_BUTTON_HEIGHT)
        ok.SetPos(16, PROMPT_HEIGHT - 42)
        API.Gumps.AddControlOnClick(ok, lambda: on_press("ok"))
        gump.Add(ok)

        cancel = API.Gumps.CreateSimpleButton("Cancel", 90, PROMPT_BUTTON_HEIGHT)
        cancel.SetPos(114, PROMPT_HEIGHT - 42)
        API.Gumps.AddControlOnClick(cancel, lambda: on_press("cancel"))
        gump.Add(cancel)

        API.Gumps.AddGump(gump)

        return gump, box, checkbox

    def ask(self):
        defaults = {"tiles_ahead": self._config["tiles_default"],
                    "catch_mode": self._config["catch_default"],
                    "debug_logs": True}
        pressed = [None]
        gump, box, checkbox = self._show(lambda button: pressed.__setitem__(0, button))

        if gump is None:
            self._log("not asking - the run is being stopped")

            return defaults

        self._log("asking - %s / %s" % (self._config["tiles_text"], self._config["catch_text"]))

        def resolve():
            return pressed[0]

        # A gump closed by hand and a Cancel press read the same: both take the defaults
        why = wait_for_gump(gump, self._stop_reason, self._config["poll"], resolve,
                            closed_message="cancel")
        answers = ({"tiles_ahead": self._tiles_ahead(box), "catch_mode": self._catch_mode(),
                    "debug_logs": self._debug_logs(checkbox)}
                  if why == "ok" else defaults)

        self._log("%s, casting %d tiles ahead, junk catches: %s"
                  % (why, answers["tiles_ahead"], answers["catch_mode"]))

        return answers


# src/uo/clock.py
def now():
    return time.time()


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


# By the value as well as the base: with no base reported, or a lifted value, the run never ends
def skill_capped(name):
    def clause():
        skill = API.GetSkill(name) if name is not None else None

        if skill is None:
            return None

        base = getattr(skill, "Base", None) or 0.0
        value = skill.Value

        if max(base, value) <= 0 or max(base, value) < skill.Cap:
            return None

        if base >= skill.Cap:
            return "%s is capped at %.1f" % (name, base)

        if base > 0:
            return ("%s shows %.1f against its %.1f cap while its base is %.1f - take off what lifts "
                    "it to keep gaining" % (name, value, skill.Cap, base))

        return "%s is capped at %.1f" % (name, value)

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
HOLD_WIDTH = 340
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

        gump.SetRect(0, 0, HOLD_WIDTH, HEIGHT)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.85, "#1E1E1E")
        background.SetRect(0, 0, HOLD_WIDTH, HEIGHT)
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

        def resolve():
            return "the button was pressed" if pressed[0] else None

        why = wait_for_gump(gump, self._stop_reason, self._config["poll"], resolve, each=each)

        self._heartbeat.reset()
        self._log("%s, carrying on" % why)

        return why in ("the button was pressed", "the gump was closed")


# src/uo/log.py
def make_log(prefix):
    stamp = prefix + ": "

    def log(message):
        if log.enabled:
            API.SysMsg(stamp + message)

    # The client puts a SysMsg in the journal beside the shard's own lines, so a script reading the
    # journal back needs to know which lines it wrote itself - without this a report of an unreadable
    # outcome quotes the last report of an unreadable outcome. Lowercase, because that is how the
    # journal readers compare. Carried on the function itself rather than a module-level list: a
    # bundle is one script and one prefix, and a shared list would leak between scripts sharing this
    # process, such as the test suite.
    log.stamp = stamp.lower()
    log.enabled = True

    return log


# src/uo/loop.py
def backoff_for(count, step, cap):
    return min(step * count, cap)


# src/uo/mount.py
def dismount(attempts, timeout, poll):
    if not API.Player.IsMounted:
        return True

    for _attempt in range(attempts):
        API.Dismount()

        if settled(timeout, poll, lambda: not API.Player.IsMounted):
            return True

    return False


# src/uo/paths.py
# TazUO's working directory is its own folder, and the scripts live in this subfolder of it
SCRIPTS_FOLDER = "LegionScripts"


# A bare name lands in TazUO's working directory; beside the script is where anyone looks for it.
# A name with a folder in it, relative or absolute, is left as written.
def beside_script(name):
    if not name or "/" in name or "\\" in name:
        return name

    script = getattr(API, "ScriptPath", None) or ""
    cut = max(script.rfind("/"), script.rfind("\\"))

    # A client that does not say where the script is still runs it out of the standard folder
    if cut < 0:
        return SCRIPTS_FOLDER + "/" + name

    return script[:cut + 1] + name


def append_line(path, line):
    handle = open(path, "a")

    try:
        handle.write(line + "\n")
    finally:
        handle.close()


# src/uo/gainpath.py
COMMAND = "[SkillGainMode"
PROMPT = "skill gain path is"
PATHS = ("Modern", "Legacy", "Perilous")


def _named(text):
    low = (text or "").lower()
    at = low.find(PROMPT)

    if at < 0:
        return None

    words = words_of(text[at + len(PROMPT):])

    for path in PATHS:
        if path.lower() in words:
            return path

    return None


# Sent once per run, ahead of the loop that records attempts: the client answers "Your skill gain
# path is Modern. This character's ..." and every recorded row carries whichever of Modern, Legacy
# or Perilous follows.
def read_gain_path(budget, poll, log):
    API.Msg(COMMAND)

    waited = 0.0

    while not API.StopRequested:
        for entry in API.GetJournalEntries(budget + poll) or []:
            path = _named(getattr(entry, "Text", None))

            if path is not None:
                return path

        if waited >= budget:
            log("no skill gain path reported - recording without one")
            return None

        API.Pause(poll)
        waited += poll

    return None


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


class AttemptLog(object):
    """One JSON object per attempt, appended as it happens.

    A row is buffered when the attempt resolves and written when the *next* attempt is recorded,
    carrying that attempt's starting value as its own end: the client applies a gain some time after
    the outcome, and a value read on the next cycle still misses one that lands during a pause,
    where the next attempt's read cannot. close() writes the last row at the end of the run. The
    cost is one row in the air at any moment, which a killed script loses; the alternative is a
    file that under-reports every gain it exists to measure.
    """

    def __init__(self, path, character, serial, skill, log, append=None, gain_path=None):
        self._path = path or ""
        self._character = character or ""
        self._serial = serial
        self._skill = skill
        self._gain_path = gain_path
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

    # The end of the run. skill_to is None only where no reading ever arrived, and the row is
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
            '"gainPath":%s' % (quoted(self._gain_path) if self._gain_path else "null"),
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

    where = beside_script(path)

    if where:
        log("recording to %s" % where)

    gain_path = read_gain_path(GAIN_PATH_TIMEOUT, GAIN_PATH_POLL, log) if where else None

    return AttemptLog(where, getattr(me, "Name", ""), getattr(me, "Serial", 0), skill, log,
                       gain_path=gain_path)


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
        self._last = None

    def read(self):
        skill = API.GetSkill(self._name)

        if skill is None:
            return None

        value = skill.Value

        if value <= 0.0 and not self._seen:
            return None

        self._seen = True
        self._last = value

        return value

    # Once the stop button is pressed the client answers nothing, so the last row of a run would
    # end unknown; the latest reading that did arrive is never further off than that
    def last(self):
        value = self.read()

        return value if value is not None else self._last

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
                return self._accept_zero()

            API.Pause(poll)
            waited += poll

        return None

    # A 0 the client still answers once the wait is over is a real 0, not an unsent skill list
    def _accept_zero(self):
        skill = API.GetSkill(self._name)

        if skill is None:
            return None

        self._seen = True
        self._last = skill.Value

        return skill.Value


# src/uo/target.py
# The serial one cursor answered, or None for ESC or a timeout. Clears a cursor left open from
# before, and the one just answered too, so a target flag never survives past it.
def request_one(timeout):
    if API.HasTarget():
        API.CancelTarget()

    serial = API.RequestTarget(timeout)

    if API.HasTarget():
        API.CancelTarget()

    return serial or None


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
                # The button means the player has judged it safe, so every ambush line from while
                # the gump was up is stale - including the hold's own log line, which the client
                # files in the journal and which carries the very phrase this watch waits on
                forget(self._config["ambush_text"])
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


# src/uo/vitals.py
def weight_reading():
    me = player()

    return "?/?" if me is None else "%d/%d" % (me.Weight, me.WeightMax)


def where():
    me = player()

    return "somewhere" if me is None else "at %d,%d" % (me.X, me.Y)


def position_and_weight():
    return "%s, %s" % (where(), weight_reading())


# src/fishing/index.py
log = make_log("fishing")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "casts", position_and_weight)

skill_name = find_skill_name(SKILL_NAMES)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(skill_name)])


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

# Hold.wait() calls heartbeat.reset() - the only reason this script keeps one at all
hold_ambush = Hold({
    "text": AMBUSH_HOLD_TEXT,
    "button": AMBUSH_HOLD_BUTTON,
    "hue": AMBUSH_HOLD_HUE,
    "poll": AMBUSH_HOLD_POLL,
}, log, stop_reason, heartbeat)

hold_boat_stopped = Hold({
    "text": BOAT_STOPPED_HOLD_TEXT,
    "button": AMBUSH_HOLD_BUTTON,
    "hue": BOAT_STOPPED_HUE,
    "poll": AMBUSH_HOLD_POLL,
}, log, stop_reason, heartbeat)

# No companion aboard: fishing has no pet to lose track of, so both watches take no-ops for it
threat_ambush = ThreatWatch({
    "watch": WATCH_FOR_TROUBLE,
    "range": THREAT_RANGE,
    "ambush_text": AMBUSH_TEXT,
    "ambush_alarm": AMBUSH_ALARM,
    "ambush_notices": AMBUSH_NOTICES,
    "ambush_warning": AMBUSH_WARNING,
    "ambush_hue": AMBUSH_HUE,
    "ambush_repeats": AMBUSH_REPEATS,
}, log, lambda: None, lambda friend: "", hold_ambush if AMBUSH_HOLD else None)

# The same mechanism as an ambush - sound, HeadMsg, notices, an optional hold - just a different
# trigger phrase and wording
threat_boat_stopped = ThreatWatch({
    "watch": WATCH_FOR_TROUBLE,
    "range": THREAT_RANGE,
    "ambush_text": BOAT_STOPPED_TEXT,
    "ambush_alarm": AMBUSH_ALARM,
    "ambush_notices": AMBUSH_NOTICES,
    "ambush_warning": BOAT_STOPPED_WARNING,
    "ambush_hue": BOAT_STOPPED_HUE,
    "ambush_repeats": AMBUSH_REPEATS,
}, log, lambda: None, lambda friend: "", hold_boat_stopped if BOAT_STOPPED_HOLD else None)

CAST_CONFIG = {
    "cursor_timeout": CURSOR_TIMEOUT,
    "cursor_poll": CURSOR_POLL,
    "prompt_text": PROMPT_TEXT,
    "no_cursor_read": NO_CURSOR_READ,
    "cast_timeout": CAST_TIMEOUT,
    "cast_poll": CAST_POLL,
    "caught_text": CAUGHT_TEXT,
    "tail_seconds": JOURNAL_TAIL_SECONDS,
    "tail_lines": JOURNAL_TAIL_LINES,
}


def pack_counts():
    return counts_by_graphic(pack_contents())


def pack_total(counts):
    return sum(counts.values())


# Measured off the pack rather than read off the journal: the line names the catch, the pack says
# what art it arrived as
def record_cast(recorder, skill, start, outcome, caught, before):
    if outcome == "caught":
        settled(CATCH_SETTLE, CATCH_POLL, lambda: pack_total(pack_counts()) > pack_total(before))

    gained, _lost = diff_counts(before, pack_counts())
    rows = [(caught, graphic, hue, quantity)
            for (graphic, hue), quantity in sorted(gained.items())]

    recorder.record(start, outcome, "fishing pole", gained=rows)
    settled(GAIN_SETTLE, GAIN_POLL, lambda: skill.read() != start)
    recorder.close(skill.last())


def gained_items(before):
    settled(CATCH_SETTLE, CATCH_POLL, lambda: pack_total(pack_counts()) > pack_total(before))
    gained, _lost = diff_counts(before, pack_counts())

    return [item for graphic, hue in gained for item in pack_contents()
            if item.Graphic == graphic and hue_of(item) == hue]


# x/y are an offset from your own position (confirmed off TazUO's own LegionAPI.cs), so (0, 0)
# already drops at your feet - one of the eight adjacent tiles is used instead so catches spread out
# rather than stack underfoot. Picked off the clock since the sandbox has no random module
def drop_caught(before):
    for item in gained_items(before):
        x, y = DROP_OFFSETS[int(now() * 1000) % len(DROP_OFFSETS)]
        API.MoveItemOffset(item.Serial, amount_of(item), x, y, 0)


def move_caught(container, before):
    for item in gained_items(before):
        API.MoveItem(item.Serial, container, amount_of(item))
        API.Pause(MOVE_DELAY)


skill = SkillReader(skill_name or SKILL_NAMES[0])
recorder = attempt_log(DATA_PATH if skill_name else "", skill.name(), log)

stop = None
start = None

if skill_name is None:
    stop = "the client reports none of %s - check SKILL_NAMES" % ", ".join(SKILL_NAMES)
else:
    start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)

    if start is None:
        stop = "%s is not reading yet - run it again once the skill list has arrived" % skill_name

container = None

if stop is None:
    answers = StartPrompt({
        "tiles_text": TILES_AHEAD_PROMPT_TEXT,
        "tiles_default": TILES_AHEAD_DEFAULT,
        "tiles_hue": TILES_AHEAD_HUE,
        "catch_text": CATCH_MODE_TEXT,
        "catch_options": CATCH_MODE_OPTIONS,
        "catch_default": CATCH_MODE_DEFAULT,
        "catch_hue": CATCH_MODE_HUE,
        "poll": TILES_AHEAD_POLL,
    }, log, stop_reason).ask()
    tiles_ahead = answers["tiles_ahead"]
    catch_mode = answers["catch_mode"]
    log.enabled = answers["debug_logs"]

    if catch_mode == "container":
        log("target the container to move junk catches into - ESC keeps them in the pack instead")
        serial = request_one(PICK_TIMEOUT)

        if serial is not None and serial != API.Backpack:
            container = serial
            log("moving junk catches into %s" % hex_of(container))
        else:
            catch_mode = "keep"
            log("nothing picked - junk catches will stay in the pack")

    angler = Angler(OUTCOME_TEXT, CAST_CONFIG, log, log.stamp)
    log("%s at %s, aiming %d tiles ahead, junk catches: %s"
        % (skill_name, reading(start), tiles_ahead, catch_mode))

    # Said once, before the loop: the pets stay guarding, so this does not need repeating every cast
    if GUARD_PHRASE:
        API.Msg(GUARD_PHRASE)

tally = 0
fails = 0
unknown = 0
throttled = 0
reported = 0
cycle = 0
unreadable_reports = 0

try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1
        stop = stop_reason()

        if stop is not None:
            break

        # A frozen shard reads as every failure below, so it is waited out before any of them
        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            continue

        threat_ambush.look()
        threat_boat_stopped.look()

        # Asked every cycle, so a remount costs a single cycle instead of the rest of the run
        if not dismount(DISMOUNT_ATTEMPTS, DISMOUNT_TIMEOUT, DISMOUNT_POLL):
            stop = "could not get off the mount"
            break

        pole = find_pole(POLE_GRAPHICS, POLE_NAME_WORDS, HAND_LAYERS, log)

        if pole is None:
            stop = "no fishing pole in hand or in the pack"
            break

        turn_toward_water(tiles_ahead, WATER_LAND_GRAPHICS, WATER_STATIC_GRAPHICS, TURN_DELAY)
        tile = tile_ahead(tiles_ahead, WATER_LAND_GRAPHICS, WATER_STATIC_GRAPHICS,
                         LAND_TILE_GRAPHIC)
        log("casting at %d,%d,%d (graphic %s, %s), standing at %d,%d, facing %s"
            % (tile["x"], tile["y"], tile["z"], hex_of(tile["graphic"]), tile["source"],
               API.Player.X, API.Player.Y, API.Player.Direction))
        value = skill.read()
        before = pack_counts()
        outcome, caught = angler.cast_once(pole, tile)

        # Recorded before the item moves - drop_caught/move_caught's own diff would otherwise see
        # nothing gained, the item having already left the pack they are both diffing against
        if outcome in ("caught", "failed") and recorder.recording():
            record_cast(recorder, skill, value, outcome, caught, before)

        if outcome == "caught" and any_in(caught, JUNK_TEXT):
            if catch_mode == "discard":
                drop_caught(before)
            elif catch_mode == "container":
                move_caught(container, before)

        if outcome == "caught":
            tally += 1
            unknown = 0
            throttled = 0
            unreadable_reports = 0
            log("caught %s" % (caught or "something the journal did not name"))
        elif outcome == "failed":
            tally += 1
            fails += 1
            unknown = 0
            throttled = 0
        elif outcome == "saving":
            saves.wait_out()
            unknown = 0
            throttled = 0
        elif outcome == "throttled":
            throttled += 1
            unknown = 0
            log("shard says wait (%d/%d), backing off" % (throttled, MAX_THROTTLED))
            API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

            if throttled >= MAX_THROTTLED:
                stop = "the shard kept refusing the cast"
                break
        elif outcome in ("empty", "tooFar", "notWater", "mounted", "busy"):
            unknown = 0
        # An unreadable outcome does not stop the run - only noCursor counts toward MAX_UNKNOWN. A
        # short CAST_TIMEOUT hits this often as a matter of course, so the journal dump is capped
        # rather than printed every time - MAX_UNREADABLE_REPORTS resets once a catch lands clean
        elif outcome == "unknown":
            if unreadable_reports < MAX_UNREADABLE_REPORTS:
                unreadable_reports += 1
                log("unreadable outcome (%d/%d shown), check OUTCOME_TEXT"
                    % (unreadable_reports, MAX_UNREADABLE_REPORTS))

                for line in journal_tail(JOURNAL_TAIL_SECONDS, JOURNAL_TAIL_LINES, log.stamp):
                    log("  " + line)
        # noCursor: the pole raised no cursor and the shard said nothing either
        else:
            unknown += 1
            log("no target cursor (%d/%d), backing off" % (unknown, MAX_UNKNOWN))
            API.Pause(backoff_for(unknown, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

        if unknown >= MAX_UNKNOWN:
            stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
            break

        if tally >= reported + LOG_EVERY:
            reported = tally
            log("%d casts, %d caught, %d failed" % (tally, tally - fails, fails))

        API.Pause(STEP_DELAY)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    if stop is None:
        stop = "threw - %s" % error
finally:
    recorder.close(skill.last())

if API.Pathfinding():
    API.CancelPathfinding()

reason = stop or "hit the %d working cycle backstop" % MAX_CYCLES

log("%d casts, %d caught, %d failed" % (tally, tally - fails, fails))
log("stopping - %s" % reason)
API.Stop()
