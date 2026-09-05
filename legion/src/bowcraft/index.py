import API

from bowcraft.bands import band_for, find_skill_name
from bowcraft.config import (BANDS, BATCH_SIZE, BOWYER_TITLES, BUTTON_STRIDE, CATEGORY_BUTTON_TYPE,
                             CATEGORY_NAMES, CONTAINER_RANGE, CONTEXT_TIMEOUT, CRAFT_POLL,
                             CRAFT_SETTLE, CRAFT_TIMEOUT, CRAFT_TITLE, CRAFT_TITLE_FRAGMENTS,
                             CRAFT_TITLE_TEXT, DATA_PATH, GUMP_POLL, GUMP_TIMEOUT, HEARTBEAT_EVERY,
                             ITEM_BUTTON_TYPE, JOURNAL_TAIL_LINES, JOURNAL_TAIL_SECONDS,
                             LAST_TEN_LABEL, LOG_EVERY, MAKE_LAST_BUTTON, MATERIAL_GRAPHICS,
                             MAX_CATEGORIES, MAX_CYCLES, MAX_EMPTY_MOVES, MAX_ITEM_PROBES,
                             MAX_ITEM_ROWS, MAX_NO_MATERIAL, MAX_NO_TOOL, MAX_PICKS,
                             MAX_SELL_MISSES, MAX_THROTTLED, MAX_UNKNOWN, MAX_UNREADABLE_REPORTS,
                             MIN_CRAFT_WOOD, MIN_SKILL, MOVE_DELAY, OPEN_DELAY, OPL_WAIT,
                             OUTCOME_TEXT, PATHFIND_TIMEOUT, PICK_TIMEOUT, PRODUCT_GRAPHICS,
                             PRODUCTS, RECIPES, REFUND_POLL, REFUND_SETTLE, RESTOCK_AT,
                             RETURN_WRONG_WOOD, SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT, SAVING_TEXT,
                             SELL_AT, SELL_ENTRY, SELL_PHRASE, SELL_POLL, SELL_RETRY_AFTER,
                             SELL_TIMEOUT, SKILL_NAMES, SKILL_POLL, SKILL_TIMEOUT, STALL_STOP,
                             STALL_WARN, STEP_DELAY, STOPPED, THROTTLE_BACKOFF,
                             THROTTLE_BACKOFF_MAX, TOOL_GRAPHICS, TOOL_NAME_WORDS,
                             UNREADABLE_TEXT_LIMIT, VENDOR_RANGE, VENDOR_SCAN_RADIUS,
                             VENDOR_SERIAL, VENDOR_STEPS, WOOD_HUES, WOOD_KINDS, WOOD_TYPE,
                             WOOD_TYPES)
from bowcraft.craft import Crafter
from bowcraft.materials import Materials
from bowcraft.menu import CraftMenu
from bowcraft.restock import Restock
from bowcraft.sources import Sources
from bowcraft.tools import Tools
from bowcraft.vendor import Vendor
from bowcraft.wood import WoodBook
from uo.guards import dead, first_reason, skill_capped, stopped
from uo.heartbeat import Heartbeat
from uo.log import make_log
from uo.loop import StallWatch, backoff_for
from uo.pack import count_of
from uo.record import attempt_log
from uo.save import SaveWatch
from uo.skill import SkillReader, reading
from uo.vitals import position_and_weight

log = make_log("bowcraft")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "made", position_and_weight)
stall = StallWatch("cycles without a craft", STALL_WARN, STALL_STOP, heartbeat, log)

if API.HasTarget():
    API.CancelTarget()

skill_name = find_skill_name(SKILL_NAMES)

if skill_name is None:
    log("the client reports none of %s - check SKILL_NAMES" % ", ".join(SKILL_NAMES))
    API.Stop()

skill = SkillReader(skill_name)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(skill_name)])


def products_in_pack():
    return count_of(PRODUCT_GRAPHICS)


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

