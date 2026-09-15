# Built from src/assembly/index.py by build.py - do not edit.

import API
import time


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

STOPPED = "stopped from the script manager"


# src/assembly/config.py
KEG = "keg"
POTION_KEG = "potion keg"

STAVES = "barrel staves"
LID = "barrel lid"
HOOPS = "barrel hoops"
BOTTLE = "bottle"
TAP = "barrel tap"
BOARDS = "boards"
INGOTS = "ingots"

CLOCK_FRAME = "clock frame"
CLOCK_PARTS = "clock parts"
# The menu spells it out; a bare "clock" is not a row on either table
CLOCK = "clock (right)"

# Stock art, unverified on UOAlive; an art learned by name joins its set. Board hue is not matched:
# the menu spends whichever wood it is set to, so set it to the boards in the pack.
PART_KINDS = [
    (BOARDS, set([0x1BD7, 0x1BD9, 0x1BDA, 0x1BDB]), ["board", "boards"]),
    (INGOTS, set([0x1BEF, 0x1BF2]), ["ingot", "ingots"]),
    (STAVES, set([0x1EB1, 0x1EB2, 0x1EB3, 0x1EB4]), ["staves"]),
    (LID, set([0x1DB8]), ["lid"]),
    (HOOPS, set([0x1DB7]), ["hoops"]),
    (KEG, set([0x1940]), ["keg"]),
    (BOTTLE, set([0x0F0E]), ["bottle", "bottles"]),
    (TAP, set([0x1004]), ["tap"]),
    (CLOCK_FRAME, set([0x104D, 0x104E]), ["frame"]),
    (CLOCK_PARTS, set([0x104F, 0x1050]), ["parts"]),
]
PART_ORDER = [kind for kind, _graphics, _words in PART_KINDS]

# A made potion keg is the same 0x1940 as the empty keg it took; only the name tells them apart
MADE_KEG_TYPES = ["specially lined"]

# One (key, caption, stages) per radio option. A stage is (row, menu, what one press spends), a part
# always above whatever spends it: the run presses the first row the next product still lacks,
# counted back through the pack, so parts already there are used first. The last row is the product.
# Bottles have no row on either menu. Stock DefCarpentry and DefTinkering.
#
# The clock's rows are the ones a 10-clock run was watched pressing. Its clock parts are the Parts
# group's, which spends ingots, not the Assemblies group's axle with gears and springs.
ASSEMBLIES = [
    ("keg", "Keg", [
        (STAVES, "carpentry", {BOARDS: 5}),
        (LID, "carpentry", {BOARDS: 4}),
        (HOOPS, "tinkering", {INGOTS: 5}),
        (KEG, "carpentry", {STAVES: 3, LID: 1, HOOPS: 1}),
    ]),
    ("potion keg", "Potion keg", [
        (STAVES, "carpentry", {BOARDS: 5}),
        (LID, "carpentry", {BOARDS: 4}),
        (HOOPS, "tinkering", {INGOTS: 5}),
        (TAP, "tinkering", {INGOTS: 2}),
        (KEG, "carpentry", {STAVES: 3, LID: 1, HOOPS: 1}),
        (POTION_KEG, "tinkering", {KEG: 1, BOTTLE: 10, LID: 1, TAP: 1}),
    ]),
    ("clock", "Clock", [
        (CLOCK_PARTS, "tinkering", {INGOTS: 5}),
        (CLOCK_FRAME, "tinkering", {BOARDS: 6}),
        (CLOCK, "tinkering", {CLOCK_FRAME: 1, CLOCK_PARTS: 1}),
    ]),
]

# One craft menu each, as craft-map.py read them off UOAlive; only the rows the stages press
MENUS = {
    "carpentry": {
        "tool_noun": "carpentry tools",
        "tool_graphics": set([
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
        ]),
        "tool_name_words": ["saw", "plane", "nails", "froe", "inshave", "scorp"],
        "title": "CARPENTRY",
        "title_text": ["CARPENTRY", "CARPENTER"],
        "category_names": ["other", "furniture", "containers", "weapons", "armor", "instruments",
                           "misc. add-ons", "tailoring and cooking", "anvils and forges",
                           "training"],
        "recipes": {STAVES: (1, 2), LID: (1, 22), KEG: (41, 382)},
    },
    "tinkering": {
        "tool_noun": "tinker's tools",
        "tool_graphics": set([0x1EB8, 0x1EB9]),
        "tool_name_words": ["tinker", "tinkers"],
        "title": "TINKERING",
        "title_text": ["TINKERING", "TINKER"],
        "category_names": ["jewelry", "wooden items", "tools", "parts", "utensils",
                           "miscellaneous", "assemblies", "traps", "magic jewelry"],
        "recipes": {TAP: (61, 42), HOOPS: (61, 102), POTION_KEG: (121, 142), CLOCK_FRAME: (21, 82),
                    CLOCK_PARTS: (61, 22), CLOCK: (121, 62)},
    },
}

