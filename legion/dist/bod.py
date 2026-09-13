# Built from src/bod/index.py by build.py - do not edit.

import API
import time
import clr
import System


# src/bod/deed.py
def strip_article(name, articles):
    for article in articles:
        if name.startswith(article):
            return name[len(article):]

    return name


def to_int(text):
    try:
        return int(text.strip())
    except ValueError:
        return None


def parse_deed(lines, config):
    text = config["text"]
    low = [line.strip().lower() for line in lines if line and line.strip()]
    total = None
    exceptional = False
    large = False
    material = config["plain"]
    items = []

    for line in low:
        if text["large"] in line:
            large = True
        elif line.startswith(text["amount"]):
            total = to_int(line[len(text["amount"]):])
        elif text["exceptional"] in line:
            exceptional = True
        elif text["material_before"] in line:
            after = line.split(text["material_before"], 1)[1]
            material = after.replace(text["material_after"], "").strip(" .")
        elif ":" in line:
            name, count = line.rsplit(":", 1)
            done = to_int(count)

            if done is not None:
                items.append((strip_article(name.strip(), config["articles"]), done))

    if total is None or len(items) == 0:
        return None, "could not read it - the tooltip says '%s'" % " | ".join(low)

    request = {
        "large": large or len(items) > 1,
        "entries": items,
        "total": total,
        "exceptional": exceptional,
        "material": material,
    }

    if not request["large"]:
        request["item"] = items[0][0]
        request["done"] = items[0][1]

    return request, None


def entry_request(request, item, done):
    return {
        "large": False,
        "entries": [(item, done)],
        "item": item,
        "done": done,
        "total": request["total"],
        "exceptional": request["exceptional"],
        "material": request["material"],
    }


class Deed(object):
    def __init__(self, serial, config, log):
        self.serial = serial
        self._config = config
        self._log = log
        self.request = None
        self._said_behind = False

    def _lines(self):
        props = API.ItemNameAndProps(self.serial, True, self._config["opl_timeout"]) or ""

        return [line.strip() for line in props.splitlines() if line.strip()]

    def read(self):
        request, why = parse_deed(self._lines(), self._config)

        if request is not None:
            self.request = request

        return request, why

    def describe(self):
        request = self.request
        flags = "%s, %s" % (", exceptional" if request["exceptional"] else "", request["material"])

        if request["large"]:
            return "large deed x%d: %s%s" % (
                request["total"],
                ", ".join("%s (%d done)" % entry for entry in request["entries"]), flags)

        return "%s x%d, %d done%s" % (request["item"], request["total"], request["done"], flags)

    # Asked for once, then read as it stands: a wait per read would stretch the settle by its
    # timeout on every poll
    def _lines_now(self):
        props = API.ItemNameAndProps(self.serial, False) or ""

        return [line.strip() for line in props.splitlines() if line.strip()]

    # The pack proved the combine; the tooltip catches up later, or on some builds never
    def settle_after_combine(self, count):
        waited = 0.0
        API.RequestOPLData([self.serial])

        while not API.StopRequested:
            request, _why = parse_deed(self._lines_now(), self._config)

            if request is not None and request["done"] >= count:
                if request["done"] > count:
                    self._log("the deed says %d done, more than the %d counted - taking the deed's"
                              % (request["done"], count))

                self.request["done"] = request["done"]

                return request["done"]

            if waited >= self._config["reread_settle"]:
                break

            API.Pause(self._config["reread_poll"])
            waited += self._config["reread_poll"]

        if not self._said_behind:
            self._said_behind = True
            self._log("the deed's tooltip is behind the count - trusting the pack from here on")

        self.request["done"] = count

        return count


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


def untagged(text):
    kept = []
    inside = False

    for char in text or "":
        if char == "<":
            inside = True
        elif char == ">":
            inside = False
        elif not inside:
            kept.append(char)

    return "".join(kept)


def clipped(text, limit):
    flat = " ".join((text or "").split())

    return flat if len(flat) <= limit else flat[:limit] + "..."


# A craft gump is a header, then a notice, then every row it can make: the sentence talking to you
# sits in the middle, where neither end of a clip reaches it
def spoken(text, word, limit):
    flat = " ".join((text or "").split())
    at = flat.lower().find(word.lower())

    if at <= 0:
        return clipped(flat, limit)

    return "..." + clipped(flat[at:], limit)


# src/bod/smalls.py
def is_deed(item, config):
    return item.Graphic in config["deed_graphics"] or any_in(item.Name, config["deed_words"])


def matches(small, large):
    return (not small["large"]
            and small["item"] in [item for item, _done in large["entries"]]
            and small["total"] == large["total"]
            and small["exceptional"] == large["exceptional"]
            and small["material"] == large["material"])


# The small deeds in the pack that belong to the large one, the fuller of two for one item
def find_small_deeds(large, large_serial, config):
    found = {}

    for item in pack_contents():
        if item.Serial == large_serial or not is_deed(item, config):
            continue

        props = API.ItemNameAndProps(item.Serial, True, config["opl_timeout"]) or ""
        small, _why = parse_deed(props.splitlines(), config)

        if small is None or not matches(small, large):
            continue

        known = found.get(small["item"])

        if known is None or small["done"] > known["done"]:
            found[small["item"]] = {"serial": item.Serial, "done": small["done"]}

    return found


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


# src/uo/retry.py
def settled(timeout, poll, landed):
    waited = 0.0

    while waited < timeout:
        API.Pause(poll)
        waited += poll

        if landed():
            return True

    return False


# src/bod/box.py
class DeedBox(object):
    """The Bulk Order Deed Box: one large deed in, the small deeds and the large back out."""

    def __init__(self, config, log):
        self._config = config
        self._log = log

    def find(self):
        for item in pack_contents():
            if any_in(item.Name, self._config["names"]):
                return item.Serial

        return None

    def _deeds(self):
        return set(item.Serial for item in pack_contents() if is_deed(item, self._config))

    def _container_of(self, serial):
        item = API.FindItem(serial)

        return None if item is None else getattr(item, "Container", None)

    def generate(self, box, large):
        before = self._deeds()

        API.MoveItem(large, box)
        API.Pause(self._config["move_delay"])

        if self._container_of(large) != box:
            self._log("the large deed did not go into the box - it is in %s"
                      % hex_of(self._container_of(large) or 0))

            return None

        API.UseObject(box)

        def landed():
            return (self._container_of(large) == API.Backpack
                    and len(self._deeds() - before) > 0)

        if not settled(self._config["timeout"], self._config["poll"], landed):
            back = self._container_of(large) == API.Backpack
            self._log("the box put no deeds in the pack within %.0fs%s"
                      % (self._config["timeout"],
                         "" if back else " - and the large deed is still in it"))

            return []

        # The box drops them in one go, but the client lists them as they arrive
        API.Pause(self._config["move_delay"])
        fresh = sorted(self._deeds() - before)
        self._log("the box put %d deed(s) in the pack" % len(fresh))

        return fresh


# src/bod/checks.py
def is_ingot(item, config):
    return item.Graphic in config["ingot_graphics"] or word_in(item.Name, config["ingot_words"])


# The name is where the shard writes the metal ('Valorite Ingots'); plain ingots carry none and
# fall through to the hue
def material_of(item, config):
    words = words_of(item.Name)

    for material in config["materials"]:
        wanted = words_of(material)

        if words[:len(wanted)] == wanted:
            return material

    hue = hue_of(item)

    return config["hues"].get(hue, "hue 0x%x" % hue)


def ingot_counts(config):
    counts = {}

    for item in pack_contents():
        if not is_ingot(item, config):
            continue

        material = material_of(item, config)
        counts[material] = counts.get(material, 0) + amount_of(item)

    return counts


def ingot_report(config):
    counts = ingot_counts(config)

    if len(counts) == 0:
        return "no ingots"

    return ", ".join("%d %s" % (counts[name], name) for name in sorted(counts))


def uses_of(props, config):
    for line in (props or "").splitlines():
        low = line.strip().lower()

        if config["uses_text"] in low and ":" in low:
            return to_int(low.rsplit(":", 1)[1])

    return None


# Every tool's charges added up, and how many tools said nothing
def tool_uses(serials, config):
    total = 0
    unread = 0

    for serial in serials:
        uses = uses_of(API.ItemNameAndProps(serial, True, config["opl_timeout"]), config)

        if uses is None:
            unread += 1
        else:
            total += uses

    return total, unread


# Problems stop the run; notes are said and the run goes on. Requests are summed: a large deed
# is checked as every small it still needs
def preflight(requests, tool_serials, config):
    problems = []
    notes = []
    owed = 0
    unknown = []
    needed = {}
    exceptional = False

    for request in requests:
        pieces = request["total"] - request["done"]
        owed += pieces
        exceptional = exceptional or request["exceptional"]
        cost = config["costs"].get(request["item"])

        if cost is None:
            unknown.append(request["item"])
        else:
            needed[request["material"]] = needed.get(request["material"], 0) + cost * pieces

    if len(unknown) > 0:
        notes.append("no ingot cost is known for %s, so those are not checked"
                     % ", ".join("'%s'" % item for item in unknown))

    held = ingot_counts(config)

    for material in sorted(needed):
        have = held.get(material, 0)

        if have < needed[material]:
            problems.append("%d %s ingots for the %d pieces owed, and the pack holds %d"
                            % (needed[material], material, owed, have))
        else:
            notes.append("%d %s ingots cover the %d pieces owed, %d in the pack"
                         % (needed[material], material, owed, have))

    uses, unread = tool_uses(tool_serials, config)

    if unread == len(tool_serials):
        notes.append("no tool reports its uses remaining, so the charges are not checked")
    elif uses < owed:
        problems.append("%d uses left across %d tool(s) for %d pieces owed"
                        % (uses, len(tool_serials), owed))
    else:
        notes.append("%d uses left across %d tool(s) for %d pieces owed"
                     % (uses, len(tool_serials), owed))

    if exceptional and len(problems) == 0:
        notes.append("an exceptional deed takes more crafts than pieces - the counts above cover "
                     "the pieces only")

    return problems, notes


