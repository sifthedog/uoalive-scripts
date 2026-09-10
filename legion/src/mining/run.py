import API

from mining.beetle import Beetle
from mining.combine import Combiner
from mining.config import (AMBUSH_ALARM, AMBUSH_HOLD, AMBUSH_HOLD_BUTTON, AMBUSH_HOLD_HUE,
                           AMBUSH_HOLD_POLL, AMBUSH_HOLD_TEXT, AMBUSH_HUE, AMBUSH_NOTICES,
                           AMBUSH_REPEATS, AMBUSH_TEXT, AMBUSH_WARNING, BEETLE_SCAN_RADIUS,
                           COMBINE_DELAY, COMBINE_POLL,
                           COMBINE_TIMEOUT, DATA_PATH, DIFFERENT_ORE_TEXT, DIG_PROMPT_TEXT,
                           DIG_TARGET_POLL, DIG_TARGET_TIMEOUT, DIG_TIMEOUT, DISMOUNT_ATTEMPTS,
                           DISMOUNT_POLL, DISMOUNT_TIMEOUT, EQUIP_ATTEMPTS, EQUIP_POLL,
                           EQUIP_TIMEOUT, FIRE_BEETLE_GRAPHICS, FIRE_BEETLE_SERIAL,
                           HEARTBEAT_EVERY, INGOT_GRAPHICS,
                           MAX_COMBINE_ATTEMPTS, MAX_SMELT_PASSES, METAL_ASKS, METAL_LINE_EXTRA,
                           METAL_MISSES, MIN_SMELT_AMOUNT, NO_CURSOR_READ,
                           NOT_METAL_WORDS, ORE_GRAPHICS, ORE_METALS, ORE_NAME_WORD,
                           OUTCOME_TEXT, PACK_LIMIT, PATHFIND_TIMEOUT, PICK_TIMEOUT, PICKAXE_NAMES,
                           PLAIN_METAL, SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT, SAVING_TEXT,
                           SKILL_NAMES, SKILL_POLL, SKILL_TIMEOUT,
                           SMELT_ATTEMPTS, SMELT_DELAY, SMELT_POLL, SMELT_RANGE, SMELT_TIMEOUT,
                           SMELT_UNSKILLED_TEXT, SPARE_BAG_SERIAL, STALL_STOP, STALL_WARN, STOPPED,
                           TARGET_TIMEOUT, THREAT_RANGE, THROTTLED_TEXT,
                           WATCH_FOR_TROUBLE)
from mining.metal import MetalBook
from mining.ore import OrePack
from mining.smelt import Smelter
from uo.entity import hex_of
from uo.gathered import Gathered
from uo.guards import dead, first_reason, pack_full, skill_capped, stopped
from uo.heartbeat import Heartbeat
from uo.hold import Hold
from uo.log import make_log
from uo.loop import StallWatch
from uo.mount import dismount
from uo.record import attempt_log
from uo.save import SaveWatch
from uo.skill import SkillReader, find_skill_name, reading
from uo.threat import ThreatWatch
from uo.tool import Tool
from uo.vitals import position_and_weight

class Run(object):
    """Everything both mining entries wire up alike. The prefix is what they differ on."""

    def __init__(self, prefix):
        log = make_log(prefix)
        heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "swings", position_and_weight)
        stall = StallWatch("cycles without a swing landing", STALL_WARN, STALL_STOP, heartbeat, log)


        def stop_reason():
            return first_reason([stopped(STOPPED), dead(), pack_full(PACK_LIMIT)])


        saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)
        hold = Hold({
            "text": AMBUSH_HOLD_TEXT,
            "button": AMBUSH_HOLD_BUTTON,
            "hue": AMBUSH_HOLD_HUE,
            "poll": AMBUSH_HOLD_POLL,
        }, log, stop_reason, heartbeat)

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

        skill_name = find_skill_name(SKILL_NAMES)

        if skill_name is None and DATA_PATH:
            log("the client reports none of %s - not recording" % ", ".join(SKILL_NAMES))

        skill = SkillReader(skill_name or SKILL_NAMES[0])
        recorder = attempt_log(DATA_PATH if skill_name else "", skill.name(), log)


        def metal_name(item):
            metal = metals.of(item)

            return None if metal is None else "%s ore" % metal


        gathered = Gathered(recorder, skill, skill_capped(skill_name), {
            "is_resource": ore.is_ore,
            "name_of": metal_name,
            "resource_graphics": ORE_GRAPHICS,
            "noun": "ore",
            "tool": "pickaxe",
            "converter_tool": "fire beetle",
            "made": "smelted",
        }, log)
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
            "about_to_convert": gathered.before_convert,
            "converted": gathered.after_convert,
        }, log)
        threat = ThreatWatch({
            "watch": WATCH_FOR_TROUBLE,
            "range": THREAT_RANGE,
            "ambush_text": AMBUSH_TEXT,
            "ambush_alarm": AMBUSH_ALARM,
            "ambush_notices": AMBUSH_NOTICES,
            "ambush_warning": AMBUSH_WARNING,
            "ambush_hue": AMBUSH_HUE,
            "ambush_repeats": AMBUSH_REPEATS,
        }, log, beetle.find, lambda friend: "beetle", hold if AMBUSH_HOLD else None)

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

            if recorder.recording():
                start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)
                cap = skill.cap()
                log("%s at %s%s%s" % (
                    skill.name(), reading(start),
                    "/%.1f" % cap if cap is not None and cap > 0 else "",
                    "" if gathered.recording() else ", capped - not recording"))
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

        self.log = log
        self.heartbeat = heartbeat
        self.stall = stall
        self.stop_reason = stop_reason
        self.saves = saves
        self.pickaxe = pickaxe
        self.ore = ore
        self.combiner = combiner
        self.beetle = beetle
        self.smelter = smelter
        self.threat = threat
        self.gathered = gathered
        self.dig_config = DIG_CONFIG
        self.get_off_the_mount = get_off_the_mount
        self.say_where_we_stand = say_where_we_stand
