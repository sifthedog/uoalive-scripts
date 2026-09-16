# Built from src/spellweaving/index.py by build.py - do not edit.

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

GAIN_PATH_TIMEOUT = 5.0
GAIN_PATH_POLL = 0.25


# src/spellweaving/config.py
# Every success and failure is appended here, one JSON object per line, for legion/skilldb.py to
# turn into a table later. "" turns recording off. A bare name lands beside the script.
DATA_PATH = "skill-attempts.jsonl"

# up_to is the skill value the row trains to, exclusive, so the bands butt together. `buff` is a
# BuffIconType member name matched against str(buff.Type); `title` is the localized fallback.
# target_kind is the cursor the shard raises - the two area rows are harmful, and a pre-target set
# to the wrong kind does not fire at all. cast_timeout is the book's own casting delay with a
# margin; cast_delay is the floor between casts. The spell names are the strings handed to
# API.CastSpell, so they have to read the way your spellbook does.
#
# How the rows were picked, because the book is bigger than the table. A spell the loop can grind
# has to be castable twice running, which rules out most of it:
#
#   - anything that leaves a timed buff on the caster answers the recast with "This spell is already
#     in effect" and can be cast once a duration. That is Arcane Empowerment (20 seconds), Ethereal
#     Voyage, Gift of Life, and on top of their own cooldowns Gift of Renewal and Attunement.
#   - Dryad Allure wants a humanoid to charm, Nature's Fury leaves a swarm, the two summons leave a
#     creature in your follower slots.
#
# What is left recasts freely: an enchant that renews (Arcane Circle, Immolating Weapon), a form
# that toggles (Reaper Form), and the three that resolve and are gone. Of those, each band takes the
# hardest it can cast: min_skill first, because that is the book's own difficulty ranking, then mana
# where two spells share a minimum.
# The top three bands open on their spell's minimum exactly, with no margin: a spell the shard has
# only just allowed fizzles more, and a fizzle is still a roll. The two below them carry a margin
# because nothing harder was available to move up to. min_skill is the shard's figure and nothing
# reads it but the test that holds the order.
#
# Every mana figure is the unfocused one; an arcane focus takes roughly a third off each.
STAGES = [
    # Casts solo on this shard - it renews the arcane focus and gains, which is what the cast
    # wordings below are read off. The focus it lights is what makes every row under it cheaper,
    # and the journal put its life at 7199 seconds.
    {
        "up_to": 20.0,
        "spell": "Arcane Circle",
        "min_skill": 0,
        "mana": 24,
        "cast_timeout": 3.5,
        "cast_delay": 0.4,
    },
    # Enchants what is in hand, so the run stows and redraws the weapon around every trance. The
    # fastest cast in the book at 1.0s, and Thunderstorm's equal on mana without the aggravation.
    {
        "up_to": 35.0,
        "spell": "Immolating Weapon",
        "min_skill": 10,
        "buff": "Immolating",
        "title": "Immolating Weapon",
        "mana": 32,
        "needs_weapon": True,
        "cast_timeout": 3.5,
        "cast_delay": 0.4,
    },
    # A transformation, and a toggle: every other cast takes it back off, which is still a cast the
    # shard charged for and rolled - see DISABLED_IS_PROGRESS. The only spell at its minimum that
    # can be cast twice running, so it holds the band until Essence of Wind's minimum lands.
    {
        "up_to": 52.0,
        "spell": "Reaper Form",
        "min_skill": 24,
        "buff": "ReaperForm",
        "title": "Reaper Form",
        "mana": 34,
        "cast_timeout": 4.0,
        "cast_delay": 0.5,
    },
    # Frost damage to everything hostile in six tiles, so this band and the two above it belong
    # somewhere empty. Centred on the caster, so no cursor.
    {
        "up_to": 66.0,
        "spell": "Essence of Wind",
        "min_skill": 52,
        "mana": 40,
        "cast_timeout": 4.5,
        "cast_delay": 0.5,
    },
    # Laid on the ground rather than on anything, so the cursor is answered at the caster the way
    # mysticism.py answers Hail Storm's
    {
        "up_to": 90.0,
        "spell": "Wildfire",
        "min_skill": 66,
        "mana": 50,
        "target": "self",
        "target_kind": "harmful",
        "cast_timeout": 4.0,
        "cast_delay": 0.5,
    },
    # Cast at the caster, who is a player: the book says it slays creatures and only chips players,
    # so this is chip damage in a loop rather than a way to die. HURT_FLOOR ends it either way.
    {
        "up_to": 120.0,
        "spell": "Word of Death",
        "min_skill": 83,
        "mana": 50,
        "target": "self",
        "target_kind": "harmful",
        "cast_timeout": 5.0,
        "cast_delay": 0.6,
    },
]

