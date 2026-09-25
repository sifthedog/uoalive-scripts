# Built from src/skills/index.py by build.py - do not edit.

import API
import time


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


# src/uo/timings.py
"""The constants the scripts agreed on. Every one is in seconds - API.Pause takes seconds."""

SAVE_WAIT = 60.0
SAVE_POLL = 1.0
HEARTBEAT_EVERY = 30.0

GAIN_PATH_TIMEOUT = 5.0
GAIN_PATH_POLL = 0.25


# src/skills/config.py
# Every success and failure is appended here, one JSON object per line, for legion/skilldb.py to
# turn into a table later. "" turns recording off. A bare name lands beside the script.
DATA_PATH = "skill-attempts.jsonl"

# The whole pause between two uses, flat: a throttle is counted and the next use goes out anyway
DELAY = 0.5

PICK_TIMEOUT = 30.0
TARGET_TIMEOUT = 1.0

READ_TIMEOUT = 1.5
READ_POLL = 0.1

SKILL_CHOICE = {
    "text": "Which skill to train?",
    "hue": 996,
    "poll": 0.5,
    "timeout": 60.0,
    "rows": 6,
}

SHARED_OUTCOMES = [
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]

# One row per skill; `skills` is the client's name for it, first one found wins. `targets` asks for one target at the start and answers every cursor with it.
# `flag` proves an unread roll off the hidden flag, `gump` off a gump the use opened (closed after).
# `outcomes` is polled in order, first match wins, and a bucket that is neither the row's success
# nor its failure is counted and said, never recorded. Only Hiding and Arms Lore have been watched
# on UOAlive; every other phrase is a RunUO guess, so a wrong table under-reports rather than lies.
SKILLS = [
    {
        "key": "anatomy", "caption": "Anatomy", "skills": ["Anatomy"],
        "targets": True, "flag": False, "gump": False, "success": "read", "failure": "missed",
        "outcomes": [
            ("missed", ["You can not analyze", "You cannot analyze", "You can't analyze"]),
        ] + SHARED_OUTCOMES + [
            ("read", ["That being is", "looks", "appears to be"]),
        ],
    },
    {
        "key": "animalLore", "caption": "Animal Lore", "skills": ["Animal Lore"],
        "targets": True, "flag": False, "gump": True, "success": "read", "failure": "missed",
        "outcomes": [
            ("missed", ["You can't think of anything you know offhand",
                        "You cannot think of anything you know offhand"]),
            ("refused", ["That's not an animal", "At your skill level, you can only lore"]),
        ] + SHARED_OUTCOMES,
    },
    {
        "key": "armsLore", "caption": "Arms Lore", "skills": ["Arms Lore"],
        "targets": True, "flag": False, "gump": False, "success": "read", "failure": "missed",
        "outcomes": [
            ("missed", ["You are not certain", "You have no idea", "You are not sure",
                        "You can not tell anything about", "You cannot tell anything about",
                        "You can't tell anything about"]),
        ] + SHARED_OUTCOMES + [
            ("read", ["damage", "durability", "quality", "appears to be", "is made of"]),
        ],
    },
    {
        "key": "hiding", "caption": "Hiding", "skills": ["Hiding"],
        "targets": False, "flag": True, "gump": False, "success": "hidden", "failure": "failed",
        # `busy` before `failed`, which contains its stem. Neither hides you: fighting or casting
        "outcomes": [
            ("busy", ["You can't seem to hide right now", "You cannot seem to hide right now",
                      "You are busy doing something else and cannot hide"]),
            ("failed", ["You fail to hide", "You can't seem to hide here",
                        "You cannot seem to hide here"]),
            ("hidden", ["You have hidden yourself well"]),
        ] + SHARED_OUTCOMES,
    },
    {
        "key": "itemId", "caption": "Item ID", "skills": ["Item ID", "Item Identification"],
        "targets": True, "flag": False, "gump": False, "success": "read", "failure": "missed",
        "outcomes": [
            ("missed", ["You are not certain", "You have no idea", "You are not sure"]),
        ] + SHARED_OUTCOMES + [
            ("read", ["You identify", "appears to be", "is made of"]),
        ],
    },
    {
        "key": "tasteId", "caption": "Taste ID", "skills": ["Taste ID", "Taste Identification"],
        "targets": True, "flag": False, "gump": False, "success": "read", "failure": "missed",
        "outcomes": [
            ("missed", ["You cannot discern anything", "You can't discern anything",
                        "You are not sure"]),
        ] + SHARED_OUTCOMES + [
            ("read", ["is not poisoned", "It is a", "tastes like"]),
        ],
    },
    {
        "key": "begging", "caption": "Begging", "skills": ["Begging"],
        "targets": True, "flag": False, "gump": False, "success": "given", "failure": "refused",
        "outcomes": [
            ("refused", ["no gold for thee", "Thou dost not look trustworthy"]),
            ("broke", ["I have not enough money"]),
            ("tooFar", ["Thou art too far", "too far away"]),
            ("given", ["I feel sorry for thee", "Thou dost look hungry", "worthy fellow"]),
        ] + SHARED_OUTCOMES,
    },
]


