import API

from lumberjacking.boards import Boards
from lumberjacking.chop import Chopper
from lumberjacking.config import (AIM_AT_SELF, ANIMAL_SCAN_RADIUS, ATTACK_TEXT, AXE_NAMES,
                                  BOARD_GRAPHICS, BOARD_NAME_WORDS, CHOP_PROMPT_TEXT, CHOP_RANGE,
                                  CHOP_TARGET_POLL, CHOP_TARGET_TIMEOUT, CHOP_TIMEOUT, CHOP_Z_RANGE,
                                  CONVERT_ATTEMPTS, CONVERT_DELAY, CONVERT_POLL, CONVERT_TIMEOUT,
                                  EMPTY_HINT, EQUIP_ATTEMPTS, EQUIP_POLL, EQUIP_TIMEOUT,
                                  GUARD_CALL, GUARD_CALL_DELAY, GUARD_CALLS, GUARD_REPLY_WAIT,
                                  GUARD_ZONE_TEXT, HAUL_BUFFER, HEARTBEAT_EVERY, IDLE_LOG_EVERY,
                                  IDLE_POLL, LOG_EVERY, LOG_GRAPHICS, LOG_NAME_WORDS,
                                  MAX_CONVERT_PASSES, MAX_CYCLES, MAX_EMPTY_HAULS, MAX_NO_CURSOR,
                                  MAX_NO_TOOL, MAX_PATH_PROBES, MAX_PICKS, MAX_THROTTLED,
                                  MAX_TREE_WALKS, MAX_UNKNOWN, MOVE_DELAY, NO_CURSOR_READ,
                                  NO_GUARDS_TEXT, NOT_AXE_NAMES, NOT_TREE_GRAPHICS,
                                  OUTCOME_TEXT, PACK_ANIMAL_GRAPHICS, PACK_ANIMAL_SERIALS,
                                  PACK_LIMIT, PATHFIND_TIMEOUT, PICK_PACK_ANIMALS, PICK_TIMEOUT,
                                  REGROW_DELAY, ROAM_RADIUS, SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT,
                                  SAVING_TEXT, SCAN_RADIUS, SPARE_BAG_SERIAL, STALL_STOP,
                                  STALL_WARN, STEP_DELAY, STOPPED, SURVEY_ARTS, TARGET_TIMEOUT,
                                  THREAT_RANGE, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX,
                                  THROTTLED_TEXT, TREE_GRAPHICS, TREE_NAME, UNGUARDED_TEXT,
                                  UNLOAD_RANGE, UNREACHABLE_DELAY, UNSKILLED_TEXT,
                                  WATCH_FOR_TROUBLE, WEIGHT_BUFFER)
from lumberjacking.haul import Haul
from lumberjacking.trees import Trees
from lumberjacking.wood import Wood
from uo.entity import hex_of
from uo.guards import dead, first_reason, overweight, pack_full, stopped
from uo.heartbeat import Heartbeat
from uo.log import make_log
from uo.loop import StallWatch, backoff_for
from uo.roam import Roam
from uo.save import SaveWatch
from uo.threat import ThreatWatch
from uo.tiles import TileMemory
from uo.tool import Tool
from uo.vitals import position_and_weight

log = make_log("lumberjack")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "chops", position_and_weight)
stall = StallWatch("cycles without a chop", STALL_WARN, STALL_STOP, heartbeat, log)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), overweight(WEIGHT_BUFFER),
                         pack_full(PACK_LIMIT)])


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

axe = Tool("axe", AXE_NAMES, NOT_AXE_NAMES, ["twohanded", "onehanded"], SPARE_BAG_SERIAL,
           EQUIP_ATTEMPTS, EQUIP_TIMEOUT, EQUIP_POLL, log)
