# Built from src/buffs/index.py by build.py - do not edit.

import API
import time


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


# src/buffs/cast.py
def cast_once(entry, standing, buckets, timeout, wait_slice):
    up_before = standing(entry)

    # Re-issuing a buff that is already standing is the one thing this script exists not to do
    if up_before:
        return "alreadyUp"

    mana_before = API.Player.Mana

    # Cancelled only when there is one to cancel: an unconditional cancel just before an action left
    # the next cursor unusable in the run this was copied from
    if API.HasTarget():
        API.CancelTarget()

    API.ClearJournal()
    API.CastSpell(entry["spell"])

    hit = read_outcome(buckets, timeout, wait_slice)

    if hit is not None:
        return hit

    # The proofs that do not go through the journal. A transition, not a state: one already standing
    # proves nothing, which is why up_before was read first.
    if standing(entry):
        return "cast"

    if API.Player.Mana < mana_before:
        return "cast"

    return None


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


# src/buffs/config.py
# Cast in this order within a pass. `buff` is a BuffIconType member name, matched against
# str(buff.Type); `title` is the localized fallback. `mana` is a ceiling - the shard charges a
# paladin less as Chivalry rises - and the client's own Chivalry table says 10 for both.
KEEP = [
    {
        "spell": "Consecrate Weapon",
        "buff": "ConsecrateWeapon",
        "title": "Consecrate Weapon",
        "mana": 10,
        "tithing": 10,
        "needs_weapon": True,
    },
    {
        "spell": "Divine Fury",
        "buff": "DivineFury",
        "title": "Divine Fury",
        "mana": 15,
        "tithing": 10,
    },
]

# Off is a keeper that puts the buffs up and stops. On it keeps them up until you stop the script.
KEEP_UP = True

# Between passes. The buff bar is fed by server packets, so this is how stale the run's picture of
# it can be, and roughly how long a lapsed buff stays down.
POLL = 1.0

# Long enough for the buff packet to land after the incantation, which is what a shard that words
# these differently is read by
CAST_TIMEOUT = 1.0
CAST_WAIT_SLICE = 0.2

# Between two casts inside one pass, to stay under the action throttle
CAST_DELAY = 0.6

# Consecutive casts the shard said nothing readable about, and that put no buff up and spent no
# mana, before the entry is set aside
MAX_MISSES = 5

# How long an entry refused for something a pass cannot fix is left alone before it is tried again
SET_ASIDE = 60.0

# Runs for a day at POLL. A keeper standing over a character with both buffs up is working, so
# nothing here counts cycles against it.
MAX_CYCLES = 100000

MAX_THROTTLED = 20

# Guesses, apart from the tithing wording. Ordered, not a dict: the first bucket holding a match
# wins, which is why alreadyCasting sits before throttled - THROTTLED_TEXT ends in a bare
# 'You must wait' that the longer sentence contains.
OUTCOME_TEXT = [
    # Not depended on: the buff arriving and the mana leaving the pool are the proof
    ("cast", ["Your weapon is consecrated", "You are filled with divine fury"]),
    ("fizzled", ["You fail to cast the spell", "The spell fizzles"]),
    (
        "noTithing",
        [
            "You do not have enough tithing points",
            "You must have at least",
            "You need to make an offering",
        ],
    ),
    ("noMana", ["You do not have enough mana", "Insufficient mana"]),
    ("alreadyUp", ["You are already under the effect"]),
    (
        "noWeapon",
        [
            "You cannot consecrate your fists",
            "You must have a weapon",
            "You must be wielding a weapon",
        ],
    ),
    ("unskilled", ["You are not pious enough", "Your karma is not high enough"] + UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("alreadyCasting", ["You are already casting a spell", "You are already casting"]),
    ("throttled", THROTTLED_TEXT),
]


# src/uo/clock.py
def now():
    return time.time()


# src/buffs/schedule.py
def make_table(keep):
    return [{"entry": entry, "name": entry["spell"], "misses": 0, "until": 0.0, "retired": None}
            for entry in keep]


def due(item):
    return item["retired"] is None and now() >= item["until"]


def set_aside(item, for_seconds):
    item["misses"] = 0
    item["until"] = now() + for_seconds


def retire(item, why):
    item["retired"] = why


# The run has nothing left to do: every entry refused for a reason no later pass can change
def spent(table):
    return all(item["retired"] is not None for item in table)


# What a KEEP_UP=False run waits for. A retired entry counts as settled or it would never finish.
def settled(table, standing):
    return all(item["retired"] is not None or standing(item["entry"]) for item in table)


# src/uo/buffbar.py
class BuffBar(object):
    """ApiBuff never refreshes after it is handed over, so the bar is re-read every time it matters."""

    def __init__(self, log):
        self._log = log
        self._dumped = False

    def active(self):
        buffs = API.ActiveBuffs()

        if not buffs:
            return []

        if not self._dumped:
            self._dumped = True
            self._log("buff bar: " + ", ".join("%s/%s" % (b.Type, b.Title or "") for b in buffs))

        return buffs

    # title is the localized fallback for a shard whose BuffIconType member name does not match
    def standing(self, kind, title=None):
        if not kind:
            return False

        for buff in self.active():
            if str(buff.Type) == kind:
                return True

            if title and title.lower() in (buff.Title or "").lower():
                return True

        return False


# src/uo/gear.py
# Either hand: a katana is one-handed and a no-dachi two-handed, and meditation is refused while
# anything at all is held
def in_hand():
    return API.FindLayer("onehanded") or API.FindLayer("twohanded")


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
    def log(message):
        API.SysMsg(prefix + ": " + message)

    return log


# src/uo/loop.py
def backoff_for(count, step, cap):
    return min(step * count, cap)


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


# src/uo/vitals.py
def mana_reading():
    me = player()

    return "?/?" if me is None else "%d/%d mana" % (me.Mana, me.ManaMax)


def where():
    me = player()

    return "somewhere" if me is None else "at %d,%d" % (me.X, me.Y)


def position_and_mana():
    return "%s, %s" % (where(), mana_reading())


# src/buffs/index.py
log = make_log("buffs")
bar = BuffBar(log)


def standing(entry):
    return bar.standing(entry["buff"], entry["title"])


def armed():
    return in_hand() is not None
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "casts", position_and_mana)


