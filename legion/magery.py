import time

import API

# up_to is the skill value the row trains to, exclusive, so the bands butt together. These are the
# spells the guides name as gaining without a victim: a punchbag has to be found, kept alive and in
# range. `buff` is a BuffIconType member name matched against str(buff.Type); `title` is the
# localized fallback. cast_timeout and cast_delay are per row because the circles are seconds
# apart - a 3rd-circle cast answered at 1.8s here, and each timeout is that time with a margin.
STAGES = [
    # 3rd circle. Below about 30 the sensible thing is to buy the skill from an NPC trainer.
    {
        "up_to": 45.0,
        "spell": "Bless",
        "buff": "Bless",
        "title": "Bless",
        "mana": 9,
        "target": "self",
        "cast_timeout": 3.0,
        "cast_delay": 0.3,
    },
    # 4th circle
    {
        "up_to": 60.0,
        "spell": "Arch Protection",
        "buff": "ArchProtection",
        "title": "Arch Protection",
        "mana": 11,
        "target": "self",
        "cast_timeout": 3.5,
        "cast_delay": 0.35,
    },
    # 6th. The 5th and 7th circles are skipped because their spells want a cursor over ground or a
    # gump answered, and neither is something this loop can do.
    {
        "up_to": 80.0,
        "spell": "Invisibility",
        "buff": "Invisibility",
        "title": "Invisibility",
        "mana": 20,
        "target": "self",
        "cast_timeout": 4.0,
        "cast_delay": 0.4,
    },
    # 8th. An area attack that hits everything nearby, so this band belongs somewhere empty. The
    # only row with no buff to prove itself by - the mana falling is the whole proof.
    {
        "up_to": 120.0,
        "spell": "Earthquake",
        "mana": 50,
        "cast_timeout": 5.0,
        "cast_delay": 0.6,
    },
]

SKILL = "Magery"
MEDITATION = "Meditation"

# The BuffIconType the client publishes while a trance is running
MEDITATION_BUFF = "ActiveMeditation"

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms.

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
# the read - it was measured landing 0.2s behind the flag
PROOF_GRACE = 0.6

# What a cast issued before the last one finished costs. Flat, and never counted towards a stop:
# this is the pacing finding the shard's real cast time rather than anything going wrong. Short
# because the refusal itself is read in one slice, so overshooting costs another cheap retry.
CASTING_WAIT = 0.5

BUFF_WAIT = 2.0

# Gating on the buff would cap the run at one cast per buff duration
SKIP_WHEN_BUFFED = False

# A toggle the shard turned back off was still a cast it charged for and rolled the skill on
DISABLED_IS_PROGRESS = True

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

STEP_DELAY = 0.3
MAX_CYCLES = 5000

MAX_THROTTLED = 20
THROTTLE_BACKOFF = 1.0
THROTTLE_BACKOFF_MAX = 8.0

LOG_EVERY = 25
HEARTBEAT_EVERY = 30.0

SAVE_WAIT = 60.0
SAVE_POLL = 1.0

SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"]
SAVING_TEXT = ["The world is saving", "Saving world", "World save started"]

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