# src/uo/gump.py
# HasGump() only ever answers the last gump the shard sent, and a gump the shard re-sends on its own
# steals that slot: the id-addressed calls below do not go through it
def open_ids():
    found = []
    last = API.HasGump()

    if last:
        found.append(last)

    try:
        for gump in API.GetAllGumps() or []:
            serial = getattr(gump, "ServerSerial", 0)

            if serial and serial not in found:
                found.append(serial)
    except Exception:
        if API.StopRequested:
            raise

    return found


def is_open(ident):
    return bool(ident) and bool(API.WaitForGump(ident, 0))


def await_gump(ident, timeout):
    if not ident:
        return 0

    return ident if API.WaitForGump(ident, timeout) else 0


# A getter can throw on its own (Control.X does), which is not the whole gump being unreadable
def _field(control, name):
    try:
        return getattr(control, name, None)
    except Exception:
        if API.StopRequested:
            raise

        return None


# The controls in the order the layout drew them, every page at once, as (button id, text) with
# None for whichever a control lacks. None for the list is "could not read them", which no caller
# treats as "none": the shard drops the connection for a button the gump does not have, so an
# unreadable gump must not be mistaken for an empty one
def controls(ident):
    if not ident:
        return None

    try:
        gump = API.GetGump(ident)

        if gump is None:
            return None

        found = []

        for control in gump.Children or []:
            button = _field(control, "ButtonID")
            text = _field(control, "Text")

            found.append((None if button is None else int(button), text or None))

        return found
    except Exception:
        if API.StopRequested:
            raise

        return None


def button_ids(ident):
    read = controls(ident)

    if read is None:
        return None

    return set(button for button, _text in read if button is not None)


# A recognised gump wins; failing that, one that was not up before the use. Returns (id, recognised)
def await_recognised(known, before, timeout, poll):
    waited = 0.0
    newcomer = 0

    while waited < timeout:
        for ident in open_ids():
            if known(ident):
                return ident, True

            if not newcomer and ident not in before:
                newcomer = ident

        if newcomer:
            return newcomer, False

        API.Pause(poll)
        waited += poll

    return 0, False


def gump_says(gump, texts):
    for text in texts:
        if API.GumpContains(text, gump):
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


# What the shard itself speaks under - anything else in the journal is a mobile in earshot
SHARD_SPEAKERS = ["", "system"]


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


# What the shard said is preferred rather than kept alone: a chatty NPC used to fill the whole tail
# and evict the line a craft was reported on, but a shard answering under some other name still has
# to reach the report. shard_first off keeps every speaker, which is what the notes file wants.
def journal_report(seconds, limit, stamp=None, shard_first=True):
    entries = journal_entries(seconds, stamp)
    me = player()
    speakers = SHARD_SPEAKERS + [(getattr(me, "Name", "") or "").strip().lower()]
    theirs = [pair for pair in entries if pair[0].lower() in speakers]
    shown = (theirs or entries) if shard_first else entries

    if limit is not None:
        shown = shown[-limit:]

    return [text if name.lower() in speakers else "%s: %s" % (name, text)
            for name, text in shown]


# Line by line rather than the whole journal: a wholesale clear before every swing wiped the ambush
# warning before the threat watch got its once-a-cycle look at it
def forget(phrases):
    for text in phrases:
        API.ClearJournal(text)


def matched_bucket(buckets):
    for name, phrases in buckets:
        # clearMatches, or a line already read answers the next wait as well
        if API.InJournalAny(phrases, True):
            return name

    return None


# src/uo/clock.py
def now():
    return time.time()


def time_text():
    return time.strftime("%Y-%m-%d %H:%M:%S")


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


# src/uo/notes.py
class NoteLog(object):
    """One block per report, appended to a file beside the script."""

    def __init__(self, path, log, append=None):
        self._path = path or ""
        self._log = log
        self._append = append if append is not None else append_line
        self._off = not self._path
        self._said = False

    def writing(self):
        return not self._off

    def where(self):
        return self._path

    def write(self, heading, rows):
        if self._off:
            return

        out = ["[%s] %s" % (time_text(), heading)]

        for label, values in rows:
            out.append("  %s:" % label)

            for value in values or ["(nothing)"]:
                out.append("    %s" % value)

        self._put("\n".join(out))

    # A run that cannot write its notes is still a run: the sink retires itself and says so once
    def _put(self, block):
        try:
            self._append(self._path, block)
        except Exception as error:
            self._off = True

            if not self._said:
                self._said = True
                self._log("cannot write %s (%s) - not writing notes this run"
                          % (self._path, error))


def note_log(path, log):
    return NoteLog(beside_script(path), log)


class Reporter(object):
    """What a craft could not read: a short line in the window, the whole of it in the notes.

    The window quotes the gump from the shard's own sentence on: the header before it and the rows
    after it are the same boilerplate every time.
    """

    def __init__(self, lines_of, config, log, notes=None, stamp=None):
        self._lines_of = lines_of
        self._config = config
        self._log = log
        self._notes = notes
        self._stamp = stamp
        self._said = 0
        self._said_where = False

    def forget(self):
        self._said = 0

    # extra is (label, sentence) pairs: the window says the sentence, the notes file labels it
    def say(self, why, gump, extra=None):
        text = untagged(" ".join(self._lines_of(gump))) if gump else ""
        rest = list(extra or [])

        self._write(why, text, rest)

        if self._said >= self._config["max_reports"]:
            return

        self._said += 1
        lines = journal_report(self._config["tail_seconds"], self._config["tail_lines"],
                               self._stamp)

        self._log("%s - the gump says '%s'"
                  % (why, spoken(text, "you", self._config["text_limit"]) or "(nothing)"))
        self._log("the journal says '%s'" % (" | ".join(lines) or "(nothing)"))

        for _label, sentence in rest:
            self._log(sentence)

        self._say_where()

    # Said when there is something to read rather than at startup, where the form has not yet told
    # the run whether it wants any logs at all
    def _say_where(self):
        if self._notes is None or not self._notes.writing() or self._said_where:
            return

        self._said_where = True
        self._log("the whole of it is in %s" % self._notes.where())

    # Uncapped, and untruncated: the window's two reports are a pointer, the file is the evidence
    def _write(self, why, text, rest):
        if self._notes is None or not self._notes.writing():
            return

        rows = [("gump", [text] if text else []),
                ("journal", journal_report(self._config["notes_seconds"], None, self._stamp,
                                           False))]

        self._notes.write(why, rows + [(label, [sentence]) for label, sentence in rest])


# src/bod/combine.py
class DeedCombiner(object):
    """The deed's 'combine with contained items', aimed at the bag the pieces are in."""

    def __init__(self, deed, items, buckets, config, log, stamp=None, notes=None):
        self._deed = deed
        self._items = items
        self._buckets = buckets
        self._config = config
        self._log = log
        self._report = Reporter(self._lines, config, log, notes, stamp)
        self._said_gump_text = False
        self._gump = 0

    def _lines(self, gump):
        text = API.GetGumpContents(gump)

        return [line.strip() for line in (text or "").split("\n") if line.strip()]

    def _is_deed_gump(self, ident):
        return gump_says(ident, self._config["gump_text"])

    def _open(self):
        before = open_ids()

        API.UseObject(self._deed.serial)

        found, recognised = await_recognised(self._is_deed_gump, before,
                                             self._config["gump_timeout"],
                                             self._config["gump_poll"])

        if found and not recognised and not self._said_gump_text:
            self._said_gump_text = True
            lines = self._lines(found)
            self._log("the deed opened a gump that does not say bulk order - it starts '%s'"
                      % (lines[0] if lines else "(no text)"))

        self._gump = found

        return found

    # Without a book the pack itself is read, which is what the large flow watches
    def _serials(self):
        if self._items is not None:
            return self._items.serials()

        return set(item.Serial for item in pack_contents())

    def _gone(self, offered):
        here = self._serials()

        return [serial for serial in offered if serial not in here]

    # The pieces leaving the bag are the proof; the wording is read only when none did, because a
    # bag holding both kinds gets a refusal per piece alongside the successes
    def _read_outcome(self, offered):
        waited = 0.0

        while not API.StopRequested:
            gone = self._gone(offered)

            if len(gone) > 0:
                API.Pause(self._config["combine_poll"])

                return "combined", self._gone(offered)

            hit = matched_bucket(self._buckets)

            if hit is not None and hit != "combined":
                return hit, []

            if waited >= self._config["combine_timeout"]:
                return None, []

            API.Pause(self._config["combine_poll"])
            waited += self._config["combine_poll"]

    # The shard re-sends the deed gump before it raises the cursor, so one is left up either way
    def _close(self):
        if API.HasTarget():
            API.CancelTarget()

        if self._gump:
            API.CloseGump(self._gump)

    def combine(self, container, offered):
        gump = self._open()

        if not gump:
            return "noGump", []

        # The shard drops the connection for a button the gump does not have
        known = button_ids(gump)

        if known is not None and self._config["combine_button"] not in known:
            self._report.say("the deed gump has no button %d" % self._config["combine_button"], gump)

            return "noGump", []

        API.ClearJournal()

        if not API.ReplyGump(self._config["combine_button"], gump):
            return "noGump", []

        if not API.WaitForTarget("any", self._config["target_timeout"]):
            self._report.say("no cursor came up for the combine", gump)
            self._close()

            return "noCursor", []

        API.Target(container)

        outcome, taken = self._read_outcome(offered)

        if outcome is None:
            self._report.say("nothing readable came back from the combine", gump)

        self._close()

        return outcome, taken


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


