# Built from src/chivalry/index.py by build.py - do not edit.

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

LOG_EVERY = 25
HEARTBEAT_EVERY = 30.0

STEP_DELAY = 0.3


# src/chivalry/config.py
# Every success and failure is appended here, one JSON object per line, for legion/skilldb.py to
# turn into a table later. "" turns recording off. A bare name lands in TazUO's working directory
# rather than beside the script - set an absolute path to put it somewhere you will find it.
DATA_PATH = "skill-attempts.jsonl"

# up_to is the skill value the row trains to, exclusive. `buff` is a BuffIconType member name matched
# against str(buff.Type); `title` is the localized fallback. `mana` is a ceiling - the shard charges
# less as Chivalry rises. `tithing` is the other currency, gated before the cast because nothing a
# script does refills it. No row raises a cursor. The shard's own minimums are Consecrate Weapon 15,
# Divine Fury 25, Enemy of One 45, Holy Light 55, Noble Sacrifice 65, and every band opens above its own.
STAGES = [
    # Enchants what is in hand, so the run stows and redraws the weapon around every trance
    {
        "up_to": 45.0,
        "spell": "Consecrate Weapon",
        "buff": "ConsecrateWeapon",
        "title": "Consecrate Weapon",
        "mana": 10,
        "tithing": 10,
        "needs_weapon": True,
        "cast_timeout": 2.0,
        "cast_delay": 0.5,
    },
    {
        "up_to": 60.0,
        "spell": "Divine Fury",
        "buff": "DivineFury",
        "title": "Divine Fury",
        "mana": 15,
        "tithing": 10,
        "cast_timeout": 2.0,
        "cast_delay": 0.5,
    },
    # A toggle: cast while standing it comes off, which is still a cast the shard charged for
    {
        "up_to": 70.0,
        "spell": "Enemy of One",
        "buff": "EnemyOfOne",
        "title": "Enemy of One",
        "mana": 20,
        "tithing": 10,
        "cast_timeout": 2.0,
        "cast_delay": 0.5,
    },
    # An area attack on everything non-blue nearby, and the client publishes no buff for it
    {
        "up_to": 90.0,
        "spell": "Holy Light",
        "mana": 10,
        "tithing": 10,
        "cast_timeout": 2.0,
        "cast_delay": 0.5,
    },
    # Where it finds anything to heal it sets the caster's hits, mana and stamina to 1
    {
        "up_to": 120.0,
        "spell": "Noble Sacrifice",
        "mana": 20,
        "tithing": 30,
        "cast_timeout": 2.0,
        "cast_delay": 0.5,
    },
]

SKILL = "Chivalry"
MEDITATION = "Meditation"

# The BuffIconType the client publishes while a trance is running
MEDITATION_BUFF = "ActiveMeditation"

# Under it the first band is mostly fizzles, and a trainer sells the skill faster
FIRST_BAND = 40.0

# The layers a trance wants empty. A shield sits on onehanded too.
HAND_LAYERS = ["onehanded", "twohanded"]

EQUIP_ATTEMPTS = 3
EQUIP_TIMEOUT = 2.0
EQUIP_POLL = 0.2

# Fraction of max hits under which the run bandages itself, and stops if that cannot get it back
HURT_FLOOR = 0.5

# Off is a run that simply stops when it is hurt
BANDAGE = True

# Clean bandages; the bloodied ones are a different item
BANDAGE_GRAPHIC = 0x0E21

BANDAGE_ATTEMPTS = 4
BANDAGE_TIMEOUT = 8.0
BANDAGE_CURSOR_TIMEOUT = 1.0

SKILL_TIMEOUT = 1.0
SKILL_POLL = 0.5

# Consecutive cycles the client answered nothing for the skill before the run gives up
MAX_BLIND_READS = 5

# The fallback for a row that names neither, and every row in STAGES names both
CAST_TIMEOUT = 2.0
CAST_DELAY = 0.5

CAST_WAIT_SLICE = 0.2

