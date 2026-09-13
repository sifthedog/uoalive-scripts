import API

from bowcraft.config import (BANDS, BATCH_SIZE, BOX, BOX_PRESS_POLL, BOX_PRESS_TIMEOUT, BOX_TAKE,
                             BUTTON_STRIDE, CATEGORY_BUTTON_TYPE, CATEGORY_NAMES, CONTAINER_RANGE,
                             CONTEXT_TIMEOUT, CRAFT_POLL, CRAFT_SETTLE, CRAFT_TIMEOUT, CRAFT_TITLE,
                             CRAFT_TITLE_FRAGMENTS, CRAFT_TITLE_TEXT, DATA_PATH, DUMP_AT,
                             FETCH_POLL, FETCH_TIMEOUT, GUMP_POLL, GUMP_TIMEOUT, HEARTBEAT_EVERY,
                             ITEM_BUTTON_TYPE, JOURNAL_TAIL_LINES, JOURNAL_TAIL_SECONDS,
                             LAST_TEN_LABEL, LOG_EVERY, MAKE_LAST_BUTTON, MATERIAL_GRAPHICS,
                             MAX_CATEGORIES, MAX_CYCLES, MAX_DUMP_MISSES, MAX_EMPTY_MOVES,
                             MAX_HELD, MAX_ITEM_PROBES, MAX_ITEM_ROWS, MAX_NO_MATERIAL,
                             MAX_NO_TOOL, MAX_PICKS, MAX_SELL_MISSES, MAX_THROTTLED, MAX_UNKNOWN,
                             MAX_UNREADABLE_REPORTS, MIN_CRAFT_WOOD, MIN_SKILL, MOVE_DELAY,
                             OPEN_DELAY, OPL_WAIT, OUTCOME_TEXT, PATHFIND_TIMEOUT, PICK_TIMEOUT,
                             PRODUCTS, PRODUCT_GRAPHICS, RECIPES, REFUND_POLL, REFUND_SETTLE,
                             REGULAR_WOOD, RESTOCK_AT, RETURN_WRONG_WOOD, SAVE_DONE_TEXT,
                             SAVE_POLL, SAVE_WAIT, SAVING_TEXT, SELL_AT, SELL_ENTRY, SELL_PHRASE,
                             SELL_POLL, SELL_RETRY_AFTER, SELL_TIMEOUT, SETUP, SKILL_NAMES,
                             SKILL_POLL, SKILL_TIMEOUT, STALL_STOP, STALL_WARN, STEP_DELAY,
                             STOPPED, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX, TOOL_GRAPHICS,
                             TOOL_NAME_WORDS, TOO_HEAVY_TEXT, UNREADABLE_TEXT_LIMIT, VENDORS,
                             VENDOR_RANGE, VENDOR_SCAN_RADIUS, VENDOR_SERIAL, VENDOR_STEPS,
                             WOOD_COST, WOOD_HUES, WOOD_KINDS, WOOD_TYPE, WOOD_TYPES)
from uo.restock import Restock
from uo.sources import Sources
from uo.cost import cost_of, short_by
from uo.craft import Crafter
from uo.craftmenu import CraftMenu
from uo.craftrun import CraftRecorder, Seller, Unloader, end_cycle, make_room
from uo.crafttool import CraftTool
from uo.dump import Dump
from uo.guards import dead, first_reason, skill_capped, stopped
from uo.heartbeat import Heartbeat
from uo.log import make_log
from uo.loop import StallWatch, backoff_for
from uo.materials import Materials
from uo.pack import count_of
from uo.record import attempt_log
from uo.save import SaveWatch
from uo.setup import Setup
from uo.skill import SkillReader, find_skill_name, reading
from uo.stages import band_for, band_rows
from uo.stock import StockBook
from uo.toolstore import ToolStore
from uo.vendor import Vendor
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
product = None


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(skill_name)])


def wood_cost(item):
    return cost_of(item, WOOD_COST, MIN_CRAFT_WOOD)


def wood_short(item):
    return short_by(item, wood.in_pack(), WOOD_COST, MIN_CRAFT_WOOD)


# The band's product only: a yumi left from the band before would send a bowyer trip every cycle
def products_in_pack():
    return count_of(PRODUCTS[product] if product is not None else PRODUCT_GRAPHICS)


def unsold_ahead(value):
    for ceiling, name in BANDS:
        if VENDORS[name] is None and (ceiling is None or ceiling > value):
            return True

    return False