tools = Tools(TOOL_GRAPHICS, TOOL_NAME_WORDS, log)
wood = WoodBook({
    "kinds": WOOD_KINDS,
    "types": WOOD_TYPES,
    "hues": WOOD_HUES,
    "wanted": WOOD_TYPE,
    "move_delay": MOVE_DELAY,
}, log)
sources = Sources(wood, {
    "max_picks": MAX_PICKS,
    "pick_timeout": PICK_TIMEOUT,
    "open_delay": OPEN_DELAY,
    "container_range": CONTAINER_RANGE,
    "pathfind_timeout": PATHFIND_TIMEOUT,
}, log)
restock = Restock(wood, sources, {
    "batch": BATCH_SIZE,
    "move_delay": MOVE_DELAY,
    "max_empty_moves": MAX_EMPTY_MOVES,
    "return_wrong_wood": RETURN_WRONG_WOOD,
}, log)
menu = CraftMenu(tools, {
    "stride": BUTTON_STRIDE,
    "category_type": CATEGORY_BUTTON_TYPE,
    "item_type": ITEM_BUTTON_TYPE,
    "category_names": CATEGORY_NAMES,
    "last_ten_label": LAST_TEN_LABEL,
    "title": CRAFT_TITLE,
    "title_text": CRAFT_TITLE_TEXT,
    "title_fragments": CRAFT_TITLE_FRAGMENTS,
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
    "max_categories": MAX_CATEGORIES,
    "max_item_rows": MAX_ITEM_ROWS,
}, log)
crafter = Crafter(tools, menu, wood, OUTCOME_TEXT, {
    "recipes": RECIPES,
    "products": PRODUCTS,
    "make_last_button": MAKE_LAST_BUTTON,
    "gump_timeout": GUMP_TIMEOUT,
    "craft_timeout": CRAFT_TIMEOUT,
    "craft_poll": CRAFT_POLL,
    "craft_settle": CRAFT_SETTLE,
    "max_probes": MAX_ITEM_PROBES,
    "max_categories": MAX_CATEGORIES,
    "max_reports": MAX_UNREADABLE_REPORTS,
    "text_limit": UNREADABLE_TEXT_LIMIT,
    "tail_seconds": JOURNAL_TAIL_SECONDS,
    "tail_lines": JOURNAL_TAIL_LINES,
    "wood_type": WOOD_TYPE,
}, log)
vendor = Vendor(wood, menu, {
    "serial": VENDOR_SERIAL,
    "titles": BOWYER_TITLES,
    "scan_radius": VENDOR_SCAN_RADIUS,
    "range": VENDOR_RANGE,
    "steps": VENDOR_STEPS,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "step_delay": STEP_DELAY,
    "sell_entry": SELL_ENTRY,
    "sell_phrase": SELL_PHRASE,
    "context_timeout": CONTEXT_TIMEOUT,
    "sell_timeout": SELL_TIMEOUT,
    "sell_poll": SELL_POLL,
    "opl_wait": OPL_WAIT,
    "text_limit": UNREADABLE_TEXT_LIMIT,
}, log, heartbeat, products_in_pack)

start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)

if start is None:
    log("%s is not reading yet - start it again once the skill list has arrived" % skill_name)
    API.Stop()
elif start < MIN_SKILL:
    log("%s is at %.1f and the table starts at %.1f - train it up by hand first"
        % (skill_name, start, MIN_SKILL))
    API.Stop()

if tools.serial() is None:
    log("no fletcher's tools in the pack")
    API.Stop()

sources.pick()

# A run that starts on the wood it is already carrying needed no cursor at all
if len(sources.picked()) == 0 and wood.in_pack() == 0:
    log("nothing picked and no wood in the pack")
    API.Stop()

log("%s at %.1f, %s in the pack, %s" % (skill_name, start, wood.pack_report(),
                                        sources.stock_line()))

if wood.in_pack() < RESTOCK_AT:
    restock.run()

recorder = attempt_log(DATA_PATH, skill_name, log)
materials = Materials(wood, MATERIAL_GRAPHICS)

stop = None
tally = 0
fails = 0
unknown = 0
throttled = 0
no_tool = 0
no_material = 0
throttle_tally = 0
said_throttle = False
sell_misses = 0
sell_paused_until = 0
reported = 0
cycle = 0
product = None
last_skill = start


def end_cycle(phase):
    global stop

    stall.end_cycle(phase, cycle, tally)

    if stop is None:
        stop = stall.reason()


# Measured either side of the craft rather than read off the recipe: a failure refunds part of it
def record_craft(outcome, skill_from, before):
    if not recorder.recording():
        return

    after = materials.settled_snapshot(REFUND_SETTLE, REFUND_POLL)
    recorder.record(skill_from, outcome, outcome == "made", materials.spent(before, after),
                    (materials.wood_total(before), materials.wood_total(after)))