# How long the cursor is given to go down once it has been answered, which is what says whether the
# shard took that answer
SELF_TARGET_TIMEOUT = 1.0
SELF_TARGET_POLL = 0.1

# Fallbacks for a cursor the pre-target did not take, tried in this order until one brings it down
SELF_ANSWERS = ["Target(player)", "TargetSelf", "Target(serial)"]

# The mana leaves the pool a beat after the incantation ends, so IsCasting falling is not the end of
# the read - it was measured landing 0.2s behind the flag
PROOF_GRACE = 0.6

# What a cast issued before the last one finished costs. Flat, and never counted towards a stop.
CASTING_WAIT = 0.5

BUFF_WAIT = 2.0

# Gating on the buff would cap the run at one cast per buff duration
SKIP_WHEN_BUFFED = False

# Enemy of One coming off was still a cast the shard charged for and rolled the skill on
DISABLED_IS_PROGRESS = True

# Off waits for natural regeneration instead: slower, always available
MEDITATE = True

# Every trance costs a stow and a draw, so a pool topped right up pays for several casts
MEDITATE_TO_FULL = True

MEDITATE_TIMEOUT = 20.0
MEDITATE_ATTEMPTS = 4
MEDITATE_START_TIMEOUT = 2.0

MANA_POLL = 0.5
MANA_LOG_EVERY = 10.0

REGEN_TIMEOUT = 120.0

# Cycles that produced neither a readable cast nor any movement in the skill before the run gives
# up. A dry mana stretch is charged what it cost in cycles, so this ceiling covers that case too.
MAX_STALE = 500

MAX_CYCLES = 5000

MAX_THROTTLED = 20

# Guesses apart from the tithing and recovery wordings, which are UOAlive's own. Ordered, not a
# dict: the first bucket holding a match wins, which is why alreadyCasting sits before throttled -
# THROTTLED_TEXT ends in a bare 'You must wait' that the longer sentence contains.
OUTCOME_TEXT = [
    # Not depended on: the buff arriving and the mana leaving the pool are the proof
    (
        "cast",
        ["Your weapon is consecrated", "You are filled with divine fury", "You are now"],
    ),
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
    ("disabled", ["You are no longer", "You lose your focus"]),
    # Karma refusals mean the same thing as unskilled: this character cannot cast it, so stop
    (
        "unskilled",
        ["You are not pious enough", "Your karma is not high enough", "You must have proper karma"]
        + UNSKILLED_TEXT,
    ),
    ("saving", SAVING_TEXT),
    (
        "alreadyCasting",
        [
            "You have not yet recovered from casting a spell",
            "You are already casting a spell",
            "You are already casting",
        ],
    ),
    ("throttled", THROTTLED_TEXT),
]

# trance is the only wording here that is not a guess: it is the client's own documented example.
MEDITATE_OUTCOME_TEXT = [
    ("trance", ["You enter a meditative trance."]),
    ("full", ["You are at peace"]),
    # Before unfocused, whose trailing full stop is deliberate: without it 'You cannot focus your
    # concentration' would also match the equipped-weapon sentence.
    (
        "blocked",
        [
            "You cannot focus your concentration with an equipped weapon",
            "You cannot focus your concentration with an equipped shield",
            "You are preoccupied with thoughts of battle",
        ],
    ),
    ("unfocused", ["You cannot focus your concentration.", "You lose your concentration"]),
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("throttled", ["You must wait a few moments to use another skill"] + THROTTLED_TEXT),
]

# Guesses. A heal is proved by the hits going up, so these only explain the failures.
HEAL_OUTCOME_TEXT = [
    ("healed", ["You finish applying the bandages", "You heal", "You apply the bandages"]),
    (
        "noBandages",
        ["You do not have a bandage", "You must have bandages", "You do not have any bandages"],
    ),
    ("busy", ["You are already applying bandages"]),
    ("interrupted", ["You have been interrupted"]),
    ("saving", SAVING_TEXT),
    ("throttled", THROTTLED_TEXT),
]


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