# src/uo/timings.py
"""The constants the scripts agreed on. Every one is in seconds - API.Pause takes seconds."""

SAVE_WAIT = 60.0
SAVE_POLL = 1.0

THROTTLE_BACKOFF = 1.0
THROTTLE_BACKOFF_MAX = 8.0
HEARTBEAT_EVERY = 30.0

STALL_WARN = 60
STALL_STOP = 300

STEP_DELAY = 0.3


# src/bod/config.py
SKILL_NAMES = ["Blacksmithy", "Blacksmith"]

TOOL_GRAPHICS = set([
    0x13E3, 0x13E4,  # smith's hammer
    0x0FBB, 0x0FBC,  # tongs
    0x0FB4, 0x0FB5,  # sledge hammer
])

# Whole words: 'smith' is in "smith's hammer" and not in "war hammer"
TOOL_NAME_WORDS = ["tongs", "smith"]

# Used ahead of any other tool found
TOOL_PREFERENCE = set([0x0FBB, 0x0FBC])

# Opened at start so the client can see the tools inside. Matched as a name fragment.
TOOL_BAG_NAMES = ["salvage bag"]
OPEN_DELAY = 0.6

INGOT_GRAPHICS = set([0x1BF2, 0x1BEF])
INGOT_NAME_WORDS = ["ingot", "ingots"]

# What a deed that names no material wants, and the menu row it is set back to
PLAIN_MATERIAL = "iron"

# The material rows follow this toggle in the page's one-line text
MATERIAL_ROWS_AFTER = "do not color"

# The material page's rows in stock order, for a page whose text cannot be read
MATERIAL_ORDER = ["iron", "dull copper", "shadow iron", "copper", "bronze", "gold", "agapite",
                  "verite", "valorite"]

# The deed's wording first, then how the menu row and the item's tooltip may shorten it
MATERIAL_ALIASES = {
    "shadow iron": ["shadow"],
}

# For the 'the pack holds ...' line only. Incomplete on purpose: an unknown hue is reported as such
INGOT_HUES = {
    0: "iron",
    0x973: "dull copper",
    0x966: "shadow iron",
    0x96D: "copper",
    0x972: "bronze",
    0x8A5: "gold",
    0x979: "agapite",
    0x89F: "verite",
    0x8AB: "valorite",
}

# Refuse to start on too few ingots or tool charges
CHECK_BEFORE_START = True
USES_TEXT = "uses remaining"

# Ingots per piece from uoalive.com/wiki/Blacksmithy, keyed as the deed names the item. Items
# that need more than ingots are left out.
INGOT_COST = {
    "ringmail gloves": 10, "ringmail leggings": 16, "ringmail sleeves": 14, "ringmail tunic": 18,
    "chainmail coif": 10, "chainmail leggings": 18, "chainmail tunic": 20,
    "platemail arms": 18, "platemail gloves": 12, "platemail gorget": 10, "platemail legs": 20,
    "platemail tunic": 25, "platemail": 25, "female plate": 20, "female platemail": 20,
    "platemail do": 28, "platemail haidate": 20, "platemail hiro sode": 16, "platemail mempo": 18,
    "platemail suneate": 20, "gargish amulet": 3, "gargish platemail arms": 18,
    "gargish platemail chest": 25, "gargish platemail kilt": 12, "gargish platemail leggings": 20,
    "dragon barding deed": 750,
    "bascinet": 15, "close helmet": 15, "helmet": 15, "norse helm": 15, "plate helm": 15,
    "chainmail hatsuburi": 20, "platemail hatsuburi": 20, "heavy platemail jingasa": 20,
    "light platemail jingasa": 20, "small platemail jingasa": 20,
    "decorative platemail kabuto": 25, "platemail battle kabuto": 25,
    "standard platemail kabuto": 25, "circlet": 6, "royal circlet": 6,
    "buckler": 10, "bronze shield": 12, "heater shield": 18, "metal shield": 14,
    "metal kite shield": 16, "tear kite shield": 8, "chaos shield": 25, "order shield": 25,
    "small plate shield": 12, "medium plate shield": 14, "large plate shield": 18,
    "gargish kite shield": 16, "gargish chaos shield": 25, "gargish order shield": 25,
    "axe": 14, "battle axe": 14, "double axe": 12, "executioner's axe": 14,
    "large battle axe": 12, "two handed axe": 16, "war axe": 16, "ornate axe": 18,
    "dual short axes": 24, "gargish axe": 14, "gargish battle axe": 14,
    "bardiche": 18, "bladed staff": 12, "double bladed staff": 16, "halberd": 20, "lance": 20,
    "pike": 12, "short spear": 6, "scythe": 14, "spear": 12, "war fork": 12,
    "dual pointed spear": 12, "gargish bardiche": 18, "gargish lance": 20, "gargish pike": 12,
    "gargish scythe": 14, "gargish war fork": 12,
    "bone harvester": 10, "broadsword": 10, "crescent blade": 14, "cutlass": 8, "dagger": 3,
    "katana": 8, "kryss": 8, "longsword": 12, "scimitar": 10, "viking sword": 14,
    "no-dachi": 18, "wakizashi": 8, "lajatang": 25, "daisho": 15, "tekagi": 12, "shuriken": 5,
    "kama": 14, "sai": 12, "radiant scimitar": 15, "war cleaver": 18, "elven spellblade": 14,
    "assassin spike": 9, "leafblade": 12, "rune blade": 15, "elven machete": 14,
    "bloodblade": 8, "shortblade": 12, "dread sword": 14, "gargish katana": 8,
    "gargish kryss": 8, "gargish bone harvester": 10, "gargish tekagi": 12, "gargish daisho": 15,
    "gargish talwar": 18, "gargish dagger": 3,
    "hammer pick": 16, "mace": 6, "maul": 10, "scepter": 10, "war mace": 14, "war hammer": 16,
    "diamond mace": 20, "disc mace": 20, "gargish maul": 10, "gargish war hammer": 16,
    "cannonball": 12, "boomerang": 5, "cyclone": 9, "soul glaive": 9, "metal keg": 25,
}

# Deeds in the pack, for the large flow: the stock art, or the name
DEED_GRAPHICS = set([0x2258])
DEED_NAME_WORDS = ["bulk order deed"]

# The Bulk Order Deed Box: one large deed in, the smalls and the large back in the pack
BOX_NAMES = ["bulk order deed box"]
MOVE_DELAY = 0.7
BOX_TIMEOUT = 10.0
BOX_POLL = 0.5

# The large deed's own gump: 2 raises a cursor for a filled small deed
LARGE_COMBINE_BUTTON = 2

# The tooltip's own lines, lower-cased
DEED_TEXT = {
    "large": "large bulk order",
    "amount": "amount to make:",
    "exceptional": "must be exceptional",
    "material_before": "must be made with",
    "material_after": "ingots",
}

ARTICLES = ["a ", "an "]
EXCEPTIONAL_TEXT = "exceptional"

# The CATEGORIES rows, lowercased, as craft-map.py read them off UOAlive's menu
CATEGORY_NAMES = [
    "metal armor",
    "helmets",
    "shields",
    "bladed",
    "axes",
    "polearms",
    "bashing",
    "cannons",
    "throwing",
    "miscellaneous",
]

CRAFT_TITLE = "BLACKSMITHY"
CRAFT_TITLE_TEXT = [CRAFT_TITLE, "BLACKSMITH"]
CRAFT_TITLE_FRAGMENTS = [phrase.lower() for phrase in CRAFT_TITLE_TEXT]
LAST_TEN_LABEL = "LAST TEN"

# Buttons are 1 + type + index * 20 on this shard: categories 1, 21, 41 ..., rows 2, 22, 42 ...,
# a row's details 3, 23, 43 ..., the material page on 7 with its rows on 6, 26, 46 ...
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MATERIAL_ROW_TYPE = 5
MATERIAL_BUTTON_TYPE = 6

MAX_MATERIAL_ROWS = 12

