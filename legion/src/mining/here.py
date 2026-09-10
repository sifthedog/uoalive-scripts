import API

from mining.config import (LOG_EVERY, MAX_CYCLES, MAX_NO_CURSOR, MAX_NO_TOOL, MAX_THROTTLED,
                           MAX_UNKNOWN, ORE_SETTLE_POLL, ORE_SETTLE_TIMEOUT, OUTCOME_TEXT,
                           PICK_BEETLE, STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)
from mining.dig import Digger
from mining.relieve import Relief
from mining.run import Run
from uo.loop import backoff_for
from uo.weight import too_heavy

run = Run("mine-here")

log = run.log
heartbeat = run.heartbeat
stall = run.stall
stop_reason = run.stop_reason
saves = run.saves
pickaxe = run.pickaxe
ore = run.ore
combiner = run.combiner
beetle = run.beetle
smelter = run.smelter
threat = run.threat
gathered = run.gathered
get_off_the_mount = run.get_off_the_mount
say_where_we_stand = run.say_where_we_stand

WORKED_OUT = "the spot is worked out"

# No pathfind to cancel: this run never walks, so a cancel here would only fight the player
digger = Digger(ore, OUTCOME_TEXT, run.dig_config, log, False)
relief = Relief(ore, combiner, smelter, saves, beetle.in_range,
                " - the beetle has to be standing next to you", log)

say_where_we_stand()

# Before the cursor, so the beetle you click is one standing next to you rather than the one you are
# sitting on
afoot = get_off_the_mount()

if PICK_BEETLE:
    beetle.pick()

# A pack that arrives full has no room for the first swing's ore. Smelting only once off the mount:
# a smelt aimed at the beetle you ride is silent, and three silent passes write the hue off.
combiner.group()

if afoot and too_heavy():
    relief.smelt()

stop = None
tally = 0
fails = 0
unknown = 0
throttled = 0
no_cursor = 0
no_tool = 0
reported = 0
cycle = 0


def end_cycle(phase):
    global stop

    stall.end_cycle(phase, cycle, tally)

    if stop is None:
        stop = stall.reason()


try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1

        stop = stop_reason()

        if stop is not None:
            break

        # Everything below reads a frozen shard as its own failure: a smelt that converts nothing is
        # ore that cannot be worked
        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        threat.look()

        # Asked every cycle, so a remount costs a single cycle instead of the rest of the run
        if not get_off_the_mount():
            stop = "could not get off the mount"
            break

        if not pickaxe.equip():
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = "no pickaxe"
                break

            log("no pickaxe (%d/%d), looking again" % (no_tool, MAX_NO_TOOL))
            end_cycle("no tool")
            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
            continue

        no_tool = 0

        relieved = relief.smelt_for_room()

        if relieved is not None:
            if isinstance(relieved, dict):
                stop = relieved["stop"]
                break

            end_cycle(relieved)
            API.Pause(STEP_DELAY)
            continue

        value = gathered.settle()
        before = gathered.before_swing()
        ore_before = ore.total()
        outcome = digger.dig_once(pickaxe.serial())

        if outcome == "dug":
            tally += 1
            unknown = 0
            throttled = 0
            stall.progressed()

            # Ore arrives as a new pile after the sentence that announced it, so grouping every
            # swing keeps the pack at one pile per metal and the item cap out of reach
            ore.wait_for_ore(ore_before, ORE_SETTLE_TIMEOUT, ORE_SETTLE_POLL)
            combiner.group()
            gathered.after_swing(value, "dug", before)

        elif outcome == "failed":
            tally += 1
            fails += 1
            unknown = 0
            throttled = 0
            stall.progressed()
            gathered.after_swing(value, "failed", before)

        elif outcome == "wornOut":
            log("pickaxe worn out, swapping")
            unknown = 0

        elif outcome == "saving":
            saves.wait_out()
            unknown = 0
            throttled = 0
            stall.progressed()

        elif outcome == "throttled":
            throttled += 1

            # A refusal is a read outcome, so it clears the unreadable count: left standing, a shard
            # alternating refusals with silence ends the run on MAX_UNKNOWN
            unknown = 0
            log("shard says wait (%d/%d), backing off" % (throttled, MAX_THROTTLED))
            API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

            if throttled >= MAX_THROTTLED:
                stop = "the shard kept refusing the swing"

        elif outcome == "noCursor":
            no_cursor += 1
            log("no target cursor (%d/%d), backing off" % (no_cursor, MAX_NO_CURSOR))
            API.Pause(backoff_for(no_cursor, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

            if no_cursor >= MAX_NO_CURSOR:
                stop = "the shard never opened a target cursor"

        # One branch, not two: the pair differ by scope, and scope only matters to a run with
        # somewhere else to walk
        elif outcome == "empty" or outcome == "nothingNearby":
            unknown = 0
            combiner.group()
            relief.smelt()
            stop = WORKED_OUT

        # No art to ban and nowhere to walk, so it is an ending
        elif outcome == "notOre":
            unknown = 0
            stop = "nothing here can be mined"

        # Neither is answerable by moving, and this run does not move
        elif outcome == "tooFar":
            unknown = 0
            stop = "the shard says the ore is out of reach from where you are standing"

        elif outcome == "notSeen":
            unknown = 0
            stop = "the shard cannot see the ore from where you are standing"

        # The ore this swing produced was destroyed rather than dropped, so a full pack is answered
        # by consolidating: forty piles of one become one pile of forty
        elif outcome == "packFull":
            unknown = 0
            log("pack is full, consolidating before the next swing")
            combiner.group()

        else:
            unknown += 1
            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        # Done here rather than inside each branch the way unknown is: every branch but one clears
        # it, and one added later would have to remember to
        if outcome != "noCursor":
            no_cursor = 0

        if unknown >= MAX_UNKNOWN:
            stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
            break

        if tally >= reported + LOG_EVERY:
            reported = tally
            log(
                "%d swings, %d ore, %d/%d"
                % (tally, ore.total(), API.Player.Weight, API.Player.WeightMax)
            )

        end_cycle(outcome if outcome is not None else "unknown")
        API.Pause(STEP_DELAY)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error

reason = stop or "hit the %d working cycle backstop" % MAX_CYCLES

# Smelted only if the run is ending over the limit: what is in the pack is a few swings' worth
combiner.group()

if too_heavy():
    relief.smelt()

gathered.settle()

# Swings rather than an ore delta: smelted ore has left the pack, so the pack cannot total the run
log("%d swings, %d failed, %d ore still in the pack" % (tally, fails, ore.total()))

if reason == WORKED_OUT and tally == 0:
    log("no swing ever landed - the character is probably not standing next to a vein")
log("stopping - %s" % reason)
API.Stop()