# src/uo/cast.py
class Caster(object):
    def __init__(self, buckets, standing, self_target, skip_when_buffed, fallback_timeout,
                 fallback_delay, wait_slice, proof_grace, log):
        self._buckets = buckets
        self._standing = standing
        self._self_target = self_target
        self._skip_when_buffed = skip_when_buffed
        self._fallback_timeout = fallback_timeout
        self._fallback_delay = fallback_delay
        self._wait_slice = wait_slice
        self._proof_grace = proof_grace
        self._log = log

    # The wording wins over the two silent proofs, so it is read first on every slice: a fizzle that
    # somehow spent mana still reads as a fizzle. Giving up early once IsCasting has gone up and come
    # back down saves the rest of the budget; a shard that publishes no flag spends all of it.
    def _read_outcome(self, stage, up_before, mana_before):
        budget = stage.get("cast_timeout", self._fallback_timeout)
        wants_self = stage.get("target") == "self"
        waited = 0.0
        started = False
        ended = None
        answered = False

        while not API.StopRequested:
            hit = matched_bucket(self._buckets)

            if hit is not None:
                return hit

            # Answered here rather than in a blocking wait before the poll: the pre-target usually
            # takes the cursor before the script sees one at all, and that wait was spent on every
            # cast
            if wants_self and not answered and API.HasTarget():
                answered = self._self_target.answer()

            # A transition, not a state: a buff already standing proves nothing, which is why
            # up_before is read before the cast
            if not up_before and self._standing(stage):
                return "cast"

            if API.Player.Mana < mana_before:
                return "cast"

            if API.Player.IsCasting:
                started = True

            elif started:
                if ended is None:
                    ended = waited

                # Not while a self row still has a cursor to answer: the shard raises it as the
                # incantation ends, so leaving on the flag falling walks out just before it appears
                elif waited - ended >= self._proof_grace and (answered or not wants_self):
                    return None

            if waited >= budget:
                return None

            API.Pause(self._wait_slice)
            waited += self._wait_slice

    def cast_once(self, stage):
        up_before = self._standing(stage)

        if self._skip_when_buffed and up_before:
            return "alreadyUp"

        mana_before = API.Player.Mana

        # Cancelled only when there is one to cancel: an unconditional cancel just before an action
        # left the next cursor unusable in the run this was copied from
        if API.HasTarget():
            API.CancelTarget()

        API.ClearJournal()

        wants_self = stage.get("target") == "self"

        # Queued before the cast, the order the client's own CastSpell example uses. The type has to
        # be the one the shard raises - a pre-target set to the wrong one does not fire at all, and
        # leaves the cursor standing with the cast unspent - so an area spell names its own.
        if wants_self:
            try:
                API.PreTarget(API.Player.Serial, stage.get("target_kind", "beneficial"))
            except Exception as error:
                self._log("PreTarget threw - %s" % error)

        API.CastSpell(stage["spell"])

        outcome = self._read_outcome(stage, up_before, mana_before)

        # Or a queued target the cast never used is still armed for whatever the next one raises
        if wants_self:
            API.CancelPreTarget()

        return outcome

    # The row's floor and nothing else. Waiting out IsRecovering as well made a Bless cycle several
    # seconds of standing still, and it buys nothing the shard does not already say: a cast issued
    # too early is refused in words, and that refusal costs one flat CASTING_WAIT.
    def pace(self, stage):
        API.Pause(stage.get("cast_delay", self._fallback_delay))


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


# src/uo/hands.py
def describe_item(item):
    if item is None:
        return "nothing"

    return "%s ('%s')" % (hex_of(item.Serial), item.Name or "unnamed")