# (category button, row button) for every row, as craft-map.py read them off UOAlive's menu, keyed
# as the deed names the item. Run craft-map.py again and paste its block over this one when the
# menu changes.
RECIPES = {
    # Metal Armor (button 1)
    "ringmail gloves": (1, 2),
    "ringmail leggings": (1, 22),
    "ringmail sleeves": (1, 42),
    "ringmail tunic": (1, 62),
    "chainmail coif": (1, 82),
    "chainmail leggings": (1, 102),
    "chainmail tunic": (1, 122),
    "platemail arms": (1, 142),
    "platemail gloves": (1, 162),
    "platemail gorget": (1, 182),
    "platemail legs": (1, 202),
    "platemail (tunic)": (1, 222),
    "platemail (female)": (1, 242),
    "universal barding deed": (1, 262),
    "platemail mempo": (1, 282),
    "platemail do": (1, 302),
    "platemail hiro sode": (1, 322),
    "platemail suneate": (1, 342),
    "platemail haidate": (1, 362),
    "gargish platemail arms": (1, 382),
    "gargish platemail chest": (1, 402),
    "gargish platemail leggings": (1, 422),
    "gargish platemail kilt": (1, 442),
    # "gargish platemail arms": (1, 462),  listed again, the first kept
    # "gargish platemail chest": (1, 482),  listed again, the first kept
    # "gargish platemail leggings": (1, 502),  listed again, the first kept
    # "gargish platemail kilt": (1, 522),  listed again, the first kept
    "gargish amulet": (1, 542),
    "britches of warding": (1, 562),
    # Helmets (button 21)
    "bascinet": (21, 2),
    "close helmet": (21, 22),
    "helmet": (21, 42),
    "norse helm": (21, 62),
    "plate helm": (21, 82),
    "chainmail hatsuburi": (21, 102),
    "platemail hatsuburi": (21, 122),
    "heavy platemail jingasa": (21, 142),
    "light platemail jingasa": (21, 162),
    "small platemail jingasa": (21, 182),
    "decorative platemail kabuto": (21, 202),
    "platemail battle kabuto": (21, 222),
    "standard platemail kabuto": (21, 242),
    "circlet": (21, 262),
    "royal circlet": (21, 282),
    "gemmed circlet": (21, 302),
    # Shields (button 41)
    "buckler": (41, 2),
    "bronze shield": (41, 22),
    "heater shield": (41, 42),
    "metal shield": (41, 62),
    "metal kite shield": (41, 82),
    "tear kite shield": (41, 102),
    "chaos shield": (41, 122),
    "order shield": (41, 142),
    "small plate shield": (41, 162),
    "gargish kite shield": (41, 182),
    "large plate shield": (41, 202),
    "medium plate shield": (41, 222),
    "gargish chaos shield": (41, 242),
    "gargish order shield": (41, 262),
    # Bladed (button 61)
    "bone harvester": (61, 2),
    "broadsword": (61, 22),
    "crescent blade": (61, 42),
    "cutlass": (61, 62),
    "dagger": (61, 82),
    "katana": (61, 102),
    "kryss": (61, 122),
    "longsword": (61, 142),
    "scimitar": (61, 162),
    "viking sword": (61, 182),
    "paladin sword": (61, 202),
    "no-dachi": (61, 222),
    "wakizashi": (61, 242),
    "lajatang": (61, 262),
    "daisho": (61, 282),
    "tekagi": (61, 302),
    "shuriken": (61, 322),
    "kama": (61, 342),
    "sai": (61, 362),
    "radiant scimitar": (61, 382),
    "war cleaver": (61, 402),
    "elven spellblade": (61, 422),
    "assassin spike": (61, 442),
    "leafblade": (61, 462),
    "rune blade": (61, 482),
    "elven machete": (61, 502),
    "rune carving knife": (61, 522),
    "cold forged blade": (61, 542),
    "overseer sundered blade": (61, 562),
    "luminous rune blade": (61, 582),
    "true spellblade": (61, 602),
    "icy spellblade": (61, 622),
    "fiery spellblade": (61, 642),
    "spellblade of defense": (61, 662),
    "true assassin spike": (61, 682),
    "charged assassin spike": (61, 702),
    "magekiller assassin spike": (61, 722),
    "wounding assassin spike": (61, 742),
    "true leafblade": (61, 762),
    "luckblade": (61, 782),
    "magekiller leafblade": (61, 802),
    "leafblade of ease": (61, 822),
    "knight's war cleaver": (61, 842),
    "butcher's war cleaver": (61, 862),
    "serrated war cleaver": (61, 882),
    "true war cleaver": (61, 902),
    "adventurer's machete": (61, 922),
    "orcish machete": (61, 942),
    "machete of defense": (61, 962),
    "diseased machete": (61, 982),
    "runesabre": (61, 1002),
    "mage's rune blade": (61, 1022),
    "rune blade of knowledge": (61, 1042),
    "corrupted rune blade": (61, 1062),
    "true radiant scimitar": (61, 1082),
    "darkglow scimitar": (61, 1102),
    "icy scimitar": (61, 1122),
    "twinkling scimitar": (61, 1142),
    "bone machete": (61, 1162),
    "gargish katana": (61, 1182),
    "gargish kryss": (61, 1202),
    "gargish bone harvester": (61, 1222),
    "gargish tekagi": (61, 1242),
    "gargish daisho": (61, 1262),
    "dread sword": (61, 1282),
    "gargish talwar": (61, 1302),
    "gargish dagger": (61, 1322),
    "bloodblade": (61, 1342),
    "shortblade": (61, 1362),
    # Axes (button 81)
    "axe": (81, 2),
    "battle axe": (81, 22),
    "double axe": (81, 42),
    "executioner's axe": (81, 62),
    "large battle axe": (81, 82),
    "two handed axe": (81, 102),
    "war axe": (81, 122),
    "ornate axe": (81, 142),
    "guardian axe": (81, 162),
    "singing axe": (81, 182),
    "thundering axe": (81, 202),
    "heavy ornate axe": (81, 222),
    "gargish battle axe": (81, 242),
    "gargish axe": (81, 262),
    "dual short axes": (81, 282),
    # Polearms (button 101)
    "bardiche": (101, 2),
    "bladed staff": (101, 22),
    "double bladed staff": (101, 42),
    "halberd": (101, 62),
    "lance": (101, 82),
    "pike": (101, 102),
    "short spear": (101, 122),
    "scythe": (101, 142),
    "spear": (101, 162),
    "war fork": (101, 182),
    "gargish bardiche": (101, 202),
    "gargish war fork": (101, 222),
    "gargish scythe": (101, 242),
    "gargish pike": (101, 262),
    "gargish lance": (101, 282),
    "dual pointed spear": (101, 302),
    # Bashing (button 121)
    "hammer pick": (121, 2),
    "mace": (121, 22),
    "maul": (121, 42),
    "scepter": (121, 62),
    "war mace": (121, 82),
    "war hammer": (121, 102),
    "tessen": (121, 122),
    "diamond mace": (121, 142),
    "shard thrasher": (121, 162),
    "ruby mace": (121, 182),
    "emerald mace": (121, 202),
    "sapphire mace": (121, 222),
    "silver-etched mace": (121, 242),
    "gargish war hammer": (121, 262),
    "gargish maul": (121, 282),
    "gargish tessen": (121, 302),
    "disc mace": (121, 322),
    # Cannons (button 141)
    "cannonball": (141, 2),
    "grapeshot": (141, 22),
    "culverin": (141, 42),
    "carronade": (141, 62),
    # Throwing (button 161)
    "boomerang": (161, 2),
    "cyclone": (161, 22),
    "soul glaive": (161, 42),
    # Miscellaneous (button 181)
    "dragon gloves": (181, 2),
    "dragon helm": (181, 22),
    "dragon leggings": (181, 42),
    "dragon sleeves": (181, 62),
    "dragon breastplate": (181, 82),
    "crushed glass": (181, 102),
    "powdered iron": (181, 122),
    "metal keg": (181, 142),
    "exodus sacrificial dagger": (181, 162),
    "gloves of feudal grip": (181, 182),
    # As the deed words the two rows the menu brackets
    "platemail tunic": (1, 222),
    "platemail": (1, 222),
    "female plate": (1, 242),
    "female platemail": (1, 242),
}

# On the row's details page: 1 MAKE NOW, 2 MAKE NUMBER, 3 MAKE MAX. CANCEL MAKE is 1 + 6 + 11 * 20
MAKE_NUMBER_BUTTON = 2
CANCEL_MAKE_BUTTON = 227

# How long the shard's number prompt takes to arrive before it is answered
PROMPT_DELAY = 0.8

# A craft's animation plus the auto craft's own gap, for the batch's time budget
CRAFT_INTERVAL = 3.0

# No new piece and no failure line for this long ends a batch
BATCH_IDLE = 8.0

# 'Combine this deed with contained items', aimed at the bag; 2 is the one-item combine
BOD_COMBINE_BUTTON = 4
BOD_GUMP_TEXT = ["bulk order", "Combine this deed"]

# Once the deed is full: the bag's context menu entry, matched by its text
SALVAGE_AT_END = True
SALVAGE_ENTRIES = ["Salvage All"]
CONTEXT_TIMEOUT = 3.0
SALVAGE_SETTLE = 2.0

# Played once on this Mac when the deed is filled, so the client's sound setting does not matter.
# An empty list turns it off
DONE_SOUND = ["afplay", "/System/Library/Sounds/Glass.aiff"]

# Seconds throughout - API.Pause takes seconds
PICK_TIMEOUT = 60.0

# Whole seconds: the API takes an int here
OPL_TIMEOUT = 2

# Tooltip reads one item gets before it is given up on for the pass
OPL_ASKS = 3
OPL_SETTLE = 0.5

GUMP_TIMEOUT = 5.0
GUMP_POLL = 0.15