START_PROMPT = {
    "text": "What to make",
    "options": [(key, caption) for key, caption, _stages in ASSEMBLIES],
    "assembly_default": "potion keg",
    "count_text": "How many?",
    "default": 1,
    "hue": 996,
    "poll": 0.25,
}

WEIGHT_BUFFER = 40

# Its own button rather than a group, so it does not count toward the category index
LAST_TEN_LABEL = "LAST TEN"

# Buttons are 1 + type + index * 20 on this shard's menus. MAKE LAST is the stock
# GetButtonID(6, 2): 1 + 6 + 2 * 20
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1
MAKE_LAST_BUTTON = 47

GUMP_TIMEOUT = 5.0
GUMP_POLL = 0.15

# Has to outlast the craft animation, which plays before the shard answers
CRAFT_TIMEOUT = 10.0
CRAFT_POLL = 0.2

MOVE_DELAY = 0.7

MAX_UNKNOWN = 5
MAX_THROTTLED = 20
MAX_NO_TOOL = 10

# What an unreadable outcome reports before it goes quiet, and how much of it
MAX_UNREADABLE_REPORTS = 2
UNREADABLE_TEXT_LIMIT = 160
JOURNAL_TAIL_SECONDS = 20.0
JOURNAL_TAIL_LINES = 4

# The whole gump and journal behind a report, appended here so the game window stays quiet. "" turns
# it off; a bare name lands beside the script.
NOTES_PATH = "assembly-notes.log"
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
            "You do not have sufficient wood",
            "You do not have sufficient metal",
            "You don't have the resources",
            "You do not have the resources",
            "There is not enough wood",
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


# src/assembly/plan.py
# Demand runs backwards from one product through what the pack already holds, and the first stage
# still missing is pressed. The product itself is counted as absent however many are in the pack:
# a keg or a clock is its own part elsewhere, and the ones already made would otherwise plan nothing.
def next_stage(stages, stock):
    product = stages[-1][0]
    demand = {product: 1}
    missing = {}

    for row, _menu, needs in reversed(stages):
        held = 0 if row == product else stock.get(row, 0)
        missing[row] = max(0, demand.get(row, 0) - held)

        for part in needs:
            demand[part] = demand.get(part, 0) + needs[part] * missing[row]

    for stage in stages:
        if missing[stage[0]] > 0:
            return stage

    return stages[-1]


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


# src/uo/setup.py
RADIO_CHAR = 8
RADIO_GAP = 40


# src/assembly/prompt.py
PROMPT_WIDTH = 340
PROMPT_HEIGHT = 178
PROMPT_BUTTON_HEIGHT = 26
PROMPT_BOX_WIDTH = 60
RADIO_LABEL_Y = 16
RADIO_ROW_Y = 40
COUNT_LABEL_Y = 74
COUNT_BOX_Y = 100