class Hands(object):
    """What the hands held at start-up, put in the pack for a trance and drawn again by serial."""

    def __init__(self, layers, attempts, timeout, poll, log):
        self._layers = layers
        self._attempts = attempts
        self._timeout = timeout
        self._poll = poll
        self._log = log
        self._held = []

    def remember(self):
        self._held = []
        items = []

        for layer in self._layers:
            item = API.FindLayer(layer)

            if item is not None:
                self._held.append((item.Serial, layer))
                items.append(item)

        return items

    def remembered(self):
        return len(self._held) > 0

    def _on_layer(self, serial, layer):
        item = API.FindLayer(layer)

        return item is not None and item.Serial == serial

    def _cancel_cursor(self):
        if API.HasTarget():
            API.CancelTarget()

    def stow(self):
        stowed = True

        for serial, layer in self._held:
            if not self._on_layer(serial, layer):
                continue

            self._cancel_cursor()

            for _attempt in range(self._attempts):
                API.MoveItem(serial, API.Backpack)

                if settled(self._timeout, self._poll, lambda: not self._on_layer(serial, layer)):
                    break
            else:
                stowed = False
                self._log("could not put %s in the pack" % hex_of(serial))

        return stowed

    def restore(self):
        restored = True

        for serial, layer in self._held:
            if self._on_layer(serial, layer):
                continue

            self._cancel_cursor()

            for _attempt in range(self._attempts):
                API.EquipItem(serial)

                if settled(self._timeout, self._poll, lambda: self._on_layer(serial, layer)):
                    break
            else:
                restored = False
                self._log("could not draw %s again" % hex_of(serial))

        return restored


# src/uo/pack.py
def pack_contents():
    items = API.ItemsInContainer(API.Backpack, True)

    return items if items else []


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


# src/uo/heal.py
class Bandager(object):
    """Bandages the character it runs on; the hits rising are the proof, the wordings only explain."""

    def __init__(self, graphic, buckets, timeout, cursor_timeout, wait_slice, attempts, recovered,
                 saves, log):
        self._graphic = graphic
        self._buckets = buckets
        self._timeout = timeout
        self._cursor_timeout = cursor_timeout
        self._wait_slice = wait_slice
        self._attempts = attempts
        self._recovered = recovered
        self._saves = saves
        self._log = log
        self._ran_out = None

    def empty(self):
        return self._ran_out

    def in_pack(self):
        for item in pack_contents():
            if item.Graphic == self._graphic:
                return item

        return None

    def _apply_once(self):
        bandages = self.in_pack()

        if bandages is None:
            self._ran_out = "no bandages left in the pack"

            return False

        if API.HasTarget():
            API.CancelTarget()

        API.ClearJournal()
        API.UseObject(bandages.Serial)

        if not API.WaitForTarget("any", self._cursor_timeout):
            self._log("no cursor for the bandage")

            return False

        before = API.Player.Hits
        API.TargetSelf()

        outcome = read_outcome(self._buckets, self._timeout, self._wait_slice)

        if outcome == "noBandages":
            self._ran_out = "the shard says there are no bandages"

            return False

        if outcome == "saving":
            self._saves.wait_out()

        return API.Player.Hits > before or outcome == "healed"

    def mend(self):
        if self._recovered():
            return True

        if self._ran_out is not None:
            return False

        self._log("%d/%d hits, bandaging" % (API.Player.Hits, API.Player.HitsMax))

        for _attempt in range(self._attempts):
            if self._ran_out is not None:
                break

            self._apply_once()

            if self._recovered():
                self._log("healed to %d/%d" % (API.Player.Hits, API.Player.HitsMax))

                return True

            if API.Player.IsDead:
                break

        if self._ran_out is not None:
            self._log(self._ran_out)

        return False


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


# src/uo/log.py
def make_log(prefix):
    def log(message):
        API.SysMsg(prefix + ": " + message)

    return log


# src/uo/loop.py
def backoff_for(count, step, cap):
    return min(step * count, cap)


