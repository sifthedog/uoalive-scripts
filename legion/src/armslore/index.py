import API

from armslore.config import (DATA_PATH, DELAY, OUTCOME_TEXT, PICK_TIMEOUT, READ_POLL, READ_TIMEOUT,
                             SKILL, TARGET_TIMEOUT)
from uo.entity import hex_of
from uo.journal import read_outcome
from uo.log import make_log
from uo.record import attempt_log
from uo.skill import SkillReader, reading

log = make_log("arms-lore")
skill = SkillReader(SKILL)

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

while not API.StopRequested:
    value = skill.read()

    # The gain a reading earned lands here rather than at the reading: the client applies it some
    # time after the outcome, so the row waits a cycle for a value worth writing
    recorder.settle(value)

    cap = skill.cap()

    if value is not None and cap is not None and cap > 0 and value >= cap:
        log("%s is capped at %s" % (skill.name(), reading(value)))
        break

    if API.FindItem(weapon) is None:
        log("'%s' is gone - stopping" % name)
        break

    API.ClearJournal()
    API.UseSkill(SKILL)

    # A refused use puts no cursor up, so this times out and the next pass simply asks again
    if API.WaitForTarget("any", TARGET_TIMEOUT):
        API.Target(weapon)

        outcome = read_outcome(OUTCOME_TEXT, READ_TIMEOUT, READ_POLL)

        if outcome == "read":
            reads += 1
            recorder.record(value, outcome, name)

        # The roll happened and the shard said it did not go: that is the half of the data a tally
        # of reads alone cannot show
        elif outcome == "missed":
            missed += 1
            recorder.record(value, outcome, name)

        # Everything else - a refusal, a save, a wording OUTCOME_TEXT has not got - is left out of
        # the record rather than guessed at, and reported at the end so a wrong table is obvious
        else:
            unread += 1

    API.Pause(DELAY)

ended = skill.read()
recorder.settle(ended)

log("%d read, %d missed, %s %s -> %s"
    % (reads, missed, skill.name(), reading(start), reading(ended)))

if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to OUTCOME_TEXT" % unread)

API.Stop()