class StartPrompt(object):
    """Asked once, before the loop: which assembly to make, and how many. None means do not start."""

    def __init__(self, config, log, stop_reason):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason
        self._radios = []

    # A blank, zero, negative or non-numeric box answers the default rather than refusing to start
    def _count(self, box):
        text = (box.Text or "").strip()

        return int(text) if text.isdigit() and int(text) > 0 else self._config["default"]

    # None until something has actually clicked one: a radio's isChecked at creation is not always
    # something GetIsChecked reflects back
    def _checked(self):
        options = self._config["options"]

        for index in range(len(self._radios)):
            if self._radios[index].GetIsChecked():
                return options[index][0]

        return None

    def _show(self, on_press):
        gump = API.Gumps.CreateGump(True, True)

        if gump is None:
            return None, None

        gump.SetRect(0, 0, PROMPT_WIDTH, PROMPT_HEIGHT)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.85, "#1E1E1E")
        background.SetRect(0, 0, PROMPT_WIDTH, PROMPT_HEIGHT)
        gump.Add(background)

        label = API.Gumps.CreateGumpLabel(self._config["text"], self._config["hue"])
        label.SetPos(16, RADIO_LABEL_Y)
        gump.Add(label)

        options = self._config["options"]
        default = self._config["assembly_default"]
        x = 16

        # Spaced by caption: the classic font runs about RADIO_CHAR pixels a letter
        for index in range(len(options)):
            key, caption = options[index]
            radio = API.Gumps.CreateGumpRadioButton(caption, 1, 0x00D0, 0x00D1,
                                                    self._config["hue"], key == default)
            radio.SetPos(x, RADIO_ROW_Y)
            gump.Add(radio)
            self._radios.append(radio)
            x += RADIO_GAP + RADIO_CHAR * len(caption)

        count_label = API.Gumps.CreateGumpLabel(self._config["count_text"], self._config["hue"])
        count_label.SetPos(16, COUNT_LABEL_Y)
        gump.Add(count_label)

        box = API.Gumps.CreateGumpTextBox(str(self._config["default"]), PROMPT_BOX_WIDTH,
                                          PROMPT_BUTTON_HEIGHT, False, 20)
        box.SetPos(16, COUNT_BOX_Y)
        gump.Add(box)

        ok = API.Gumps.CreateSimpleButton("OK", 90, PROMPT_BUTTON_HEIGHT)
        ok.SetPos(16, PROMPT_HEIGHT - 42)
        API.Gumps.AddControlOnClick(ok, lambda: on_press("ok"))
        gump.Add(ok)

        cancel = API.Gumps.CreateSimpleButton("Cancel", 90, PROMPT_BUTTON_HEIGHT)
        cancel.SetPos(114, PROMPT_HEIGHT - 42)
        API.Gumps.AddControlOnClick(cancel, lambda: on_press("cancel"))
        gump.Add(cancel)

        API.Gumps.AddGump(gump)

        return gump, box

    def ask(self):
        pressed = [None]
        answers = {"assembly": self._config["assembly_default"], "wanted": self._config["default"]}
        gump, box = self._show(lambda button: pressed.__setitem__(0, button))

        if gump is None:
            self._log("not asking - the run is being stopped")

            return None

        self._log("asking - %s" % self._config["text"])

        # Read every slice, not once at the end: wait_for_gump disposes the gump before returning
        # and a disposed radio reports nothing checked, which read as the default and sent a clock
        # run down the potion keg rows
        def resolve():
            checked = self._checked()

            if checked is not None:
                answers["assembly"] = checked

            answers["wanted"] = self._count(box)

            return pressed[0]

        why = wait_for_gump(gump, self._stop_reason, self._config["poll"], resolve,
                            closed_message="cancel")

        if why != "ok":
            self._log(why)

            return None

        return answers


# src/uo/components.py
def short_of(needs, counts):
    short = {}

    for kind in needs:
        missing = needs[kind] - counts.get(kind, 0)

        if missing > 0:
            short[kind] = missing

    return short


# In the caller's kind order, so the line reads the same each time
def shortfall_report(short, order):
    parts = ["%d %s" % (short[kind], kind) for kind in order if kind in short]
    parts += ["%d %s" % (short[kind], kind) for kind in sorted(short) if kind not in order]

    return ", ".join(parts)


# src/uo/clock.py
def time_text():
    return time.strftime("%Y-%m-%d %H:%M:%S")


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


# src/uo/journal.py
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


