# Built from src/taming/index.py by build.py - do not edit.

import API
import time


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


def find_mobile(serial):
    found = API.FindMobile(serial)

    return None if found is None or found.IsDestroyed else found


def distance_of(serial):
    found = find_mobile(serial)

    return None if found is None else found.Distance


# src/taming/quarry.py
class Hunt(object):
    """The animals this run is finished with, and the scan that leaves them out."""

    def __init__(self, pet_name, radius, opl_timeout):
        self._pet_name = pet_name
        self._radius = radius
        self._opl_timeout = opl_timeout
        self._skipped = set()

    def leave_out(self, serial):
        self._skipped.add(serial)

    def mine(self, name):
        return self._pet_name != "" and name.lower() == self._pet_name.lower()

    # Names read empty until the client has tooltip data, so the one about to be taken is asked for
    # by tooltip rather than every candidate on every scan
    def named(self, mobile):
        if mobile.Name:
            return mobile.Name

        props = mobile.NameAndProps(True, self._opl_timeout) or ""
        first = props.splitlines()[0].strip() if props else ""

        return first or hex(mobile.Serial)

    def next_quarry(self, graphic):
        if self._radius <= 0:
            return None

        candidates = [
            mobile
            for mobile in API.GetAllMobiles(graphic=graphic, distance=self._radius)
            if not mobile.IsDestroyed
            and mobile.Serial not in self._skipped
            and not mobile.IsDead
            # True for pets and followers, so this is every animal the run has already kept
            and not mobile.IsRenamable
            and not self.mine(mobile.Name or "")
        ]

        for mobile in candidates:
            name = self.named(mobile)

            # Released under the name rather than kept, so nothing but the name says it was yours
            if self.mine(name):
                self.leave_out(mobile.Serial)
                continue

            return (
                {"serial": mobile.Serial, "name": name, "graphic": mobile.Graphic},
                len(candidates),
            )

        return None


def is_pet(serial):
    found = find_mobile(serial)

    return found is not None and found.IsRenamable


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


# src/taming/attempt.py
class Tamer(object):
    def __init__(self, skill, buckets, resolution, start_timeout, resolve_timeout, wait_slice):
        self._skill = skill
        self._buckets = buckets
        self._resolution = resolution
        self._start_timeout = start_timeout
        self._resolve_timeout = resolve_timeout
        self._wait_slice = wait_slice

    def _settle(self, serial, was_pet, between):
        first = read_outcome(self._buckets, self._start_timeout, self._wait_slice, between)

        if first is not None and first != "starting":
            return first

        resolved = read_outcome(self._resolution, self._resolve_timeout, self._wait_slice, between)

        if resolved is not None:
            return resolved

        # Silence is what a shard with other wordings looks like, so the flag is the proof that does
        # not go through the journal - false to true, since one already renamable proves nothing
        if not was_pet and is_pet(serial):
            return "tamed"

        return "pending" if first == "starting" else "unknown"

    def tame_once(self, serial, between):
        if API.HasTarget():
            API.CancelTarget()

        was_pet = is_pet(serial)

        API.ClearJournal()

        # Pre-targeted rather than answered through a cursor of our own: a cursor left unanswered is
        # what leaves the next cycle asking while the shard is still resolving this attempt
        API.PreTarget(serial, "neutral")
        API.UseSkill(self._skill)

        try:
            return self._settle(serial, was_pet, between)
        finally:
            # Or an attempt the shard never answered leaves the pre-target armed for the next cycle
            API.CancelPreTarget()


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

LOG_EVERY = 25
HEARTBEAT_EVERY = 30.0

STALL_WARN = 60
STALL_STOP = 300


# src/taming/config.py
# Every success and failure is appended here, one JSON object per line, for legion/skilldb.py to
# turn into a table later. "" turns recording off. A bare name lands in TazUO's working directory
# rather than beside the script - set an absolute path to put it somewhere you will find it.
DATA_PATH = "skill-attempts.jsonl"

PET_NAME = "sifinha"

# What becomes of the animal once it is yours: 'kill' keeps it and puts it to work, 'release' hands
# the follower slot back, 'keep' does neither.
AFTER_TAME = "kill"

