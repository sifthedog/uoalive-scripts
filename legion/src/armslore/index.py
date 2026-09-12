import API

from armslore.config import (DATA_PATH, DELAY, HEARTBEAT_EVERY, MAX_THROTTLED, OUTCOME_TEXT,
                             PICK_TIMEOUT, READ_POLL, READ_TIMEOUT, SAVE_DONE_TEXT, SAVE_POLL,
                             SAVE_WAIT, SAVING_TEXT, SKILL, STOPPED, TARGET_TIMEOUT,
                             THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)
from uo.entity import hex_of
from uo.guards import dead, first_reason, skill_capped, stopped
from uo.heartbeat import Heartbeat
from uo.journal import read_outcome
from uo.log import make_log
from uo.loop import backoff_for
from uo.record import attempt_log
from uo.save import SaveWatch
from uo.skill import SkillReader, reading
from uo.vitals import position_and_weight

log = make_log("arms-lore")
skill = SkillReader(SKILL)
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "reads", position_and_weight)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(SKILL)])


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

# A cursor left open by whatever ran last would swallow this query
if API.HasTarget():
    API.CancelTarget()

log("target the weapon to read, ESC to stop")

weapon = API.RequestTarget(PICK_TIMEOUT)

if not weapon:
    if API.HasTarget():
        API.CancelTarget()

    log("nothing targeted - stopping")
    API.Stop()

item = API.FindItem(weapon)
name = (item.Name if item is not None else None) or hex_of(weapon)

start = skill.read()
recorder = attempt_log(DATA_PATH, skill.name(), log)

if start is None:
    log("the client is not reporting %s - reading '%s' anyway" % (SKILL, name))
else:
    log("reading '%s' - %s at %s/%s" % (name, skill.name(), reading(start), reading(skill.cap())))

reads = 0
missed = 0
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

        if API.FindItem(weapon) is None:
            stop = "'%s' is gone" % name
            break

        value = skill.read()

        API.ClearJournal()
        API.UseSkill(SKILL)
        heartbeat.beat("reading", cycle, reads)

        # A refused use puts no cursor up, so this times out and the next pass simply asks again
        if API.WaitForTarget("any", TARGET_TIMEOUT):
            API.Target(weapon)

            outcome = read_outcome(OUTCOME_TEXT, READ_TIMEOUT, READ_POLL)

            if outcome != "throttled":
                throttled = 0

            if outcome == "read":
                reads += 1
                recorder.record(value, outcome, name)

            # The roll happened and the shard said it did not go: that is the half of the data a
            # tally of reads alone cannot show
            elif outcome == "missed":
                missed += 1
                recorder.record(value, outcome, name)

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
                    stop = "the shard kept refusing the read"

            # Everything else - a refusal this table has no bucket for, or a wording OUTCOME_TEXT
            # has not got - is left out of the record rather than guessed at, and reported at the
            # end so a wrong table is obvious
            else:
                unread += 1

        API.Pause(DELAY)
finally:
    recorder.close(skill.last())

ended = skill.read()

log("%d read, %d missed, %s %s -> %s"
    % (reads, missed, skill.name(), reading(start), reading(ended)))

if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to OUTCOME_TEXT" % unread)

if stop is not None:
    log(stop)

API.Stop()
