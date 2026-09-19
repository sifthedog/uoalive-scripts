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
            material = line.split(text["material_before"], 1)[1]

            for noun in text["material_nouns"]:
                material = material.replace(noun, "")

            material = material.strip(" .")
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


# The first trade, in order, whose recipes make every item the deed asks for
def trade_of(request, trades):
    for name, trade in trades:
        if all(item in trade["recipes"] for item, _done in request["entries"]):
            return name

    return None


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
        flags = "%s, %s" % (", exceptional" if request["exceptional"] else "",
                            request["material"] or "no material")

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
# API.Stop() only lands at the next Pause, and every client call before it answers nothing - so the
# backpack reads as null for the rest of a stopping script, and ItemsInContainer throws on a null
# container rather than answering none. Every caller here wants "nothing in the pack" for that
def _contents(recursive):
    backpack = API.Backpack

    if not backpack:
        return []

    items = API.ItemsInContainer(backpack, recursive)

    return items if items else []


def pack_contents():
    return _contents(True)


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
def is_stock(item, config):
    return item.Graphic in config["stock_graphics"] or word_in(item.Name, config["stock_words"])


# The name is where the shard writes the material ('Valorite Ingots'); a plain stack carries none
# and falls through to the hue
def material_of(item, config):
    words = words_of(item.Name)

    for material in config["materials"]:
        wanted = words_of(material)

        if words[:len(wanted)] == wanted:
            return material

    hue = hue_of(item)

    return config["hues"].get(hue, "hue 0x%x" % hue)


def kind_of(item, kinds):
    for name in kinds:
        if item.Graphic in kinds[name]:
            return name

    return None


# The trade's own stock by the material it is ('iron ingots'), and every other kind by its art
def stock_counts(config):
    counts = {}
    kinds = config.get("kinds", {})

    for item in pack_contents():
        if is_stock(item, config):
            name = "%s %s" % (material_of(item, config), config["stock_noun"])
        else:
            name = kind_of(item, kinds)

        if name is not None:
            counts[name] = counts.get(name, 0) + amount_of(item)

    return counts


def stock_report(config):
    counts = stock_counts(config)

    if len(counts) == 0:
        return "no stock"

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


# A cost is the trade's stock in the deed's material when it is a number ('oak boards'), and stock
# per kind when it is a dict
def needs_of(request, cost, noun):
    if isinstance(cost, dict):
        return dict(cost)

    return {"%s %s" % (request["material"], noun): cost}


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
            for name, each in needs_of(request, cost, config["stock_noun"]).items():
                needed[name] = needed.get(name, 0) + each * pieces

    if len(unknown) > 0:
        notes.append("no cost is known for %s, so those are not checked"
                     % ", ".join("'%s'" % item for item in unknown))

    held = stock_counts(config)

    for name in sorted(needed):
        have = held.get(name, 0)

        if have < needed[name]:
            problems.append("%d %s for the %d pieces owed, and the pack holds %d"
                            % (needed[name], name, owed, have))
        else:
            notes.append("%d %s cover the %d pieces owed, %d in the pack"
                         % (needed[name], name, owed, have))

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

# Named apart from INGOT_HUES rather than derived from it: a stack is matched on its name first, so
# this has to hold every material, including any whose hue is not known
INGOT_MATERIALS = sorted(set(INGOT_HUES.values()), key=len, reverse=True)

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
    # Stripped in turn, so one list covers every trade: the deed is parsed before the trade is known
    "material_nouns": ["ingots", "boards"],
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

# Alchemy deeds: the mortar's menu, as craft-map.py read it on 2026-09-13. Same button layout as
# the smith menu down to CANCEL MAKE on 227, and no material page. A row's details page reads
# 'MAKE NOW MAKE NUMBER MAKE MAX BACK' on 1, 2, 3, 0, and names the reagent and the bottle
ALCHEMY_SKILL_NAMES = ["Alchemy"]
ALCHEMY_TOOL_GRAPHICS = set([0x0E9B])
ALCHEMY_TOOL_NAME_WORDS = ["mortar"]
ALCHEMY_CRAFT_TITLE_TEXT = ["ALCHEMY", "ALCHEMIST"]

ALCHEMY_CATEGORY_NAMES = [
    "healing and curative",
    "enhancement",
    "toxic",
    "explosive",
    "strange brew",
    "ingredients",
    "skill tinctures",
]

# Keyed as the deed names the potion
ALCHEMY_RECIPES = {
    # Healing and Curative (button 1)
    "refresh potion": (1, 2),
    "greater refreshment potion": (1, 22),
    "lesser heal potion": (1, 42),
    "heal potion": (1, 62),
    "greater heal potion": (1, 82),
    "lesser cure potion": (1, 102),
    "cure potion": (1, 122),
    "greater cure potion": (1, 142),
    # Enhancement (button 21)
    "agility potion": (21, 2),
    "greater agility potion": (21, 22),
    "night sight potion": (21, 42),
    "strength potion": (21, 62),
    "greater strength potion": (21, 82),
    "invisibility potion": (21, 102),
    # Toxic (button 41)
    "lesser poison potion": (41, 2),
    "poison potion": (41, 22),
    "greater poison potion": (41, 42),
    "deadly poison potion": (41, 62),
    # Explosive (button 61)
    "lesser explosion potion": (61, 2),
    "explosion potion": (61, 22),
    "greater explosion potion": (61, 42),
    "conflagration potion": (61, 62),
    "greater conflagration potion": (61, 82),
    "confusion blast potion": (61, 102),
    "greater confusion blast potion": (61, 122),
}

# Stock art, unverified on UOAlive
REAGENT_KINDS = {
    "empty bottles": set([0x0F0E]),
    "black pearl": set([0x0F7A]),
    "blood moss": set([0x0F7B]),
    "garlic": set([0x0F84]),
    "ginseng": set([0x0F85]),
    "mandrake root": set([0x0F86]),
    "nightshade": set([0x0F88]),
    "spider's silk": set([0x0F8D]),
    "sulfurous ash": set([0x0F8C]),
    "grave dust": set([0x0F8F]),
    "pig iron": set([0x0F8A]),
}


def _potion(reagent, count):
    return {"empty bottles": 1, reagent: count}