SKILL_NAME = "Animal Taming"

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms.
TAME_START_TIMEOUT = 3.0
TAME_RESOLVE_TIMEOUT = 15.0

# Both waits are taken in slices this long, because the animal walks while the attempt resolves and
# a script sat in one long wait cannot follow it
TAME_WAIT_SLICE = 0.5

TAME_RANGE = 2

# How far the run looks for the next animal of the type you picked. 0 turns the hunt off and asks
# for every animal.
HUNT_RADIUS = 12

CHASE_TIMEOUT = 10

# A floor, not the cadence: the shard's skill timer is not something the client can be asked for, so
# the pace below raises this until the refusals stop.
TAME_DELAY = 1.5
PACE_STEP = 0.4
PACE_MAX = 8.0

# Easing after a single success oscillates between an attempt and a refusal
PACE_EASE_AFTER = 5

ANGRY_DELAY = 10.0

MAX_CYCLES = 5000
MAX_AWAY = 10
MAX_CONTESTED = 20
MAX_ANGRY = 10
MAX_PENDING = 10
MAX_THROTTLED = 20

# A failed tame turns the animal on you, so this run has a health floor
HEALTH_FLOOR = 0.5

SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25

OPL_TIMEOUT = 1

# Waiting on a person rather than on the shard - and unlike the web client's cursor, this one
# has a timeout, which expires into the same "nothing picked" that ESC does
TARGET_TIMEOUT = 60.0


CONTEXT_TIMEOUT = 2.0

KILL_MENU_TEXT = ["Kill", "Attack"]
KILL_CURSOR_TIMEOUT = 2.0

# Long, because this one is waiting on a person rather than on the shard
KILL_PICK_TIMEOUT = 60.0
KILL_PICK_POLL = 0.25

RELEASE_MENU_TEXT = ["Release"]

# The shard asks before it lets a pet go. Which button is 'yes' is not something the client reports,
# so the release is retried with each of these until the animal is actually let go.
RELEASE_CONFIRM_BUTTONS = [1, 2, 0]
RELEASE_CONFIRM_TEXT = ["release this creature", "release this", "Are you sure"]
RELEASE_CONFIRM_TIMEOUT = 3.0
RELEASE_CONFIRM_POLL = 0.15

# Goes each candidate button gets, and separately how many early menus are tolerated: a confirm that
# arrives late loses a press, and a menu asked for too early comes back without the entry
RELEASE_ATTEMPTS = 3

RELEASE_TIMEOUT = 3.0
RELEASE_POLL = 0.25

RENAME_TIMEOUT = 3.0
RENAME_POLL = 0.25
RENAME_ATTEMPTS = 3

# A tame lands in the journal before the shard has finished making the animal yours, and both the
# rename packet and the Release entry are refused until it has
PET_SETTLE_TIMEOUT = 5.0
PET_SETTLE_POLL = 0.25

MENU_RETRY_DELAY = 0.5

# Guesses for a RunUO-family shard, apart from `tamed` and `failed` which are read off this one.
# Ordered, not a dict: the first bucket holding a match wins, which is why `unskilled`, `saving` and
# `throttled` sit last.
OUTCOME_TEXT = [
    ("tamed", ["It seems to accept you as master"]),
    ("failed", ["You fail to tame the creature"]),
    # Not a result: the attempt has been accepted and will answer in a few seconds
    (
        "starting",
        [
            "You start to tame the creature",
            "You continue to tame the creature",
            "You are already taming this creature",
        ],
    ),
    ("angry", ["is too angry to continue taming", "You have been interrupted"]),
    ("contested", ["Someone else is already taming this creature"]),
    ("alreadyTame", ["That animal looks tame already"]),
    ("hopeless", ["You have no chance of taming this creature"]),
    (
        "notAnimal",
        ["That creature cannot be tamed", "You can't tame that", "That wasn't a valid target"],
    ),
    (
        "tooFar",
        [
            "You must be closer to attempt to tame this creature",
            "You are too far away to continue taming",
            "That is too far away",
            "You cannot see that",
        ],
    ),
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]

RESOLUTION_TEXT = [pair for pair in OUTCOME_TEXT if pair[0] != "starting"]