SKILL = "Spellweaving"
MEDITATION = "Meditation"

# The BuffIconType the client publishes while a trance is running
MEDITATION_BUFF = "ActiveMeditation"

# The ceiling of the Arcane Circle band, and the only band a shard reading the table strictly would
# refuse solo. The start-up line says so; the run tries it either way.
FIRST_BAND = 20.0

# The layers a trance wants empty, and where Immolating Weapon's weapon comes back to. A shield sits
# on onehanded too.
HAND_LAYERS = ["onehanded", "twohanded"]

EQUIP_ATTEMPTS = 3
EQUIP_TIMEOUT = 2.0
EQUIP_POLL = 0.2

SKILL_TIMEOUT = 1.0
SKILL_POLL = 0.5

# Consecutive cycles the client answered nothing for the skill before the run gives up
MAX_BLIND_READS = 5

# The fallback for a row that names neither, and every row in STAGES names both
CAST_TIMEOUT = 2.0
CAST_DELAY = 0.75

CAST_WAIT_SLICE = 0.2

# How long the cursor is given to go down once it has been answered, which is what says whether the
# shard took that answer
SELF_TARGET_TIMEOUT = 1.0
SELF_TARGET_POLL = 0.1

# Fallbacks for a cursor the pre-target did not take, tried in this order until one brings it down
SELF_ANSWERS = ["Target(player)", "TargetSelf", "Target(serial)"]

# The mana leaves the pool a beat after the incantation ends, so IsCasting falling is not the end of
# the read. 1.4 and not magery.py's 0.6: this shard posts the arcane focus lines well after the
# incantation, and the next cycle's ClearJournal destroys anything the window closed on - which is
# what every unreadable outcome on the first run turned out to be. It only costs wall clock on a
# cast nothing has proved yet; a mana drop or a matched line still leaves in the same slice.
PROOF_GRACE = 1.4

# What a cast issued before the last one finished costs. Flat, and never counted towards a stop:
# this is the pacing finding the shard's real cast time rather than anything going wrong.
CASTING_WAIT = 0.5

BUFF_WAIT = 2.0

# Gating on the buff would cap the run at one cast per Immolating Weapon
SKIP_WHEN_BUFFED = False

# A toggle the shard turned back off was still a cast it charged for and rolled the skill on
DISABLED_IS_PROGRESS = True

# The top two bands are cast at the caster's feet and nothing here heals, so a health floor is a
# stop rather than a pause
HURT_FLOOR = 0.5

# Off waits for natural regeneration instead: slower, always available
MEDITATE = True

# The last band charges 50 a cast, so a pool topped right up pays for several
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

