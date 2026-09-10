# Built from src/fishing/index.py by build.py - do not edit.

import API
import time


# src/uo/journal.py
def said(texts):
    for text in texts:
        if API.InJournal(text, False):
            return True

    return False


# matchingText is left off on purpose: the client only applies it as a regex, so a plain string
# there filters everything out
def journal_tail(seconds, limit):
    try:
        entries = API.GetJournalEntries(seconds)
    except Exception:
        if API.StopRequested:
            raise

        return []

    texts = []

    for entry in entries if entries else []:
        text = getattr(entry, "Text", None)

        if text and text.strip():
            texts.append(text.strip())

    return texts[-limit:]


# Line by line rather than the whole journal: a wholesale clear before every swing wiped the ambush
# warning before the threat watch got its once-a-cycle look at it
def forget(phrases):
    for text in phrases:
        API.ClearJournal(text)


def forget_outcomes(buckets):
    for _name, phrases in buckets:
        forget(phrases)


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


# src/fishing/angler.py
def caught_name(lines, fragments):
    for line in reversed(lines):
        if any_in(line, fragments):
            return line.partition(":")[2].strip()

    return None


class Angler(object):
    """One cast: the pole, the cursor, the water tile, the shard's answer."""

    def __init__(self, buckets, config, log):
        self._buckets = buckets
        self._config = config
        self._log = log
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
        return caught_name(journal_tail(self._config["tail_seconds"], self._config["tail_lines"]),
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

# Ends in a bare 'You must wait', which longer refusals contain - so a bucket that has to be told
# apart from a throttle is ordered before this one
THROTTLED_TEXT = [
    "You must wait to perform another action",
    "You must wait a moment",
    "You must wait",
]


# src/fishing/config.py
# One JSON object per cast, for legion/skilldb.py. "" turns recording off. A bare name lands in
# TazUO's working directory, not beside the script.
DATA_PATH = "skill-attempts.jsonl"

SKILL_NAMES = ["Fishing"]

# Said once, before the cast. "" says nothing.
GUARD_PHRASE = "all guard"

POLE_GRAPHICS = set([0x0DBF])
POLE_NAME_WORDS = ["fishing", "pole"]

# Two-handed on stock shards; the other layer is for a reskinned one
HAND_LAYERS = ["twohanded", "onehanded"]

# Stock RunUO Fishing.cs bands, a hypothesis about this shard. Land and statics are numbered apart,
# and the static bands are RunUO's 0x4000-offset ids brought back down.
WATER_LAND_GRAPHICS = set()
for _low, _high in [(0x00A8, 0x00AB), (0x0136, 0x0137)]:
    for _water in range(_low, _high + 1):
        WATER_LAND_GRAPHICS.add(_water)

WATER_STATIC_GRAPHICS = set()
for _low, _high in [(0x1797, 0x179C), (0x346E, 0x3485), (0x3490, 0x34AB), (0x34B5, 0x35D5)]:
    for _water in range(_low, _high + 1):
        WATER_STATIC_GRAPHICS.add(_water)

# RunUO's fishing range: past it the shard says to stand closer to the water
FISH_RANGE = 4

# The cursor prompt is a guess; HasTarget is what the wait leans on
PROMPT_TEXT = ["Where do you want to fish"]

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


# src/uo/crafttool.py
class CraftTool(object):
    """A crafting tool, used out of the pack rather than equipped."""

    def __init__(self, noun, graphics, name_words, log, prefer=None):
        self._noun = noun
        self._graphics = graphics
        self._name_words = name_words
        self._log = log
        self._prefer = prefer or set()

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


# src/uo/clock.py
def now():
    return time.time()


# src/uo/scan.py
def chebyshev_to(tile):
    return max(abs(tile["x"] - API.Player.X), abs(tile["y"] - API.Player.Y))


# src/fishing/water.py
def is_water(tile, land_graphics, static_graphics):
    table = land_graphics if tile["is_land"] else static_graphics

    return tile["graphic"] in table


# Nearest by crow flight and nothing else: the run never walks, so there is no route to price
def nearest_water(terrain, radius, land_graphics, static_graphics):
    found = [tile for tile in terrain.box(radius)
             if is_water(tile, land_graphics, static_graphics)]

    if not found:
        return None

    found.sort(key=chebyshev_to)

    return found[0]


# src/uo/guards.py
def first_reason(clauses):
    for clause in clauses:
        reason = clause()

        if reason is not None:
            return reason

    return None


def dead():
    def clause():
        me = player()

        return "you are dead" if me is not None and me.IsDead else None

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


# src/uo/log.py
def make_log(prefix):
    def log(message):
        API.SysMsg(prefix + ": " + message)

    return log


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

    A row is buffered when the attempt resolves and written on the *next* skill read, because the
    client applies a gain some time after the outcome and a value read straight away is usually
    still the old one. The cost of that is one row in the air at any moment, which a killed script
    loses; the alternative is a file that under-reports every gain it exists to measure.
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

        # A caller that records twice without settling in between would otherwise drop the first
        # row. This later read is exactly what the missed settle would have passed.
        self.settle(skill_from)

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

    def settle(self, skill_to):
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


# src/uo/terrain.py
# Plain Python types, not the client's sbyte and ushort: json cannot write those, and a .NET string
# is only a str by courtesy
def land_tile(x, y, land):
    return {"x": int(x), "y": int(y), "z": int(land.Z), "graphic": int(land.Graphic),
            "is_land": True, "name": ""}


def static_tile(x, y, static):
    return {"x": int(x), "y": int(y), "z": int(static.Z), "graphic": int(static.Graphic),
            "is_land": False, "name": str(static.Name or "")}


class Terrain(object):
    """Land and statics do not change during a session, so a coordinate is read once. Every read is
    a client frame, which is why the statics of a box come in one call and the land only on demand."""

    def __init__(self):
        self._land = {}
        self._statics = {}
        self._fresh = set()
        self.reads = 0

    def _land_at(self, x, y):
        cached = self._land.get((x, y))

        if cached is None:
            self.reads += 1
            land = API.GetTile(x, y)
            cached = [land_tile(x, y, land)] if land is not None else []
            self._land[(x, y)] = cached
            self._fresh.add((x, y))

        return cached

    def _statics_at(self, x, y):
        cached = self._statics.get((x, y))

        if cached is None:
            self.reads += 1
            cached = [static_tile(x, y, static) for static in API.GetStaticsAt(x, y) or []]
            self._statics[(x, y)] = cached
            self._fresh.add((x, y))

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
            self._fresh.add((x, y))

    def remember(self, x, y, land, statics):
        self._land[(x, y)] = land
        self._statics[(x, y)] = statics

    # Coordinates read this session with both halves in, handed out once
    def fresh(self):
        done = [xy for xy in self._fresh if xy in self._land and xy in self._statics]
        self._fresh.difference_update(done)

        return [(xy, self._land[xy], self._statics[xy]) for xy in sorted(done)]

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


# src/fishing/index.py
log = make_log("fishing")

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

ENDINGS = {
    "failed": "nothing bit",
    "empty": "the fish are not biting here - try further along the shore",
    "tooFar": "the shard says the water is out of reach - stand closer to it",
    "notWater": "the shard says that tile is not water - check WATER_LAND_GRAPHICS and "
                "WATER_STATIC_GRAPHICS",
    "mounted": "the shard says you are still mounted",
    "saving": "the world is saving - run it again in a moment",
    "throttled": "the shard says wait - run it again in a moment",
    "noCursor": "the pole raised no cursor",
    "unknown": "unreadable outcome, check OUTCOME_TEXT",
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
    recorder.settle(skill.read())


def fish():
    if API.HasTarget():
        API.CancelTarget()

    skill_name = find_skill_name(SKILL_NAMES)

    if skill_name is None:
        return "the client reports none of %s - check SKILL_NAMES" % ", ".join(SKILL_NAMES)

    skill = SkillReader(skill_name)
    start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)

    if start is None:
        return "%s is not reading yet - run it again once the skill list has arrived" % skill_name

    reason = first_reason([dead(), skill_capped(skill_name)])

    if reason is not None:
        return reason

    if not dismount(DISMOUNT_ATTEMPTS, DISMOUNT_TIMEOUT, DISMOUNT_POLL):
        return "could not get off the mount"

    if GUARD_PHRASE:
        API.Msg(GUARD_PHRASE)

    pole = find_pole(POLE_GRAPHICS, POLE_NAME_WORDS, HAND_LAYERS, log)

    if pole is None:
        return "no fishing pole in hand or in the pack"

    tile = nearest_water(Terrain(), FISH_RANGE, WATER_LAND_GRAPHICS, WATER_STATIC_GRAPHICS)

    if tile is None:
        return "no water within %d tiles" % FISH_RANGE

    log("%s at %s, casting at %d,%d" % (skill_name, reading(start), tile["x"], tile["y"]))

    recorder = attempt_log(DATA_PATH, skill_name, log)
    before = pack_counts() if recorder.recording() else {}
    outcome, caught = Angler(OUTCOME_TEXT, CAST_CONFIG, log).cast_once(pole, tile)

    if outcome in ("caught", "failed") and recorder.recording():
        record_cast(recorder, skill, start, outcome, caught, before)

    if outcome == "caught":
        return "caught %s" % (caught or "something the journal did not name")

    if outcome == "unknown":
        for line in journal_tail(JOURNAL_TAIL_SECONDS, JOURNAL_TAIL_LINES):
            log("  " + line)

    return ENDINGS.get(outcome, outcome)


try:
    ending = fish()
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    ending = "threw - %s" % error

log(ending)
API.Stop()