try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1

        stop = stop_reason()

        if stop is not None:
            break

        # A frozen shard reads as every failure below, so it is waited out before any of them
        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        value = skill.read()

        # The client applies a gain some time after the outcome, so the row waits a cycle for it
        recorder.settle(value)

        if value is not None and value != last_skill:
            last_skill = value
            stall.progressed()

        wanted = band_for(BANDS, value if value is not None else last_skill)

        if wanted is None:
            stop = "%s reads %s and no band covers it" % (skill_name, reading(value))
            break

        if wanted != product:
            log("%s at %s, making %s" % (skill_name, reading(value), wanted))
            product = wanted
            crafter.forget_last()

        if products_in_pack() >= SELL_AT and cycle >= sell_paused_until:
            if vendor.sell_trip():
                sell_misses = 0

                end_cycle("selling")
                continue

            sell_misses += 1

            # Retried, but not every cycle: otherwise the crafting never gets a turn
            if sell_misses >= MAX_SELL_MISSES:
                sell_misses = 0
                sell_paused_until = cycle + SELL_RETRY_AFTER
                log("%d sell trips bought nothing - crafting on, and asking again in %d cycles"
                    % (MAX_SELL_MISSES, SELL_RETRY_AFTER))

        if wood.in_pack() < RESTOCK_AT:
            # An unreachable container also pulls nothing, which the stall watch ends
            pulled = restock.run()

            if pulled == 0 and sources.stock_left() == 0 and wood.in_pack() < MIN_CRAFT_WOOD:
                stop = ("out of %s wood - %s in the pack, none left in what you picked"
                        % (WOOD_TYPE, wood.pack_report()))
                break

            # A short pack that can still make something crafts
            if wood.in_pack() < MIN_CRAFT_WOOD:
                end_cycle("restocking")
                continue

        spent_before = materials.snapshot() if recorder.recording() else {}
        outcome = crafter.craft_once(product)

        if outcome != "throttled":
            throttled = 0

        if outcome is not None:
            unknown = 0

        if outcome in ("made", "failed"):
            if outcome == "made":
                tally += 1
            else:
                fails += 1

            record_craft(outcome, value, spent_before)
            no_material = 0
            stall.progressed()
        elif outcome == "noMaterial":
            pulled = restock.run()

            if pulled > 0:
                no_material = 0
                stall.progressed()
            elif wood.in_pack() < RESTOCK_AT and sources.stock_left() == 0:
                stop = "the shard says there is not enough wood and there is none left to pull"
                break
            else:
                # Wood in the pack, refused, nothing to add to it: the wrong kind of wood
                no_material += 1

                if no_material >= MAX_NO_MATERIAL:
                    stop = ("the shard refused %s in the pack %d times - read the gump's own words "
                            "above; if it wants another wood, set WOOD_TYPE and the menu to match"
                            % (wood.pack_report(), no_material))
                    break
        elif outcome in ("wrongRow", "saving"):
            stall.progressed()
        elif outcome == "toolWorn":
            crafter.forget_last()
            stall.progressed()
            log("the tools wore out, looking for another pair")
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s at %s" % (product, reading(value))
            break
        elif outcome == "noRow":
            stop = "could not find the SELECTIONS row for '%s'" % product
            break
        elif outcome in ("noTool", "noGump"):
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = ("no fletcher's tools left" if outcome == "noTool"
                        else "the craft menu will not open")
                break

            log("%s (%d/%d), trying again"
                % ("no fletcher's tools in the pack" if outcome == "noTool"
                   else "the tools opened no craft menu", no_tool, MAX_NO_TOOL))
            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
        elif outcome == "throttled":
            throttled += 1
            throttle_tally += 1

            if throttled >= MAX_THROTTLED:
                stop = "%d throttled crafts in a row" % MAX_THROTTLED
                break

            waiting = backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

            # Said once, then only tallied: the pause is the shard's, and it is normal
            if not said_throttle:
                said_throttle = True
                log("the shard is pacing the crafts - waiting %.1fs, and counting these from here on"
                    % waiting)

            API.Pause(waiting)
        else:
            unknown += 1
            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        if outcome not in ("noTool", "noGump"):
            no_tool = 0

        if unknown >= MAX_UNKNOWN:
            stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
            break

        if tally >= reported + LOG_EVERY:
            reported = tally
            log(
                "%d made, %d failed, %d throttled, %s at %s, %s left"
                % (tally, fails, throttle_tally, skill_name, reading(value),
                   wood.report(wood.pack_wood()))
            )

        end_cycle(outcome if outcome is not None else "unknown")
        API.Pause(STEP_DELAY)
except Exception as error:
    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error

if API.Pathfinding():
    API.CancelPathfinding()

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES
ended = skill.read()
recorder.settle(ended)

log(
    "%d made, %d failed, %d throttled, %s %.1f -> %s"
    % (tally, fails, throttle_tally, skill_name, start, reading(ended))
)
log("stopping - %s" % reason)
API.Stop()
