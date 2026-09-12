# Built from src/armslore/index.py by build.py - do not edit.

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

UNSKILLED_TEXT = [
    "You are not skilled enough",
    "You lack the required skill",
    "You do not have enough skill",
]


# src/armslore/config.py
# Every success and failure is appended here, one JSON object per line, for legion/skilldb.py to
# turn into a table later. "" turns recording off. A bare name lands in TazUO's working directory
# rather than beside the script - set an absolute path to put it somewhere you will find it.
DATA_PATH = "skill-attempts.jsonl"

# API.Pause takes seconds where the ClassicUO port took ms
DELAY = 0.5

PICK_TIMEOUT = 30.0
TARGET_TIMEOUT = 1.0

# A reading answers within a tick or is not coming; the poll is short because the whole cycle is
READ_TIMEOUT = 1.5
READ_POLL = 0.1

SKILL = "Arms Lore"

# Polled in declaration order, first match wins - and the journal is cleared before every use, so
# what is in it belongs to this reading and nothing older.
#
# Every phrase here is a GUESS. Nothing in this repo has watched Arms Lore on this shard, and the
# stock RunUO wording is a localized message whose English this table is reconstructing. An outcome
# no bucket matches is counted and reported, never recorded - so a wrong table under-reports rather
# than writing something untrue. Watch one run and correct it.
OUTCOME_TEXT = [
    # The refusals are whole sentences, so they are asked first. `read` below is stems, which a
    # longer refusal could contain.
    (
        "missed",
        [
            "You are not certain",
            "You have no idea",
            "You are not sure",
            "You can not tell anything about",
            "You cannot tell anything about",
            "You can't tell anything about",
        ],
    ),
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
    # Stems the whole family of readings shares rather than any one wording: a shard reports the
    # weapon's damage, its durability, its quality or what it is made of, and no two phrase it the
    # same way. Last, because these are the loosest strings in the table.
    (
        "read",
        [
            "damage",
            "durability",
            "quality",
            "appears to be",
            "is made of",
        ],
    ),
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


# src/uo/journal.py
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


# src/uo/clock.py
def now():
    return time.time()


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


# src/armslore/index.py
log = make_log("arms-lore")
skill = SkillReader(SKILL)

# A cursor left open by whatever ran last would swallow this query
if API.HasTarget():
    API.CancelTarget()

log("target the weapon to read, ESC to stop")

weapon = API.RequestTarget(PICK_TIMEOUT)

if not weapon:
    if API.HasTarget():
        API.CancelTarget()

    log("nothing targeted - stopping")
    API.Stop()

item = API.FindItem(weapon)
name = (item.Name if item is not None else None) or hex_of(weapon)

start = skill.read()
recorder = attempt_log(DATA_PATH, skill.name(), log)

if start is None:
    log("the client is not reporting %s - reading '%s' anyway" % (SKILL, name))
else:
    log("reading '%s' - %s at %s/%s" % (name, skill.name(), reading(start), reading(skill.cap())))

reads = 0
missed = 0
unread = 0

while not API.StopRequested:
    value = skill.read()

    # The gain a reading earned lands here rather than at the reading: the client applies it some
    # time after the outcome, so the row waits a cycle for a value worth writing
    recorder.settle(value)

    cap = skill.cap()

    if value is not None and cap is not None and cap > 0 and value >= cap:
        log("%s is capped at %s" % (skill.name(), reading(value)))
        break

    if API.FindItem(weapon) is None:
        log("'%s' is gone - stopping" % name)
        break

    API.ClearJournal()
    API.UseSkill(SKILL)

    # A refused use puts no cursor up, so this times out and the next pass simply asks again
    if API.WaitForTarget("any", TARGET_TIMEOUT):
        API.Target(weapon)

        outcome = read_outcome(OUTCOME_TEXT, READ_TIMEOUT, READ_POLL)

        if outcome == "read":
            reads += 1
            recorder.record(value, outcome, name)

        # The roll happened and the shard said it did not go: that is the half of the data a tally
        # of reads alone cannot show
        elif outcome == "missed":
            missed += 1
            recorder.record(value, outcome, name)

        # Everything else - a refusal, a save, a wording OUTCOME_TEXT has not got - is left out of
        # the record rather than guessed at, and reported at the end so a wrong table is obvious
        else:
            unread += 1

    API.Pause(DELAY)

ended = skill.read()
recorder.settle(ended)

log("%d read, %d missed, %s %s -> %s"
    % (reads, missed, skill.name(), reading(start), reading(ended)))

if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to OUTCOME_TEXT" % unread)

API.Stop()