# Per potion, stock RunUO counts. Only greater heal is read off the menu's details page, which says
# 'Ginseng 7 Empty Bottles 1'; the rest follow the stock table
POTION_COST = {
    "refresh potion": _potion("black pearl", 1),
    "greater refreshment potion": _potion("black pearl", 5),
    "lesser heal potion": _potion("ginseng", 1),
    "heal potion": _potion("ginseng", 3),
    "greater heal potion": _potion("ginseng", 7),
    "lesser cure potion": _potion("garlic", 1),
    "cure potion": _potion("garlic", 3),
    "greater cure potion": _potion("garlic", 6),
    "agility potion": _potion("blood moss", 1),
    "greater agility potion": _potion("blood moss", 3),
    "night sight potion": _potion("spider's silk", 1),
    "strength potion": _potion("mandrake root", 2),
    "greater strength potion": _potion("mandrake root", 5),
    "invisibility potion": {"empty bottles": 1, "blood moss": 4, "nightshade": 3},
    "lesser poison potion": _potion("nightshade", 1),
    "poison potion": _potion("nightshade", 2),
    "greater poison potion": _potion("nightshade", 4),
    "deadly poison potion": _potion("nightshade", 8),
    "lesser explosion potion": _potion("sulfurous ash", 3),
    "explosion potion": _potion("sulfurous ash", 5),
    "greater explosion potion": _potion("sulfurous ash", 10),
    "conflagration potion": _potion("grave dust", 5),
    "greater conflagration potion": _potion("grave dust", 10),
    "confusion blast potion": _potion("pig iron", 5),
    "greater confusion blast potion": _potion("pig iron", 10),
}