# src/uo/craft.py
class Crafter(object):
    """Presses the RECIPES row as written and reads only the shard's words for the outcome."""

    def __init__(self, tools, menu, stock, buckets, config, log, stamp=None, notes=None):
        self._tools = tools
        self._menu = menu
        self._stock = stock
        self._buckets = buckets
        self._config = config
        self._log = log
        self._report = Reporter(menu.lines, config, log, notes, stamp)
        self._make_last = False
        self._said_no_make_last = False

    def forget_last(self):
        self._make_last = False

    def _journal_bucket(self):
        for name, phrases in self._buckets:
            for phrase in phrases:
                # clearMatches, or a line already read answers the next wait as well
                if API.InJournalAny([phrase], True):
                    return name

        return None

    def _notice_bucket(self, gump):
        if not gump:
            return None

        text = API.GetGumpContents(gump)

        for name, phrases in self._buckets:
            for phrase in phrases:
                if any_in(text, [phrase.lower()]) or API.GumpContains(phrase, gump):
                    return name

        return None

    # The gump's NOTICES panel is read too because the shard writes refusals there, not the journal
    def _read_outcome(self, opened):
        waited = 0.0

        while not API.StopRequested:
            hit = self._journal_bucket()

            if hit is None:
                hit = self._notice_bucket(opened)

            if hit is not None:
                return hit

            if waited >= self._config["craft_timeout"]:
                return None

            API.Pause(self._config["craft_poll"])
            waited += self._config["craft_poll"]

    def _report_outcome(self, why, gump):
        self._report.say(why, gump, [("pack", "the pack holds %s, and the menu is set to %s here"
                                      % (self._stock.hue_report(), self._config["material"]))])

    # MAKE LAST is the only path that skips the category: a row button is only in the gump once
    # its category is showing
    def _choose_button(self, product, gump):
        known = self._config["recipes"].get(product)

        if known is None:
            return None, "noRow"

        if self._make_last:
            if self._menu.has_button(self._config["make_last_button"], gump):
                return self._config["make_last_button"], None

            self._make_last = False

            if not self._said_no_make_last:
                self._said_no_make_last = True
                self._log("the menu has no MAKE LAST on button %d, pressing the row itself"
                          % self._config["make_last_button"])

        if not self._menu.press(known[0], gump, self._config["gump_timeout"]):
            return None, "noGump"

        return known[1], None

    def craft_once(self, product):
        # Asked apart from the gump, so an empty pack and a menu that will not open read differently
        if self._tools.serial() is None:
            return "noTool"

        gump = self._menu.open()

        if gump is None:
            return "noGump"

        button, outcome = self._choose_button(product, gump)

        if button is None:
            return outcome

        gump = self._menu.current_id() or gump

        API.ClearJournal()

        opened = self._menu.press(button, gump, self._config["craft_timeout"])
        outcome = self._read_outcome(opened)

        if outcome == "made":
            self._make_last = True
            self._report.forget()
        elif outcome == "noMaterial":
            self._report_outcome("refused for materials", opened)
        elif outcome is None:
            self._report_outcome("nothing readable came back", opened)

            if button == self._config["make_last_button"]:
                self._make_last = False
                self._log("MAKE LAST made nothing, pressing the row itself next time")

        return outcome


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


# src/uo/weight.py
# Unknown is not overweight, the same call WeightMax == 0 gets: WeightMax reads 0 before the client
# has been told, against which every weight is overweight - a live mining run ended at 436/453 on it
def over_buffer(buffer):
    me = player()

    if me is None:
        return False

    ceiling = me.WeightMax

    return ceiling > 0 and me.Weight > ceiling - buffer


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


def overweight(buffer):
    def clause():
        me = player()

        if me is None or not over_buffer(buffer):
            return None

        return "overweight at %d/%d" % (me.Weight, me.WeightMax)

    return clause


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


