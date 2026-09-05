import API

from mysticism.config import (BUFF_WAIT, CAST_DELAY, CAST_TIMEOUT, CAST_WAIT_SLICE, CASTING_WAIT,
                              DATA_PATH, DISABLED_IS_PROGRESS, FIRST_BAND, HEARTBEAT_EVERY,
                              HURT_FLOOR, LOG_EVERY, MANA_LOG_EVERY, MANA_POLL, MAX_BLIND_READS,
                              MAX_CYCLES, MAX_STALE, MAX_THROTTLED, MEDITATE, MEDITATE_ATTEMPTS,
                              MEDITATE_OUTCOME_TEXT, MEDITATE_START_TIMEOUT, MEDITATE_TIMEOUT,
                              MEDITATE_TO_FULL, MEDITATION, MEDITATION_BUFF, OUTCOME_TEXT,
                              PROOF_GRACE, REGEN_TIMEOUT, SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT,
                              SAVING_TEXT, SELF_ANSWERS, SELF_TARGET_POLL, SELF_TARGET_TIMEOUT,
                              SKILL, SKILL_POLL, SKILL_TIMEOUT, SKIP_WHEN_BUFFED, STAGES,
                              STEP_DELAY, STOPPED, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)
from uo.buffbar import BuffBar
from uo.cast import Caster
from uo.gear import in_hand
from uo.guards import dead, first_reason, hurt, stopped
from uo.heartbeat import Heartbeat
from uo.log import make_log
from uo.loop import backoff_for
from uo.mana import ManaWatch
from uo.meditate import Meditation
from uo.record import attempt_log
from uo.save import SaveWatch
from uo.skill import SkillReader
from uo.stages import cycle_cost, describe_plan, goal_of, make_plan, stage_now
from uo.target import SelfTarget
from uo.vitals import position_and_mana

log = make_log("mystic")
bar = BuffBar(log)
skill = SkillReader(SKILL)
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "casts", position_and_mana)


# The two area bands are cast on the caster, so a shard that does include them in their own damage
# is caught here rather than by the corpse
def stop_reason():
    return first_reason([stopped(STOPPED), dead(), hurt(HURT_FLOOR)])


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


def regain_mana(need):
    arrived = trance.regain(need, MEDITATE)

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

if stop is None:
    log("%s at %.1f/%.1f - %s" % (skill.name(), start, goal, describe_plan(plan)))
    log("%d/%d mana" % (API.Player.Mana, API.Player.ManaMax))

    if in_hand() is not None:
        log("something is in hand - meditation is refused until you put it away")

    # Nether Bolt is the cheapest thing in the book and it still wants skill behind it
    if start < FIRST_BAND:
        log("under %.1f a trainer sells the skill faster than this loop casts it" % FIRST_BAND)

    cap = skill.cap()

    # Said rather than corrected: a scroll may be on its way, and a run that quietly retargeted
    # itself would be lying about its plan
    if cap is not None and cap > 0 and goal > cap:
        log(
            "the last stage aims at %.1f and the shard caps %s at %.1f - it will not finish "
            "without a power scroll" % (goal, skill.name(), cap)
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

        # The gain an attempt earned lands here rather than at the attempt: the client applies
        # it some time after the outcome, so the row waits a cycle for a value worth writing
        recorder.settle(value)

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

        if API.Player.Mana < stage["mana"]:
            if not regain_mana(stage["mana"]):
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
            recorder.record(value, outcome, True)
            since_progress = 0
            unread_said = False

        # Counted rather than tallied - the shard charged nothing for it - but the roll happened
        elif outcome == "fizzled":
            fizzled += 1
            recorder.record(value, outcome, False)
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
                recorder.record(value, outcome, True)
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

        # Every band above Stone Form is unreachable while the form is up, and nothing here drops it
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
                % (casts, fizzled, skill.name(), value, goal, API.Player.Mana)
            )

        heartbeat.beat(outcome or "unknown", cycle, casts)
        caster.pace(stage)
except Exception as error:
    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error

if API.HasTarget():
    API.CancelTarget()

ended = skill.read()
recorder.settle(ended)

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
