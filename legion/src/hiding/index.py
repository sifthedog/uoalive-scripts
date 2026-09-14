import API

from hiding.config import (DATA_PATH, HEARTBEAT_EVERY, MAX_THROTTLED, OUTCOME_TEXT, PACE_EASE_AFTER,
                           PACE_FLOOR, PACE_MAX, PACE_STEP, READ_POLL, READ_TIMEOUT, SAVE_DONE_TEXT,
                           SAVE_POLL, SAVE_WAIT, SAVING_TEXT, SKILL, STOPPED, THROTTLE_BACKOFF,
                           THROTTLE_BACKOFF_MAX)
from hiding.proof import flag_outcome
from uo.entity import player
from uo.guards import dead, first_reason, skill_capped, stopped
from uo.heartbeat import Heartbeat
from uo.journal import read_outcome
from uo.log import make_log
from uo.loop import backoff_for
from uo.pace import Pace
from uo.record import attempt_log
from uo.save import SaveWatch
from uo.skill import SkillReader, reading
from uo.vitals import position_and_weight

log = make_log("hiding")
skill = SkillReader(SKILL)
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "attempts", position_and_weight)
pace = Pace(PACE_FLOOR, PACE_STEP, PACE_MAX, PACE_EASE_AFTER)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(SKILL)])


def hidden_flag():
    me = player()

    return bool(me.IsHidden) if me is not None else False


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

start = skill.read()
recorder = attempt_log(DATA_PATH, skill.name(), log)

if start is None:
    log("the client is not reporting %s - hiding anyway" % SKILL)
else:
    log("hiding - %s at %s/%s" % (skill.name(), reading(start), reading(skill.cap())))

hidden = 0
failed = 0
busy = 0
unread = 0
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

        value = skill.read()
        before = hidden_flag()

        API.ClearJournal()
        API.UseSkill(SKILL)
        heartbeat.beat("hiding", cycle, hidden + failed)

        outcome = read_outcome(OUTCOME_TEXT, READ_TIMEOUT, READ_POLL)

        if outcome is None:
            outcome = flag_outcome(before, hidden_flag())

        if outcome != "throttled":
            throttled = 0

        if outcome == "hidden":
            hidden += 1
            recorder.record(value, outcome, SKILL)
            pace.landed()

        elif outcome == "failed":
            failed += 1
            recorder.record(value, outcome, SKILL)
            pace.landed()

        # No roll: fighting or casting. Nothing to record
        elif outcome == "busy":
            busy += 1

            if busy == 1:
                log("the shard says you cannot hide right now - trying again each cycle")

        elif outcome == "unskilled":
            stop = "the shard says this character cannot use %s" % SKILL

        elif outcome == "saving":
            saves.wait_out()

        elif outcome == "throttled":
            throttled += 1
            log("shard says wait (%d/%d), now pacing at %.1fs"
                % (throttled, MAX_THROTTLED, pace.refused()))
            API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

            if throttled >= MAX_THROTTLED:
                stop = "the shard kept refusing the attempt"

        else:
            unread += 1

        API.Pause(pace.delay())
finally:
    recorder.close(skill.last())

ended = skill.read()

log("%d hidden, %d failed, %s %s -> %s"
    % (hidden, failed, skill.name(), reading(start), reading(ended)))

if busy > 0:
    log("%d attempt(s) refused for being busy" % busy)

if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to OUTCOME_TEXT" % unread)

if stop is not None:
    log(stop)

API.Stop()