CRAFT_TIMEOUT = 10.0
CRAFT_POLL = 0.2
TARGET_TIMEOUT = 4.0
COMBINE_TIMEOUT = 4.0
COMBINE_POLL = 0.2

# How long the deed's tooltip has to show a combine the pack already proved
REREAD_SETTLE = 3.0
REREAD_POLL = 0.5

MAX_CYCLES = 2000
MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_TOOL = 5
MAX_NO_CURSOR = 3

MAX_UNREADABLE_REPORTS = 2
UNREADABLE_TEXT_LIMIT = 160
JOURNAL_TAIL_SECONDS = 20.0
JOURNAL_TAIL_LINES = 4

# The whole gump and journal behind a report, appended here so the game window stays quiet. "" turns
# it off; a bare name lands beside the script.
NOTES_PATH = "bod-notes.log"
NOTES_TAIL_SECONDS = 60.0

# Ordered: 'failed' before 'made' because "You failed to create the item" contains "create the item"
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
    ("made", ["You create the item", "You create an exceptional", "You put the"]),
    (
        "noMaterial",
        [
            "You do not have sufficient metal",
            "You don't have the resources",
            "You do not have the resources",
            "not enough ingots",
            "You have insufficient",
        ],
    ),
    ("noAnvil", ["near an anvil and a forge", "anvil and forge"]),
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

LARGE_COMBINE_TEXT = [
    ("combined", ["orders have been combined"]),
    ("full", ["maximum amount of requested items"]),
    ("notComplete", ["is not completed"]),
    ("wrongDeed", ["not a bulk order for this large request"]),
    ("notBulk", ["That is not a bulk order"]),
    ("exceptionalMismatch", ["must be of exceptional quality"]),
    ("materialMismatch", ["same resource type"]),
    ("amountMismatch", ["different requested amounts"]),
]

COMBINE_TEXT = [
    ("combined", ["has been combined with the deed"]),
    ("full", ["maximum amount of requested items"]),
    ("notRequested", ["The item is not in the request"]),
    ("wrongMaterial", ["not made from the requested resource"]),
    ("notExceptional", ["The item must be exceptional"]),
    ("notInPack", ["must have the item in your backpack"]),
    ("tooMany", ["provided more than"]),
]


# src/bod/craft.py
STOPPERS = ("noMaterial", "noAnvil", "skillTooLow", "toolWorn", "throttled", "saving")


class DeedCrafter(object):
    """MAKE NUMBER batches off the RECIPES row, pressed as written."""

    def __init__(self, tool, menu, items, picker, buckets, config, log, stamp=None,
                 notes=None):
        self._tool = tool
        self._menu = menu
        self._items = items
        self._picker = picker
        self._buckets = buckets
        self._config = config
        self._log = log
        self._report = Reporter(menu.lines, config, log, notes, stamp)

    def _notice_bucket(self, gump):
        if not gump:
            return None

        for name, phrases in self._buckets:
            for phrase in phrases:
                if API.GumpContains(phrase, gump):
                    return name

        return None

    def _report_outcome(self, why, gump):
        self._report.say(why, gump)

    def _choose_button(self, product, gump):
        known = self._config["recipes"].get(product)

        if known is None:
            return None, "noRow"

        if not self._menu.press(known[0], gump, self._config["gump_timeout"]):
            return None, "noGump"

        return known[1], None

    def _ready(self, material):
        if self._tool.serial() is None:
            return None, "noTool"

        gump = self._menu.open()

        if gump is None:
            return None, "noGump"

        if self._picker.needs(material):
            gump, why = self._picker.select(material, gump)

            if why is not None:
                return None, why

        return gump, None

    def _cancel(self):
        self._menu.reply(self._config["cancel_button"], self._menu.current_id())

    # The auto craft says nothing when it ends: the pack and the journal are counted up to the
    # amount, and a stretch with no change is taken as the end. One failure line per poll is
    # enough, since a craft takes longer than a poll.
    def _watch_batch(self, amount, before):
        failed = 0
        last = 0
        idle = 0.0
        waited = 0.0
        budget = amount * self._config["craft_interval"] + self._config["craft_timeout"]

        while not API.StopRequested:
            made = len(self._items.new_since(before))
            stopper = None
            hit = matched_bucket(self._buckets)

            while hit is not None:
                if hit == "failed":
                    failed += 1
                elif hit in STOPPERS:
                    stopper = hit

                hit = matched_bucket(self._buckets)

            if stopper is None:
                notice = self._notice_bucket(self._menu.current_id())

                if notice in STOPPERS:
                    stopper = notice

            progress = made + failed

            if progress >= amount:
                return "made", made, failed

            if stopper is not None:
                self._cancel()

                return stopper, made, failed

            if progress == last:
                idle += self._config["craft_poll"]
            else:
                idle = 0.0
                last = progress
                self._log("batch: %d made, %d failed of %d" % (made, failed, amount))

            if idle >= self._config["batch_idle"] or waited >= budget:
                if progress > 0:
                    self._log("the batch went quiet at %d of %d - a failure the journal did not "
                              "carry, or the shard stopped early" % (progress, amount))

                return ("made" if progress > 0 else None), made, failed

            API.Pause(self._config["craft_poll"])
            waited += self._config["craft_poll"]

        return None, len(self._items.new_since(before)), failed

    # Details button is the row's button plus one: type 2 against the row's type 1
    def craft_batch(self, product, material, amount):
        gump, why = self._ready(material)

        if why is not None:
            return why, 0, 0

        button, why = self._choose_button(product, gump)

        if why is not None:
            return why, 0, 0

        gump = self._menu.current_id() or gump
        details = self._menu.press_page(button + 1, gump, self._config["gump_timeout"])

        if not details:
            return "noGump", 0, 0

        before = self._items.serials()
        API.ClearJournal()

        if not self._menu.reply_page(self._config["make_number_button"], details):
            return "noGump", 0, 0

        API.Pause(self._config["prompt_delay"])
        API.PromptResponse(str(amount))

        outcome, made, failed = self._watch_batch(amount, before)

        if outcome is None:
            self._report_outcome("the batch of %d made nothing" % amount, self._menu.current_id())
        elif outcome == "noMaterial":
            self._report_outcome("refused for materials", self._menu.current_id())

        return outcome, made, failed


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


# src/uo/menu.py
# ContextMenu opens the menu itself, and cannot tell an entry that is missing from one that never
# arrived - both come back False
def context_menu(serial, texts, timeout):
    for text in texts:
        # Guarded: a build whose ContextMenu throws for a serial it cannot resolve would otherwise
        # end the run over a vendor that stepped away
        try:
            if API.ContextMenu(serial, text, timeout):
                return True
        except Exception:
            if API.StopRequested:
                raise

            continue

    return False


