import API

from taming.attempt import Tamer
from taming.config import (AFTER_TAME, ANGRY_DELAY, CHASE_TIMEOUT, CONTEXT_TIMEOUT, DATA_PATH,
                           GIVE_UP_REASON, HEARTBEAT_EVERY, HUNT_RADIUS, KILL_CURSOR_TIMEOUT,
                           KILL_MENU_TEXT, KILL_PICK_POLL, KILL_PICK_TIMEOUT, LOG_EVERY, MAX_ANGRY,
                           MAX_AWAY, MAX_CONTESTED, MAX_CYCLES, MAX_PENDING, MAX_THROTTLED,
                           MENU_RETRY_DELAY, OPL_TIMEOUT, OUTCOME_TEXT, PACE_EASE_AFTER, PACE_MAX,
                           PACE_STEP, PET_NAME, PET_SETTLE_POLL, PET_SETTLE_TIMEOUT,
                           RELEASE_ATTEMPTS, RELEASE_CONFIRM_BUTTONS, RELEASE_CONFIRM_POLL,
                           RELEASE_CONFIRM_TEXT, RELEASE_CONFIRM_TIMEOUT, RELEASE_MENU_TEXT,
                           RELEASE_POLL, RELEASE_TIMEOUT, RENAME_ATTEMPTS, RENAME_POLL,
                           RENAME_TIMEOUT, RESOLUTION_TEXT, SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT,
                           SAVING_TEXT, SKILL_NAME, SKILL_POLL, SKILL_TIMEOUT, STALL_STOP,
                           STALL_WARN, STOPPED, TAME_DELAY, TAME_RANGE, TAME_RESOLVE_TIMEOUT,
                           TAME_START_TIMEOUT, TAME_WAIT_SLICE, TARGET_TIMEOUT, THROTTLE_BACKOFF,
                           THROTTLE_BACKOFF_MAX, HEALTH_FLOOR)
from taming.pet import Release, command_kill, rename_pet
from taming.quarry import Hunt, is_pet
from uo.entity import find_mobile
from uo.guards import dead, first_reason, hurt, no_follower_slots, stopped
from uo.heartbeat import Heartbeat
from uo.log import make_log
from uo.loop import StallWatch, backoff_for
from uo.pace import Pace
from uo.record import attempt_log
from uo.retry import settled
from uo.save import SaveWatch
from uo.skill import SkillReader, reading
from uo.travel import chase, keep_up
from uo.vitals import position_and_weight

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

            elif outcome in GIVE_UP_REASON:
                done = GIVE_UP_REASON[outcome]

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
    recorder.close(skill.last())

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