# src/uo/stock.py
class StockBook(object):
    """What in the pack is the craft's material, which type it is, and how much the menu will spend."""

    def __init__(self, config, log):
        self._noun = config["noun"]
        self._kinds = config["kinds"]
        # Longest first: 'copper' would otherwise take 'dull copper'
        self._types = sorted(config["types"], key=lambda name: -len(words_of(name)))
        self._hues = config["hues"]
        self._wanted = config["wanted"]
        self._move_delay = config["move_delay"]
        self._log = log

    def noun(self):
        return self._noun

    def wanted(self):
        return self._wanted

    # For a snapshot key, which has no item left to read a name off
    def is_stock_graphic(self, graphic):
        for _kind, graphics, _words in self._kinds:
            if graphic in graphics:
                return True

        return False

    # Names are empty until the tooltip arrives, so the graphic is tried first across every kind
    def kind_of(self, item):
        if item is None:
            return None

        for kind, graphics, _words in self._kinds:
            if item.Graphic in graphics:
                return kind

        for kind, graphics, words in self._kinds:
            if word_in(item.Name, words):
                graphics.add(item.Graphic)
                self._log("%s '%s' counts as %s, remembering the art"
                          % (hex_of(item.Graphic), item.Name, kind))

                return kind

        return None

    def is_stock(self, item):
        return self.kind_of(item) is not None

    # The name is where the shard writes it; a hue in neither table is not guessed at
    def type_of(self, item):
        words = words_of(item.Name)

        for name in self._types:
            wanted = words_of(name)

            for start in range(len(words) - len(wanted) + 1):
                if words[start:start + len(wanted)] == wanted:
                    return name

        return self._hues.get(hue_of(item))

    def usable(self, item):
        return self.is_stock(item) and self.type_of(item) == self._wanted

    def wrong(self, item):
        return self.is_stock(item) and self.type_of(item) != self._wanted

    def usable_kind(self, item, kind):
        return self.usable(item) and self.kind_of(item) == kind

    # Only what the menu will spend: counting oak let a run sit on a full pack and craft none
    def counts(self, items):
        counts = {}

        for item in items:
            if not self.usable(item):
                continue

            kind = self.kind_of(item)
            counts[kind] = counts.get(kind, 0) + amount_of(item)

        return counts

    # The rest, by type, so a pack that reads as empty says why
    def other_counts(self, items):
        counts = {}

        for item in items:
            if not self.wrong(item):
                continue

            name = self.type_of(item) or "unknown"
            counts[name] = counts.get(name, 0) + amount_of(item)

        return counts

    def other_report(self, counts):
        parts = ["%d %s" % (counts[name], name)
                 for name in sorted(counts, key=lambda name: -counts[name])]

        return ", ".join(parts)

    # In kind order, so it reads the same each time
    def report(self, counts):
        parts = []

        for kind, _graphics, _words in self._kinds:
            if counts.get(kind, 0) > 0:
                parts.append("%d %s" % (counts[kind], kind))

        return ", ".join(parts) if parts else "no %s" % self._noun

    def pack_stock(self):
        return self.counts(pack_contents())

    def pack_other(self):
        return self.other_counts(pack_contents())

    def in_pack(self):
        return total_of(self.pack_stock())

    def pack_report(self):
        text = self.report(self.pack_stock())
        other = self.other_report(self.pack_other())

        return text if not other else "%s (%s set aside)" % (text, other)

    # By hue: oak, ash and yew are all 'boards' by graphic. Missing hue rows come from here.
    def hue_report(self):
        counts = {}

        for item in pack_contents():
            kind = self.kind_of(item)

            if kind is None:
                continue

            key = (kind, hue_of(item), self.type_of(item) or "unknown")
            counts[key] = counts.get(key, 0) + amount_of(item)

        parts = ["%d %s %s hue %s" % (counts[key], key[2], key[0], hex_of(key[1]))
                 for key in sorted(counts, key=lambda pair: -counts[pair])]

        return ", ".join(parts) if parts else "no %s" % self._noun

    def wrong_piles(self):
        return [item for item in pack_contents() if self.wrong(item)]

    # The craft may not reach into a bag inside the pack
    def _nested(self):
        top = set(item.Serial for item in pack_top_level())
        piles = [item for item in pack_contents()
                 if item.Serial not in top and self.usable(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def lift_from_bags(self):
        moved = 0

        for pile in self._nested():
            before = total_of(self.counts(pack_top_level()))

            API.MoveItem(pile.Serial, API.Backpack, amount_of(pile))
            API.Pause(self._move_delay)

            gained = total_of(self.counts(pack_top_level())) - before

            if gained > 0:
                moved += gained

        if moved > 0:
            self._log("brought %d %s up out of the bags in your pack" % (moved, self._noun))

        return moved


def total_of(counts):
    return sum(counts[kind] for kind in counts)


# src/uo/timings.py
"""The constants the scripts agreed on. Every one is in seconds - API.Pause takes seconds."""

THROTTLE_BACKOFF = 1.0
THROTTLE_BACKOFF_MAX = 8.0

STEP_DELAY = 0.3


# src/assembly/index.py
log = make_log("assembly")

if API.HasTarget():
    API.CancelTarget()


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), overweight(WEIGHT_BUFFER)])


parts = StockBook({
    "noun": "assembly parts",
    "kinds": PART_KINDS,
    "types": MADE_KEG_TYPES,
    "hues": {},
    "wanted": None,
    "move_delay": MOVE_DELAY,
}, log)
notes = note_log(NOTES_PATH, log)


