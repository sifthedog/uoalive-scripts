# Built from src/hiding/index.py by build.py - do not edit.

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

THROTTLE_BACKOFF = 1.0
THROTTLE_BACKOFF_MAX = 8.0
HEARTBEAT_EVERY = 30.0

GAIN_PATH_TIMEOUT = 5.0
GAIN_PATH_POLL = 0.25


# src/hiding/config.py
# Every success and failure is appended here, one JSON object per line. "" turns recording off.
DATA_PATH = "skill-attempts.jsonl"

SKILL = "Hiding"

READ_TIMEOUT = 1.5
READ_POLL = 0.1

# The whole pause between two attempts. ServUO's Hiding holds the skill timer for 10s after a roll
# and 1s after a refusal, and a refusal costs one cycle and says so.
HIDE_DELAY = 1.0

MAX_THROTTLED = 20

# Polled in declaration order, first match wins. `hidden` and the first `failed` phrase were watched
# on UOAlive; the rest are ServUO guesses. `busy` sits before `failed`, which contains its stem.
OUTCOME_TEXT = [
    (
        "busy",
        [
            "You can't seem to hide right now",
            "You cannot seem to hide right now",
            "You are busy doing something else and cannot hide",
        ],
    ),
    ("failed", ["You fail to hide", "You can't seem to hide here", "You cannot seem to hide here"]),
    ("hidden", ["You have hidden yourself well"]),
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]


# src/hiding/proof.py
# The shard sets the flag on a success and reveals on a failed roll, so a flip is a roll the
# journal did not name
def flag_outcome(hidden_before, hidden_after):
    if not hidden_before and hidden_after:
        return "hidden"

    if hidden_before and not hidden_after:
        return "failed"

    return None


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


# src/uo/loop.py
def backoff_for(count, step, cap):
    return min(step * count, cap)


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


# src/hiding/index.py
log = make_log("hiding")
skill = SkillReader(SKILL)
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "attempts", position_and_weight)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(SKILL)])


def hidden_flag():
    me = player()

    return bool(me.IsHidden) if me is not None else False


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

start = skill.read()
recorder = attempt_log(DATA_PATH, skill.name(), log)

if start is None:
    log("the client is not reporting %s - hiding anyway" % SKILL)
else:
    log("hiding - %s at %s/%s" % (skill.name(), reading(start), reading(skill.cap())))

hidden = 0
failed = 0
busy = 0
unread = 0
throttled = 0
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
            throttled = 0
            continue

        value = skill.read()
        before = hidden_flag()

        API.ClearJournal()
        API.UseSkill(SKILL)
        heartbeat.beat("hiding", cycle, hidden + failed)

        outcome = read_outcome(OUTCOME_TEXT, READ_TIMEOUT, READ_POLL)

        if outcome is None:
            outcome = flag_outcome(before, hidden_flag())

        if outcome != "throttled":
            throttled = 0

        if outcome == "hidden":
            hidden += 1
            recorder.record(value, outcome, SKILL)

        elif outcome == "failed":
            failed += 1
            recorder.record(value, outcome, SKILL)

        # No roll: fighting or casting. Nothing to record
        elif outcome == "busy":
            busy += 1

            if busy == 1:
                log("the shard says you cannot hide right now - trying again each cycle")

        elif outcome == "unskilled":
            stop = "the shard says this character cannot use %s" % SKILL

        elif outcome == "saving":
            saves.wait_out()

        elif outcome == "throttled":
            throttled += 1
            log("shard says wait (%d/%d), backing off" % (throttled, MAX_THROTTLED))
            API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

            if throttled >= MAX_THROTTLED:
                stop = "the shard kept refusing the attempt"

        else:
            unread += 1

        API.Pause(HIDE_DELAY)
finally:
    recorder.close(skill.last())

ended = skill.read()

log("%d hidden, %d failed, %s %s -> %s"
    % (hidden, failed, skill.name(), reading(start), reading(ended)))

if busy > 0:
    log("%d attempt(s) refused for being busy" % busy)

if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to OUTCOME_TEXT" % unread)

if stop is not None:
    log(stop)

API.Stop()