# src/uo/mana.py
class ManaWatch(object):
    def __init__(self, to_full, poll, log_every, log, stop_reason, meditating):
        self._to_full = to_full
        self._poll = poll
        self._log_every = log_every
        self._log = log
        self._stop_reason = stop_reason
        self._meditating = meditating

    # Worked out on every read rather than once: ManaMax is 0 while the client refreshes stats, and
    # a ceiling taken in that window would either end the wait as it started or never end it at all
    def target(self, need):
        ceiling = API.Player.ManaMax

        if not self._to_full or ceiling <= 0:
            return need

        return max(need, ceiling)

    # >= and never !=: a regenerating pool passes a figure as often as it lands on it
    def enough(self, need):
        return API.Player.Mana >= self.target(need)

    # Sliced rather than slept through, so the guards get a look in and the pool is reported on
    def watch(self, need, budget):
        waited = 0.0
        since = 0.0

        while waited < budget:
            if self.enough(need):
                return True

            if self._stop_reason() is not None:
                return False

            API.Pause(self._poll)
            waited += self._poll
            since += self._poll

            if since >= self._log_every:
                since = 0.0
                self._log(
                    "%d/%d mana%s"
                    % (
                        API.Player.Mana,
                        self.target(need),
                        ", meditating" if self._meditating() else "",
                    )
                )

        return self.enough(need)


# src/uo/meditate.py
class Meditation(object):
    def __init__(self, skill, buckets, mana, meditating, log, saves, attempts, timeout,
                 start_timeout, wait_slice, regen_timeout):
        self._skill = skill
        self._buckets = buckets
        self._mana = mana
        self._meditating = meditating
        self._log = log
        self._saves = saves
        self._attempts = attempts
        self._timeout = timeout
        self._start_timeout = start_timeout
        self._wait_slice = wait_slice
        self._regen_timeout = regen_timeout
        self._refused = None

    def refused(self):
        return self._refused

    def _start_outcome(self):
        hit = read_outcome(self._buckets, self._start_timeout, self._wait_slice)

        if hit is not None:
            return hit

        # Silence is what every use looks like on a shard whose wordings this table has wrong, so
        # the buff is the proof that does not go through the journal at all
        if self._meditating() or settled(self._start_timeout, self._wait_slice, self._meditating):
            return "trance"

        return "unknown"

    def _for(self, need):
        for attempt in range(1, self._attempts + 1):
            # Using the skill again mid-trance is at best a wasted action and at worst the shard
            # ending the very trance this attempt is waiting on
            if not self._meditating():
                API.ClearJournal()
                API.UseSkill(self._skill)

                outcome = self._start_outcome()

                # Nothing here undresses the character, so a refusal is final for the run
                if outcome == "blocked" or outcome == "unskilled":
                    self._refused = "the shard refuses meditation (%s)" % outcome
                    self._log("%s - empty your hands; falling back on natural regeneration"
                              % self._refused)

                    return self._mana.watch(need, self._regen_timeout)

                # The shard knows the pool is full better than a stat read does
                if outcome == "full":
                    return True

                # A pause and not a refusal: nothing about meditation is learned from it
                if outcome == "saving":
                    self._saves.wait_out()

            if self._mana.watch(need, self._timeout):
                return True

            # Not 'gave up': a failed concentration roll, a trance broken by a hit and a use the
            # shard threw away all look like this, and all are answered by using the skill again
            self._log("meditation attempt %d did not fill the pool, using the skill again" % attempt)

        return False

    def regain(self, need, allowed):
        if self._mana.enough(need):
            return True

        self._log("%d mana, waiting for %d" % (API.Player.Mana, self._mana.target(need)))

        if allowed and self._refused is None:
            return self._for(need)

        return self._mana.watch(need, self._regen_timeout)


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


# src/uo/stages.py
def make_plan(stages):
    return sorted(stages, key=lambda stage: stage["up_to"])


def goal_of(plan):
    return max([stage["up_to"] for stage in plan]) if plan else 0.0


# The same table that picks the spell answers whether there is one left, so the two cannot disagree
def stage_now(plan, value):
    for stage in plan:
        if value < stage["up_to"]:
            return stage

    return None


def describe_plan(plan):
    return ", ".join("%s to %.1f" % (stage["spell"], stage["up_to"]) for stage in plan)


# What one casting cycle of a row costs in wall clock, and the denominator a dry mana stretch is
# priced against
def cycle_cost(stage, fallback_timeout, fallback_delay):
    return max(0.1, stage.get("cast_timeout", fallback_timeout)
               + stage.get("cast_delay", fallback_delay))