UNSOLD = [name for name in VENDORS if VENDORS[name] is None]


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

tools = CraftTool("fletcher's tool", TOOL_GRAPHICS, TOOL_NAME_WORDS, log)
wood = StockBook({
    "noun": "wood",
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
    "move_delay": MOVE_DELAY,
    "container_range": CONTAINER_RANGE,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "box": BOX,
    "plain": REGULAR_WOOD,
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
    "box_take": BOX_TAKE,
    "press_timeout": BOX_PRESS_TIMEOUT,
    "press_poll": BOX_PRESS_POLL,
}, log)
restock = Restock(wood, sources, {
    "batch": BATCH_SIZE,
    "move_delay": MOVE_DELAY,
    "max_empty_moves": MAX_EMPTY_MOVES,
    "return_wrong_wood": RETURN_WRONG_WOOD,
    "heavy_text": TOO_HEAVY_TEXT,
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
    "tool_noun": "fletcher's tools",
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
    "material": WOOD_TYPE,
}, log, log.stamp)
vendor = Vendor(menu, {
    "serial": VENDOR_SERIAL,
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
tool_store = ToolStore(tools, sources, {
    "noun": "fletcher's tools",
    "pick_timeout": PICK_TIMEOUT,
    "move_delay": MOVE_DELAY,
    "fetch_timeout": FETCH_TIMEOUT,
    "fetch_poll": FETCH_POLL,
}, log)
# Kept: a bow carried in is the character's own, and it is never unloaded into a barrel
dump = Dump(sources, PRODUCTS, {
    "pick_timeout": PICK_TIMEOUT,
    "move_delay": MOVE_DELAY,
    "keep_existing": True,
}, log)
setup = Setup(SETUP, log, stop_reason)

start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)

# Before the cursor: a capped character has nothing to pick containers for
capped = skill_capped(skill_name)()

if start is None:
    log("%s is not reading yet - start it again once the skill list has arrived" % skill_name)
    API.Stop()
elif start < MIN_SKILL:
    log("%s is at %.1f and the table starts at %.1f - train it up by hand first"
        % (skill_name, start, MIN_SKILL))
    API.Stop()
elif capped is not None:
    log(capped)
    API.Stop()

cap = skill.cap()


def training_rows():
    heading = "%s %s%s" % (skill_name, reading(start),
                           " / %.1f" % cap if cap is not None and cap > 0 else "")

    return heading, band_rows(BANDS, start, lambda name: VENDORS[name][0] if VENDORS[name]
                              else "nobody buys it: unloaded", MIN_SKILL)


answers = setup.ask({
    "table": training_rows,
    "tools": tool_store.pick,
    "tools_ready": lambda: tool_store.count() > 0,
    "source": sources.pick_one,
    "clear": sources.clear,
    "unload": dump.pick_line,
    "unload_ready": dump.picked,
    "has_wood": lambda: wood.in_pack() > 0,
    "unsold_ahead": lambda: unsold_ahead(start),
})

# The stop lands at the next Pause, so the lines until then read a form that was never answered
output = answers["output"] if answers is not None else "keep"
dump_at = answers["dump_at"] if answers is not None else DUMP_AT
log.enabled = answers["debug_logs"] if answers is not None else False

if answers is None:
    API.Stop()

if output == "sell":
    dump.limit_to(UNSOLD)
    log("selling every %d to the bowyer" % SELL_AT)

    if unsold_ahead(start) and not dump.picked():
        log("nothing picked to unload into - the run ends once the pack holds %d unsold products"
            % MAX_HELD)
elif output == "unload":
    log("unloading every %d products" % dump_at)
elif output == "keep":
    log("keeping what is made - the run ends once the pack holds %d" % MAX_HELD)

# A picked tool container fills an empty pack before the first craft
if (tools.find(FETCH_TIMEOUT, FETCH_POLL) is None
        and not (tool_store.picked() and tool_store.fetch())):
    log("no fletcher's tools in the pack")
    API.Stop()

log("%s at %s%s, %s in the pack, %s"
    % (skill_name, reading(start), "/%.1f" % cap if cap is not None and cap > 0 else "",
       wood.pack_report(), sources.stock_line()))

if wood.in_pack() < RESTOCK_AT:
    restock.run()

recorder = attempt_log(DATA_PATH, skill_name, log)
materials = Materials(wood, MATERIAL_GRAPHICS)
craft_recorder = CraftRecorder(recorder, materials, REFUND_SETTLE, REFUND_POLL)
seller = Seller(vendor, MAX_SELL_MISSES, SELL_RETRY_AFTER, log)
unloader = Unloader(dump)

stop = None
tally = 0
fails = 0
unknown = 0
throttled = 0
no_tool = 0
no_material = 0
throttle_tally = 0
said_throttle = False
reported = 0
cycle = 0
last_skill = start


def sells_this_band():
    return output == "sell" and VENDORS[product] is not None


def unloads_this_band():
    return output == "unload" or (output == "sell" and VENDORS[product] is None and dump.picked())


# A pack the shard will not load for weight is emptied first, the way the band's products leave
def try_make_room():
    return make_room(
        restock, log, "wood",
        sell=(lambda: sells_this_band() and seller.due(cycle),
              products_in_pack,
              lambda: seller.sell(VENDORS[product][1], VENDORS[product][0], cycle)),
        unload=(unloads_this_band, dump.held, unloader.run),
    )


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
            stop = end_cycle(stall, "saving", cycle, tally, stop)
            continue

        value = skill.read()

        if value is not None and value != last_skill:
            last_skill = value
            stall.progressed()

        wanted = band_for(BANDS, value if value is not None else last_skill)

        if wanted is None:
            stop = "%s reads %s and no band covers it" % (skill_name, reading(value))
            break

        # Whether anyone buys changes with the band, so the paused trips get a fresh start too
        if wanted != product:
            log("%s at %s, making %s" % (skill_name, reading(value), wanted))
            product = wanted
            crafter.forget_last()
            seller.forget()

        held = dump.held()

        if output == "unload":
            if held >= dump_at:
                if unloader.run():
                    stop = end_cycle(stall, "unloading", cycle, tally, stop)
                    continue

                if unloader.misses >= MAX_DUMP_MISSES:
                    stop = ("%d unloads in a row moved nothing into '%s'"
                            % (unloader.misses, dump.name()))
                    break
        elif output == "sell":
            if VENDORS[product] is None:
                if held >= dump_at and dump.picked():
                    if unloader.run():
                        stop = end_cycle(stall, "unloading", cycle, tally, stop)
                        continue

                    if unloader.misses >= MAX_DUMP_MISSES:
                        stop = ("%d unloads in a row moved nothing into '%s'"
                                % (unloader.misses, dump.name()))
                        break
                elif held >= MAX_HELD and not dump.picked():
                    stop = "the pack holds %d unsold and nothing was picked to unload into" % held
                    break
            elif (products_in_pack() >= SELL_AT and seller.due(cycle)
                  and seller.sell(VENDORS[product][1], VENDORS[product][0], cycle)):
                stop = end_cycle(stall, "selling", cycle, tally, stop)
                continue
        elif held >= MAX_HELD:
            stop = "the pack holds %d and nothing was picked to unload into" % held
            break

        if wood.in_pack() < RESTOCK_AT:
            # An unreachable container also pulls nothing, which the stall watch ends
            pulled = restock.run()

            phase = try_make_room()

            if phase is not None:
                stop = end_cycle(stall, phase, cycle, tally, stop)
                continue

            if pulled == 0 and sources.stock_left() == 0 and wood_short(product) > 0:
                stop = ("out of %s wood - %s in the pack, none left in what you picked, and one "
                        "%s takes %d" % (WOOD_TYPE, wood.pack_report(), product, wood_cost(product)))
                break

            # A short pack that can still make something crafts
            if wood_short(product) > 0:
                stop = end_cycle(stall, "restocking", cycle, tally, stop)
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

            craft_recorder.record(outcome, value, spent_before, product)
            no_material = 0
            stall.progressed()
        elif outcome == "noMaterial":
            pulled = restock.run()

            phase = try_make_room()

            if phase is not None:
                stop = end_cycle(stall, phase, cycle, tally, stop)
                continue

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
        elif outcome == "noTool" and tool_store.picked() and tool_store.fetch():
            crafter.forget_last()
            stall.progressed()
            log("the tools ran out - fetched another")
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
                   wood.report(wood.pack_stock()))
            )

        stop = end_cycle(stall, outcome if outcome is not None else "unknown", cycle, tally, stop)
        API.Pause(STEP_DELAY)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    # Nothing else catches: a throw out of a client call used to end the run with no line at all
    if stop is None:
        stop = "threw - %s" % error
finally:
    recorder.close(skill.last())

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