# src/bod/fill.py
class SmallFill(object):
    """The cycle loop for one small deed: combine what qualifies, else craft, until full."""

    def __init__(self, deed, items, crafter, picker, combiner, config, log, watch):
        self._deed = deed
        self._request = deed.request
        self._items = items
        self._crafter = crafter
        self._picker = picker
        self._combiner = combiner
        self._config = config
        self._log = log
        self._heartbeat = watch["heartbeat"]
        self._stall = watch["stall"]
        self._saves = watch["saves"]
        self._stop_reason = watch["stop_reason"]

        self.done = self._request["done"]
        self.combined = 0
        self.made = 0
        self.fails = 0
        self._unknown = 0
        self._throttled = 0
        self._no_tool = 0
        self._no_cursor = 0
        self._cycle = 0
        self._said_throttle = False

    def owed(self):
        return self._request["total"] - self.done

    def summary(self):
        return "%d combined, %d made, %d failed, %d/%d in the deed" % (
            self.combined, self.made, self.fails, self.done, self._request["total"])

    def _end_cycle(self, phase):
        self._stall.end_cycle(phase, self._cycle, self.combined)

        return self._stall.reason()

    def _combine_now(self, offered):
        outcome, taken = self._combiner.combine(self._config["combine_target"], offered)

        if len(taken) > 0:
            self.combined += len(taken)
            self._no_cursor = 0
            self._items.forget_missing()
            self.done = self._deed.settle_after_combine(self.done + len(taken))
            self._stall.progressed()
            self._log("combined %d (%d/%d)" % (len(taken), self.done, self._request["total"]))
        elif outcome == "full":
            return "the deed is full"
        elif outcome in ("notRequested", "notExceptional", "wrongMaterial", "tooMany"):
            # Which of the offered pieces the shard meant is not said, so none is offered again
            self._items.reject(*offered)
            self._stall.progressed()
            self._log("the deed took none of the %d offered (%s), leaving them in the bag"
                      % (len(offered), outcome))

            if outcome == "wrongMaterial":
                self._picker.forget()
        elif outcome == "notInPack":
            return "the shard says the pieces are not in your pack"
        elif outcome in ("noCursor", "noGump"):
            self._no_cursor += 1

            if self._no_cursor >= self._config["max_no_cursor"]:
                return ("the deed's gump raised no cursor %d times - check BOD_COMBINE_BUTTON"
                        % self._config["max_no_cursor"])

            API.Pause(backoff_for(self._no_cursor, self._config["backoff"],
                                  self._config["backoff_max"]))
        else:
            self._unknown += 1
            self._log("unreadable combine outcome (%d/%d), check COMBINE_TEXT"
                      % (self._unknown, self._config["max_unknown"]))

        return None

    def salvage(self):
        bag = self._config["bag"]

        if not self._config["salvage"] or bag is None or len(self._items.leftovers()) == 0:
            return

        before = len(API.ItemsInContainer(bag, True) or [])

        if not context_menu(bag, self._config["salvage_entries"], self._config["context_timeout"]):
            self._log("the bag's menu has no %s entry - salvage it yourself"
                      % " / ".join(self._config["salvage_entries"]))

            return

        API.Pause(self._config["salvage_settle"])
        self._items.forget_missing()
        after = len(API.ItemsInContainer(bag, True) or [])
        self._log("salvaged: the bag went from %d items to %d, %s in the pack"
                  % (before, after, ingot_report(self._config["ingots"])))

    def _craft(self):
        item = self._request["item"]
        material = self._request["material"]

        batch = self.owed()
        outcome, made, failed = self._crafter.craft_batch(item, material, batch)
        self.made += made
        self.fails += failed

        if made + failed > 0:
            self._log("batch of %d: %d made, %d failed%s"
                      % (batch, made, failed, "" if outcome == "made" else " (%s)" % outcome))
            self._stall.progressed()

        return "batch" if outcome == "made" else outcome

    def _after_craft(self, outcome, waiting):
        config = self._config
        item = self._request["item"]

        if outcome != "throttled":
            self._throttled = 0

        if outcome is not None:
            self._unknown = 0

        if outcome in ("batch", "saving"):
            self._stall.progressed()
        elif outcome == "noMaterial":
            # What is already made goes in before the run ends
            if len(waiting) > 0:
                self._combine_now(waiting)

            return ("the shard says there are not enough %s ingots - %s in the pack, %d still owed"
                    % (self._request["material"], ingot_report(config["ingots"]), self.owed()))
        elif outcome == "toolWorn":
            self._stall.progressed()
            self._log("the tool wore out, looking for another")
        elif outcome == "skillTooLow":
            return "the shard says you cannot make a %s" % item
        elif outcome == "noAnvil":
            return "stand next to an anvil and a forge"
        elif outcome == "noRow":
            return "'%s' is not in RECIPES" % item
        elif outcome == "noMaterialRow":
            return "the material page has no row for %s" % self._request["material"]
        elif outcome in ("noTool", "noGump"):
            self._no_tool += 1

            if self._no_tool >= config["max_no_tool"]:
                return ("no smith's tool left" if outcome == "noTool"
                        else "the craft menu will not open")

            self._log("%s (%d/%d), trying again"
                      % ("no smith's tool in the pack" if outcome == "noTool"
                         else "the tool opened no craft menu", self._no_tool, config["max_no_tool"]))
            API.Pause(backoff_for(self._no_tool, config["backoff"], config["backoff_max"]))
        elif outcome == "throttled":
            self._throttled += 1

            if self._throttled >= config["max_throttled"]:
                return "%d throttled crafts in a row" % config["max_throttled"]

            waiting = backoff_for(self._throttled, config["backoff"], config["backoff_max"])

            if not self._said_throttle:
                self._said_throttle = True
                self._log("the shard is pacing the crafts - waiting %.1fs" % waiting)

            API.Pause(waiting)
        else:
            self._unknown += 1
            self._log("unreadable outcome (%d/%d), check OUTCOME_TEXT"
                      % (self._unknown, config["max_unknown"]))

        if outcome not in ("noTool", "noGump"):
            self._no_tool = 0

        return None

    # None when the deed is full, otherwise why it stopped
    def run(self):
        config = self._config
        stop = None

        while stop is None and self._cycle < config["max_cycles"]:
            self._cycle += 1
            stop = self._stop_reason()

            if stop is not None:
                break

            if self._saves.is_saving():
                self._saves.wait_out()
                self._unknown = 0
                self._throttled = 0
                self._stall.progressed()
                stop = self._end_cycle("saving")
                continue

            if self.owed() <= 0:
                break

            waiting = self._items.qualifying()

            if len(waiting) > 0:
                stop = self._combine_now(waiting)

                if stop == "the deed is full":
                    stop = None
                    self.done = self._request["total"]
                    break

                if stop is None and self._unknown >= config["max_unknown"]:
                    stop = "%d unreadable outcomes in a row" % config["max_unknown"]

                if stop is None:
                    self.salvage()
                    stop = self._end_cycle("combining")
                    API.Pause(config["step_delay"])

                continue

            outcome = self._craft()
            stop = self._after_craft(outcome, waiting)

            if stop is None and self._unknown >= config["max_unknown"]:
                stop = "%d unreadable outcomes in a row" % config["max_unknown"]

            if stop is None:
                stop = self._end_cycle(outcome if outcome is not None else "unknown")
                API.Pause(config["step_delay"])

        if stop is None and self.owed() > 0:
            stop = "hit the %d cycle backstop" % config["max_cycles"]

        if self.owed() <= 0:
            self.salvage()

        return stop


# src/bod/items.py
class ItemBook(object):
    """What the tooltip says each pack item is, and whether the deed would take it."""

    def __init__(self, request, config, log):
        self._request = request
        self._config = config
        self._log = log
        self._verdicts = {}
        self._asked = {}
        self._rejected = set()

    def _material_names(self):
        material = self._request["material"]

        return [material] + list(self._config["aliases"].get(material, []))

    def _plain(self):
        return self._request["material"] == self._config["plain"]

    # Stock folds the material into the name: 'dull copper platemail gorget'
    def _product_names(self):
        item = self._request["item"]
        names = [item]

        if not self._plain():
            names.extend("%s %s" % (name, item) for name in self._material_names())

        return names

    def _judge(self, lines):
        name = strip_article(lines[0].lower(), self._config["articles"])

        body = [line.lower() for line in lines[1:]]
        product = name in self._product_names()
        exceptional = word_in(" ".join(body), [self._config["exceptional_text"]])

        if self._plain():
            material = True
        else:
            wanted = [words_of(alias) for alias in self._material_names()]
            material = (name != self._request["item"]
                        or len([line for line in body if words_of(line) in wanted]) > 0)

        return {
            "product": product,
            "qualifies": product and material and (exceptional or not self._request["exceptional"]),
        }

    def look(self, serial):
        if serial in self._verdicts:
            return self._verdicts[serial]

        if self._asked.get(serial, 0) >= self._config["asks"]:
            return None

        self._asked[serial] = self._asked.get(serial, 0) + 1
        props = API.ItemNameAndProps(serial, True, self._config["opl_timeout"]) or ""
        lines = [line.strip() for line in props.splitlines() if line.strip()]

        if len(lines) == 0:
            return None

        self._verdicts[serial] = self._judge(lines)
        self._verdicts[serial]["name"] = lines[0]

        return self._verdicts[serial]

    def name_of(self, serial):
        verdict = self.look(serial)

        return "(no tooltip)" if verdict is None else verdict["name"]

    def is_product(self, serial):
        verdict = self.look(serial)

        return None if verdict is None else verdict["product"]

    def reject(self, *serials):
        self._rejected.update(serials)

    # Stacks and bags are never the product, and each tooltip read is a wait
    def _candidates(self):
        return [item for item in pack_contents()
                if amount_of(item) == 1 and not getattr(item, "IsContainer", False)]

    def serials(self):
        return set(item.Serial for item in pack_contents())

    def new_since(self, before):
        return [item for item in self._candidates() if item.Serial not in before]

    # One request for every unread piece, so the reads below do not each wait their turn
    def prime(self):
        unread = [item.Serial for item in self._candidates()
                  if item.Serial not in self._verdicts and item.Serial not in self._rejected
                  and self._asked.get(item.Serial, 0) < self._config["asks"]]

        if len(unread) == 0:
            return

        API.RequestOPLData(unread)
        API.Pause(self._config["opl_settle"])

    def qualifying(self):
        self.prime()
        found = []

        for item in self._candidates():
            if item.Serial in self._rejected:
                continue

            verdict = self.look(item.Serial)

            if verdict is not None and verdict["qualifies"]:
                found.append(item.Serial)

        return found

    # What a salvage would take: judged pieces the deed did not, or would not
    def leftovers(self):
        return [item.Serial for item in self._candidates()
                if item.Serial in self._verdicts
                and (item.Serial in self._rejected or not self._verdicts[item.Serial]["qualifies"])]

    # The shard reissues the serial of an item the deed took
    def forget_missing(self):
        here = self.serials()

        for serial in list(self._verdicts.keys()):
            if serial not in here:
                del self._verdicts[serial]
                self._asked.pop(serial, None)