# src/uo/target.py
class SelfTarget(object):
    """The fallback for a cursor the pre-target did not take."""

    def __init__(self, answers, timeout, poll, log):
        self._answers = answers
        self._timeout = timeout
        self._poll = poll
        self._log = log
        self._learned = None

    # Target(player) is the one that worked on the probe run and is first for that reason; each is
    # guarded on its own, because Target is an overloaded C# method and the wrong shape throws
    def answer(self):
        for how in [self._learned] if self._learned else self._answers:
            try:
                if how == "Target(player)":
                    API.Target(API.Player)
                elif how == "TargetSelf":
                    API.TargetSelf()
                else:
                    API.Target(API.Player.Serial)
            except Exception as error:
                self._log("%s threw - %s" % (how, error))
                continue

            if settled(self._timeout, self._poll, lambda: not API.HasTarget()):
                if self._learned is None:
                    self._learned = how
                    self._log("the cursor answers to %s" % how)

                return True

        self._log("the cursor would not take a self target")

        return False


# src/uo/vitals.py
def mana_reading():
    me = player()

    return "?/?" if me is None else "%d/%d mana" % (me.Mana, me.ManaMax)


def where():
    me = player()

    return "somewhere" if me is None else "at %d,%d" % (me.X, me.Y)


def position_and_mana():
    return "%s, %s" % (where(), mana_reading())


# src/chivalry/index.py
log = make_log("chiv")
bar = BuffBar(log)
skill = SkillReader(SKILL)
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "casts", position_and_mana)
hands = Hands(HAND_LAYERS, EQUIP_ATTEMPTS, EQUIP_TIMEOUT, EQUIP_POLL, log)
floor = hurt(HURT_FLOOR)


# The floor is for Noble Sacrifice, which sets the caster's hits to 1 where it finds anything to
# heal. The loop bandages before this gets a look, so it only ends a run the bandages could not save.
def stop_reason():
    return first_reason([stopped(STOPPED), dead(), floor, skill_capped(SKILL)])


def standing(stage):
    return bar.standing(stage.get("buff"), stage.get("title"))


def meditating():
    return bar.standing(MEDITATION_BUFF)


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)
mana = ManaWatch(MEDITATE_TO_FULL, MANA_POLL, MANA_LOG_EVERY, log, stop_reason, meditating)
trance = Meditation(MEDITATION, MEDITATE_OUTCOME_TEXT, mana, meditating, log, saves,
                    MEDITATE_ATTEMPTS, MEDITATE_TIMEOUT, MEDITATE_START_TIMEOUT, CAST_WAIT_SLICE,
                    REGEN_TIMEOUT)
caster = Caster(OUTCOME_TEXT, standing, SelfTarget(SELF_ANSWERS, SELF_TARGET_TIMEOUT,
                                                   SELF_TARGET_POLL, log),
                SKIP_WHEN_BUFFED, CAST_TIMEOUT, CAST_DELAY, CAST_WAIT_SLICE, PROOF_GRACE, log)
bandager = Bandager(BANDAGE_GRAPHIC, HEAL_OUTCOME_TEXT, BANDAGE_TIMEOUT, BANDAGE_CURSOR_TIMEOUT,
                    CAST_WAIT_SLICE, BANDAGE_ATTEMPTS, lambda: floor() is None, saves, log)

plan = make_plan(STAGES)
goal = goal_of(plan)


# Meditation is refused with anything in hand, so the trance is bracketed by a stow and a draw.
# Restored on every way out, or a wait the guards ended would leave the weapon in the pack.
def regain_mana(need):
    global stop

    if mana.enough(need):
        return True

    hands.stow()

    try:
        arrived = trance.regain(need, MEDITATE)
    finally:
        if not hands.restore():
            stop = "the weapon did not come back out of the pack"

    # This path has just spent up to a minute reporting on its own cadence
    heartbeat.reset()

    return arrived