wood = Wood(LOG_GRAPHICS, LOG_NAME_WORDS, BOARD_GRAPHICS, BOARD_NAME_WORDS, log)
boards = Boards(wood, axe, saves, {
    "attempts": CONVERT_ATTEMPTS,
    "passes": MAX_CONVERT_PASSES,
    "delay": CONVERT_DELAY,
    "timeout": CONVERT_TIMEOUT,
    "poll": CONVERT_POLL,
    "target_timeout": TARGET_TIMEOUT,
    "log_graphics": LOG_GRAPHICS,
    "board_graphics": BOARD_GRAPHICS,
    "throttled_text": THROTTLED_TEXT,
    "unskilled_text": UNSKILLED_TEXT,
}, log)
haul = Haul(wood, boards, saves, {
    "serials": PACK_ANIMAL_SERIALS,
    "graphics": PACK_ANIMAL_GRAPHICS,
    "radius": ANIMAL_SCAN_RADIUS,
    "unload_range": UNLOAD_RANGE,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "move_delay": MOVE_DELAY,
    "max_picks": MAX_PICKS,
    "pick_timeout": PICK_TIMEOUT,
    "buffer": HAUL_BUFFER,
    "max_empty_hauls": MAX_EMPTY_HAULS,
}, log)
memory = TileMemory(REGROW_DELAY, UNREACHABLE_DELAY, "tree", "chopped", log)
trees = Trees(memory, {
    "graphics": TREE_GRAPHICS,
    "not_graphics": NOT_TREE_GRAPHICS,
    "names": TREE_NAME,
    "z_range": CHOP_Z_RANGE,
    "range": CHOP_RANGE,
    "scan_radius": SCAN_RADIUS,
    "roam_radius": ROAM_RADIUS,
    "probes": MAX_PATH_PROBES,
    "regrow_delay": REGROW_DELAY,
}, log)
threat = ThreatWatch({
    "watch": WATCH_FOR_TROUBLE,
    "range": THREAT_RANGE,
    "call": GUARD_CALL,
    "calls": GUARD_CALLS,
    "call_delay": GUARD_CALL_DELAY,
    "reply_wait": GUARD_REPLY_WAIT,
    "no_guards_text": NO_GUARDS_TEXT,
    "zone_text": GUARD_ZONE_TEXT,
    "unguarded_text": UNGUARDED_TEXT,
    "attack_text": ATTACK_TEXT,
}, log, haul.companion, lambda friend: "'%s'" % (friend.Name or "?"))
roam = Roam(trees, memory, saves, threat, {
    "noun": "tree",
    "idle_message": "everything in reach is regrowing, waiting for the soonest one",
    "none_left": "no tree in range",
    "range": CHOP_RANGE,
    "scan_radius": SCAN_RADIUS,
    "z_range": CHOP_Z_RANGE,
    "survey_arts": SURVEY_ARTS,
    "max_walks": MAX_TREE_WALKS,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "idle_poll": IDLE_POLL,
    "idle_log_every": IDLE_LOG_EVERY,
}, log, heartbeat, stop_reason)
chopper = Chopper(wood, axe, OUTCOME_TEXT, {
    "cursor_timeout": CHOP_TARGET_TIMEOUT,
    "cursor_poll": CHOP_TARGET_POLL,
    "prompt_text": CHOP_PROMPT_TEXT,
    "no_cursor_read": NO_CURSOR_READ,
    "chop_timeout": CHOP_TIMEOUT,
    "aim_at_self": AIM_AT_SELF,
}, log)

axe.learn(axe.held())

log("%d logs in the pack to start, at %d,%d" % (wood.log_total(), API.Player.X, API.Player.Y))

# Read before anything acts, or a run that stops on its first cycle looks exactly like a script that
# never started
held = axe.held()
log(
    "mounted %s, hand %s, weight %d/%d, aiming %s"
    % (
        "yes" if API.Player.IsMounted else "no",
        (held.Name or hex_of(held.Graphic)) if held is not None else "empty",
        API.Player.Weight,
        API.Player.WeightMax,
        "at yourself" if AIM_AT_SELF else "at the tree",
    )
)

if PICK_PACK_ANIMALS:
    haul.pick()

# A pack pasted in already over the buffer would otherwise be stopped on cycle zero by the weight
# guard, before a haul had ever had its turn
haul.haul_for_room()

stop = None
tally = 0
unknown = 0
throttled = 0
no_cursor = 0
no_tool = 0
idled = 0
reported = 0
barren = 0
cycle = 0


