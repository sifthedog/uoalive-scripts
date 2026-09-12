import API

from mining.config import (LOG_EVERY, MAP_PATH, MAX_CYCLES, MAX_NO_CURSOR, MAX_NO_TOOL,
                           MAX_THROTTLED, MAX_UNKNOWN, MAX_VEIN_WALKS, MAX_PATH_PROBES, MIN_SPOT_ORE,
                           MINE_FOOTPRINT, MINE_Z_RANGE, NOT_ORE_GRAPHICS, NOTHING_NEARBY_HINT,
                           ONLY_CONNECTED_GROUND,
                           ORE_SETTLE_POLL, ORE_SETTLE_TIMEOUT, ORE_STATIC_NAME, ORE_TILE_GRAPHICS,
                           OUTCOME_TEXT, PARKED_PATH, PATHFIND_TIMEOUT, PICK_BEETLE, PLAN_MAP,
                           RESPAWN_DELAY, SCAN_RADIUS, SLOW_CYCLE, STAND_RANGE, STEP_DELAY,
                           STOP_WHEN_WORKED_OUT, SURVEY_ARTS,
                           THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX, UNREACHABLE_DELAY,
                           IDLE_LOG_EVERY, IDLE_POLL)
from mining.dig import Digger
from mining.plan import Planner
from mining.relieve import Relief
from mining.run import Run
from mining.vein import Veins
from uo.clock import now
from uo.loop import backoff_for
from uo.mapfile import MapFile
from uo.parked import Parked
from uo.roam import Roam
from uo.store import Store
from uo.tiles import TileMemory
from uo.terrain import Terrain
from uo.weight import too_heavy

run = Run("mining")

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

terrain = Terrain()
map_file = MapFile(terrain, Store(MAP_PATH, log), log)
parked = Parked(Store(PARKED_PATH, log), log)
memory = TileMemory(RESPAWN_DELAY, UNREACHABLE_DELAY, "vein", "mined", log, parked.save)
spots = TileMemory(RESPAWN_DELAY, UNREACHABLE_DELAY, "spot", "stood on", log)
veins = Veins(terrain, memory, {
    "tile_graphics": ORE_TILE_GRAPHICS,
    "not_ore_graphics": NOT_ORE_GRAPHICS,
    "static_names": ORE_STATIC_NAME,
    "z_range": MINE_Z_RANGE,
}, log)
planner = Planner(veins, terrain, memory, spots, {
    "reach": MINE_FOOTPRINT,
    "scan_radius": SCAN_RADIUS,
    "probes": MAX_PATH_PROBES,
    "min_ore": MIN_SPOT_ORE,
    "connected": ONLY_CONNECTED_GROUND,
    "map": PLAN_MAP,
    "respawn_delay": RESPAWN_DELAY,
}, log)
roam = Roam(planner, spots, saves, threat, {
    "noun": "spot",
    "idle_message": "everything in reach is worked out, waiting for a vein to come back",
    "none_left": "no ore in range",
    "wait": not STOP_WHEN_WORKED_OUT,
    "worked_out": "the ground you stand on is worked out",
    "range": STAND_RANGE,
    "scan_radius": SCAN_RADIUS,
    "z_range": MINE_Z_RANGE,
    "survey_arts": SURVEY_ARTS,
    "max_walks": MAX_VEIN_WALKS,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "idle_poll": IDLE_POLL,
    "idle_log_every": IDLE_LOG_EVERY,
}, log, heartbeat, stop_reason)
digger = Digger(ore, OUTCOME_TEXT, run.dig_config, log, True)
relief = Relief(ore, combiner, smelter, saves, beetle.walk_to, "", log)

say_where_we_stand()
map_file.load()
parked.load(memory)

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
idled = 0
reported = 0
barren = 0
cycle = 0
cycle_started = now()
spent = {}


def describe_spent():
    parts = []

    if "walk" in spent:
        scan = planner.stats
        parts.append("scan %.1fs (%d reads, %d probes, %d walled), walk %.1fs"
                     % (scan.get("seconds", 0.0), scan.get("reads", 0), scan.get("probes", 0),
                        scan.get("walled", 0), spent["walk"]))

    for name in ["smelt", "dig", "after"]:
        if spent.get(name, 0.0) >= 0.1:
            parts.append("%s %.1fs" % (name, spent[name]))

    return ", ".join(parts) or "nothing timed"