# src/skills/proof.py
# The shard sets the flag on a success and reveals on a failed roll, so a flip is a roll the
# journal did not name
def flag_outcome(hidden_before, hidden_after):
    if not hidden_before and hidden_after:
        return "hidden"

    if hidden_before and not hidden_after:
        return "failed"

    return None


# Only a success opens the lore gump, so a gump that was not up before the use is one
def gump_outcome(gump_before, gump_after):
    return "read" if gump_after and gump_after != gump_before else None


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


# src/uo/choice.py
CHOICE_WIDTH = 340
CHOICE_BUTTON_WIDTH = 96
CHOICE_BUTTON_HEIGHT = 26
CHOICE_GAP = 8
CHOICE_SCROLLBAR = 16


class Choice(object):
    """A gump the script draws with one button per option, answered by the first press."""

    def __init__(self, config, log, stop_reason):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason

    # Stacked in a scroll area when `rows` says how many show at once, otherwise side by side
    def _show(self, options, on_press):
        rows = self._config.get("rows")
        step = CHOICE_BUTTON_HEIGHT + CHOICE_GAP

        if rows:
            width = CHOICE_WIDTH
            height = 16 + 20 + 16 + min(rows, len(options)) * step + 16
        else:
            width = max(CHOICE_WIDTH, 16 + len(options) * (CHOICE_BUTTON_WIDTH + CHOICE_GAP) + 8)
            height = 16 + 20 + 16 + CHOICE_BUTTON_HEIGHT + 16

        gump = API.Gumps.CreateGump(True, True)

        if gump is None:
            return None

        gump.SetRect(0, 0, width, height)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.85, "#1E1E1E")
        background.SetRect(0, 0, width, height)
        gump.Add(background)

        label = API.Gumps.CreateGumpLabel(self._config["text"], self._config["hue"])
        label.SetPos(16, 16)
        gump.Add(label)

        if rows:
            area = API.Gumps.CreateGumpScrollArea(16, 16 + 20 + 16, width - 32,
                                                  min(rows, len(options)) * step)
            gump.Add(area)

        for index in range(len(options)):
            key, caption = options[index]

            if rows:
                button = API.Gumps.CreateSimpleButton(caption, width - 32 - CHOICE_SCROLLBAR,
                                                      CHOICE_BUTTON_HEIGHT)
                button.SetPos(0, index * step)
                area.Add(button)
            else:
                button = API.Gumps.CreateSimpleButton(caption, CHOICE_BUTTON_WIDTH,
                                                      CHOICE_BUTTON_HEIGHT)
                button.SetPos(16 + index * (CHOICE_BUTTON_WIDTH + CHOICE_GAP),
                              height - CHOICE_BUTTON_HEIGHT - 16)
                gump.Add(button)

            API.Gumps.AddControlOnClick(button, self._presser(key, on_press))

        API.Gumps.AddGump(gump)

        return gump

    # A closure per button rather than one in the loop: the loop variable would be the last key
    def _presser(self, key, on_press):
        def press():
            on_press(key)

        return press

    # The pressed key, or None when the gump was closed, timed out, or the run has a reason to stop
    def ask(self, options):
        if API.HasTarget():
            API.CancelTarget()

        chosen = [None]

        def on_press(key):
            chosen[0] = key

        gump = self._show(options, on_press)

        # API.Stop() only lands at the next Pause, and every client call before it answers nothing
        if gump is None:
            self._log("not asking - the run is being stopped")
            return None

        self._log("asking - %s" % self._config["text"])

        def resolve():
            return "'%s' was pressed" % dict(options)[chosen[0]] if chosen[0] is not None else None

        why = wait_for_gump(gump, self._stop_reason, self._config["poll"], resolve,
                            timeout=self._config["timeout"])

        self._log(why)

        return chosen[0]


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