def stalled(idle):
    if idle >= MAX_STALE:
        return "%d cycles without a cast or a change in the skill" % MAX_STALE

    return None


casts = 0
fizzled = 0
throttled = 0
blind = 0

# Outcomes this loop could not read. Reported at the end so a wrong OUTCOME_TEXT is still obvious,
# but never a reason to stop on its own.
unread = 0

# The ones since the skill last moved, credited to the tally when it does
unread_pending = 0

# Said once per stretch rather than once per cast
unread_said = False

since_progress = 0
reported = 0
casting = None
cycle = 0

stop = None
start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)

if start is None:
    start = 0.0
    stop = "the client is not reporting the skill"

last_value = start
recorder = attempt_log(DATA_PATH, skill.name(), log)
held = hands.remember()

if stop is None:
    log("%s at %.1f/%.1f - %s" % (skill.name(), start, goal, describe_plan(plan)))
    log("hand %s, %d/%d hits, %d/%d mana"
        % (", ".join(describe_item(item) for item in held) or "empty",
           API.Player.Hits, API.Player.HitsMax, API.Player.Mana, API.Player.ManaMax))
    log("%d tithing points; every cast spends some, tithe gold at a shrine"
        % API.Player.TithingPoints)

    if held:
        log("it goes in the pack for every trance and comes back out after")
    else:
        log("nothing in hand - Consecrate Weapon will be refused, the other bands will not")

    if BANDAGE and bandager.in_pack() is None:
        log("no bandages in the pack - the health floor will stop the run instead")

    if start < FIRST_BAND:
        log("under %.1f a trainer sells the skill faster than this loop casts it" % FIRST_BAND)

    cap = skill.cap()

    # Said rather than corrected: a scroll may be on its way, and a run that quietly retargeted
    # itself would be lying about its plan
    if cap is not None and cap > 0 and goal > cap:
        log(
            "the last stage aims at %.1f and the shard caps %s at %.1f - it will stop there"
            % (goal, skill.name(), cap)
        )

    if stage_now(plan, start) is None:
        stop = "%s is already at %.1f" % (skill.name(), start)