def stop_reason():
    return first_reason([stopped(STOPPED), dead()])


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

table = make_table(KEEP)

casts = 0
reported = 0
throttled = 0
stop = None

# Said once per stretch rather than once per pass, or an unarmed character scrolls the journal at
# POLL for as long as they stay unarmed
said_unarmed = False
said_short = False
said_untithed = False

proved = set()


# The first cast of each spell, so a wrong OUTCOME_TEXT or a wrong buff id shows up in the first
# minute rather than as a run that quietly never casts
def say_first(item):
    if item["name"] in proved:
        return

    proved.add(item["name"])
    log("%s up" % item["name"])


def back_off():
    global throttled, stop

    throttled += 1

    if throttled >= MAX_THROTTLED:
        stop = "the shard refused %d casts in a row" % MAX_THROTTLED
        return

    API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))


def put_up(item):
    global casts, throttled

    outcome = cast_once(item["entry"], standing, OUTCOME_TEXT, CAST_TIMEOUT, CAST_WAIT_SLICE)

    if outcome == "cast":
        casts += 1
        throttled = 0
        item["misses"] = 0
        say_first(item)

    # The shard answered, so the table is right and the roll simply lost. Next pass tries again.
    elif outcome in ("fizzled", "alreadyUp"):
        throttled = 0
        item["misses"] = 0

    # The gate above cleared, so this entry's mana figure is understated for this shard
    elif outcome == "noMana":
        item["misses"] = 0
        log(
            "%s costs more than %d mana here - raise it in KEEP"
            % (item["name"], item["entry"]["mana"])
        )

    # Nothing a script does refills tithing points, so this entry is finished for the run
    elif outcome == "noTithing":
        retire(item, "out of tithing points - tithe gold at a shrine")

    elif outcome == "unskilled":
        retire(item, "the shard refuses it at this skill or karma")

    # The hand check above missed it, so believe the shard rather than the client's layers
    elif outcome == "noWeapon":
        set_aside(item, SET_ASIDE)

    elif outcome == "saving":
        saves.wait_out()

    elif outcome in ("cooldown", "throttled", "alreadyCasting"):
        back_off()

    # Nothing said, no buff, and no mana left the pool: whatever this was, it did not happen
    else:
        item["misses"] += 1

        if item["misses"] >= MAX_MISSES:
            set_aside(item, SET_ASIDE)
            log(
                "%s did nothing %d times - set aside; check OUTCOME_TEXT"
                % (item["name"], MAX_MISSES)
            )


def one_pass():
    global said_unarmed, said_short, said_untithed

    hands = armed()

    if hands:
        said_unarmed = False

    for item in table:
        if stop is not None or not due(item):
            continue

        if standing(item["entry"]):
            item["misses"] = 0
            continue

        entry = item["entry"]

        if entry.get("needs_weapon") and not hands:
            if not said_unarmed:
                said_unarmed = True
                log("nothing in hand - %s is waiting for you to draw something" % item["name"])

            continue

        if API.Player.Mana < entry["mana"]:
            if not said_short:
                said_short = True
                log(
                    "%d/%d mana for %s - waiting for it"
                    % (API.Player.Mana, entry["mana"], item["name"])
                )

            continue

        said_short = False

        # Not in the ClassicUO run, which had no tithing gate: a noTithing retires the entry for the
        # whole run, so a character who forgot to tithe would lose every buff on the first pass
        if API.Player.TithingPoints < entry["tithing"]:
            if not said_untithed:
                said_untithed = True
                log(
                    "%d/%d tithing points for %s - tithe gold at a shrine"
                    % (API.Player.TithingPoints, entry["tithing"], item["name"])
                )

            continue

        said_untithed = False

        put_up(item)
        API.Pause(CAST_DELAY)


log("keeping %s up" % " and ".join(item["name"] for item in table))

if not armed() and any(item["entry"].get("needs_weapon") for item in table):
    log("nothing in hand - the weapon enchants will be refused until you draw something")

log("%d tithing points; every cast spends some, tithe gold at a shrine" % API.Player.TithingPoints)

for cycle in range(MAX_CYCLES):
    if stop is not None:
        break

    stop = stop_reason()

    if stop is not None:
        break

    if saves.is_saving():
        saves.wait_out()
        continue

    one_pass()

    if stop is not None:
        break

    if spent(table):
        stop = "every buff was refused for good"
        break

    if not KEEP_UP and settled(table, standing):
        stop = "everything that could go up is up"
        break

    if casts >= reported + LOG_EVERY:
        reported = casts
        log("%d casts, %d/%d mana" % (casts, API.Player.Mana, API.Player.ManaMax))

    heartbeat.beat("watching the buff bar", cycle, casts)
    API.Pause(POLL)

for item in table:
    if item["retired"] is not None:
        log("%s was set aside - %s" % (item["name"], item["retired"]))

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES

log("%d casts, stopping - %s" % (casts, reason))
API.Stop()