# The shard pours a craft into a keg of that potion instead of a bottle, so a keg is its own stop
ALCHEMY_OUTCOME_TEXT = [
    (
        "failed",
        [
            "You fail to create a useful potion",
            "You failed to create the item",
            "You fail to create",
            "You have failed to create",
            "lost some of the raw material",
        ],
    ),
    ("keg", ["pour it into a keg"]),
    (
        "made",
        [
            "You pour the potion into a bottle",
            "You create the item",
            "You create an exceptional",
            "You put the",
        ],
    ),
    (
        "noMaterial",
        [
            "You don't have the components",
            "You do not have the components",
            "You don't have the resources",
            "You do not have the resources",
            "enough empty bottles",
            "enough black pearl",
            "enough blood moss",
            "enough bloodmoss",
            "enough garlic",
            "enough ginseng",
            "enough mandrake",
            "enough nightshade",
            "enough spider",
            "enough sulfurous",
            "enough grave dust",
            "enough pig iron",
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

# Carpentry deeds: the menu's rows as craft-map.py read them on 2026-09-13, transcribed from
# src/carpentry rather than imported - build.py refuses two modules that define the same top-level
# name, and both configs carry RECIPES, CATEGORY_NAMES and OUTCOME_TEXT
CARPENTRY_SKILL_NAMES = ["Carpentry"]
CARPENTRY_TOOL_GRAPHICS = set([
    0x1034, 0x1035,  # saw
    0x1028, 0x1029,  # dovetail saw
    0x102A, 0x102B,  # hammer
    0x102C, 0x102D,  # moulding plane
    0x102E, 0x102F,  # nails
    0x1030, 0x1031,  # jointing plane
    0x1032, 0x1033,  # smoothing plane
    0x10E4,  # draw knife
    0x10E5,  # froe
    0x10E6,  # inshave
    0x10E7,  # scorp
])

# Whole words: 'hammer' is left out on purpose, a smith's hammer carries it
CARPENTRY_TOOL_NAME_WORDS = ["saw", "plane", "nails", "froe", "inshave", "scorp"]

CARPENTRY_CRAFT_TITLE_TEXT = ["CARPENTRY", "CARPENTER"]

CARPENTRY_CATEGORY_NAMES = [
    "other",
    "furniture",
    "containers",
    "weapons",
    "armor",
    "instruments",
    "misc. add-ons",
    "tailoring and cooking",
    "anvils and forges",
    "training",
]

# Hue is deliberately not matched: a shard with special woods hues them, and those craft too
BOARD_GRAPHICS = set([0x1BD7, 0x1BD9, 0x1BDA, 0x1BDB])

# No name words to go with the graphics: pack_contents reaches into the bag, and a crafted
# 'bulletin board' in there would otherwise be counted as board stock
CARPENTRY_STOCK_WORDS = []

# What a deed that names no wood wants, and the menu row it is set back to. Not None: that is the
# flag for a trade with no material page at all, and carpentry has one
PLAIN_WOOD = "regular"

WOOD_TYPES = ["oak", "ash", "yew", "heartwood", "bloodwood", "frostwood"]

# Named apart from WOOD_HUES because that table is short: a stack is matched on its name first
WOOD_MATERIALS = [PLAIN_WOOD] + WOOD_TYPES

# The material page's rows in stock order, for a page whose text cannot be read
WOOD_ORDER = [PLAIN_WOOD] + WOOD_TYPES

# The deed's wording first, then how the menu row and the item's tooltip may shorten it
WOOD_ALIASES = {
    PLAIN_WOOD: ["wood", "plain"],
}

# Unverified: the smith page's toggle, which the carpentry page need not carry. A marker that is
# not on the page leaves the split untrimmed, and select() logs the page when no row reads the wood
WOOD_ROWS_AFTER = "do not color"

# For the stack whose tooltip has not arrived. Incomplete on purpose: an unknown hue is reported
# as such, never treated as regular
WOOD_HUES = {
    0: PLAIN_WOOD,
    1191: "ash",
    2010: "oak",
}

CARPENTRY_RECIPES = {
    # Other (button 1)
    "barrel staves": (1, 2),
    "barrel lid": (1, 22),
    "short music stand (left)": (1, 42),
    "short music stand (right)": (1, 62),
    "tall music stand (left)": (1, 82),
    "tall music stand (right)": (1, 102),
    "easel (south)": (1, 122),
    "easel (east)": (1, 142),
    "easel (north)": (1, 162),
    "red hanging lantern": (1, 182),
    "white hanging lantern": (1, 202),
    "shoji screen": (1, 222),
    "bamboo screen": (1, 242),
    "fishing pole": (1, 262),
    "wooden container engraving tool": (1, 282),
    "runed switch": (1, 302),
    "arcanist statue (south)": (1, 322),
    "arcanist statue (east)": (1, 342),
    "warrior statue (south)": (1, 362),
    "warrior statue (east)": (1, 382),
    "squirrel statue (south)": (1, 402),
    "squirrel statue (east)": (1, 422),
    "giant replica acorn": (1, 442),
    "mounted dread horn": (1, 462),
    "acid proof rope": (1, 482),
    "gargish banner": (1, 502),
    "an incubator": (1, 522),
    "a chicken coop": (1, 542),
    "exodus summoning altar": (1, 562),
    "dark wooden sign hanger": (1, 582),
    "light wooden sign hanger": (1, 602),
    # Furniture (button 21)
    "foot stool": (21, 2),
    "stool": (21, 22),
    "straw chair": (21, 42),
    "wooden chair": (21, 62),
    "vesper-style chair": (21, 82),
    "trinsic-style chair": (21, 102),
    "wooden bench": (21, 122),
    "wooden throne": (21, 142),
    "magincia-style throne": (21, 162),
    "small table": (21, 182),
    "writing table": (21, 202),
    "yew-wood table": (21, 222),
    "large table": (21, 242),
    "elegant low table": (21, 262),
    "plain low table": (21, 282),
    "ornate table (south)": (21, 302),
    "ornate table (east)": (21, 322),
    "hardwood table (south)": (21, 342),
    "hardwood table (east)": (21, 362),
    "elven podium": (21, 382),
    "ornate elven chair": (21, 402),
    "cozy elven chair": (21, 422),
    "reading chair": (21, 442),
    "ter-mur style chair": (21, 462),
    "ter-mur style table": (21, 482),
    "upholstered chair": (21, 502),
    # Containers (button 41)
    "wooden box": (41, 2),
    "small crate": (41, 22),
    "medium crate": (41, 42),
    "large crate": (41, 62),
    "wooden chest": (41, 82),
    "wooden shelf": (41, 102),
    "armoire (red)": (41, 122),
    "armoire": (41, 142),
    "plain wooden chest": (41, 162),
    "ornate wooden chest": (41, 182),
    "gilded wooden chest": (41, 202),
    "wooden footlocker": (41, 222),
    "finished wooden chest": (41, 242),
    "tall cabinet": (41, 262),
    "short cabinet": (41, 282),
    "red armoire": (41, 302),
    "elegant armoire": (41, 322),
    "maple armoire": (41, 342),
    "cherry armoire": (41, 362),
    "keg": (41, 382),
    "arcane bookshelf (south)": (41, 402),
    "arcane bookshelf (east)": (41, 422),
    "ornate elven chest (south)": (41, 442),
    "ornate elven chest (east)": (41, 462),
    "elven wash basin (south)": (41, 482),
    "elven wash basin (east)": (41, 502),
    "elven dresser (south)": (41, 522),
    "elven dresser (east)": (41, 542),
    "elven armoire (fancy)": (41, 562),
    "elven armoire (simple)": (41, 582),
    "rarewood chest": (41, 602),
    "decorative box": (41, 622),
    "academic bookcase": (41, 642),
    "gargish chest": (41, 662),
    "empty liquor barrel": (41, 682),
    # Weapons (button 61)
    "shepherd's crook": (61, 2),
    "quarter staff": (61, 22),
    "gnarled staff": (61, 42),
    "bokuto": (61, 62),
    "fukiya": (61, 82),
    "tetsubo": (61, 102),
    "wild staff": (61, 122),
    "phantom staff": (61, 142),
    "arcanist's wild staff": (61, 162),
    "ancient wild staff": (61, 182),
    "thorned wild staff": (61, 202),
    "hardened wild staff": (61, 222),
    "serpentstone staff": (61, 242),
    "gargish gnarled staff": (61, 262),
    "club": (61, 282),
    "black staff": (61, 302),
    "kotl black rod": (61, 322),
    # Armor (button 81)
    "wooden shield": (81, 2),
    "woodland chest": (81, 22),
    "woodland arms": (81, 42),
    "woodland gauntlets": (81, 62),
    "woodland leggings": (81, 82),
    "woodland gorget": (81, 102),
    "raven helm": (81, 122),
    "vulture helm": (81, 142),
    "winged helm": (81, 162),
    "ironwood crown": (81, 182),
    "bramble coat": (81, 202),
    "darkwood crown": (81, 222),
    "darkwood chest": (81, 242),
    "darkwood gorget": (81, 262),
    "darkwood leggings": (81, 282),
    "darkwood pauldrons": (81, 302),
    "darkwood gauntlets": (81, 322),
    "gargish wooden shield": (81, 342),
    "pirate shield": (81, 362),
    # Instruments (button 101)
    "lap harp": (101, 2),
    "standing harp": (101, 22),
    "drum": (101, 42),
    "lute": (101, 62),
    "tambourine": (101, 82),
    "tambourine (tassel)": (101, 102),
    "bamboo flute": (101, 122),
    "aud-char": (101, 142),
    "snake charmer flute": (101, 162),
    "cello": (101, 182),
    "wall mounted bell (south)": (101, 202),
    "wall mounted bell (east)": (101, 222),
    "trumpet": (101, 242),
    "cowbell": (101, 262),
    # Misc. Add-Ons (button 121)
    "bulletin board": (121, 2),
    # "bulletin board": (121, 22),  listed again, the first kept
    "parrot perch": (121, 42),
    "arcane circle": (121, 62),
    "tall elven bed (south)": (121, 82),
    "tall elven bed (east)": (121, 102),
    "elven bed (south)": (121, 122),
    "elven bed (east)": (121, 142),
    "elven loveseat (east)": (121, 162),
    "elven loveseat (south)": (121, 182),
    "alchemist table (south)": (121, 202),
    "alchemist table (east)": (121, 222),
    "small bed (south)": (121, 242),
    "small bed (east)": (121, 262),
    "large bed (south)": (121, 282),
    "large bed (east)": (121, 302),
    "dartboard (south)": (121, 322),
    "dartboard (east)": (121, 342),
    "ballot box": (121, 362),
    "pentagram": (121, 382),
    "abbatoir": (121, 402),
    "gargish couch (east)": (121, 422),
    "gargish couch (south)": (121, 442),
    "gargish short table": (121, 462),
    "long table (south)": (121, 482),
    "long table (east)": (121, 502),
    "ter-mur style dresser (east)": (121, 522),
    "ter-mur style dresser (south)": (121, 542),
    "rustic bench (south)": (121, 562),
    "rustic bench (east)": (121, 582),
    "plain wooden shelf (south)": (121, 602),
    "plain wooden shelf (east)": (121, 622),
    "fancy wooden shelf (south)": (121, 642),
    "fancy wooden shelf (east)": (121, 662),
    "fancy loveseat (south)": (121, 682),
    "fancy loveseat (east)": (121, 702),
    "plush loveseat (south)": (121, 722),
    "plush loveseat (east)": (121, 742),
    "plant tapestry (south)": (121, 762),
    "plant tapestry (east)": (121, 782),
    "metal table (south)": (121, 802),
    "metal table (east)": (121, 822),
    "long metal table (south)": (121, 842),
    "long metal table (east)": (121, 862),
    "wooden table (south)": (121, 882),
    "wooden table (east)": (121, 902),
    "long wooden table (south)": (121, 922),
    "long wooden table (east)": (121, 942),
    "small display case (south)": (121, 962),
    "small display case (east)": (121, 982),
    "fancy loveseat (north)": (121, 1002),
    "fancy loveseat (west)": (121, 1022),
    "fancy couch (north)": (121, 1042),
    "fancy couch (west)": (121, 1062),
    "fancy couch (south)": (121, 1082),
    "fancy couch (east)": (121, 1102),
    "small elegant aquarium": (121, 1122),
    "wall mounted aquarium": (121, 1142),
    "large elegant aquarium": (121, 1162),
    # Tailoring and Cooking (button 141)
    "dressform (front)": (141, 2),
    "dressform (side)": (141, 22),
    "elven spinning wheel (east)": (141, 42),
    "elven spinning wheel (south)": (141, 62),
    "elven oven (south)": (141, 82),
    "elven oven (east)": (141, 102),
    "spinning wheel (east)": (141, 122),
    "spinning wheel (south)": (141, 142),
    "loom (east)": (141, 162),
    "loom (south)": (141, 182),
    "stone oven (east)": (141, 202),
    "stone oven (south)": (141, 222),
    "flour mill (east)": (141, 242),
    "flour mill (south)": (141, 262),
    "water trough (east)": (141, 282),
    "water trough (south)": (141, 302),
    # Anvils and Forges (button 161)
    "elven forge": (161, 2),
    "soulforge": (161, 22),
    "small forge": (161, 42),
    "large forge (east)": (161, 62),
    "large forge (south)": (161, 82),
    "anvil (east)": (161, 102),
    "anvil (south)": (161, 122),
    # Training (button 181)
    "training dummy (east)": (181, 2),
    "training dummy (south)": (181, 22),
    "pickpocket dip (east)": (181, 42),
    "pickpocket dip (south)": (181, 62),
}

# Boards per piece from uoalive.com/wiki/Carpentry, keyed as the deed names the item. Items that
# need more than boards are left out - the keg wants staves, the pirate shield and the display case
# want ingots, every instrument but the flute wants cloth, and the woodland and darkwood armour
# wants reagents. A left-out item is a preflight note, not a refusal, so an unclear row is omitted
# rather than guessed: understating only runs the pack dry mid-batch, overstating refuses the run.
BOARD_COST = {
    # Other (button 1)
    "barrel staves": 5,
    "barrel lid": 4,
    "short music stand (left)": 15,
    "short music stand (right)": 15,
    "tall music stand (left)": 20,
    "tall music stand (right)": 20,
    "easel (south)": 20,
    "easel (east)": 20,
    "easel (north)": 20,
    "arcanist statue (south)": 250,
    "arcanist statue (east)": 250,
    "warrior statue (south)": 250,
    "warrior statue (east)": 250,
    "squirrel statue (south)": 250,
    "squirrel statue (east)": 250,
    "giant replica acorn": 35,
    "mounted dread horn": 50,
    "an incubator": 100,
    "a chicken coop": 150,
    "dark wooden sign hanger": 5,
    "light wooden sign hanger": 5,
    # Furniture (button 21)
    "foot stool": 9,
    "stool": 9,
    "straw chair": 13,
    "wooden chair": 13,
    "vesper-style chair": 15,
    "trinsic-style chair": 15,
    "wooden bench": 17,
    "wooden throne": 17,
    "magincia-style throne": 19,
    "small table": 17,
    "writing table": 17,
    "yew-wood table": 27,
    "large table": 23,
    "elegant low table": 35,
    "plain low table": 35,
    "ornate table (south)": 60,
    "ornate table (east)": 60,
    "hardwood table (south)": 50,
    "hardwood table (east)": 50,
    "elven podium": 20,
    "ornate elven chair": 30,
    "cozy elven chair": 40,
    "reading chair": 30,
    "ter-mur style chair": 40,
    "ter-mur style table": 50,
    # Containers (button 41)
    "wooden box": 10,
    "small crate": 8,
    "medium crate": 15,
    "large crate": 18,
    "wooden chest": 20,
    "wooden shelf": 25,
    "armoire": 35,
    "plain wooden chest": 30,
    "ornate wooden chest": 30,
    "gilded wooden chest": 30,
    "wooden footlocker": 30,
    "finished wooden chest": 30,
    "tall cabinet": 35,
    "short cabinet": 35,
    "elegant armoire": 40,
    "maple armoire": 40,
    "cherry armoire": 40,
    "arcane bookshelf (south)": 80,
    "arcane bookshelf (east)": 80,
    "ornate elven chest (south)": 40,
    "ornate elven chest (east)": 40,
    "elven wash basin (south)": 40,
    "elven wash basin (east)": 40,
    "elven dresser (south)": 45,
    "elven dresser (east)": 45,
    "elven armoire (fancy)": 60,
    "elven armoire (simple)": 60,
    "rarewood chest": 30,
    "decorative box": 25,
    "gargish chest": 30,
    "empty liquor barrel": 50,
    # Weapons (button 61)
    "shepherd's crook": 7,
    "quarter staff": 6,
    "gnarled staff": 7,
    "bokuto": 6,
    "fukiya": 8,
    "tetsubo": 10,
    "wild staff": 16,
    "gargish gnarled staff": 7,
    "club": 10,
    "black staff": 9,
    # Armor (button 81)
    "wooden shield": 9,
    "gargish wooden shield": 9,
    # Instruments (button 101)
    "bamboo flute": 15,
    # Misc. Add-ons (button 121)
    "bulletin board": 50,
    "parrot perch": 50,
    "elven loveseat (east)": 50,
    "elven loveseat (south)": 50,
    "alchemist table (south)": 70,
    "alchemist table (east)": 70,
    "dartboard (south)": 5,
    "dartboard (east)": 5,
    "ballot box": 5,
    "gargish couch (east)": 75,
    "gargish couch (south)": 75,
    "gargish short table": 60,
    "long table (south)": 80,
    "long table (east)": 80,
    "ter-mur style dresser (east)": 60,
    "ter-mur style dresser (south)": 60,
    "rustic bench (south)": 35,
    "rustic bench (east)": 35,
    "plain wooden shelf (south)": 15,
    "plain wooden shelf (east)": 15,
    "fancy wooden shelf (south)": 15,
    "fancy wooden shelf (east)": 15,
    "wooden table (south)": 20,
    "wooden table (east)": 20,
    "long wooden table (south)": 80,
    "long wooden table (east)": 80,
    # Tailoring and Cooking (button 141)
    "elven oven (south)": 80,
    "elven oven (east)": 80,
    # Anvils and Forges (button 161)
    "elven forge": 200,
}

# Ordered: 'failed' before 'made' because "You failed to create the item" contains "create the item"
CARPENTRY_OUTCOME_TEXT = [
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
            # An exceptional craft says nothing else, and went unread as a result
            "You create an exceptional",
            "You put the",
        ],
    ),
    # Said in the gump's NOTICES panel, which the journal may never carry
    (
        "noMaterial",
        [
            "You do not have sufficient wood",
            "You do not have sufficient metal",
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

# Tinkering deeds: the menu's rows as craft-map.py read them on 2026-09-13, transcribed from
# src/tinkering rather than imported - build.py refuses two modules that define the same top-level
# name, and both configs carry RECIPES, CATEGORY_NAMES and OUTCOME_TEXT. A tinker spends the smith's
# ingots, so the material page, hues and aliases above are the ones this trade uses too.
TINKERING_SKILL_NAMES = ["Tinkering"]

# Stock art, unverified on UOAlive: an art learned by name joins the set
TINKERING_TOOL_GRAPHICS = set([0x1EB8, 0x1EB9])
TINKERING_TOOL_NAME_WORDS = ["tinker", "tinkers"]

TINKERING_CRAFT_TITLE_TEXT = ["TINKERING", "TINKER"]

# The CATEGORIES rows, lowercased, as craft-map.py read them off UOAlive's menu
TINKERING_CATEGORY_NAMES = [
    "jewelry",
    "wooden items",
    "tools",
    "parts",
    "utensils",
    "miscellaneous",
    "assemblies",
    "traps",
    "magic jewelry",
]

# (category button, row button) for every row, as craft-map.py read them off UOAlive's menu. Run
# craft-map.py again and paste its block over this one when the menu changes.
TINKERING_RECIPES = {
    # Jewelry (button 1)
    "ring": (1, 2),
    "bracelet": (1, 22),
    "gargish necklace": (1, 42),
    "gargish bracelet": (1, 62),
    "gargish ring": (1, 82),
    "gargish earrings": (1, 102),
    "star sapphire ring": (1, 122),
    "star sapphire necklace (silver)": (1, 142),
    "star sapphire necklace (jewelled)": (1, 162),
    "star sapphire earrings": (1, 182),
    "star sapphire necklace (golden)": (1, 202),
    "star sapphire bracelet": (1, 222),
    "emerald ring": (1, 242),
    "emerald necklace (silver)": (1, 262),
    "emerald necklace (jewelled)": (1, 282),
    "emerald earrings": (1, 302),
    "emerald necklace (golden)": (1, 322),
    "emerald bracelet": (1, 342),
    "sapphire ring": (1, 362),
    "sapphire necklace (silver)": (1, 382),
    "sapphire necklace (jewelled)": (1, 402),
    "sapphire earrings": (1, 422),
    "sapphire necklace (golden)": (1, 442),
    "sapphire bracelet": (1, 462),
    "ruby ring": (1, 482),
    "ruby necklace (silver)": (1, 502),
    "ruby necklace (jewelled)": (1, 522),
    "ruby earrings": (1, 542),
    "ruby necklace (golden)": (1, 562),
    "ruby bracelet": (1, 582),
    "citrine ring": (1, 602),
    "citrine necklace (silver)": (1, 622),
    "citrine necklace (jewelled)": (1, 642),
    "citrine earrings": (1, 662),
    "citrine necklace (golden)": (1, 682),
    "citrine bracelet": (1, 702),
    "amethyst ring": (1, 722),
    "amethyst necklace (silver)": (1, 742),
    "amethyst necklace (jewelled)": (1, 762),
    "amethyst earrings": (1, 782),
    "amethyst necklace (golden)": (1, 802),
    "amethyst bracelet": (1, 822),
    "tourmaline ring": (1, 842),
    "tourmaline necklace (silver)": (1, 862),
    "tourmaline necklace (jewelled)": (1, 882),
    "tourmaline earrings": (1, 902),
    "tourmaline necklace (golden)": (1, 922),
    "tourmaline bracelet": (1, 942),
    "amber ring": (1, 962),
    "amber necklace (silver)": (1, 982),
    "amber necklace (jewelled)": (1, 1002),
    "amber earrings": (1, 1022),
    "amber necklace (golden)": (1, 1042),
    "amber bracelet": (1, 1062),
    "diamond ring": (1, 1082),
    "diamond necklace (silver)": (1, 1102),
    "diamond necklace (jewelled)": (1, 1122),
    "diamond earrings": (1, 1142),
    "diamond necklace (golden)": (1, 1162),
    "diamond bracelet": (1, 1182),
    "krampus minion earrings": (1, 1202),
    "candied staff": (1, 1222),
    # Wooden Items (button 21)
    "nunchaku": (21, 2),
    "jointing plane": (21, 22),
    "moulding planes": (21, 42),
    "smoothing plane": (21, 62),
    "clock frame": (21, 82),
    "axle": (21, 102),
    "rolling pin": (21, 122),
    "ramrod": (21, 142),
    "softened reeds": (21, 162),
    "round basket": (21, 182),
    "bushel": (21, 202),
    "small bushel": (21, 222),
    "picnic basket": (21, 242),
    "winnowing basket": (21, 262),
    "square basket": (21, 282),
    "basket": (21, 302),
    "tall round basket": (21, 322),
    "small square basket": (21, 342),
    "tall basket": (21, 362),
    "small round basket": (21, 382),
    "enchanted picnic basket": (21, 402),
    # Tools (button 41)
    "scissors": (41, 2),
    "mortar and pestle": (41, 22),
    "scorp": (41, 42),
    "tinker's tools": (41, 62),
    "hatchet": (41, 82),
    "draw knife": (41, 102),
    "sewing kit": (41, 122),
    "saw": (41, 142),
    "dovetail saw": (41, 162),
    "froe": (41, 182),
    "shovel": (41, 202),
    "hammer": (41, 222),
    "tongs": (41, 242),
    "smith's hammer": (41, 262),
    "sledge hammer": (41, 282),
    "inshave": (41, 302),
    "pickaxe": (41, 322),
    "lockpick": (41, 342),
    "skillet": (41, 362),
    "flour sifter": (41, 382),
    "fletcher's tools": (41, 402),
    "mapmaker's pen": (41, 422),
    "scribe's pen": (41, 442),
    "clippers": (41, 462),
    "metal container engraving tool": (41, 482),
    "pitchfork": (41, 502),
    # Parts (button 61)
    "gears": (61, 2),
    "clock parts": (61, 22),
    "barrel tap": (61, 42),
    "springs": (61, 62),
    "sextant parts": (61, 82),
    "barrel hoops": (61, 102),
    "hinge": (61, 122),
    "bola balls": (61, 142),
    "jeweled filigree": (61, 162),
    # Utensils (button 81)
    "butcher knife": (81, 2),
    "spoon (left)": (81, 22),
    "spoon (right)": (81, 42),
    "plate": (81, 62),
    "fork (left)": (81, 82),
    "fork (right)": (81, 102),
    "cleaver": (81, 122),
    "knife (left)": (81, 142),
    "knife (right)": (81, 162),
    "goblet": (81, 182),
    "pewter mug": (81, 202),
    "pewter bowl": (81, 222),
    "a plant bowl": (81, 242),
    "skinning knife": (81, 262),
    "gargish cleaver": (81, 282),
    "gargish butcher's knife": (81, 302),
    # Miscellaneous (button 101)
    "key ring": (101, 2),
    "candelabra": (101, 22),
    "scales": (101, 42),
    "iron key": (101, 62),
    "globe": (101, 82),
    "spyglass": (101, 102),
    "lantern": (101, 122),
    "heating stand": (101, 142),
    "shoji lantern": (101, 162),
    "paper lantern": (101, 182),
    "round paper lantern": (101, 202),
    "wind chimes": (101, 222),
    "fancy wind chimes": (101, 242),
    "ter-mur style candelabra": (101, 262),
    "communication crystal": (101, 282),
    "gorgon lens": (101, 302),
    "a scale collar": (101, 322),
    "dragon lamp": (101, 342),
    "stained glass lamp": (101, 362),
    "tall double lamp": (101, 382),
    "curled metal sign hanger": (101, 402),
    "flourished metal sign hanger": (101, 422),
    "inward curled metal sign hanger": (101, 442),
    "end curled metal sign hanger": (101, 462),
    "left metal door (s in)": (101, 482),
    "right metal door (s in)": (101, 502),
    "left metal door (e out)": (101, 522),
    "right metal door (e out)": (101, 542),
    "currency wall safe": (101, 562),
    "left metal door (e in)": (101, 582),
    "right metal door (e in)": (101, 602),
    "left metal door (s out)": (101, 622),
    "right metal door (s out)": (101, 642),
    "kotl power core": (101, 662),
    "weathered bronze globe sculpture": (101, 682),
    "weathered bronze man on a bench sculpture": (101, 702),
    "weathered bronze fairy sculpture": (101, 722),
    "weathered bronze archer sculpture": (101, 742),
    "barbed whip": (101, 762),
    "spiked whip": (101, 782),
    "bladed whip": (101, 802),
    # Assemblies (button 121)
    "axle with gears": (121, 2),
    # "clock parts": (121, 22),  listed again, the first kept
    # "sextant parts": (121, 42),  listed again, the first kept
    "clock (right)": (121, 62),
    "clock (left)": (121, 82),
    "sextant": (121, 102),
    "bola": (121, 122),
    "potion keg": (121, 142),
    "leather wolf assembly": (121, 162),
    "clockwork scorpion assembly": (121, 182),
    "vollem assembly": (121, 202),
    "hitching rope": (121, 222),
    "hitching post (replica)": (121, 242),
    "arcanic rune stone": (121, 262),
    "void orb": (121, 282),
    "advanced training dummy (south)": (121, 302),
    "advanced training dummy (east)": (121, 322),
    "distillery (south)": (121, 342),
    "distillery (east)": (121, 362),
    "kotl automaton": (121, 382),
    "telescope": (121, 402),
    "oracle of the sea": (121, 422),
    # Traps (button 141)
    "dart trap": (141, 2),
    "poison trap": (141, 22),
    "explosion trap": (141, 42),
    # Magic Jewelry (button 161)
    "brilliant amber bracelet": (161, 2),
    "fire ruby bracelet": (161, 22),
    "dark sapphire bracelet": (161, 42),
    "white pearl bracelet": (161, 62),
    "ecru citrine ring": (161, 82),
    "blue diamond ring": (161, 102),
    "perfect emerald ring": (161, 122),
    "turquoise ring": (161, 142),
    "resilient bracer": (161, 162),
    "essence of battle": (161, 182),
    "pendant of the magi": (161, 202),
    "dr. spector's lenses": (161, 222),
    "bracelet of primal consumption": (161, 242),
    # As the deed words a row the menu names otherwise. The deed uses the item's own name, the menu
    # its recipe's: 'frypan' is made by the skillet row and 'arrow fletching' by the fletcher's
    # tools row, and the utensils the menu brackets left and right the deed names bare.
    # uo.com/wiki/ultima-online-wiki/skills/tinkering/tinker-bulk-orders lists the four groups a
    # large tinker deed draws from. Every item in them is below or above except 'earrings', which
    # the menu only offers gemmed, one row per gem - an earrings deed stops on noRow by design
    # rather than spending a gem on a guess
    "spoon": (81, 22),
    "fork": (81, 82),
    "knife": (81, 142),
    "frypan": (41, 362),
    "arrow fletching": (41, 402),
}

# Ingots per piece from uoalive.com/wiki/Tinkering, keyed as the deed names the item. Only the rows
# whose whole cost is ingots: a number is ingots of the deed's material, so anything wanting gems,
# boards, shafts or a part made first is left out - the gemmed and magic jewelry, every wooden item,
# the paper and shoji lanterns, the candied staff, the three traps, every assembly, the jewelled
# filigree, the engraving tool, the lamps, the kotl core, the gorgon lens and the scale collar. The
# four weathered bronze sculptures want 200 *bronze* ingots, which a plain number cannot say. A
# left-out item is a preflight note, not a refusal.
TINKERING_INGOT_COST = {
    # Jewelry (button 1)
    "ring": 3, "bracelet": 3, "gargish necklace": 3, "gargish bracelet": 3, "gargish ring": 3,
    "gargish earrings": 3, "krampus minion earrings": 3,
    # Tools (button 41)
    "scissors": 2, "mortar and pestle": 3, "scorp": 2, "tinker's tools": 2, "hatchet": 4,
    "draw knife": 2, "sewing kit": 2, "saw": 4, "dovetail saw": 4, "froe": 2, "shovel": 4,
    "hammer": 1, "tongs": 1, "smith's hammer": 4, "sledge hammer": 4, "inshave": 2, "pickaxe": 4,
    "lockpick": 1, "skillet": 4, "flour sifter": 3, "fletcher's tools": 3, "mapmaker's pen": 1,
    "scribe's pen": 1, "clippers": 4, "pitchfork": 8,
    # Parts (button 61)
    "gears": 2, "clock parts": 1, "barrel tap": 2, "springs": 2, "sextant parts": 4,
    "barrel hoops": 5, "hinge": 2, "bola balls": 10,
    # Utensils (button 81)
    "butcher knife": 2, "spoon (left)": 1, "spoon (right)": 1, "plate": 2, "fork (left)": 1,
    "fork (right)": 1, "cleaver": 3, "knife (left)": 1, "knife (right)": 1, "goblet": 2,
    "pewter mug": 2, "pewter bowl": 2, "skinning knife": 2, "gargish cleaver": 3,
    "gargish butcher's knife": 2,
    # Miscellaneous (button 101)
    "key ring": 2, "candelabra": 4, "scales": 4, "iron key": 3, "globe": 4, "spyglass": 4,
    "lantern": 4, "heating stand": 4, "wind chimes": 15, "fancy wind chimes": 15,
    "ter-mur style candelabra": 4, "curled metal sign hanger": 8,
    "flourished metal sign hanger": 8, "inward curled metal sign hanger": 8,
    "end curled metal sign hanger": 8, "left metal door (s in)": 8, "right metal door (s in)": 8,
    "left metal door (e out)": 8, "right metal door (e out)": 8, "left metal door (e in)": 8,
    "right metal door (e in)": 8, "left metal door (s out)": 8, "right metal door (s out)": 8,
    "currency wall safe": 20,
    # As the deed words the rows above: the bracketed utensils, the skillet and the fletcher's tools
    "spoon": 1, "fork": 1, "knife": 1, "frypan": 4, "arrow fletching": 3,
}

# Ordered: 'failed' before 'made' because "You failed to create the item" contains "create the item"
TINKERING_OUTCOME_TEXT = [
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
            "You create an exceptional",
            "You put the",
        ],
    ),
    # Said in the gump's NOTICES panel, which the journal may never carry
    (
        "noMaterial",
        [
            "You do not have sufficient metal",
            "You don't have the resources",
            "You do not have the resources",
            "not enough ingots",
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

# The first trade whose recipes make every item on the deed fills it. A number cost is ingots of
# the deed's material; a dict cost is stock per kind. plain is what a deed with no material line
# wants: None means there is no material page to press
TRADES = [
    ("smith", {
        "skill_names": SKILL_NAMES,
        "tool_noun": "smith's tool",
        "tool_graphics": TOOL_GRAPHICS,
        "tool_words": TOOL_NAME_WORDS,
        "tool_preference": TOOL_PREFERENCE,
        "title": CRAFT_TITLE,
        "title_text": CRAFT_TITLE_TEXT,
        "category_names": CATEGORY_NAMES,
        "recipes": RECIPES,
        "costs": INGOT_COST,
        "kinds": {},
        "stock_graphics": INGOT_GRAPHICS,
        "stock_words": INGOT_NAME_WORDS,
        "stock_noun": "ingots",
        "materials": INGOT_MATERIALS,
        "hues": INGOT_HUES,
        "material_aliases": MATERIAL_ALIASES,
        "material_order": MATERIAL_ORDER,
        "material_rows_after": MATERIAL_ROWS_AFTER,
        "outcome_text": OUTCOME_TEXT,
        "salvage": SALVAGE_AT_END,
        "plain": PLAIN_MATERIAL,
    }),
    # Every potion cost is a dict, so the stock keys are empty rather than unused: reagents are
    # counted by art through kinds, and an ingot in the pack is not this run's stock
    ("alchemy", {
        "skill_names": ALCHEMY_SKILL_NAMES,
        "tool_noun": "mortar and pestle",
        "tool_graphics": ALCHEMY_TOOL_GRAPHICS,
        "tool_words": ALCHEMY_TOOL_NAME_WORDS,
        "tool_preference": None,
        "title": ALCHEMY_CRAFT_TITLE_TEXT[0],
        "title_text": ALCHEMY_CRAFT_TITLE_TEXT,
        "category_names": ALCHEMY_CATEGORY_NAMES,
        "recipes": ALCHEMY_RECIPES,
        "costs": POTION_COST,
        "kinds": REAGENT_KINDS,
        "stock_graphics": set(),
        "stock_words": [],
        "stock_noun": None,
        "materials": [],
        "hues": {},
        "material_aliases": {},
        "material_order": [],
        # Never read behind a plain of None, and "" leaves the row split a no-op where None throws
        "material_rows_after": "",
        "outcome_text": ALCHEMY_OUTCOME_TEXT,
        "salvage": False,
        "plain": None,
    }),
    # Boards are one pool told apart by the wood they are, so the cost is a number and kinds is
    # empty - the same shape as the smith's ingots
    ("carpentry", {
        "skill_names": CARPENTRY_SKILL_NAMES,
        "tool_noun": "carpentry tool",
        "tool_graphics": CARPENTRY_TOOL_GRAPHICS,
        "tool_words": CARPENTRY_TOOL_NAME_WORDS,
        "tool_preference": None,
        "title": CARPENTRY_CRAFT_TITLE_TEXT[0],
        "title_text": CARPENTRY_CRAFT_TITLE_TEXT,
        "category_names": CARPENTRY_CATEGORY_NAMES,
        "recipes": CARPENTRY_RECIPES,
        "costs": BOARD_COST,
        "kinds": {},
        "stock_graphics": BOARD_GRAPHICS,
        "stock_words": CARPENTRY_STOCK_WORDS,
        "stock_noun": "boards",
        "materials": WOOD_MATERIALS,
        "hues": WOOD_HUES,
        "material_aliases": WOOD_ALIASES,
        "material_order": WOOD_ORDER,
        "material_rows_after": WOOD_ROWS_AFTER,
        "outcome_text": CARPENTRY_OUTCOME_TEXT,
        "salvage": False,
        "plain": PLAIN_WOOD,
    }),
    # A tinker spends the smith's ingot pool and needs no forge, so the stock tables above are
    # reused whole and the outcome set carries no noAnvil. Nothing salvages a pewter mug
    ("tinkering", {
        "skill_names": TINKERING_SKILL_NAMES,
        "tool_noun": "tinker's tools",
        "tool_graphics": TINKERING_TOOL_GRAPHICS,
        "tool_words": TINKERING_TOOL_NAME_WORDS,
        "tool_preference": None,
        "title": TINKERING_CRAFT_TITLE_TEXT[0],
        "title_text": TINKERING_CRAFT_TITLE_TEXT,
        "category_names": TINKERING_CATEGORY_NAMES,
        "recipes": TINKERING_RECIPES,
        "costs": TINKERING_INGOT_COST,
        "kinds": {},
        "stock_graphics": INGOT_GRAPHICS,
        "stock_words": INGOT_NAME_WORDS,
        "stock_noun": "ingots",
        "materials": INGOT_MATERIALS,
        "hues": INGOT_HUES,
        "material_aliases": MATERIAL_ALIASES,
        "material_order": MATERIAL_ORDER,
        "material_rows_after": MATERIAL_ROWS_AFTER,
        "outcome_text": TINKERING_OUTCOME_TEXT,
        "salvage": False,
        "plain": PLAIN_MATERIAL,
    }),
]


# src/bod/craft.py
STOPPERS = ("noMaterial", "noAnvil", "keg", "skillTooLow", "toolWorn", "throttled", "saving")


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
                  % (before, after, stock_report(self._config["stock"])))

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

            return ("the shard says the materials ran out - %s in the pack, %d still owed"
                    % (stock_report(config["stock"]), self.owed()))
        elif outcome == "keg":
            return "a potion keg in the pack is swallowing the crafts - take it out and run again"
        elif outcome == "toolWorn":
            self._stall.progressed()
            self._log("the tool wore out, looking for another")
        elif outcome == "skillTooLow":
            return "the shard says you cannot make a %s" % item
        elif outcome == "noAnvil":
            return "stand next to an anvil and a forge"
        elif outcome == "noRow":
            return "'%s' is not in the %s recipes" % (item, config["trade"])
        elif outcome == "noMaterialRow":
            return "the material page has no row for %s" % self._request["material"]
        elif outcome in ("noTool", "noGump"):
            self._no_tool += 1

            if self._no_tool >= config["max_no_tool"]:
                return ("no %s left" % config["tool_noun"] if outcome == "noTool"
                        else "the craft menu will not open")

            self._log("%s (%d/%d), trying again"
                      % ("no %s in the pack" % config["tool_noun"] if outcome == "noTool"
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
            self._log("unreadable outcome (%d/%d), check the %s outcome text"
                      % (self._unknown, config["max_unknown"], config["trade"]))

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

    # A deed that names no material (a potion deed) never opens the page
    def needs(self, material):
        return material is not None and self._selected != material

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

        if self.has_button(button, gump):
            return self._send(button, gump)

        self._send(button, gump)

        # Up under the menu's id without the table's button, it is not the menu the table was read
        # off: a popup the recogniser took for it, or a redraw the client reads empty. Left open it
        # answers every retry the same, so it is closed and the tool opens a fresh one.
        if is_open(gump):
            API.CloseGump(gump)

        self._id = 0

        return False

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

    # Every craft menu comes up under the same id, so the one remembered may now be showing another
    # skill's menu, which would take this menu's buttons. Only a gump naming another menu is let go:
    # a build whose GetGumpContents answers nothing still answers for its own.
    def _is_other_menu(self, ident):
        return any_in(API.GetGumpContents(ident) or "", self._config.get("foreign_fragments", []))

    def open(self):
        if self._id and is_open(self._id):
            if not self._is_other_menu(self._id):
                return self._id

            self._id = 0

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


# plain is the trade's once the deed says which trade it is
DEEDS = {
    "text": DEED_TEXT,
    "plain": None,
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

trade_name = trade_of(request, TRADES)

if trade_name is None:
    log("no trade in TRADES makes %s" % ", ".join(item for item, _done in request["entries"]))
    API.Stop()

# Stop() only lands at the next client call, so the lines below still run once: the first trade
# stands in so they read something rather than throwing ahead of it
trade = dict(TRADES).get(trade_name, TRADES[0][1])

# Read before the trade was known, so the material a deed did not name is filled in here; the
# smalls the large flow reads later get it from DEEDS
DEEDS["plain"] = trade["plain"]

STOCK = {
    "stock_graphics": trade["stock_graphics"],
    "stock_words": trade["stock_words"],
    "stock_noun": trade["stock_noun"],
    "materials": trade["materials"],
    "hues": trade["hues"],
    "costs": trade["costs"],
    "kinds": trade["kinds"],
    "uses_text": USES_TEXT,
    "opl_timeout": OPL_TIMEOUT,
}

if request["material"] is None:
    request["material"] = trade["plain"]

skill_name = find_skill_name(trade["skill_names"])
skill = SkillReader(skill_name) if skill_name is not None else None

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

tool = CraftTool(trade["tool_noun"], trade["tool_graphics"], trade["tool_words"], log,
                 trade["tool_preference"])

if tool.serial() is None:
    log("no %s in the pack" % trade["tool_noun"])
    API.Stop()

menu = CraftMenu(tool, {
    "stride": BUTTON_STRIDE,
    "category_type": CATEGORY_BUTTON_TYPE,
    "item_type": ITEM_BUTTON_TYPE,
    "category_names": trade["category_names"],
    "last_ten_label": LAST_TEN_LABEL,
    "title": trade["title"],
    "title_text": trade["title_text"],
    "title_fragments": [phrase.lower() for phrase in trade["title_text"]],
    "tool_noun": trade["tool_noun"],
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
}, log)
picker = MaterialPicker(menu, {
    "aliases": trade["material_aliases"],
    "order": trade["material_order"],
    "rows_after": trade["material_rows_after"],
    "button_type": MATERIAL_BUTTON_TYPE,
    "row_type": MATERIAL_ROW_TYPE,
    "max_rows": MAX_MATERIAL_ROWS,
    "gump_timeout": GUMP_TIMEOUT,
}, log)

FILL = {
    # The pieces land beside the tool, so the bag is what the deed is aimed at
    "combine_target": bag if bag is not None else API.Backpack,
    "bag": bag,
    "salvage": trade["salvage"],
    "trade": trade_name,
    "tool_noun": trade["tool_noun"],
    "salvage_entries": SALVAGE_ENTRIES,
    "context_timeout": CONTEXT_TIMEOUT,
    "salvage_settle": SALVAGE_SETTLE,
    "stock": STOCK,
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
        "aliases": trade["material_aliases"],
        "plain": trade["plain"],
        "articles": ARTICLES,
        "exceptional_text": EXCEPTIONAL_TEXT,
        "opl_timeout": OPL_TIMEOUT,
        "opl_settle": OPL_SETTLE,
        "asks": OPL_ASKS,
    }, log)
    crafter = DeedCrafter(tool, menu, items, picker, trade["outcome_text"], {
        "make_number_button": MAKE_NUMBER_BUTTON,
        "cancel_button": CANCEL_MAKE_BUTTON,
        "prompt_delay": PROMPT_DELAY,
        "craft_interval": CRAFT_INTERVAL,
        "batch_idle": BATCH_IDLE,
        "gump_timeout": GUMP_TIMEOUT,
        "craft_timeout": CRAFT_TIMEOUT,
        "craft_poll": CRAFT_POLL,
        "recipes": trade["recipes"],
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

    problems, notes = preflight(requests, tool.serials(), STOCK)

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
    % (deed.describe(), skill_name or trade["skill_names"][0], " at %s" % reading(start),
       stock_report(STOCK)))

try:
    reason = run_large() if request["large"] else run_small()
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    reason = "threw - %s" % error

finish(reason)