try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1

        # Before the guards: the floor that asks for the bandaging is the floor that ends the run
        if BANDAGE:
            bandager.mend()

        stop = stop_reason()

        if stop is not None:
            break

        value = skill.read()

        # A client that has stopped answering is a blip, not an ending: read as 0 it trains a capped
        # character, read as finished it ends a good run
        if value is None:
            blind += 1

            if blind >= MAX_BLIND_READS:
                stop = "the client stopped reporting the skill"
                break

            heartbeat.beat("unreadable skill", cycle, casts)
            API.Pause(STEP_DELAY)
            continue

        blind = 0

        # The gain an attempt earned lands here rather than at the attempt: the client applies
        # it some time after the outcome, so the row waits a cycle for a value worth writing
        recorder.settle(value)

        # Either direction counts - a skill falling because another is gaining is still the shard
        # saying it is processing these casts
        if value != last_value:
            last_value = value
            since_progress = 0
            casts += unread_pending
            unread_pending = 0
            unread_said = False

        stage = stage_now(plan, value)

        if stage is None:
            stop = "the last stage is finished"
            break

        if stage is not casting:
            casting = stage
            log("%.1f - %s until %.1f" % (value, stage["spell"], stage["up_to"]))

        if stage.get("needs_weapon") and not hands.remembered():
            stop = "nothing in hand for %s - draw a weapon and start again" % stage["spell"]
            break

        # Gated here because nothing a script does refills tithing: a refusal in words would be the
        # same ending one cast later
        if API.Player.TithingPoints < stage["tithing"]:
            stop = "out of tithing points (%d/%d) - tithe gold at a shrine" % (
                API.Player.TithingPoints, stage["tithing"])
            break

        if API.Player.Mana < stage["mana"]:
            arrived = regain_mana(stage["mana"])

            if stop is not None:
                break

            if not arrived:
                # Weighted, because a dry stretch has just spent the whole REGEN_TIMEOUT standing
                # still where a casting cycle costs cycle_cost
                since_progress += max(1, int(round(
                    REGEN_TIMEOUT / cycle_cost(stage, CAST_TIMEOUT, CAST_DELAY))))
                log("mana did not come back (%d/%d idle)" % (since_progress, MAX_STALE))

            stop = stalled(since_progress)

            if stop is not None:
                break

            heartbeat.beat("recovering mana", cycle, casts)
            API.Pause(STEP_DELAY)
            continue

        outcome = caster.cast_once(stage)

        if outcome != "throttled":
            throttled = 0

        if outcome == "cast":
            casts += 1
            recorder.record(value, outcome, stage["spell"])
            since_progress = 0
            unread_said = False

        # Counted rather than tallied - the shard charged nothing for it - but the roll happened
        elif outcome == "fizzled":
            fizzled += 1
            recorder.record(value, outcome, stage["spell"])
            since_progress = 0
            unread_said = False

        elif outcome == "alreadyUp":
            since_progress = 0
            unread_said = False
            API.Pause(BUFF_WAIT)

        # Waited out flat rather than backed off: this is a spell that finishes on its own
        elif outcome == "alreadyCasting":
            since_progress = 0
            unread_said = False
            API.Pause(CASTING_WAIT)

        elif outcome == "disabled":
            since_progress = 0
            unread_said = False

            if DISABLED_IS_PROGRESS:
                casts += 1
                recorder.record(value, outcome, stage["spell"])
            else:
                log("the shard toggled %s off - check its buff in STAGES" % stage["spell"])

        # The loop gathered mana before casting, so this row's mana figure understates the cost
        elif outcome == "noMana":
            since_progress = 0
            unread_said = False
            log(
                "refused for mana at %d - raise %s's mana in STAGES"
                % (API.Player.Mana, stage["spell"])
            )
            regain_mana(stage["mana"])

        elif outcome == "noTithing":
            stop = "out of tithing points - tithe gold at a shrine"

        # The layers said the weapon was there, so believe the shard and draw it again
        elif outcome == "noWeapon":
            since_progress = 0
            unread_said = False

            if not hands.remembered() or not hands.restore():
                stop = "the shard says nothing is in hand for %s" % stage["spell"]

        elif outcome == "unskilled":
            stop = "the shard says this character cannot use %s" % stage["spell"]

        elif outcome == "saving":
            saves.wait_out()
            since_progress = 0
            unread_said = False

        elif outcome == "throttled":
            throttled += 1
            since_progress = 0
            unread_said = False
            log("shard says wait (%d/%d), backing off" % (throttled, MAX_THROTTLED))
            API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

            if throttled >= MAX_THROTTLED:
                stop = "the shard kept refusing the cast"

        # The commonest cause is a cast that worked with its buff already standing, leaving only
        # the mana to prove it. The skill moving is what settles it, above.
        else:
            unread += 1
            unread_pending += 1
            since_progress += 1

            if not unread_said:
                unread_said = True
                log("outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls")

        stop = stop or stalled(since_progress)

        if stop is not None:
            break

        if casts >= reported + LOG_EVERY:
            reported = casts
            log(
                "%d casts, %d fizzles, %s at %.1f/%.1f, %d mana, %d tithing"
                % (casts, fizzled, skill.name(), value, goal, API.Player.Mana,
                   API.Player.TithingPoints)
            )

        heartbeat.beat(outcome or "unknown", cycle, casts)
        caster.pace(stage)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    if stop is None:
        stop = "threw - %s" % error

if API.HasTarget():
    API.CancelTarget()

ended = skill.read()
recorder.settle(ended)

log(
    "%d casts, %d fizzles, %s %.1f -> %s"
    % (casts, fizzled, skill.name(), start, "unknown" if ended is None else "%.1f" % ended)
)

if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to OUTCOME_TEXT" % unread)

if bandager.empty() is not None:
    log(bandager.empty())

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES

log("stopping - %s" % reason)
API.Stop()