# src/bod/material.py
class MaterialPicker(object):
    """The craft menu's material page: pressed once, and again when the deed says it was wrong."""

    def __init__(self, menu, config, log):
        self._menu = menu
        self._config = config
        self._log = log
        self._selected = None
        self._said_unsplit = False

    def needs(self, material):
        return self._selected != material

    def forget(self):
        self._selected = None

    def _names_for(self, material):
        return [material] + list(self._config["aliases"].get(material, []))

    # Matched on the leading words, so 'copper' does not take 'DULL COPPER (12)'
    def row_of(self, material, rows):
        wanted = [words_of(name) for name in self._names_for(material)]

        for index in range(min(len(rows), self._config["max_rows"])):
            words = words_of(rows[index])

            for name in wanted:
                if len(name) > 0 and words[:len(name)] == name:
                    return index

        return None

    # GetGumpContents hands the page back as one line; the material rows in it read 'IRON (1587)
    # DULL COPPER (111) ...' after the DO NOT COLOR toggle, so they are split on the counts
    def rows_from_text(self, text):
        low = (text or "").lower()
        marker = self._config["rows_after"]

        if marker in low:
            text = text[low.index(marker) + len(marker):]

        rows = []
        words = []

        for token in (text or "").split():
            if token.startswith("(") and token.endswith(")") and token[1:-1].isdigit():
                if len(words) > 0:
                    rows.append(" ".join(words) + " " + token)

                words = []
            else:
                words.append(token)

        return rows

    # The stock order, for a page whose text could not be split into rows
    def _stock_index(self, material):
        order = self._config["order"]

        return order.index(material) if material in order else None

    def select(self, material, gump):
        timeout = self._config["gump_timeout"]
        page = self._menu.press(self._menu.button_id(self._config["button_type"], 0), gump, timeout)

        if not page:
            return 0, "noGump"

        rows = self._menu.item_rows(page)

        if len(rows) == 0:
            rows = self.rows_from_text(API.GetGumpContents(page))

        index = self.row_of(material, rows)

        if index is None and len(rows) == 0:
            index = self._stock_index(material)

            if index is not None and not self._said_unsplit:
                self._said_unsplit = True
                self._log("the material page names no rows - pressing row %d for %s on the stock "
                          "order; the page says '%s'"
                          % (index, material, " | ".join(self._menu.lines(page)) or "(no text)"))

        if index is None:
            self._log("no material row reads '%s' - the page says '%s'"
                      % (material, " | ".join(rows or self._menu.lines(page)) or "(no text)"))

            return page, "noMaterialRow"

        button = self._menu.button_id(self._config["row_type"], index)
        opened = self._menu.press(button, page, timeout)

        if not opened:
            return 0, "noGump"

        self._selected = material
        self._log("the menu is set to %s, the material row on button %d" % (material, button))

        return opened, None


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


# src/uo/craftmenu.py
class CraftMenu(object):
    """A craft gump: opening it, finding the category, and finding the row."""

    def __init__(self, tools, config, log):
        self._tools = tools
        self._config = config
        self._log = log
        self._id = 0
        self._page = 0
        self._ignored = set()
        self._said_gump_text = False
        self._said_no_button = set()
        self._said_not_menu = False

    def current_id(self):
        return self._id

    def button_id(self, kind, index):
        return 1 + kind + index * self._config["stride"]

    def has_button(self, button, gump):
        known = button_ids(gump)

        return known is None or button in known

    # The shard drops the connection for a button the gump does not have, so nothing is sent blind
    def _send(self, button, gump):
        if not self.has_button(button, gump):
            if button not in self._said_no_button:
                self._said_no_button.add(button)
                self._log("gump %s has no button %d - not pressing it" % (hex_of(gump), button))

            return False

        return bool(API.ReplyGump(button, gump))

    def reply(self, button, gump):
        if not gump or gump != self._id:
            if not self._said_not_menu:
                self._said_not_menu = True
                self._log("not pressing button %d on %s - it is not the craft menu"
                          % (button, hex_of(gump)))

            return False

        return self._send(button, gump)

    def press(self, button, gump, timeout):
        if not self.reply(button, gump):
            return 0

        return await_gump(self._id, timeout)

    # For a button that opens another gump: the one that was not up before answers, else the menu
    def press_page(self, button, gump, timeout):
        before = open_ids() + list(self._ignored)

        if not self.reply(button, gump):
            return 0

        found, _recognised = await_recognised(lambda ident: False, before, timeout,
                                              self._config["gump_poll"])

        if not found:
            found = await_gump(self._id, 0)

        self._page = found

        return found

    def reply_page(self, button, page):
        if not page or page != self._page:
            return False

        return self._send(button, page)

    def is_craft_gump(self, ident):
        if not ident:
            return False

        if any_in(API.GetGumpContents(ident) or "", self._config["title_fragments"]):
            return True

        # GumpContains reads controls GetGumpContents may not put in text
        for phrase in self._config["title_text"]:
            if API.GumpContains(phrase, ident):
                return True

        # The title is a cliloc that may not render; the group rows are read here regardless
        for line in self.lines(ident):
            if (line.lower() in self._config["category_names"]
                    or line.upper() == self._config["last_ten_label"]):
                return True

        return False

    def lines(self, gump):
        text = API.GetGumpContents(gump)

        return [line.strip() for line in (text or "").split("\n") if line.strip()]

    def _ignore(self, ident):
        if ident in self._ignored:
            return

        self._ignored.add(ident)
        lines = self.lines(ident)
        self._log("ignoring gump %s - it is not the craft menu, it starts '%s'"
                  % (hex_of(ident), lines[0] if lines else "(no text)"))

    def open(self):
        if self._id and is_open(self._id):
            return self._id

        before = open_ids()

        for ident in before:
            if self.is_craft_gump(ident):
                self._id = ident

                return ident

            self._ignore(ident)

        serial = self._tools.serial()

        if serial is None:
            return None

        API.UseObject(serial)

        # A foreign gump the shard re-sends during the wait is not what the tools opened
        found, recognised = await_recognised(self.is_craft_gump, before + list(self._ignored),
                                             self._config["gump_timeout"],
                                             self._config["gump_poll"])

        if not found:
            return None

        if not recognised and not self._said_gump_text:
            self._said_gump_text = True
            lines = self.lines(found)
            self._log("the %s opened a gump that does not name %s - it starts '%s'"
                      % (self._config["tool_noun"], self._config["title"],
                         lines[0] if lines else "(no text)"))

        self._id = found

        return found

    def _is_button_of(self, kind, button):
        return (button is not None and button > 0
                and (button - 1 - kind) % self._config["stride"] == 0)

    # The stock layout draws a row as its button then its name (a SELECTIONS row's details button
    # follows), and every page's rows are in the gump at once: the pairs are read off the controls
    # whichever page shows. A page-turn label follows a page button, so it never pairs.
    def _labelled(self, gump, kind):
        read = controls(gump)

        if read is None:
            return []

        rows = []
        pending = None

        for button, text in read:
            if text is None:
                pending = button if self._is_button_of(kind, button) else None
                continue

            label = text.strip()

            if pending is not None and label:
                rows.append((label, pending))

            pending = None

        return rows

    def rows_of(self, gump):
        return self._labelled(gump, self._config["item_type"])

    def categories_of(self, gump):
        return self._labelled(gump, self._config["category_type"])

    def item_rows(self, gump):
        return [label for label, _button in self.rows_of(gump)]


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


# src/uo/vitals.py
def weight_reading():
    me = player()

    return "?/?" if me is None else "%d/%d" % (me.Weight, me.WeightMax)


def where():
    me = player()

    return "somewhere" if me is None else "at %d,%d" % (me.X, me.Y)


def position_and_weight():
    return "%s, %s" % (where(), weight_reading())


# src/bod/index.py
log = make_log("bod")
note_file = note_log(NOTES_PATH, log)
DEED_FULL = "the deed is full"
LARGE_COMPLETE = "the large deed is complete"
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "combined", position_and_weight)
stall = StallWatch("cycles without progress", STALL_WARN, STALL_STOP, heartbeat, log)

if API.HasTarget():
    API.CancelTarget()


def stop_reason():
    return first_reason([stopped(STOPPED), dead()])


# RootContainer resolves to the mobile carrying the item, not to the backpack
def in_pack(item):
    me = player()
    mine = [API.Backpack] + ([me.Serial] if me is not None else [])

    return (getattr(item, "Container", None) in mine
            or getattr(item, "RootContainer", None) in mine)


INGOTS = {
    "ingot_graphics": INGOT_GRAPHICS,
    "ingot_words": INGOT_NAME_WORDS,
    "materials": sorted(set(INGOT_HUES.values()), key=len, reverse=True),
    "hues": INGOT_HUES,
    "costs": INGOT_COST,
    "uses_text": USES_TEXT,
    "opl_timeout": OPL_TIMEOUT,
}

DEEDS = {
    "text": DEED_TEXT,
    "plain": PLAIN_MATERIAL,
    "articles": ARTICLES,
    "opl_timeout": OPL_TIMEOUT,
    "reread_settle": REREAD_SETTLE,
    "reread_poll": REREAD_POLL,
    "deed_graphics": DEED_GRAPHICS,
    "deed_words": DEED_NAME_WORDS,
}

COMBINES = {
    "gump_text": BOD_GUMP_TEXT,
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
    "target_timeout": TARGET_TIMEOUT,
    "combine_timeout": COMBINE_TIMEOUT,
    "combine_poll": COMBINE_POLL,
    "max_reports": MAX_UNREADABLE_REPORTS,
    "text_limit": UNREADABLE_TEXT_LIMIT,
    "tail_seconds": JOURNAL_TAIL_SECONDS,
    "tail_lines": JOURNAL_TAIL_LINES,
    "notes_seconds": NOTES_TAIL_SECONDS,
}


def combine_config(button):
    config = dict(COMBINES)
    config["combine_button"] = button

    return config


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)
skill_name = find_skill_name(SKILL_NAMES)
skill = SkillReader(skill_name) if skill_name is not None else None

log("target the bulk order deed to fill, small or large, ESC to stop")

