import API

from chivalry.config import (BANDAGE, BANDAGE_ATTEMPTS, BANDAGE_CURSOR_TIMEOUT, BANDAGE_GRAPHIC,
                             BANDAGE_TIMEOUT, BUFF_WAIT, CAST_DELAY, CAST_TIMEOUT, CAST_WAIT_SLICE,
                             CASTING_WAIT, DATA_PATH, DISABLED_IS_PROGRESS, EQUIP_ATTEMPTS,
                             EQUIP_POLL, EQUIP_TIMEOUT, FIRST_BAND, HAND_LAYERS, HEAL_OUTCOME_TEXT,
                             HEARTBEAT_EVERY, HURT_FLOOR, JOURNAL_TAIL_LINES, JOURNAL_TAIL_SECONDS,
                             LOG_EVERY, MANA_LOG_EVERY, MANA_POLL, MAX_BLIND_READS, MAX_CYCLES,
                             MAX_STALE, MAX_THROTTLED, MAX_UNREAD_REPORTS, MEDITATE,
                             MEDITATE_ATTEMPTS, MEDITATE_OUTCOME_TEXT, MEDITATE_START_TIMEOUT,
                             MEDITATE_TIMEOUT, MEDITATE_TO_FULL, MEDITATION, MEDITATION_BUFF,
                             OUTCOME_TEXT, PROOF_GRACE, REGEN_TIMEOUT, SAVE_DONE_TEXT, SAVE_POLL,
                             SAVE_WAIT, SAVING_TEXT, SELF_ANSWERS, SELF_TARGET_POLL,
                             SELF_TARGET_TIMEOUT, SKILL, SKILL_POLL, SKILL_TIMEOUT,
                             SKIP_WHEN_BUFFED, STAGES, STEP_DELAY, STOPPED, THROTTLE_BACKOFF,
                             THROTTLE_BACKOFF_MAX)
from uo.buffbar import BuffBar
from uo.cast import Caster
from uo.hands import Hands, describe_item
from uo.guards import dead, first_reason, hurt, skill_capped, stopped
from uo.heal import Bandager
from uo.heartbeat import Heartbeat
from uo.journal import journal_tail
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
# Tithing is the last argument: a paladin's spells say nothing when they fail, and mana only leaves
# the pool when one lands, so the point the shard takes for the roll is all that separates a fizzle
# from a cast that never went off
caster = Caster(OUTCOME_TEXT, standing, SelfTarget(SELF_ANSWERS, SELF_TARGET_TIMEOUT,
                                                   SELF_TARGET_POLL, log),
                SKIP_WHEN_BUFFED, CAST_TIMEOUT, CAST_DELAY, CAST_WAIT_SLICE, PROOF_GRACE, log,
                lambda: API.Player.TithingPoints)
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

# How many of those stretches showed the journal with it, since the words that name the missing
# bucket are the same words on the tenth report as on the first
unread_reports = 0

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

        # Whatever is left once the journal, the buff, the mana and the tithing have all said
        # nothing. Recorded anyway, and shown the shard's own words the first few times: an attempt
        # nobody can name is still an attempt, and a file without it reads as a run that never
        # failed. The skill moving is what credits it to the tally, above.
        else:
            unread += 1
            unread_pending += 1
            since_progress += 1
            recorder.record(value, "unknown", stage["spell"])

            if not unread_said:
                unread_said = True
                log("outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls")

                if unread_reports < MAX_UNREAD_REPORTS:
                    unread_reports += 1
                    lines = journal_tail(JOURNAL_TAIL_SECONDS, JOURNAL_TAIL_LINES, log.stamp)

                    for line in lines or ["(the journal said nothing)"]:
                        log("  " + line)

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
finally:
    recorder.close(skill.last())

if API.HasTarget():
    API.CancelTarget()

ended = skill.read()

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