# src/uo/text.py
def words_of(text):
    letters = []

    for char in (text or "").lower():
        letters.append(char if char.isalnum() else " ")

    return "".join(letters).split()


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


# src/uo/vitals.py
def weight_reading():
    me = player()

    return "?/?" if me is None else "%d/%d" % (me.Weight, me.WeightMax)


def where():
    me = player()

    return "somewhere" if me is None else "at %d,%d" % (me.X, me.Y)


def position_and_weight():
    return "%s, %s" % (where(), weight_reading())


# src/skills/index.py
log = make_log("skills")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "attempts", position_and_weight)


def picking_reason():
    return first_reason([stopped(STOPPED), dead()])


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(skill_name)])


def hidden_flag():
    me = player()

    return bool(me.IsHidden) if me is not None else False


def caption_of(option):
    return option[1]


def target_gone(serial):
    return API.FindItem(serial) is None and API.FindMobile(serial) is None


def target_name(serial):
    found = API.FindItem(serial) or API.FindMobile(serial)

    return (found.Name if found is not None else None) or hex_of(serial)


chosen = Choice(SKILL_CHOICE, log, picking_reason).ask(
    sorted([(row["key"], row["caption"]) for row in SKILLS], key=caption_of))

if chosen is None:
    log("nothing chosen - stopping")
    API.Stop()

row = [row for row in SKILLS if row["key"] == chosen][0]
skill_name = find_skill_name(row["skills"]) or row["skills"][0]
skill = SkillReader(skill_name)
saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)
target = None
used = skill_name

if row["targets"]:
    log("target what to use %s on, ESC to stop" % row["caption"])
    target = request_one(PICK_TIMEOUT)

    if target is None:
        log("nothing targeted - stopping")
        API.Stop()

    used = target_name(target)

start = skill.read()
recorder = attempt_log(DATA_PATH, skill.name(), log)

if start is None:
    log("the client is not reporting %s - using it on '%s' anyway" % (skill_name, used))
else:
    log("using %s on '%s' - at %s/%s" % (skill.name(), used, reading(start), reading(skill.cap())))

succeeded = 0
failed = 0
others = {}
unread = 0
cycle = 0
stop = None

try:
    while stop is None:
        cycle += 1
        stop = stop_reason()

        if stop is not None:
            break

        if saves.is_saving():
            saves.wait_out()
            continue

        if target is not None and target_gone(target):
            stop = "'%s' is gone" % used
            break

        value = skill.read()
        hidden_before = hidden_flag() if row["flag"] else False
        gump_before = API.HasGump() if row["gump"] else 0

        API.ClearJournal()
        API.UseSkill(skill_name)
        heartbeat.beat("using", cycle, succeeded + failed)

        # A refused use puts no cursor up, so this times out and the next pass simply asks again
        answered = True

        if target is not None:
            answered = bool(API.WaitForTarget("any", TARGET_TIMEOUT))

            if answered:
                API.Target(target)

        if answered:
            outcome = read_outcome(row["outcomes"], READ_TIMEOUT, READ_POLL)

            if outcome is None and row["flag"]:
                outcome = flag_outcome(hidden_before, hidden_flag())

            if row["gump"]:
                gump_after = API.HasGump()

                if outcome is None:
                    outcome = gump_outcome(gump_before, gump_after)

                if gump_after:
                    API.CloseGump(gump_after)

            if outcome == row["success"]:
                succeeded += 1
                recorder.record(value, outcome, used)

            elif outcome == row["failure"]:
                failed += 1
                recorder.record(value, outcome, used)

            elif outcome == "unskilled":
                stop = "the shard says this character cannot use %s" % skill_name

            elif outcome == "saving":
                saves.wait_out()

            elif outcome is None:
                unread += 1

            else:
                others[outcome] = others.get(outcome, 0) + 1

                if others[outcome] == 1:
                    log("the shard answered '%s' - not a roll, using again in %.1fs" % (outcome, DELAY))

        API.Pause(DELAY)
finally:
    recorder.close(skill.last())

ended = skill.read()

log("%d %s, %d %s, %s %s -> %s" % (succeeded, row["success"], failed, row["failure"],
                                    skill.name(), reading(start), reading(ended)))

for name in sorted(others):
    log("%d attempt(s) answered '%s' and were not recorded" % (others[name], name))

if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to SKILLS" % unread)

if stop is not None:
    log(stop)

API.Stop()