# The outcomes no amount of retrying gets past, and what the run says about each
STOP_REASON = {
    "hopeless": "the shard says this creature cannot be tamed by you",
    "notAnimal": "that is not something Animal Taming works on",
    "alreadyTame": "that animal is already tame",
    "unskilled": "not skilled enough to tame this creature",
}


# src/uo/gump.py
# The answer is the gump id *changing*. WaitForGump with no id resolves to whatever LastGumpID
# already is, so it answers a stale gump when one is open and times out when none is.
def await_changed(before, timeout, poll):
    waited = 0.0

    while waited < timeout:
        found = API.HasGump()

        if found and found != before:
            return found

        API.Pause(poll)
        waited += poll

    return 0


def gump_says(gump, texts):
    for text in texts:
        if API.GumpContains(text, gump):
            return True

    return False


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


# src/uo/retry.py
def settled(timeout, poll, landed):
    waited = 0.0

    while waited < timeout:
        API.Pause(poll)
        waited += poll

        if landed():
            return True

    return False


# src/taming/pet.py
# Rename returns nothing, so the new name is polled for - and reissued, because a rename refused for
# an animal the shard has not finished handing over is silent and looks exactly like a slow one
def rename_pet(serial, name, attempts, timeout, poll):
    def answers_to():
        found = find_mobile(serial)

        return found is not None and (found.Name or "").lower() == name.lower()

    for _ in range(attempts):
        if answers_to():
            return "renamed"

        API.Rename(serial, name)

        if settled(timeout, poll, answers_to):
            return "renamed"

    return "unnamed"


class Release(object):
    def __init__(self, config, log):
        self._config = config
        self._log = log
        self._button = None
        self._said_no_gump = False
        self._said_no_button = False

    def _answer_confirm(self, before, button):
        gump = await_changed(before, self._config["confirm_timeout"], self._config["confirm_poll"])

        if not gump:
            if not self._said_no_gump:
                self._said_no_gump = True
                self._log("found no gump to confirm the release with")

            return

        if not self._said_no_button and not gump_says(gump, self._config["confirm_text"]):
            self._said_no_button = True
            self._log("the release gump says none of RELEASE_CONFIRM_TEXT - answering it anyway")

        API.ReplyGump(button, gump)

    def release(self, serial):
        attempts = self._config["attempts"]
        buttons = list(self._config["buttons"]) if self._button is None else [self._button]
        pressed = False
        missing = 0

        for button in buttons * attempts:
            before = API.HasGump()

            if not context_menu(serial, self._config["menu_text"], self._config["context_timeout"]):
                # Better proof than the flag, and free: the entry is on the menu only while it is
                # your pet, so one that has gone since a press means the press worked
                if pressed:
                    return "released"

                # Before any press it means the menu was asked for early - ContextMenu gives up the
                # moment the shard sends a menu without the entry on it
                missing += 1

                if missing >= attempts:
                    return "noEntry"

                API.Pause(self._config["retry_delay"])
                continue

            pressed = True
            self._answer_confirm(before, button)

            if settled(self._config["timeout"], self._config["poll"], lambda: not is_pet(serial)):
                if self._button is None:
                    self._button = button
                    self._log("the release gump answers to button %d" % button)

                return "released"

        # A confirmation nobody answered is modal on some clients, and would refuse the context menu
        # of every animal after this one
        if API.HasGump():
            API.CloseGump()

        return "stillPet" if pressed else "noEntry"


# The cursor the shard raises is left for the player to answer - nothing here targets anything, so
# what the pet attacks is always a human decision
def command_kill(serial, name, config, log):
    if API.HasTarget():
        API.CancelTarget()

    if not context_menu(serial, config["menu_text"], config["context_timeout"]):
        return "noEntry"

    if not API.WaitForTarget("any", config["cursor_timeout"]):
        return "noCursor"

    log("told '%s' to kill - pick its target" % name)

    picked = settled(config["pick_timeout"], config["pick_poll"], lambda: not API.HasTarget())

    return "ordered" if picked else "unanswered"


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


def no_follower_slots():
    def clause():
        me = player()

        if me is None:
            return None

        slots = me.FollowersMax

        # Keeping the tames fills the slots, and a shard with no room left refuses every attempt
        # without saying why
        if slots > 0 and me.Followers >= slots:
            return "no follower slots left"

        return None

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