def end_cycle(phase):
    global stop

    stall.end_cycle(phase, cycle, tally)

    if stop is None:
        stop = stall.reason()


try:
    while stop is None and cycle - idled < MAX_CYCLES:
        cycle += 1

        stop = stop_reason()

        if stop is not None:
            break

        # Everything below reads a frozen shard as its own failure: a walk that does not move is a
        # wall, a conversion that changes nothing is wood that cannot be worked
        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        threat.look()

        if not axe.equip():
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = "no axe"
                break

            log("no axe (%d/%d), looking again" % (no_tool, MAX_NO_TOOL))
            end_cycle("no tool")
            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
            continue

        no_tool = 0

        relieved = haul.haul_for_room()

        if relieved is not None:
            end_cycle(relieved)
            API.Pause(STEP_DELAY)
            continue

        found = roam.approach()

        if found[0] == "stop":
            stop = found[1]
            break

        # No pause: a tree coming back has already waited out its own clock, and a wait is the
        # script working rather than stalling
        if found[0] == "waited":
            idled += 1
            stall.progressed()
            continue

        if found[0] == "walked":
            end_cycle("walking")
            continue

        tree = found[1]

        outcome = chopper.chop_once(axe.serial(), tree)

        if outcome == "chopped":
            tally += 1
            unknown = 0
            throttled = 0
            barren = 0
            stall.progressed()

        elif outcome == "wornOut":
            log("axe worn out, swapping")
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

        # A stump, not a dead tile. The two outcomes differ only in scope: nothingNearby is the
        # shard answering about everything it can reach, so it always parks the ground, while empty
        # is about the trunk - unless a self-target let the shard pick, in which case it is about
        # the spot as well.
        elif outcome == "empty" or outcome == "nothingNearby":
            unknown = 0
            barren += 1

            if outcome == "nothingNearby" or AIM_AT_SELF:
                trees.mark_area_depleted(CHOP_RANGE)
                trees.forget_current()
            else:
                memory.mark_depleted(tree)

            # Said once, at the point it stops looking like bad luck
            if barren == EMPTY_HINT:
                log(
                    "%d spots in a row had nothing to chop - either the stand is worked out, or "
                    "the tree test is matching scenery the shard will not harvest" % EMPTY_HINT
                )
                trees.survey(CHOP_RANGE, SURVEY_ARTS)

        # The art ban is only sound when the swing named the tile: aimed at yourself the shard chose
        # what to refuse, and banning the art of the trunk the scan happened to pick would write off
        # a perfectly good tree. Aimed that way the tile is set aside one at a time instead.
        elif outcome == "notTree":
            unknown = 0

            if not AIM_AT_SELF:
                memory.ban_art(tree)

            memory.mark_unusable(tree, "is not harvestable")

        elif outcome == "tooFar":
            unknown = 0
            memory.mark_unusable(tree, "is out of reach at %d tiles" % tree["distance"])

        elif outcome == "notSeen":
            unknown = 0
            memory.mark_unusable(tree, "is not in line of sight")

        # Consolidating would give back almost nothing here - one log stack converts to one board
        # stack - so what frees slots is the boards leaving for the animal
        elif outcome == "packFull":
            unknown = 0
            log("pack is full, hauling before the next swing")
            haul.haul_now()

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
                "%d chops, %d logs, %d/%d"
                % (tally, wood.log_total(), API.Player.Weight, API.Player.WeightMax)
            )

        end_cycle(outcome if outcome is not None else "unknown")
        API.Pause(STEP_DELAY)
except Exception as error:
    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error

if API.Pathfinding():
    API.CancelPathfinding()

reason = stop or "hit the %d working cycle backstop" % MAX_CYCLES

# However the run ended, it finishes with boards on the animal rather than logs in the pack
boards.make_boards()

if haul.hauling():
    haul.unload()

# Chops rather than a log delta: hauled wood has left the pack, so the pack cannot total the run
log("%d chops, %d logs still in the pack" % (tally, wood.log_total()))
log("stopping - %s" % reason)
API.Stop()