# Guesses - correct them against the real journal after the first run. Ordered, not a dict: the
# first bucket holding a match wins, which is why alreadyCasting sits before throttled: the latter
# ends in a bare 'You must wait' that the longer sentence contains.
OUTCOME_TEXT = [
    # Read off a live run. The focus lines are Arcane Circle's own receipt, and the band needs one:
    # it puts up no buff this loop reads, so without them a cast the client had not yet refreshed
    # the mana for went down as unreadable.
    (
        "cast",
        [
            "Your arcane focus is renewed",
            "Arcane Focus will expire",
            "You have gained an arcane focus",
        ],
    ),
    ("fizzled", ["The spell fizzles", "You have failed to cast the spell"]),
    ("noMana", ["You do not have enough mana", "Insufficient mana"]),
    # The first is this shard's own, off a live run: what every timed self-buff in the book answers
    # a recast with. A row that hits it belongs out of STAGES, not waited on.
    (
        "alreadyUp",
        ["This spell is already in effect", "You are already under the effect"],
    ),
    # The layers said the weapon was there, so this is the shard disagreeing rather than a missing
    # weapon: the run draws it again and carries on
    (
        "noWeapon",
        [
            "You must have a weapon",
            "You must be wielding a weapon",
            "You must have a weapon equipped",
        ],
    ),
    (
        "disabled",
        ["You are no longer in reaper form", "You are no longer", "You have dispelled"],
    ),
    # Reaper Form shuts the rest of the book on some shards, which strands the bands above it
    ("formLocked", ["You cannot cast this spell while in", "while in this form"]),
    # The first band, every time, unless a second spellweaver is standing on the circle with you
    (
        "noCircle",
        [
            "You must be in an arcane circle",
            "You need to be standing on an arcane circle",
            "Arcane Circle requires",
            "There are not enough spellweavers",
        ],
    ),
    ("unskilled", UNSKILLED_TEXT),
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


# src/uo/text.py
def words_of(text):
    letters = []

    for char in (text or "").lower():
        letters.append(char if char.isalnum() else " ")

    return "".join(letters).split()


def any_in(text, fragments):
    low = (text or "").lower()

    for fragment in fragments:
        if fragment in low:
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


# The text alone: fishing reads the catch off the end of the line it returns
def journal_tail(seconds, limit, stamp=None):
    return [text for _name, text in journal_entries(seconds, stamp)][-limit:]


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
                 fallback_delay, wait_slice, proof_grace, log, spent=None):
        self._buckets = buckets
        self._standing = standing
        self._self_target = self_target
        self._skip_when_buffed = skip_when_buffed
        self._fallback_timeout = fallback_timeout
        self._fallback_delay = fallback_delay
        self._wait_slice = wait_slice
        self._proof_grace = proof_grace
        self._log = log
        self._spent = spent
        self._paced = False

    # Chivalry fizzles in silence - a sound, and nothing said at all - so a school whose currency is
    # taken for the roll rather than for the result can still tell a failed cast from no cast.
    # Reached only once the two proofs of a success have had their whole window.
    def _unproved(self, mana_before, spent_before):
        if API.Player.Mana < mana_before:
            return "cast"

        if spent_before is not None and self._spent() < spent_before:
            return "fizzled"

        return None

    # The window closing is not proof that nothing arrived - it was measured landing a beat late -
    # and the loop owes this row a cast_delay of standing still either way. Spent here instead, it
    # buys the one attempt that needs it another look at all three proofs for no wall clock of its
    # own; pace() is told not to spend it twice. Raising cast_timeout would buy the same look and
    # charge every attempt for it.
    def _late_look(self, stage, mana_before, spent_before):
        API.Pause(stage.get("cast_delay", self._fallback_delay))
        self._paced = True

        return matched_bucket(self._buckets) or self._unproved(mana_before, spent_before)

    # The wording wins over the two silent proofs, so it is read first on every slice: a fizzle that
    # somehow spent mana still reads as a fizzle. Giving up early once IsCasting has gone up and come
    # back down saves the rest of the budget; a shard that publishes no flag spends all of it.
    def _read_outcome(self, stage, up_before, mana_before, spent_before):
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
                    return self._unproved(mana_before, spent_before)

            if waited >= budget:
                return self._unproved(mana_before, spent_before)

            API.Pause(self._wait_slice)
            waited += self._wait_slice

    def cast_once(self, stage):
        up_before = self._standing(stage)

        if self._skip_when_buffed and up_before:
            return "alreadyUp"

        mana_before = API.Player.Mana
        spent_before = None if self._spent is None else self._spent()

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

        outcome = self._read_outcome(stage, up_before, mana_before, spent_before)

        if outcome is None:
            outcome = self._late_look(stage, mana_before, spent_before)

        # Or a queued target the cast never used is still armed for whatever the next one raises
        if wants_self:
            API.CancelPreTarget()

        return outcome

    # The row's floor and nothing else, and nothing at all where the late look already stood there
    # for it. Waiting out IsRecovering as well made a Bless cycle several seconds of standing still,
    # and it buys nothing the shard does not already say: a cast issued too early is refused in
    # words, and that refusal costs one flat CASTING_WAIT.
    def pace(self, stage):
        if self._paced:
            self._paced = False
            return

        API.Pause(stage.get("cast_delay", self._fallback_delay))


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


# src/uo/mana.py
LMC_CAP = 40  # OSI caps Lower Mana Cost at 40%; raise on shards that don't


# ceil(base * (100 - lmc) / 100), the server's Spell.ScaleMana. `or 0`: the field is None between
# world states and 0 while the client refreshes stats
def cost(base):
    lmc = min(API.Player.LowerManaCost or 0, LMC_CAP)
    return -(-base * (100 - lmc) // 100)


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


# src/spellweaving/index.py
log = make_log("weaver")
bar = BuffBar(log)
skill = SkillReader(SKILL)
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "casts", position_and_mana)
hands = Hands(HAND_LAYERS, EQUIP_ATTEMPTS, EQUIP_TIMEOUT, EQUIP_POLL, log)