# src/uo/pace.py
class Pace(object):
    """The shard's own skill timer, learned from its refusals rather than configured."""

    def __init__(self, floor, step, cap, ease_after):
        self._floor = floor
        self._step = step
        self._max = cap
        self._ease_after = ease_after
        self._delay = floor
        self._landed = 0

    def delay(self):
        return self._delay

    def refused(self):
        self._landed = 0
        self._delay = min(self._delay + self._step, self._max)

        return self._delay

    # Easing after a single success oscillates between an attempt and a refusal
    def landed(self):
        self._landed += 1

        if self._landed < self._ease_after:
            return self._delay

        self._landed = 0
        self._delay = max(self._floor, self._delay - self._step)

        return self._delay


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


# src/uo/travel.py
def chase(serial, within, timeout):
    """'gained' is ground made up on something still walking away, and is worth another cycle."""
    before = distance_of(serial)

    if API.PathfindEntity(serial, within, True, timeout, True):
        return "closed"

    after = distance_of(serial)

    if before is not None and after is not None and after < before:
        return "gained"

    return "stuck"


# Called between the slices of a wait, so a mobile is followed while an attempt resolves
def keep_up(serial, within, timeout):
    found = find_mobile(serial)

    if found is not None and found.Distance > within and not API.Pathfinding():
        API.PathfindEntity(serial, within, False, timeout, True)


# src/uo/vitals.py
def weight_reading():
    me = player()

    return "?/?" if me is None else "%d/%d" % (me.Weight, me.WeightMax)


def where():
    me = player()

    return "somewhere" if me is None else "at %d,%d" % (me.X, me.Y)


def position_and_weight():
    return "%s, %s" % (where(), weight_reading())


# src/taming/index.py
log = make_log("tame")
skill = SkillReader(SKILL_NAME)
pace = Pace(TAME_DELAY, PACE_STEP, PACE_MAX, PACE_EASE_AFTER)
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "attempts", position_and_weight)
stall = StallWatch("cycles without an attempt", STALL_WARN, STALL_STOP, heartbeat, log)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), hurt(HEALTH_FLOOR), no_follower_slots()])


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)
hunt = Hunt(PET_NAME, HUNT_RADIUS, OPL_TIMEOUT)
tamer = Tamer(SKILL_NAME, OUTCOME_TEXT, RESOLUTION_TEXT, TAME_START_TIMEOUT, TAME_RESOLVE_TIMEOUT,
              TAME_WAIT_SLICE)
releases = Release({
    "menu_text": RELEASE_MENU_TEXT,
    "buttons": RELEASE_CONFIRM_BUTTONS,
    "confirm_text": RELEASE_CONFIRM_TEXT,
    "confirm_timeout": RELEASE_CONFIRM_TIMEOUT,
    "confirm_poll": RELEASE_CONFIRM_POLL,
    "attempts": RELEASE_ATTEMPTS,
    "timeout": RELEASE_TIMEOUT,
    "poll": RELEASE_POLL,
    "context_timeout": CONTEXT_TIMEOUT,
    "retry_delay": MENU_RETRY_DELAY,
}, log)

KILL_CONFIG = {
    "menu_text": KILL_MENU_TEXT,
    "context_timeout": CONTEXT_TIMEOUT,
    "cursor_timeout": KILL_CURSOR_TIMEOUT,
    "pick_timeout": KILL_PICK_TIMEOUT,
    "pick_poll": KILL_PICK_POLL,
}

start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)

log("%s at %s" % (SKILL_NAME, reading(start)))

recorder = attempt_log(DATA_PATH, skill.name(), log)

tamed = 0
attempts = 0
last_value = start
failures = 0
reported = 0
stop = None

# Reported at the end so a wrong OUTCOME_TEXT is still obvious, but never a reason to stop
unread = 0
unnamed = 0
unfinished = 0

# Said once per stretch rather than once per cycle, so a real ending does not scroll away
unread_said = False


