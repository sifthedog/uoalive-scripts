# Built from src/armslore/index.py by build.py - do not edit.

import API


# src/armslore/config.py
# API.Pause takes seconds where the ClassicUO port took ms
DELAY = 0.5

PICK_TIMEOUT = 30.0
TARGET_TIMEOUT = 1.0

SKILL = "Arms Lore"


# src/uo/entity.py
def hex_of(value):
    return "0x%x" % (value & 0xFFFFFFFF)


# src/uo/log.py
def make_log(prefix):
    def log(message):
        API.SysMsg(prefix + ": " + message)

    return log


# src/armslore/index.py
log = make_log("arms-lore")

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

skill = API.GetSkill(SKILL)
start = skill.Value if skill is not None else 0.0

if skill is None:
    log("the client is not reporting %s - reading '%s' anyway" % (SKILL, name))
else:
    log("reading '%s' - %s at %.1f/%.1f" % (name, SKILL, skill.Value, skill.Cap))

reads = 0

while not API.StopRequested:
    skill = API.GetSkill(SKILL)

    if skill is not None and skill.Value >= skill.Cap:
        log("%s is capped at %.1f" % (SKILL, skill.Value))
        break

    if API.FindItem(weapon) is None:
        log("'%s' is gone - stopping" % name)
        break

    API.UseSkill(SKILL)

    # A refused use puts no cursor up, so this times out and the next pass simply asks again
    if API.WaitForTarget("any", TARGET_TIMEOUT):
        API.Target(weapon)
        reads += 1

    API.Pause(DELAY)

ended = API.GetSkill(SKILL)

log("%d reads, %s %.1f -> %.1f" % (reads, SKILL, start, ended.Value if ended is not None else start))
API.Stop()
