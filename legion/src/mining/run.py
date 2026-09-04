import API

from mining.beetle import Beetle
from mining.combine import Combiner
from mining.config import (ATTACK_TEXT, BEETLE_SCAN_RADIUS, COMBINE_DELAY, COMBINE_POLL,
                           COMBINE_TIMEOUT, DIFFERENT_ORE_TEXT, DIG_PROMPT_TEXT,
                           DIG_TARGET_POLL, DIG_TARGET_TIMEOUT, DIG_TIMEOUT, DISMOUNT_ATTEMPTS,
                           DISMOUNT_POLL, DISMOUNT_TIMEOUT, EQUIP_ATTEMPTS, EQUIP_POLL,
                           EQUIP_TIMEOUT, FIRE_BEETLE_GRAPHICS, FIRE_BEETLE_SERIAL,
                           GUARD_CALL, GUARD_CALL_DELAY, GUARD_CALLS, GUARD_REPLY_WAIT,
                           GUARD_ZONE_TEXT, HEARTBEAT_EVERY, INGOT_GRAPHICS,
                           MAX_COMBINE_ATTEMPTS, MAX_SMELT_PASSES, METAL_ASKS, METAL_LINE_EXTRA,
                           METAL_MISSES, MIN_SMELT_AMOUNT, NO_CURSOR_READ, NO_GUARDS_TEXT,
                           NOT_METAL_WORDS, OPL_TIMEOUT, ORE_GRAPHICS, ORE_METALS, ORE_NAME_WORD,
                           OUTCOME_TEXT, PACK_LIMIT, PATHFIND_TIMEOUT, PICK_TIMEOUT, PICKAXE_NAMES,
                           PLAIN_METAL, SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT, SAVING_TEXT,
                           SMELT_ATTEMPTS, SMELT_DELAY, SMELT_POLL, SMELT_RANGE, SMELT_TIMEOUT,
                           SMELT_UNSKILLED_TEXT, SPARE_BAG_SERIAL, STALL_STOP, STALL_WARN, STOPPED,
                           TARGET_TIMEOUT, THREAT_RANGE, THROTTLED_TEXT, UNGUARDED_TEXT,
                           WATCH_FOR_TROUBLE)
from mining.metal import MetalBook
from mining.ore import OrePack
from mining.smelt import Smelter
from uo.entity import hex_of
from uo.guards import dead, first_reason, pack_full, stopped
from uo.heartbeat import Heartbeat
from uo.log import make_log
from uo.loop import StallWatch
from uo.mount import dismount
from uo.save import SaveWatch
from uo.threat import ThreatWatch
from uo.tool import Tool
from uo.vitals import position_and_weight

log = make_log("mining")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "swings", position_and_weight)
stall = StallWatch("cycles without a swing landing", STALL_WARN, STALL_STOP, heartbeat, log)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), pack_full(PACK_LIMIT)])


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

pickaxe = Tool("pickaxe", PICKAXE_NAMES, [], ["onehanded"], SPARE_BAG_SERIAL,
               EQUIP_ATTEMPTS, EQUIP_TIMEOUT, EQUIP_POLL, log)
ore = OrePack(ORE_GRAPHICS, ORE_NAME_WORD, MIN_SMELT_AMOUNT, log)
metals = MetalBook({
    "metals": ORE_METALS,
    "plain": PLAIN_METAL,
    "line_extra": METAL_LINE_EXTRA,
    "not_metal_words": NOT_METAL_WORDS,
    "asks": METAL_ASKS,
    "misses": METAL_MISSES,
    "opl_timeout": OPL_TIMEOUT,
}, log)
combiner = Combiner(ore, metals, {
    "attempts": MAX_COMBINE_ATTEMPTS,
    "delay": COMBINE_DELAY,
    "timeout": COMBINE_TIMEOUT,
    "poll": COMBINE_POLL,
    "target_timeout": TARGET_TIMEOUT,
    "different_text": DIFFERENT_ORE_TEXT,
    "throttled_text": THROTTLED_TEXT,
}, log)
beetle = Beetle(FIRE_BEETLE_GRAPHICS, FIRE_BEETLE_SERIAL, BEETLE_SCAN_RADIUS, SMELT_RANGE,
                PATHFIND_TIMEOUT, PICK_TIMEOUT, log)
smelter = Smelter(ore, beetle, saves, {
    "attempts": SMELT_ATTEMPTS,
    "passes": MAX_SMELT_PASSES,
    "delay": SMELT_DELAY,
    "timeout": SMELT_TIMEOUT,
    "poll": SMELT_POLL,
    "range": SMELT_RANGE,
    "target_timeout": TARGET_TIMEOUT,
    "ore_graphics": ORE_GRAPHICS,
    "ingot_graphics": INGOT_GRAPHICS,
    "throttled_text": THROTTLED_TEXT,
    "unskilled_text": SMELT_UNSKILLED_TEXT,
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
}, log, beetle.find, "beetle")

DIG_CONFIG = {
    "cursor_timeout": DIG_TARGET_TIMEOUT,
    "cursor_poll": DIG_TARGET_POLL,
    "prompt_text": DIG_PROMPT_TEXT,
    "no_cursor_read": NO_CURSOR_READ,
    "dig_timeout": DIG_TIMEOUT,
}


def get_off_the_mount():
    return dismount(DISMOUNT_ATTEMPTS, DISMOUNT_TIMEOUT, DISMOUNT_POLL)


# Read before the dismount, or the mounted half of it always answers no. A run that stops on its
# first cycle otherwise looks exactly like a script that never started.
def say_where_we_stand():
    pickaxe.learn(pickaxe.held())
    log("%d ore in the pack to start, at %d,%d" % (ore.total(), API.Player.X, API.Player.Y))
    held = pickaxe.held()
    log(
        "mounted %s, hand %s, weight %d/%d"
        % (
            "yes" if API.Player.IsMounted else "no",
            (held.Name or hex_of(held.Graphic)) if held is not None else "empty",
            API.Player.Weight,
            API.Player.WeightMax,
        )
    )

