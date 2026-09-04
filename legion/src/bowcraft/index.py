import API

from bowcraft.bands import band_for, find_skill_name
from bowcraft.config import (BANDS, BATCH_SIZE, BOWYER_TITLES, CATEGORY_BUTTON_TYPE,
                             CATEGORY_NAMES, CONTAINER_RANGE, CONTEXT_TIMEOUT, CRAFT_POLL,
                             CRAFT_SETTLE, CRAFT_TIMEOUT, CRAFT_TITLE, CRAFT_TITLE_FRAGMENTS,
                             CRAFT_TITLE_TEXT, GUMP_POLL, GUMP_TIMEOUT, HEARTBEAT_EVERY,
                             ITEM_BUTTON_TYPE, JOURNAL_TAIL_LINES, JOURNAL_TAIL_SECONDS,
                             LAST_TEN_LABEL, LOG_EVERY, LOG_GRAPHICS, MAKE_LAST_BUTTON,
                             MAX_CATEGORIES, MAX_CYCLES, MAX_EMPTY_MOVES, MAX_ITEM_PROBES,
                             MAX_ITEM_ROWS, MAX_NO_MATERIAL, MAX_NO_TOOL, MAX_PICKS,
                             MAX_SELL_MISSES, MAX_THROTTLED, MAX_UNKNOWN, MAX_UNREADABLE_REPORTS,
                             MIN_CRAFT_WOOD, MIN_SKILL, MOVE_DELAY, OPEN_DELAY, OPL_WAIT,
                             OUTCOME_TEXT, PACK_LIMIT, PATHFIND_TIMEOUT, PICK_TIMEOUT,
                             PRODUCT_GRAPHICS, PRODUCTS, RECIPES, RESTOCK_AT, RETURN_WRONG_WOOD,
                             SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT, SAVING_TEXT, SAY_THROTTLE_ONCE,
                             SELL_AT, SELL_ENTRY, SELL_PHRASE, SELL_POLL, SELL_RETRY_AFTER,
                             SELL_TIMEOUT, SKILL_NAMES, SKILL_POLL, SKILL_TIMEOUT, STALL_STOP,
                             STALL_WARN, STEP_DELAY, STOPPED, THROTTLE_BACKOFF,
                             THROTTLE_BACKOFF_MAX, THROTTLED_TEXT, TOOL_GRAPHICS, TOOL_NAME_WORDS,
                             UNREADABLE_TEXT_LIMIT, VENDOR_RANGE, VENDOR_SCAN_RADIUS,
                             VENDOR_SERIAL, VENDOR_STEPS, WEIGHT_BUFFER, WOOD_HUES, WOOD_KINDS,
                             WOOD_TYPE, WOOD_TYPES, WOOD_WEIGHT, BUTTON_STRIDE)
from bowcraft.craft import Crafter
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
from uo.pack import amount_of, pack_contents, pack_top_level
from uo.save import SaveWatch
from uo.skill import SkillReader, reading
from uo.vitals import position_and_weight, weight_reading
from uo.weight import over_buffer

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
    "buffer": WEIGHT_BUFFER,
    "move_delay": MOVE_DELAY,
    "max_empty_moves": MAX_EMPTY_MOVES,
    "wood_weight": WOOD_WEIGHT,
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


def products_in_pack():
    return sum(amount_of(item) for item in pack_contents()
               if item.Graphic in PRODUCT_GRAPHICS)


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

# Nothing picked is only an ending when the pack is empty too: a run that starts on the wood it is
# already carrying is a run that needed no cursor at all
if len(sources.picked()) == 0 and wood.in_pack() == 0:
    log("nothing picked and no wood in the pack")
    API.Stop()

log("%s at %.1f, %s in the pack, %s" % (skill_name, start, wood.pack_report(),
                                        sources.stock_line()))

if wood.in_pack() < RESTOCK_AT:
    restock.run()

stop = None
tally = 0
fails = 0
unknown = 0
throttled = 0
no_tool = 0
no_material = 0
throttle_tally = 0
said_throttle = False
said_overweight = False
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


# Weight stops nothing here. It is reported when it starts and when it clears, and that is all: the
# run has no way to put the pack down that is not selling it, and it is already trying to sell.
def warn_overweight():
    global said_overweight

    if over_buffer(0):
        if not said_overweight:
            said_overweight = True
            log("overweight at %s - carrying on, crafting is what takes it off" % weight_reading())
    elif said_overweight:
        said_overweight = False
        log("no longer overweight, at %s" % weight_reading())


