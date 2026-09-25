import API

from skills.config import (DATA_PATH, DELAY, HEARTBEAT_EVERY, PICK_TIMEOUT, READ_POLL,
                           READ_TIMEOUT, SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT, SAVING_TEXT,
                           SKILL_CHOICE, SKILLS, STOPPED, TARGET_TIMEOUT)
from skills.proof import flag_outcome, gump_outcome
from uo.choice import Choice
from uo.entity import hex_of, player
from uo.guards import dead, first_reason, skill_capped, stopped
from uo.heartbeat import Heartbeat
from uo.journal import read_outcome
from uo.log import make_log
from uo.record import attempt_log
from uo.save import SaveWatch
from uo.skill import SkillReader, find_skill_name, reading
from uo.target import request_one
from uo.vitals import position_and_weight

log = make_log("skills")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "attempts", position_and_weight)


def picking_reason():
    return first_reason([stopped(STOPPED), dead()])


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(skill_name)])


def hidden_flag():
    me = player()

    return bool(me.IsHidden) if me is not None else False


def caption_of(option):
    return option[1]


def target_gone(serial):
    return API.FindItem(serial) is None and API.FindMobile(serial) is None


def target_name(serial):
    found = API.FindItem(serial) or API.FindMobile(serial)

    return (found.Name if found is not None else None) or hex_of(serial)


chosen = Choice(SKILL_CHOICE, log, picking_reason).ask(
    sorted([(row["key"], row["caption"]) for row in SKILLS], key=caption_of))

if chosen is None:
    log("nothing chosen - stopping")
    API.Stop()

row = [row for row in SKILLS if row["key"] == chosen][0]
skill_name = find_skill_name(row["skills"]) or row["skills"][0]
skill = SkillReader(skill_name)
saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)
target = None
used = skill_name

if row["targets"]:
    log("target what to use %s on, ESC to stop" % row["caption"])
    target = request_one(PICK_TIMEOUT)

    if target is None:
        log("nothing targeted - stopping")
        API.Stop()

    used = target_name(target)

start = skill.read()
recorder = attempt_log(DATA_PATH, skill.name(), log)

if start is None:
    log("the client is not reporting %s - using it on '%s' anyway" % (skill_name, used))
else:
    log("using %s on '%s' - at %s/%s" % (skill.name(), used, reading(start), reading(skill.cap())))

succeeded = 0
failed = 0
others = {}
unread = 0
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
            continue

        if target is not None and target_gone(target):
            stop = "'%s' is gone" % used
            break

        value = skill.read()
        hidden_before = hidden_flag() if row["flag"] else False
        gump_before = API.HasGump() if row["gump"] else 0

        API.ClearJournal()
        API.UseSkill(skill_name)
        heartbeat.beat("using", cycle, succeeded + failed)

        # A refused use puts no cursor up, so this times out and the next pass simply asks again
        answered = True

        if target is not None:
            answered = bool(API.WaitForTarget("any", TARGET_TIMEOUT))

            if answered:
                API.Target(target)

        if answered:
            outcome = read_outcome(row["outcomes"], READ_TIMEOUT, READ_POLL)

            if outcome is None and row["flag"]:
                outcome = flag_outcome(hidden_before, hidden_flag())

            if row["gump"]:
                gump_after = API.HasGump()

                if outcome is None:
                    outcome = gump_outcome(gump_before, gump_after)

                if gump_after:
                    API.CloseGump(gump_after)

            if outcome == row["success"]:
                succeeded += 1
                recorder.record(value, outcome, used)

            elif outcome == row["failure"]:
                failed += 1
                recorder.record(value, outcome, used)

            elif outcome == "unskilled":
                stop = "the shard says this character cannot use %s" % skill_name

            elif outcome == "saving":
                saves.wait_out()

            elif outcome is None:
                unread += 1

            else:
                others[outcome] = others.get(outcome, 0) + 1

                if others[outcome] == 1:
                    log("the shard answered '%s' - not a roll, using again in %.1fs" % (outcome, DELAY))

        API.Pause(DELAY)
finally:
    recorder.close(skill.last())

ended = skill.read()

log("%d %s, %d %s, %s %s -> %s" % (succeeded, row["success"], failed, row["failure"],
                                    skill.name(), reading(start), reading(ended)))

for name in sorted(others):
    log("%d attempt(s) answered '%s' and were not recorded" % (others[name], name))

if unread > 0:
    log("%d outcome(s) went unread - add the shard's wording to SKILLS" % unread)

if stop is not None:
    log(stop)

API.Stop()