def end_cycle(phase):
    global stop

    stall.end_cycle(phase, cycle, tally)
    total = now() - cycle_started

    if total >= SLOW_CYCLE:
        log("slow cycle, %.1fs - %s" % (total, describe_spent()))

    if stop is None:
        stop = stall.reason()


try:
    while stop is None and cycle - idled < MAX_CYCLES:
        cycle += 1
        cycle_started = now()
        spent.clear()

        stop = stop_reason()

        if stop is not None:
            break

        # Everything below reads a frozen shard as its own failure: a step that does not move is a
        # wall, a smelt that converts nothing is ore that cannot be worked
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

        started = now()
        relieved = relief.smelt_for_room()
        spent["smelt"] = now() - started

        if relieved is not None:
            if isinstance(relieved, dict):
                stop = relieved["stop"]
                break

            end_cycle(relieved)
            API.Pause(STEP_DELAY)
            continue

        started = now()
        found = roam.approach()
        spent["walk"] = now() - started - planner.stats.get("seconds", 0.0)
        map_file.flush()

        if found[0] == "stop":
            stop = found[1]
            break

        # No pause: a resource coming back has already waited out its own clock, and a wait is the
        # script working rather than stalling
        if found[0] == "waited":
            idled += 1
            stall.progressed()
            continue

        if found[0] == "walked":
            end_cycle("walking")
            continue

        spot = found[1]

        value = gathered.read()
        before = gathered.before_swing()
        ore_before = ore.total()
        started = now()
        outcome = digger.dig_once(pickaxe.serial())
        spent["dig"] = now() - started
        started = now()

        if outcome == "dug":
            tally += 1
            unknown = 0
            throttled = 0
            barren = 0
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
            barren = 0
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

        # Both are about the footprint you stand in, and neither is dead: the parking times out
        elif outcome == "empty" or outcome == "nothingNearby":
            unknown = 0
            planner.exhausted()
            barren += 1
            relief.group_and_smelt()

        # The swing named no tile, so the refused art is only known when the footprint holds one
        elif outcome == "notOre":
            unknown = 0
            lone = planner.lone_ore_art()

            if lone is not None:
                memory.ban_art(lone)

            spots.mark_unusable(spot, "cannot be mined from")
            barren += 1

        elif outcome == "tooFar":
            unknown = 0
            spots.mark_unusable(spot, "is out of reach")

        elif outcome == "notSeen":
            unknown = 0
            spots.mark_unusable(spot, "is not in line of sight")

        # The ore this swing produced was destroyed rather than dropped, so a full pack is answered
        # by consolidating: forty piles of one become one pile of forty
        elif outcome == "packFull":
            unknown = 0
            log("pack is full, consolidating before the next swing")
            combiner.group()

        else:
            unknown += 1
            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        # Said once, at the point it stops looking like bad luck
        if barren == NOTHING_NEARBY_HINT:
            log(
                "%d spots in a row had nothing to mine - ORE_TILE_GRAPHICS is probably matching "
                "ground that carries no ore, or the shard refuses a self-target"
                % NOTHING_NEARBY_HINT
            )
            planner.survey(MINE_FOOTPRINT, SURVEY_ARTS)

        # Done here rather than inside each branch the way unknown is: every branch but one clears
        # it, and one added later would have to remember to
        if outcome != "noCursor":
            no_cursor = 0

        if unknown >= MAX_UNKNOWN:
            stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
            break

        spent["after"] = now() - started

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
finally:
    gathered.close()

if API.Pathfinding():
    API.CancelPathfinding()

map_file.flush()
reason = stop or "hit the %d working cycle backstop" % MAX_CYCLES

# Smelted only if the run is ending over the limit: what is in the pack is a few swings' worth
combiner.group()

if too_heavy():
    relief.smelt()

# Closed again: a conversion after the loop records a row the close above did not see
gathered.close()

# Swings rather than an ore delta: smelted ore has left the pack, so the pack cannot total the run
log("%d swings, %d failed, %d ore still in the pack" % (tally, fails, ore.total()))
log("stopping - %s" % reason)
API.Stop()
