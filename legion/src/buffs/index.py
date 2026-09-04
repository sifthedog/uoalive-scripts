import API

from buffs.bar import BuffBar, armed
from buffs.cast import cast_once
from buffs.config import (CAST_DELAY, CAST_TIMEOUT, CAST_WAIT_SLICE, HEARTBEAT_EVERY, KEEP, KEEP_UP,
                          LOG_EVERY, MAX_CYCLES, MAX_MISSES, MAX_THROTTLED, OUTCOME_TEXT, POLL,
                          SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT, SAVING_TEXT, SET_ASIDE, STOPPED,
                          THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)
from buffs.schedule import due, make_table, retire, set_aside, settled, spent
from uo.guards import dead, first_reason, stopped
from uo.heartbeat import Heartbeat
from uo.log import make_log
from uo.loop import backoff_for
from uo.save import SaveWatch
from uo.vitals import position_and_mana

log = make_log("buffs")
bar = BuffBar(log)
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "casts", position_and_mana)


def stop_reason():
    return first_reason([stopped(STOPPED), dead()])


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

table = make_table(KEEP)

casts = 0
reported = 0
throttled = 0
stop = None

# Said once per stretch rather than once per pass, or an unarmed character scrolls the journal at
# POLL for as long as they stay unarmed
said_unarmed = False
said_short = False
said_untithed = False

proved = set()


# The first cast of each spell, so a wrong OUTCOME_TEXT or a wrong buff id shows up in the first
# minute rather than as a run that quietly never casts
def say_first(item):
    if item["name"] in proved:
        return

    proved.add(item["name"])
    log("%s up" % item["name"])


def back_off():
    global throttled, stop

    throttled += 1

    if throttled >= MAX_THROTTLED:
        stop = "the shard refused %d casts in a row" % MAX_THROTTLED
        return

    API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))


def put_up(item):
    global casts, throttled

    outcome = cast_once(item["entry"], bar, OUTCOME_TEXT, CAST_TIMEOUT, CAST_WAIT_SLICE)

    if outcome == "cast":
        casts += 1
        throttled = 0
        item["misses"] = 0
        say_first(item)

    # The shard answered, so the table is right and the roll simply lost. Next pass tries again.
    elif outcome in ("fizzled", "alreadyUp"):
        throttled = 0
        item["misses"] = 0

    # The gate above cleared, so this entry's mana figure is understated for this shard
    elif outcome == "noMana":
        item["misses"] = 0
        log(
            "%s costs more than %d mana here - raise it in KEEP"
            % (item["name"], item["entry"]["mana"])
        )

    # Nothing a script does refills tithing points, so this entry is finished for the run
    elif outcome == "noTithing":
        retire(item, "out of tithing points - tithe gold at a shrine")

    elif outcome == "unskilled":
        retire(item, "the shard refuses it at this skill or karma")

    # The hand check above missed it, so believe the shard rather than the client's layers
    elif outcome == "noWeapon":
        set_aside(item, SET_ASIDE)

    elif outcome == "saving":
        saves.wait_out()

    elif outcome in ("cooldown", "throttled", "alreadyCasting"):
        back_off()

    # Nothing said, no buff, and no mana left the pool: whatever this was, it did not happen
    else:
        item["misses"] += 1

        if item["misses"] >= MAX_MISSES:
            set_aside(item, SET_ASIDE)
            log(
                "%s did nothing %d times - set aside; check OUTCOME_TEXT"
                % (item["name"], MAX_MISSES)
            )


def one_pass():
    global said_unarmed, said_short, said_untithed

    hands = armed()

    if hands:
        said_unarmed = False

    for item in table:
        if stop is not None or not due(item):
            continue

        if bar.standing(item["entry"]):
            item["misses"] = 0
            continue

        entry = item["entry"]

        if entry.get("needs_weapon") and not hands:
            if not said_unarmed:
                said_unarmed = True
                log("nothing in hand - %s is waiting for you to draw something" % item["name"])

            continue

        if API.Player.Mana < entry["mana"]:
            if not said_short:
                said_short = True
                log(
                    "%d/%d mana for %s - waiting for it"
                    % (API.Player.Mana, entry["mana"], item["name"])
                )

            continue

        said_short = False

        # Not in the ClassicUO run, which had no tithing gate: a noTithing retires the entry for the
        # whole run, so a character who forgot to tithe would lose every buff on the first pass
        if API.Player.TithingPoints < entry["tithing"]:
            if not said_untithed:
                said_untithed = True
                log(
                    "%d/%d tithing points for %s - tithe gold at a shrine"
                    % (API.Player.TithingPoints, entry["tithing"], item["name"])
                )

            continue

        said_untithed = False

        put_up(item)
        API.Pause(CAST_DELAY)


log("keeping %s up" % " and ".join(item["name"] for item in table))

if not armed() and any(item["entry"].get("needs_weapon") for item in table):
    log("nothing in hand - the weapon enchants will be refused until you draw something")

log("%d tithing points; every cast spends some, tithe gold at a shrine" % API.Player.TithingPoints)

for cycle in range(MAX_CYCLES):
    if stop is not None:
        break

    stop = stop_reason()

    if stop is not None:
        break

    if saves.is_saving():
        saves.wait_out()
        continue

    one_pass()

    if stop is not None:
        break

    if spent(table):
        stop = "every buff was refused for good"
        break

    if not KEEP_UP and settled(table, bar.standing):
        stop = "everything that could go up is up"
        break

    if casts >= reported + LOG_EVERY:
        reported = casts
        log("%d casts, %d/%d mana" % (casts, API.Player.Mana, API.Player.ManaMax))

    heartbeat.beat("watching the buff bar", cycle, casts)
    API.Pause(POLL)

for item in table:
    if item["retired"] is not None:
        log("%s was set aside - %s" % (item["name"], item["retired"]))

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES

log("%d casts, stopping - %s" % (casts, reason))
API.Stop()