# Guesses - correct them against the real journal after the first run. Ordered, not a dict: the
# first bucket holding a match wins, which is why alreadyCasting sits before throttled: the latter
# ends in a bare 'You must wait' that the longer sentence contains.
OUTCOME_TEXT = [
    # Not depended on: the mana leaving the pool and the buff arriving are the proof
    ("cast", ["You feel a surge of magic", "You are now protected"]),
    ("fizzled", ["The spell fizzles", "You have failed to cast the spell"]),
    (
        "noReagents",
        [
            "You do not have enough reagents",
            "More reagents are needed",
            "You lack the required reagents",
        ],
    ),
    ("noMana", ["You do not have enough mana", "Insufficient mana"]),
    ("alreadyUp", ["You are already under the effect"]),
    ("disabled", ["You are no longer", "You have dispelled"]),
    ("unskilled", UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    # The recovery wording is this shard's own, read off a live run; the other two are guesses
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

STOPPED = "stopped from the script manager"


def log(message):
    API.SysMsg("mage: " + message)


def backoff_for(count, step, cap):
    return min(step * count, cap)


def settled(timeout, poll, landed):
    waited = 0.0

    while waited < timeout:
        API.Pause(poll)
        waited += poll

        if landed():
            return True

    return False


class Heartbeat(object):
    """Proof of life: a loop standing still in silence looks exactly like a hung one."""

    def __init__(self, every):
        self._every = every
        self._last = None

    # The clock, not the cycle counter: a cycle can be one cast or a minute of meditation
    def beat(self, phase, cycle, tally):
        moment = time.time()

        if self._last is None:
            self._last = moment
            return

        if moment - self._last < self._every:
            return

        self._last = moment
        log(
            "still here - %s, cycle %d, at %d,%d, %d/%d mana, %d casts"
            % (
                phase,
                cycle,
                API.Player.X,
                API.Player.Y,
                API.Player.Mana,
                API.Player.ManaMax,
                tally,
            )
        )

    def reset(self):
        self._last = time.time()


heartbeat = Heartbeat(HEARTBEAT_EVERY)


def said(texts):
    for text in texts:
        if API.InJournal(text, False):
            return True

    return False


# Death only: nothing in this table hurts the caster, and nothing goes in the pack
def stop_reason():
    if API.StopRequested:
        return STOPPED

    if API.Player.IsDead:
        return "you are dead"

    return None


def is_saving():
    return said(SAVING_TEXT)


def wait_out_save():
    log("the world is saving, waiting it out")

    # Read before the clear: a save can start and finish inside one cast, and clearing first threw
    # the completion away and then stood still for the whole of SAVE_WAIT
    ended = "the shard had already finished" if said(SAVE_DONE_TEXT) else None

    API.ClearJournal()

    waited = 0.0

    while ended is None and waited < SAVE_WAIT:
        API.Pause(SAVE_POLL)
        waited += SAVE_POLL

        if said(SAVE_DONE_TEXT):
            ended = "the shard says it is done"
        elif stop_reason() is not None:
            ended = "the run has a reason to stop"

    log("%s, carrying on" % (ended or "nothing said in %ds" % int(SAVE_WAIT)))

    heartbeat.reset()


def matched_bucket(buckets):
    for name, phrases in buckets:
        # clearMatches, or a line already read answers the next wait as well
        if API.InJournalAny(phrases, True):
            return name

    return None


def read_outcome(buckets, budget, poll):
    waited = 0.0

    while True:
        hit = matched_bucket(buckets)

        if hit is not None:
            return hit

        if waited >= budget:
            return None

        API.Pause(poll)
        waited += poll


seen_skill = False


# Skill.Value reads 0.0 before the skill list arrives, which is also a real skill value, so a client
# that has not answered is reported unknown rather than coerced
def read_skill():
    global seen_skill

    skill = API.GetSkill(SKILL)

    if skill is None:
        return None

    value = skill.Value

    if value <= 0.0 and not seen_skill:
        return None

    seen_skill = True

    return value


def skill_name():
    skill = API.GetSkill(SKILL)

    return skill.Name if skill is not None and skill.Name else SKILL


def skill_cap():
    skill = API.GetSkill(SKILL)

    return skill.Cap if skill is not None else None


def wait_for_skill():
    waited = 0.0

    while True:
        value = read_skill()

        if value is not None:
            return value

        if waited >= SKILL_TIMEOUT:
            return None

        API.Pause(SKILL_POLL)
        waited += SKILL_POLL


dumped = False


# ApiBuff never refreshes after it is handed over, so the bar is re-read every time it matters
def active_buffs():
    global dumped

    buffs = API.ActiveBuffs()

    if not buffs:
        return []

    if not dumped:
        dumped = True
        log("buff bar: " + ", ".join("%s/%s" % (b.Type, b.Title or "") for b in buffs))

    return buffs


def standing(stage):
    name = stage.get("buff")

    if not name:
        return False

    title = stage.get("title")

    for buff in active_buffs():
        if str(buff.Type) == name:
            return True

        if title and title.lower() in (buff.Title or "").lower():
            return True

    return False


# Either hand: meditation is refused while anything at all is held
def held():
    return API.FindLayer("onehanded") or API.FindLayer("twohanded")


def meditating():
    for buff in active_buffs():
        if str(buff.Type) == MEDITATION_BUFF:
            return True

    return False


refused = None


# Worked out on every read rather than once: ManaMax is 0 while the client refreshes stats, and a
# ceiling taken in that window would either end the wait as it started or never end it at all
def mana_target(need):
    ceiling = API.Player.ManaMax

    if not MEDITATE_TO_FULL or ceiling <= 0:
        return need

    return max(need, ceiling)


# >= and never !=: a regenerating pool passes a figure as often as it lands on it
def enough(need):
    return API.Player.Mana >= mana_target(need)


# Sliced rather than slept through, so the guards get a look in and the pool is reported on
def watch_mana(need, budget):
    waited = 0.0
    since = 0.0

    while waited < budget:
        if enough(need):
            return True

        if stop_reason() is not None:
            return False

        API.Pause(MANA_POLL)
        waited += MANA_POLL
        since += MANA_POLL

        if since >= MANA_LOG_EVERY:
            since = 0.0
            log(
                "%d/%d mana%s"
                % (
                    API.Player.Mana,
                    mana_target(need),
                    ", meditating" if meditating() else "",
                )
            )

    return enough(need)


def start_outcome():
    hit = read_outcome(MEDITATE_OUTCOME_TEXT, MEDITATE_START_TIMEOUT, CAST_WAIT_SLICE)

    if hit is not None:
        return hit

    # Silence is what every use looks like on a shard whose wordings this table has wrong, so the
    # buff is the proof that does not go through the journal at all
    if meditating() or settled(MEDITATE_START_TIMEOUT, CAST_WAIT_SLICE, meditating):
        return "trance"

    return "unknown"


def meditate_for(need):
    global refused

    for attempt in range(1, MEDITATE_ATTEMPTS + 1):
        # Using the skill again mid-trance is at best a wasted action and at worst the shard ending
        # the very trance this attempt is waiting on
        if not meditating():
            API.ClearJournal()
            API.UseSkill(MEDITATION)

            outcome = start_outcome()

            # Nothing here undresses the character, so a refusal is final for the run
            if outcome == "blocked" or outcome == "unskilled":
                refused = "the shard refuses meditation (%s)" % outcome
                log("%s - empty your hands; falling back on natural regeneration" % refused)

                return watch_mana(need, REGEN_TIMEOUT)

            # The shard knows the pool is full better than a stat read does
            if outcome == "full":
                return True

            # A pause and not a refusal: nothing about meditation is learned from it
            if outcome == "saving":
                wait_out_save()

        if watch_mana(need, MEDITATE_TIMEOUT):
            return True

        # Not 'gave up': a failed concentration roll, a trance broken by a hit and a use the shard
        # threw away all look like this, and all are answered by using the skill again
        log("meditation attempt %d did not fill the pool, using the skill again" % attempt)

    return False


def regain_mana(need):
    if enough(need):
        return True

    log("%d mana, waiting for %d" % (API.Player.Mana, mana_target(need)))

    if MEDITATE and refused is None:
        arrived = meditate_for(need)
    else:
        arrived = watch_mana(need, REGEN_TIMEOUT)

    # This path has just spent up to a minute reporting on its own cadence
    heartbeat.reset()

    return arrived


self_target = None


# The fallback for a cursor the pre-target did not take. Target(player) is the one that worked on
# the probe run, and is first for that reason; each is guarded on its own, because Target is an
# overloaded C# method and handing it the wrong shape throws rather than failing quietly.
def answer_self():
    global self_target

    for how in [self_target] if self_target else SELF_ANSWERS:
        try:
            if how == "Target(player)":
                API.Target(API.Player)
            elif how == "TargetSelf":
                API.TargetSelf()
            else:
                API.Target(API.Player.Serial)
        except Exception as error:
            log("%s threw - %s" % (how, error))
            continue

        if settled(SELF_TARGET_TIMEOUT, SELF_TARGET_POLL, lambda: not API.HasTarget()):
            if self_target is None:
                self_target = how
                log("the cursor answers to %s" % how)

            return True

    log("the cursor would not take a self target")

    return False


# The wording wins over the two silent proofs, so it is read first on every slice: a fizzle that
# somehow spent mana still reads as a fizzle. Giving up early once IsCasting has gone up and come
# back down saves the rest of the budget; a shard that publishes no flag spends all of it.
def read_cast_outcome(stage, up_before, mana_before):
    budget = stage.get("cast_timeout", CAST_TIMEOUT)
    wants_self = stage.get("target") == "self"
    waited = 0.0
    started = False
    ended = None
    answered = False

    while True:
        hit = matched_bucket(OUTCOME_TEXT)

        if hit is not None:
            return hit

        # Answered here rather than in a blocking wait before the poll: the pre-target usually takes
        # the cursor before the script sees one at all, and that wait was spent on every cast
        if wants_self and not answered and API.HasTarget():
            answered = answer_self()

        # A transition, not a state: a buff already standing proves nothing, which is why up_before
        # is read before the cast
        if not up_before and standing(stage):
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
            elif waited - ended >= PROOF_GRACE and (answered or not wants_self):
                return None

        if waited >= budget:
            return None

        API.Pause(CAST_WAIT_SLICE)
        waited += CAST_WAIT_SLICE


def cast_once(stage):
    up_before = standing(stage)

    if SKIP_WHEN_BUFFED and up_before:
        return "alreadyUp"

    mana_before = API.Player.Mana

    # Cancelled only when there is one to cancel: an unconditional cancel just before an action left
    # the next cursor unusable in the run this was copied from
    if API.HasTarget():
        API.CancelTarget()

    API.ClearJournal()

    wants_self = stage.get("target") == "self"

    # Queued before the cast, the order the client's own CastSpell example uses. The type has to
    # be the one the shard raises: these cursors report as beneficial, and a pre-target set to
    # neutral does not fire at all - it leaves the cursor standing and the cast unspent.
    if wants_self:
        try:
            API.PreTarget(API.Player.Serial, "beneficial")
        except Exception as error:
            log("PreTarget threw - %s" % error)

    API.CastSpell(stage["spell"])

    outcome = read_cast_outcome(stage, up_before, mana_before)

    # Or a queued target the cast never used is still armed for whatever the next one raises
    if wants_self:
        API.CancelPreTarget()

    return outcome


# The row's floor and nothing else. Waiting out IsRecovering as well made a Bless cycle several
# seconds of standing still, and it buys nothing the shard does not already say: a cast issued too
# early is refused in words, and that refusal costs one flat CASTING_WAIT.
def pace(stage):
    API.Pause(stage.get("cast_delay", CAST_DELAY))


plan = sorted(STAGES, key=lambda stage: stage["up_to"])
goal = max([stage["up_to"] for stage in plan]) if plan else 0.0


# The same table that picks the spell answers whether there is one left, so the two cannot disagree
def stage_now(value):
    for stage in plan:
        if value < stage["up_to"]:
            return stage

    return None


def describe_plan():
    return ", ".join("%s to %.1f" % (stage["spell"], stage["up_to"]) for stage in plan)


# What one casting cycle of a row costs in wall clock, and the denominator a dry mana stretch is
# priced against
def cycle_cost(stage):
    return max(0.1, stage.get("cast_timeout", CAST_TIMEOUT) + stage.get("cast_delay", CAST_DELAY))


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
start = wait_for_skill()

if start is None:
    start = 0.0
    stop = "the client is not reporting the skill"

last_value = start

if stop is None:
    log("%s at %.1f/%.1f - %s" % (skill_name(), start, goal, describe_plan()))
    log("%d/%d mana" % (API.Player.Mana, API.Player.ManaMax))
    if held() is not None:
        log("something is in hand - meditation is refused until you put it away")

    cap = skill_cap()

    # Said rather than corrected: a scroll may be on its way, and a run that quietly retargeted
    # itself would be lying about its plan
    if cap is not None and cap > 0 and goal > cap:
        log(
            "the last stage aims at %.1f and the shard caps %s at %.1f - it will not finish "
            "without a power scroll" % (goal, skill_name(), cap)
        )

    if stage_now(start) is None:
        stop = "%s is already at %.1f" % (skill_name(), start)

try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1

        stop = stop_reason()

        if stop is not None:
            break

        value = read_skill()

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

        stage = stage_now(value)

        if stage is None:
            stop = "the last stage is finished"
            break

        if stage is not casting:
            casting = stage
            log("%.1f - %s until %.1f" % (value, stage["spell"], stage["up_to"]))

        if API.Player.Mana < stage["mana"]:
            if not regain_mana(stage["mana"]):
                # Weighted, because a dry stretch has just spent the whole REGEN_TIMEOUT standing
                # still where a casting cycle costs cycle_cost. Counting both as one would either
                # end a slow-gaining run in minutes or leave a starved one going for hours.
                since_progress += max(1, int(round(REGEN_TIMEOUT / cycle_cost(stage))))
                log("mana did not come back (%d/%d idle)" % (since_progress, MAX_STALE))

            stop = stalled(since_progress)

            if stop is not None:
                break

            heartbeat.beat("recovering mana", cycle, casts)
            API.Pause(STEP_DELAY)
            continue

        outcome = cast_once(stage)

        # Cleared here rather than in each branch that is not a throttle, because that is what the
        # branches were doing and three of them forgot
        if outcome != "throttled":
            throttled = 0

        if outcome == "cast":
            casts += 1
            since_progress = 0
            unread_said = False

        # Counted rather than tallied - the shard charged nothing for it - but the roll happened
        elif outcome == "fizzled":
            fizzled += 1
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

        # Nothing waited for refills a pouch
        elif outcome == "noReagents":
            stop = "out of reagents for %s" % stage["spell"]

        elif outcome == "unskilled":
            stop = "the shard says this character cannot use %s" % stage["spell"]

        elif outcome == "saving":
            wait_out_save()
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

            if not unread_said:
                unread_said = True
                log("outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls")

        stop = stop or stalled(since_progress)

        if stop is not None:
            break

        if casts >= reported + LOG_EVERY:
            reported = casts
            log(
                "%d casts, %d fizzles, %s at %.1f/%.1f, %d mana"
                % (casts, fizzled, skill_name(), value, goal, API.Player.Mana)
            )

        heartbeat.beat(outcome or "unknown", cycle, casts)
        pace(stage)
except Exception as error:
    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error

if API.HasTarget():
    API.CancelTarget()

ended = read_skill()

# A delta rather than a figure: a trainer that cast four hundred times and moved nothing has failed
log(
    "%d casts, %d fizzles, %s %.1f -> %s"
    % (casts, fizzled, skill_name(), start, "unknown" if ended is None else "%.1f" % ended)
)

if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to OUTCOME_TEXT" % unread)

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES

log("stopping - %s" % reason)
API.Stop()