# The top two bands land at the caster's feet, so what they take off is caught here rather than by
# the corpse
def stop_reason():
    return first_reason([stopped(STOPPED), dead(), hurt(HURT_FLOOR), skill_capped(SKILL)])


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

# The ones since the skill last moved, credited to the tally when it does: a cast the loop could not
# read is still a cast if the skill went up because of it
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
    log("hand %s, %d/%d mana"
        % (", ".join(describe_item(item) for item in held) or "empty",
           API.Player.Mana, API.Player.ManaMax))
    log("an arcane focus takes about a third off every mana figure here - cast Arcane Circle on a "
        "circle first and it stands for two hours")

    if held:
        log("it goes in the pack for every trance and comes back out after")
    elif stage_now(plan, start) is not None and stage_now(plan, start).get("needs_weapon"):
        log("nothing in hand - %s wants a weapon" % stage_now(plan, start)["spell"])

    # Arcane Circle is the only spell the book opens with, and some shards want company on the circle
    if start < FIRST_BAND:
        log("under %.1f only Arcane Circle gains - if this shard refuses it solo, bring a second "
            "spellweaver or buy the skill to %.1f" % (FIRST_BAND, FIRST_BAND))

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

        # The proof that cannot be argued with: every other signal is circumstantial. Either
        # direction counts - a skill falling because another is gaining is still the shard saying it
        # is processing these casts.
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

        # Before the mana gate, or an empty hand costs a trance before it is noticed
        if stage.get("needs_weapon") and not hands.remembered():
            stop = "nothing in hand for %s - draw a weapon and start again" % stage["spell"]
            break

        if API.Player.Mana < cost(stage["mana"]):
            if not regain_mana(cost(stage["mana"])):
                # Weighted, because a dry stretch has just spent the whole REGEN_TIMEOUT standing
                # still where a casting cycle costs cycle_cost. Counting both as one would either
                # end a slow-gaining run in minutes or leave a starved one going for hours.
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

        # Cleared here rather than in each branch that is not a throttle, because that is what the
        # branches were doing and three of them forgot
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
            regain_mana(cost(stage["mana"]))

        # The layers said the weapon was there, so believe the shard and draw it again
        elif outcome == "noWeapon":
            since_progress = 0
            unread_said = False

            if not hands.remembered() or not hands.restore():
                stop = "the shard says nothing is in hand for %s" % stage["spell"]

        # Nothing this loop does puts a circle down or brings anyone to stand on it
        elif outcome == "noCircle":
            stop = ("%s needs a circle and another spellweaver on it - train past %.1f elsewhere"
                    % (stage["spell"], FIRST_BAND))

        # Every band above Reaper Form is unreachable while the form is up, and nothing here drops it
        elif outcome == "formLocked":
            stop = "a form is blocking %s - drop it and start again" % stage["spell"]

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

        # The commonest cause is a cast that worked: a stage whose buff was already standing has no
        # transition to show, so only the mana can prove it, and a client that has not refreshed the
        # figure leaves this loop nothing to read. The skill moving is what settles it, above.
        else:
            unread += 1
            unread_pending += 1
            since_progress += 1

            # What it heard rather than a guess at why: an empty journal says the shard spoke too
            # late for the window and PROOF_GRACE is the knob, a line here says OUTCOME_TEXT is
            # missing that wording. matched_bucket has already taken out anything it did recognise.
            if not unread_said:
                unread_said = True
                heard = journal_tail(cycle_cost(stage, CAST_TIMEOUT, CAST_DELAY), 4)
                log("outcome unreadable - the journal held: %s" % (" | ".join(heard) or "nothing"))

        stop = stop or stalled(since_progress)

        if stop is not None:
            break

        if casts >= reported + LOG_EVERY:
            reported = casts
            log(
                "%d casts, %d fizzles, %s at %.1f/%.1f, %d mana"
                % (casts, fizzled, skill.name(), value, goal, API.Player.Mana)
            )

        heartbeat.beat(outcome or "unknown", cycle, casts)
        caster.pace(stage)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error
finally:
    recorder.close(skill.last())

if API.HasTarget():
    API.CancelTarget()

ended = skill.read()

# A delta rather than a figure: a trainer that cast four hundred times and moved nothing has failed
log(
    "%d casts, %d fizzles, %s %.1f -> %s"
    % (casts, fizzled, skill.name(), start, "unknown" if ended is None else "%.1f" % ended)
)

if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to OUTCOME_TEXT" % unread)

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES

log("stopping - %s" % reason)
API.Stop()