# Renamed before anything else is done with it: once it is not your pet the Rename packet is refused
def after_tame(serial, name):
    global unnamed, unfinished

    # IsRenamable is true for pets, so this is the shard saying the handover is done
    if not is_pet(serial) and not settled(
        PET_SETTLE_TIMEOUT, PET_SETTLE_POLL, lambda: is_pet(serial)
    ):
        log("'%s' is not showing as yours yet - going ahead anyway" % name)

    called = name

    if PET_NAME:
        if rename_pet(serial, PET_NAME, RENAME_ATTEMPTS, RENAME_TIMEOUT, RENAME_POLL) == "renamed":
            called = PET_NAME
            log("renamed '%s' to '%s'" % (name, PET_NAME))
        else:
            unnamed += 1
            log("could not rename '%s' - carrying on" % name)

    if AFTER_TAME == "kill":
        ordered = command_kill(serial, called, KILL_CONFIG, log)

        if ordered != "ordered":
            unfinished += 1
            log("could not order '%s' to kill (%s) - carrying on" % (called, ordered))

        return

    if AFTER_TAME != "release":
        return

    released = releases.release(serial)

    if released == "released":
        log("released '%s'" % called)
    else:
        unfinished += 1
        log("could not release '%s' (%s) - carrying on" % (called, released))


# The graphic the last hand-picked animal set, and so what the hunt looks for
hunting = None