picked = API.RequestTarget(PICK_TIMEOUT)

if API.HasTarget():
    API.CancelTarget()

if not picked:
    log("nothing targeted - stopping")
    API.Stop()

deed = Deed(picked, DEEDS, log)
request, refused = deed.read()

if request is None:
    log("%s is not a deed this run can fill: %s" % (hex_of(picked), refused))
    API.Stop()

deed_item = API.FindItem(picked)

if deed_item is not None and not in_pack(deed_item):
    log("the deed has to be in your pack - the shard refuses a combine from anywhere else "
        "(container %s, root %s)" % (hex_of(getattr(deed_item, "Container", 0) or 0),
                                     hex_of(getattr(deed_item, "RootContainer", 0) or 0)))
    API.Stop()

bag = None

# ItemsInContainer reads nothing out of a bag the client has not seen inside
for held in pack_contents():
    if any_in(held.Name, TOOL_BAG_NAMES):
        API.UseObject(held.Serial)
        API.Pause(OPEN_DELAY)
        log("opened '%s' - the tools, the pieces and the salvage are all in it" % held.Name)
        bag = held.Serial
        break

if bag is None:
    log("no %s in the pack - combining from the pack itself, and salvaging nothing"
        % " or ".join(TOOL_BAG_NAMES))

tool = CraftTool("smith's tool", TOOL_GRAPHICS, TOOL_NAME_WORDS, log, TOOL_PREFERENCE)

if tool.serial() is None:
    log("no smith's hammer or tongs in the pack")
    API.Stop()

menu = CraftMenu(tool, {
    "stride": BUTTON_STRIDE,
    "category_type": CATEGORY_BUTTON_TYPE,
    "item_type": ITEM_BUTTON_TYPE,
    "category_names": CATEGORY_NAMES,
    "last_ten_label": LAST_TEN_LABEL,
    "title": CRAFT_TITLE,
    "title_text": CRAFT_TITLE_TEXT,
    "title_fragments": CRAFT_TITLE_FRAGMENTS,
    "tool_noun": "smith's tools",
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
}, log)
picker = MaterialPicker(menu, {
    "aliases": MATERIAL_ALIASES,
    "order": MATERIAL_ORDER,
    "rows_after": MATERIAL_ROWS_AFTER,
    "button_type": MATERIAL_BUTTON_TYPE,
    "row_type": MATERIAL_ROW_TYPE,
    "max_rows": MAX_MATERIAL_ROWS,
    "gump_timeout": GUMP_TIMEOUT,
}, log)

FILL = {
    # The pieces land beside the tool, so the bag is what the deed is aimed at
    "combine_target": bag if bag is not None else API.Backpack,
    "bag": bag,
    "salvage": SALVAGE_AT_END,
    "salvage_entries": SALVAGE_ENTRIES,
    "context_timeout": CONTEXT_TIMEOUT,
    "salvage_settle": SALVAGE_SETTLE,
    "ingots": INGOTS,
    "max_cycles": MAX_CYCLES,
    "max_unknown": MAX_UNKNOWN,
    "max_throttled": MAX_THROTTLED,
    "max_no_tool": MAX_NO_TOOL,
    "max_no_cursor": MAX_NO_CURSOR,
    "backoff": THROTTLE_BACKOFF,
    "backoff_max": THROTTLE_BACKOFF_MAX,
    "step_delay": STEP_DELAY,
}

WATCH = {
    "heartbeat": heartbeat,
    "stall": stall,
    "saves": saves,
    "stop_reason": stop_reason,
}

fills = []


# One small deed, start to finish: its own tooltip book, combiner and row proof
def fill_small(small):
    items = ItemBook(small.request, {
        "aliases": MATERIAL_ALIASES,
        "plain": PLAIN_MATERIAL,
        "articles": ARTICLES,
        "exceptional_text": EXCEPTIONAL_TEXT,
        "opl_timeout": OPL_TIMEOUT,
        "opl_settle": OPL_SETTLE,
        "asks": OPL_ASKS,
    }, log)
    crafter = DeedCrafter(tool, menu, items, picker, OUTCOME_TEXT, {
        "make_number_button": MAKE_NUMBER_BUTTON,
        "cancel_button": CANCEL_MAKE_BUTTON,
        "prompt_delay": PROMPT_DELAY,
        "craft_interval": CRAFT_INTERVAL,
        "batch_idle": BATCH_IDLE,
        "gump_timeout": GUMP_TIMEOUT,
        "craft_timeout": CRAFT_TIMEOUT,
        "craft_poll": CRAFT_POLL,
        "recipes": RECIPES,
        "max_reports": MAX_UNREADABLE_REPORTS,
        "text_limit": UNREADABLE_TEXT_LIMIT,
        "tail_seconds": JOURNAL_TAIL_SECONDS,
        "tail_lines": JOURNAL_TAIL_LINES,
        "notes_seconds": NOTES_TAIL_SECONDS,
    }, log, log.stamp, note_file)
    combiner = DeedCombiner(small, items, COMBINE_TEXT, combine_config(BOD_COMBINE_BUTTON), log,
                            log.stamp, note_file)
    fill = SmallFill(small, items, crafter, picker, combiner, FILL, log, WATCH)
    fills.append(fill)

    return fill.run()


# True when the run may go on. Stop() ends the script only at the next client call, so nothing
# here relies on it: each flow returns its reason and finish() is called once
def check(requests):
    if not CHECK_BEFORE_START:
        return True

    problems, notes = preflight(requests, tool.serials(), INGOTS)

    for note in notes:
        log(note)

    for problem in problems:
        log("not enough: " + problem)

    if len(problems) > 0:
        log("stopping before the first craft - set CHECK_BEFORE_START = False to run anyway")

    return len(problems) == 0


def finish(reason):
    up = API.HasGump()

    if up:
        API.CloseGump(up)

    if API.HasTarget():
        API.CancelTarget()

    for fill in fills:
        log(fill.summary())

    log("stopping - %s" % reason)

    if reason in (DEED_FULL, LARGE_COMPLETE):
        Launcher(log).run(DONE_SOUND)

    API.Stop()


def run_small():
    if not check([request]):
        return "not enough to start"

    return fill_small(deed) or DEED_FULL


def small_deed_for(item, smalls):
    known = smalls.get(item)

    if known is None:
        return None

    small = Deed(known["serial"], DEEDS, log)
    small.read()

    return small


# The smalls in the pack first, the box for the rest, each small filled and combined into the
# large in the deed's own order
def run_large():
    pending = [(item, done) for item, done in request["entries"] if done < request["total"]]

    if len(pending) == 0:
        return "the large deed is already complete"

    smalls = find_small_deeds(request, picked, DEEDS)

    if not check([entry_request(request, item, smalls[item]["done"] if item in smalls else 0)
                  for item, _done in pending]):
        return "not enough to start"

    missing = [item for item, _done in pending if item not in smalls]

    if len(missing) > 0:
        log("%d of %d entries have no small deed in the pack: %s"
            % (len(missing), len(pending), ", ".join(missing)))
        box = DeedBox({
            "names": BOX_NAMES,
            "deed_graphics": DEED_GRAPHICS,
            "deed_words": DEED_NAME_WORDS,
            "move_delay": MOVE_DELAY,
            "timeout": BOX_TIMEOUT,
            "poll": BOX_POLL,
        }, log)
        box_serial = box.find()

        if box_serial is None:
            return "no %s in the pack to get the small deeds from" % " or ".join(BOX_NAMES)

        if not box.generate(box_serial, picked):
            return "the box gave no small deeds"

        smalls = find_small_deeds(request, picked, DEEDS)
        missing = [item for item, _done in pending if item not in smalls]

        if len(missing) > 0:
            return "still no small deed for %s after the box" % ", ".join(missing)

    large_combiner = DeedCombiner(deed, None, LARGE_COMBINE_TEXT,
                                  combine_config(LARGE_COMBINE_BUTTON), log, log.stamp, note_file)
    index = 0

    for item, _done in pending:
        index += 1
        small = small_deed_for(item, smalls)

        if small is None or small.request is None:
            return "could not read the small deed for %s" % item

        log("entry %d/%d: %s, small deed %s with %d/%d done"
            % (index, len(pending), item, hex_of(small.serial), small.request["done"],
               small.request["total"]))

        if small.request["done"] < small.request["total"]:
            stop = fill_small(small)

            if stop is not None:
                return "%s (on entry %d/%d, %s)" % (stop, index, len(pending), item)

        outcome, taken = large_combiner.combine(small.serial, [small.serial])

        if len(taken) == 0 and outcome not in ("combined", "full"):
            return ("the large deed refused the small deed %s for %s (%s) - read the line above"
                    % (hex_of(small.serial), item, outcome))

        log("%s is in the large deed (%d/%d)" % (item, index, len(pending)))

    final, _refused = deed.read()

    if final is not None and all(done >= final["total"] for _item, done in final["entries"]):
        return LARGE_COMPLETE

    return "every entry was combined, but the large deed reads %s" % (
        deed.describe() if final is not None else "(no tooltip)")


start = skill.read() if skill is not None else None

log("%s: %s%s, %s in the pack"
    % (deed.describe(), skill_name or "Blacksmithy", " at %s" % reading(start),
       ingot_report(INGOTS)))

try:
    reason = run_large() if request["large"] else run_small()
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    reason = "threw - %s" % error

finish(reason)