def crafter_for(spec):
    tools = CraftTool(spec["tool_noun"], spec["tool_graphics"], spec["tool_name_words"], log)
    others = [other for other in MENUS.values() if other is not spec]
    menu = CraftMenu(tools, {
        "foreign_fragments": [phrase.lower() for other in others for phrase in other["title_text"]],
        "stride": BUTTON_STRIDE,
        "category_type": CATEGORY_BUTTON_TYPE,
        "item_type": ITEM_BUTTON_TYPE,
        "category_names": spec["category_names"],
        "last_ten_label": LAST_TEN_LABEL,
        "title": spec["title"],
        "title_text": spec["title_text"],
        "title_fragments": [phrase.lower() for phrase in spec["title_text"]],
        "tool_noun": spec["tool_noun"],
        "gump_timeout": GUMP_TIMEOUT,
        "gump_poll": GUMP_POLL,
    }, log)

    return tools, Crafter(tools, menu, parts, OUTCOME_TEXT, {
        "recipes": spec["recipes"],
        "make_last_button": MAKE_LAST_BUTTON,
        "gump_timeout": GUMP_TIMEOUT,
        "craft_timeout": CRAFT_TIMEOUT,
        "craft_poll": CRAFT_POLL,
        "max_reports": MAX_UNREADABLE_REPORTS,
        "text_limit": UNREADABLE_TEXT_LIMIT,
        "tail_seconds": JOURNAL_TAIL_SECONDS,
        "tail_lines": JOURNAL_TAIL_LINES,
        "notes_seconds": NOTES_TAIL_SECONDS,
        "material": "assembly parts",
    }, log, log.stamp, notes)


crafters = dict((name, crafter_for(MENUS[name])) for name in MENUS)

answers = StartPrompt(START_PROMPT, log, stop_reason).ask()

# The stop lands at the next Pause, so the lines until then read a prompt that was never answered
picked = answers["assembly"] if answers is not None else ASSEMBLIES[0][0]
wanted = answers["wanted"] if answers is not None else 0

if answers is None:
    API.Stop()

chosen = [row for row in ASSEMBLIES if row[0] == picked][0]
stages = chosen[2]
noun = chosen[1].lower()
plural = noun if wanted == 1 else noun + "s"

for name in set([menu for _row, menu, _needs in stages]):
    if crafters[name][0].serial() is None:
        log("no %s in the pack" % MENUS[name]["tool_noun"])
        API.Stop()

log("making %d %s, %s in the pack" % (wanted, plural, parts.pack_report()))

stop = None
made = 0
fails = 0
unknown = 0
throttled = 0
no_tool = 0
last_row = {}


try:
    while stop is None and made < wanted:
        stop = stop_reason()

        if stop is not None:
            break

        stock = parts.pack_stock()
        product, menu_name, needs = next_stage(stages, stock)
        short = short_of(needs, stock)

        if short:
            stop = ("short of %s for the %s of %s %d of %d - the pack holds %s"
                    % (shortfall_report(short, PART_ORDER), product, noun, made + 1, wanted,
                       parts.pack_report()))
            break

        tools, crafter = crafters[menu_name]

        # MAKE LAST would repeat the menu's previous row
        if last_row.get(menu_name) != product:
            last_row[menu_name] = product
            crafter.forget_last()

        outcome = crafter.craft_once(product)

        if outcome != "throttled":
            throttled = 0

        if outcome not in ("noTool", "noGump"):
            no_tool = 0

        if outcome is not None:
            unknown = 0

        if outcome == "made":
            if product == stages[-1][0]:
                made += 1
                log("%s %d of %d" % (noun, made, wanted))
            else:
                log("made %s" % product)
        elif outcome == "failed":
            fails += 1
        elif outcome == "noMaterial":
            stop = ("the shard refused the parts in the pack for a %s (%s) - read the gump's words "
                    "above" % (product, parts.pack_report()))
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s yet" % product
        elif outcome == "noRow":
            stop = "'%s' is not in MENUS" % product
        elif outcome == "toolWorn":
            crafter.forget_last()
            log("the tool wore out, looking for another")
        elif outcome in ("noTool", "noGump"):
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = ("no %s left" % MENUS[menu_name]["tool_noun"] if outcome == "noTool"
                        else "the %s menu will not open" % menu_name)
                break

            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
        elif outcome == "throttled":
            throttled += 1

            if throttled >= MAX_THROTTLED:
                stop = "%d throttled crafts in a row" % MAX_THROTTLED
                break

            API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
        elif outcome is None:
            unknown += 1

            if unknown >= MAX_UNKNOWN:
                stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
                break

            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        API.Pause(STEP_DELAY)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    if stop is None:
        stop = "threw - %s" % error

log("%d made, %d failed, %s left in the pack" % (made, fails, parts.pack_report()))
log("stopping - %s" % (stop or "done"))
API.Stop()
