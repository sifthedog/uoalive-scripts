import API

from lockpicking.config import (BOX_GRAPHIC, BOX_HUE, BOX_RANGE, DATA_PATH, DELAY,
                                HEARTBEAT_EVERY, LOCKPICK_GRAPHIC, MAX_THROTTLED, OUTCOME_TEXT,
                                READ_POLL, READ_TIMEOUT, SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT,
                                SAVING_TEXT, SET_TEXT, SET_TIMEOUT, SKILL, STOPPED, TARGET_TIMEOUT,
                                THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)
from uo.guards import dead, first_reason, skill_capped, stopped
from uo.heartbeat import Heartbeat
from uo.journal import read_outcome
from uo.log import make_log
from uo.loop import backoff_for
from uo.pack import pack_contents
from uo.record import attempt_log
from uo.save import SaveWatch
from uo.skill import SkillReader, reading
from uo.vitals import position_and_weight

log = make_log("lockpicking")
skill = SkillReader(SKILL)
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "picks", position_and_weight)

SET_BUCKET = [("set", SET_TEXT)]


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(SKILL)])


# API.FindType answers None for a world item on this build - it did not see this chest one tile
# away with every filter off - so the ground is read instead. The nearest wins: the training room
# stands them two tiles apart, and the far one is picked at out of reach
def training_box():
    boxes = [item for item in API.GetItemsOnGround(BOX_RANGE, BOX_GRAPHIC) or []
             if item.Hue == BOX_HUE]

    return min(boxes, key=box_distance) if boxes else None


def box_distance(box):
    return box.Distance


def lockpick():
    for item in pack_contents():
        if item.Graphic == LOCKPICK_GRAPHIC:
            return item

    return None


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

# A cursor left open by whatever ran last would swallow the first pick
if API.HasTarget():
    API.CancelTarget()

start = skill.read()
recorder = attempt_log(DATA_PATH, skill.name(), log)

if start is None:
    log("the client is not reporting %s - picking anyway" % SKILL)
else:
    log("picking - %s at %s/%s" % (skill.name(), reading(start), reading(skill.cap())))

picked = 0
failed = 0
unread = 0
unset = 0
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

        box = training_box()

        if box is None:
            stop = "no training box within %d tiles" % BOX_RANGE
            break

        pick = lockpick()

        if pick is None:
            stop = "no lockpicks left in the pack"
            break

        # The double-click is what re-rolls the box to your skill. It is not an attempt and is
        # never recorded; a box that does not answer keeps whatever level it already held
        API.ClearJournal()
        API.UseObject(box.Serial)

        if read_outcome(SET_BUCKET, SET_TIMEOUT, READ_POLL) is None:
            unset += 1

            if unset == 1:
                log("the box did not say it was set - picking it as it stands")

        value = skill.read()

        API.ClearJournal()
        API.UseObject(pick.Serial)
        heartbeat.beat("picking", cycle, picked + failed)

        # A refused use puts no cursor up, so this times out and the next pass simply asks again
        if API.WaitForTarget("any", TARGET_TIMEOUT):
            API.Target(box.Serial)

            outcome = read_outcome(OUTCOME_TEXT, READ_TIMEOUT, READ_POLL)

            if outcome != "throttled":
                throttled = 0

            if outcome == "picked":
                picked += 1
                recorder.record(value, outcome, "lockpick")

            elif outcome == "failed":
                failed += 1
                recorder.record(value, outcome, "lockpick")

            elif outcome == "unskilled":
                stop = "the shard says this character cannot use %s" % SKILL

            # Caught here as well as by the proactive check above: a save can start between the
            # clear and the read
            elif outcome == "saving":
                saves.wait_out()

            elif outcome == "throttled":
                throttled += 1
                log("shard says wait (%d/%d), backing off" % (throttled, MAX_THROTTLED))
                API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

                if throttled >= MAX_THROTTLED:
                    stop = "the shard kept refusing the pick"

            # A refusal this table has no bucket for, or a wording OUTCOME_TEXT has not got, is left
            # out of the record rather than guessed at, and reported at the end
            else:
                unread += 1

        API.Pause(DELAY)
finally:
    recorder.close(skill.last())

ended = skill.read()

log("%d picked, %d failed, %s %s -> %s"
    % (picked, failed, skill.name(), reading(start), reading(ended)))

if unset > 0:
    log("%d box double-click(s) went unanswered" % unset)

if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to OUTCOME_TEXT" % unread)

if stop is not None:
    log(stop)

API.Stop()