try:
    while stop is None:
        stop = stop_reason()

        if stop is not None:
            break

        sighted = None if hunting is None else hunt.next_quarry(hunting)
        quarry = sighted[0] if sighted is not None else None
        in_sight = sighted[1] if sighted is not None else 1

        # Asked for only when there is nothing of that type left in sight
        if quarry is None:
            log("target the creature to tame")
            picked = API.RequestTarget(TARGET_TIMEOUT)

            # The only sign the client gives that ESC was pressed. On the first pick there is
            # nothing to show for the run, so it reads as a mistake rather than as closing the
            # session.
            if not picked:
                stop = "%d tamed" % tamed if tamed > 0 else "nothing picked"
                break

            animal = find_mobile(picked)

            # A bad pick puts the cursor back up rather than ending the session
            if animal is None:
                log("%s is not a creature" % hex(picked))
                continue

            hunting = animal.Graphic or None
            quarry = {"serial": picked, "name": hunt.named(animal), "graphic": animal.Graphic}

        name = quarry["name"]
        others = in_sight - 1

        log("taming '%s'%s" % (name, " (%d more in sight)" % others if others > 0 else ""))

        done = None
        accepted = False
        throttled = 0
        away = 0
        contested = 0
        angry = 0
        pending = 0

        for cycle in range(MAX_CYCLES):
            if stop is not None or done is not None:
                break

            stop = stop_reason()

            if stop is not None:
                break

            # Before anything else: during a save every attempt is refused, and each refusal would
            # be charged to a counter that ends the run
            if saves.is_saving():
                saves.wait_out()
                throttled = 0
                stall.progressed()
                stall.end_cycle("saving", cycle, attempts)
                continue

            found = find_mobile(quarry["serial"])

            if found is None:
                done = "'%s' is gone" % name
                break

            if found.Distance > TAME_RANGE:
                # Ground made up is reason enough for another cycle: an animal that keeps walking
                # off is chased for as long as the gap is closing
                if chase(quarry["serial"], TAME_RANGE, CHASE_TIMEOUT) != "stuck":
                    away = 0
                else:
                    away += 1

                    if away >= MAX_AWAY:
                        done = "could not get near '%s'" % name
                        break

                heartbeat.beat("walking", cycle, attempts)
                stall.end_cycle("walking", cycle, attempts)

                # Read here as well as after the switch, or a chase that never lands an attempt is
                # bounded by nothing but MAX_CYCLES
                stop = stop or stall.reason()
                continue

            value = skill.read()

            # The one signal no wording can argue with: if the number moved, the taming is working,
            # whatever the journal looked like from in here
            if value is not None and value != last_value:
                last_value = value
                unread_said = False
                stall.progressed()

            # The attempt blocks for as long as the shard takes to answer, and the animal walks the
            # whole time, so the chase carries on between the slices of that wait
            outcome = tamer.tame_once(
                quarry["serial"], lambda: keep_up(quarry["serial"], TAME_RANGE, CHASE_TIMEOUT))

            if outcome != "throttled":
                throttled = 0

            if outcome != "tooFar":
                away = 0

            if outcome != "contested":
                contested = 0

            if outcome != "angry":
                angry = 0

            if outcome != "pending":
                pending = 0

            if outcome == "tamed":
                attempts += 1
                tamed += 1
                recorder.record(value, outcome, name)
                stall.progressed()
                accepted = True
                done = "'%s' accepted you as master" % name

            # A failed tame still rolled the skill: the ordinary cycle rather than a refusal
            elif outcome == "failed":
                attempts += 1
                failures += 1
                recorder.record(value, outcome, name)
                unread_said = False
                pace.landed()
                stall.progressed()

            # The shard took the attempt and never answered. Raise TAME_RESOLVE_TIMEOUT if this run
            # ends here.
            elif outcome == "pending":
                attempts += 1
                pending += 1

                if pending >= MAX_PENDING:
                    stop = "attempts kept starting and never resolving"

            elif outcome == "angry":
                angry += 1
                log("'%s' is too angry (%d/%d), letting it settle" % (name, angry, MAX_ANGRY))
                API.Pause(ANGRY_DELAY)

                if angry >= MAX_ANGRY:
                    done = "'%s' stayed too angry to tame" % name

            elif outcome == "contested":
                contested += 1
                log("someone else has '%s' (%d/%d)" % (name, contested, MAX_CONTESTED))

                if contested >= MAX_CONTESTED:
                    done = "another tamer has '%s'" % name

            # Walked at rather than waited out, so a creature that bolted mid-attempt is chased
            elif outcome == "tooFar":
                if chase(quarry["serial"], TAME_RANGE, CHASE_TIMEOUT) != "stuck":
                    away = 0
                else:
                    away += 1

                    if away >= MAX_AWAY:
                        done = "could not get near '%s'" % name

            elif outcome == "saving":
                saves.wait_out()
                throttled = 0
                stall.progressed()

            # The shard's own skill timer, which nothing in the API reports. The pace is raised as
            # well as backed off from, or the next cycle walks straight back into it.
            elif outcome == "throttled":
                throttled += 1
                log(
                    "shard says wait (%d/%d), now pacing at %.1fs"
                    % (throttled, MAX_THROTTLED, pace.refused())
                )
                API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

                if throttled >= MAX_THROTTLED:
                    stop = "the shard kept refusing the attempt"

            elif outcome in STOP_REASON:
                done = STOP_REASON[outcome]

            else:
                unread += 1

                if not unread_said:
                    unread_said = True
                    log("outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls")

            if attempts >= reported + LOG_EVERY:
                reported = attempts
                log(
                    "%d attempts, %d failed, %s at %s"
                    % (attempts, failures, SKILL_NAME, reading(value))
                )

            stall.end_cycle(outcome, cycle, attempts)
            stop = stop or stall.reason()
            API.Pause(pace.delay())

        # Only about this animal: a session-ending fault is reported by the closing lines instead
        if done is not None:
            log(done)
        elif stop is None:
            log("hit the %d cycle backstop on '%s'" % (MAX_CYCLES, name))

        # After the line that says it was tamed, and even when the session is stopping: whatever is
        # done with the animal is not worth skipping because the run happens to be ending
        if accepted:
            after_tame(quarry["serial"], name)

        # Every ending, not just the ones that gave up: an animal this run is finished with must not
        # be the one the next scan picks straight back up
        hunt.leave_out(quarry["serial"])
finally:
    recorder.close(skill.read())

reason = stop or "the session ended"

ended = skill.read()

log(
    "%d tamed over %d attempts, %d failed, %s %s -> %s"
    % (tamed, attempts, failures, SKILL_NAME, reading(start), reading(ended))
)

# Said only when there were any, and said last so it reads as the footnote it is
if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to OUTCOME_TEXT" % unread)

if unnamed > 0 or unfinished > 0:
    log(
        "%d rename(s) and %d %s order(s) did not go through - check the menu wordings in config"
        % (unnamed, unfinished, AFTER_TAME)
    )

log("stopping - %s" % reason)
API.Stop()