try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1

        stop = stop_reason()

        if stop is not None:
            break

        # Everything below reads a frozen shard as its own failure: a craft that answers nothing is
        # an unreadable outcome, a move that gains nothing is an empty container
        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        value = skill.read()

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

        # Weight is never an ending. Said once a stretch, because a run that cannot sell can still
        # craft, and every craft turns wood the pack is carrying into one lighter item.
        warn_overweight()

        wants_sale = (
            products_in_pack() >= SELL_AT
            or over_buffer(WEIGHT_BUFFER)
            or len(pack_top_level()) >= PACK_LIMIT
        )

        if wants_sale and cycle >= sell_paused_until:
            if vendor.sell_trip():
                sell_misses = 0

                end_cycle("selling")
                continue

            sell_misses += 1

            # The trip is worth retrying, but not every cycle for ever: without this it walks to the
            # vendor and back on each pass and the crafting never gets a turn
            if sell_misses >= MAX_SELL_MISSES:
                sell_misses = 0
                sell_paused_until = cycle + SELL_RETRY_AFTER
                log("%d sell trips bought nothing - crafting on, and asking again in %d cycles"
                    % (MAX_SELL_MISSES, SELL_RETRY_AFTER))

        if wood.in_pack() < RESTOCK_AT:
            # Weight and an unreachable container also pull nothing, and neither is an empty
            # container - the stall watch is what ends those
            pulled = restock.run()

            if pulled == 0 and sources.stock_left() == 0 and wood.in_pack() < MIN_CRAFT_WOOD:
                stop = ("out of %s wood - %s in the pack, none left in what you picked"
                        % (WOOD_TYPE, wood.pack_report()))
                break

            # Only a pack with nothing makeable in it is worth spending the cycle on: a short pack
            # that can still make something crafts, which is also what takes weight off
            if wood.in_pack() < MIN_CRAFT_WOOD:
                end_cycle("restocking")
                continue

        outcome = crafter.craft_once(product)

        if outcome == "made":
            tally += 1
            unknown = 0
            throttled = 0
            no_material = 0
            stall.progressed()
        elif outcome == "failed":
            # Still a gain and still spends the wood, so it counts as the loop getting somewhere
            fails += 1
            unknown = 0
            throttled = 0
            no_material = 0
            stall.progressed()
        elif outcome == "noMaterial":
            unknown = 0
            pulled = restock.run()

            if pulled > 0:
                no_material = 0
                stall.progressed()
            elif wood.in_pack() < RESTOCK_AT and sources.stock_left() == 0:
                stop = "the shard says there is not enough wood and there is none left to pull"
                break
            else:
                # Wood in the pack that a restock cannot add to, refused all the same: what a shard
                # that crafts from only one of logs and boards looks like from in here
                no_material += 1

                if no_material >= MAX_NO_MATERIAL:
                    stop = ("the shard refused %s in the pack %d times - read the gump's own words "
                            "above; if it wants another wood, set WOOD_TYPE and the menu to match"
                            % (wood.pack_report(), no_material))
                    break
        elif outcome == "wrongRow":
            unknown = 0
            stall.progressed()
        elif outcome == "toolWorn":
            crafter.forget_last()
            unknown = 0
            stall.progressed()
            log("the tools wore out, looking for another pair")
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s at %s" % (product, reading(value))
            break
        elif outcome == "noRow":
            stop = "could not find the SELECTIONS row for '%s'" % product
            break
        elif outcome == "noTool" or outcome == "noGump":
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

            # Said once, then only tallied: the pause itself is the shard's, and it is normal
            if SAY_THROTTLE_ONCE and not said_throttle:
                said_throttle = True
                log("the shard is pacing the crafts - waiting %.1fs, and counting these from here on"
                    % waiting)

            API.Pause(waiting)
        elif outcome == "saving":
            unknown = 0
            stall.progressed()
        else:
            unknown += 1
            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        if outcome != "noTool" and outcome != "noGump":
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

log(
    "%d made, %d failed, %d throttled, %s %.1f -> %s"
    % (tally, fails, throttle_tally, skill_name, start, reading(ended))
)
log("stopping - %s" % reason)
API.Stop()
