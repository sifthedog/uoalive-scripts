import API

from tinkering.config import (BANDS, BUTTON_STRIDE, CATEGORY_BUTTON_TYPE, CATEGORY_NAMES,
                              CONTAINER_RANGE, CONTEXT_TIMEOUT, CRAFT_POLL, CRAFT_TIMEOUT,
                              CRAFT_TITLE, CRAFT_TITLE_FRAGMENTS, CRAFT_TITLE_TEXT, DATA_PATH,
                              DUMP_AT, GUMP_POLL, GUMP_TIMEOUT, HEARTBEAT_EVERY, INGOT_COST,
                              INGOT_HUES, INGOT_TYPES, IRON, ITEM_BUTTON_TYPE, JOURNAL_TAIL_LINES,
                              JOURNAL_TAIL_SECONDS, LAST_TEN_LABEL, LOG_EVERY, MAKE_LAST_BUTTON,
                              MATERIAL_GRAPHICS, MAX_CYCLES, MAX_DUMP_MISSES, MAX_HELD,
                              MAX_NO_MATERIAL, MAX_NO_TOOL, MAX_SELL_MISSES, MAX_THROTTLED,
                              MAX_UNKNOWN, MAX_UNREADABLE_REPORTS, MIN_CRAFT_INGOTS, MIN_SKILL,
                              MOVE_DELAY, NOTES_PATH, NOTES_TAIL_SECONDS, OPEN_DELAY, OPL_WAIT,
                              OUTCOME_TEXT, OUTPUT_CHOICE, OUTPUT_OPTIONS, PATHFIND_TIMEOUT,
                              PICK_TIMEOUT, PRODUCTS, PRODUCT_GRAPHICS, RECIPES, REFUND_POLL,
                              REFUND_SETTLE, SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT, SAVING_TEXT,
                              SELL_AT, SELL_ENTRY, SELL_PHRASE, SELL_POLL, SELL_RETRY_AFTER,
                              SELL_TIMEOUT, SKILL_NAMES, SKILL_POLL, SKILL_TIMEOUT, STALL_STOP,
                              STALL_WARN, STEP_DELAY, STOCK_KINDS, STOPPED, THROTTLE_BACKOFF,
                              THROTTLE_BACKOFF_MAX, TOOL_GRAPHICS, TOOL_NAME_WORDS,
                              UNREADABLE_TEXT_LIMIT, VENDORS, VENDOR_RANGE, VENDOR_SCAN_RADIUS,
                              VENDOR_SERIAL, VENDOR_STEPS)
from uo.choice import Choice
from uo.cost import cost_of, short_by
from uo.craft import Crafter
from uo.craftmenu import CraftMenu
from uo.craftrun import CraftRecorder, Seller, Unloader, end_cycle
from uo.crafttool import CraftTool
from uo.dump import Dump
from uo.guards import dead, first_reason, skill_capped, stopped
from uo.heartbeat import Heartbeat
from uo.log import make_log
from uo.loop import StallWatch, backoff_for
from uo.materials import Materials
from uo.pack import count_of
from uo.notes import note_log
from uo.record import attempt_log
from uo.save import SaveWatch
from uo.skill import SkillReader, find_skill_name, reading
from uo.sources import Sources
from uo.stages import band_for
from uo.stock import StockBook
from uo.vendor import Vendor
from uo.vitals import position_and_weight

log = make_log("tinkering")
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


# The band's product only: a provisioner will not take the tongs left from the band before, and
# counting them would send the run selling every cycle
def products_in_pack():
    return count_of(PRODUCTS[product] if product is not None else PRODUCT_GRAPHICS)


def ingot_cost(item):
    return cost_of(item, INGOT_COST, MIN_CRAFT_INGOTS)


def ingots_short(item):
    return short_by(item, stock.in_pack(), INGOT_COST, MIN_CRAFT_INGOTS)


def unsold_ahead(value):
    for ceiling, name in BANDS:
        if VENDORS[name] is None and (ceiling is None or ceiling > value):
            return True

    return False


UNSOLD = [name for name in VENDORS if VENDORS[name] is None]


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

tools = CraftTool("tinker's tool", TOOL_GRAPHICS, TOOL_NAME_WORDS, log)
stock = StockBook({
    "noun": "ingots",
    "kinds": STOCK_KINDS,
    "types": INGOT_TYPES,
    "hues": INGOT_HUES,
    "wanted": IRON,
    "move_delay": MOVE_DELAY,
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
    "tool_noun": "tinker's tools",
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
}, log)
sources = Sources(stock, {
    "max_picks": 1,
    "pick_timeout": PICK_TIMEOUT,
    "open_delay": OPEN_DELAY,
    "move_delay": MOVE_DELAY,
    "container_range": CONTAINER_RANGE,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "box": None,
}, log)
notes = note_log(NOTES_PATH, log)
crafter = Crafter(tools, menu, stock, OUTCOME_TEXT, {
    "recipes": RECIPES,
    "make_last_button": MAKE_LAST_BUTTON,
    "gump_timeout": GUMP_TIMEOUT,
    "craft_timeout": CRAFT_TIMEOUT,
    "craft_poll": CRAFT_POLL,
    "max_reports": MAX_UNREADABLE_REPORTS,
    "text_limit": UNREADABLE_TEXT_LIMIT,
    "tail_seconds": JOURNAL_TAIL_SECONDS,
    "tail_lines": JOURNAL_TAIL_LINES,
    "notes_seconds": NOTES_TAIL_SECONDS,
    "material": IRON,
}, log, log.stamp, notes)
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
choice = Choice(OUTPUT_CHOICE, log, stop_reason)

start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)
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

if tools.serial() is None:
    log("no tinker's tools in the pack")
    API.Stop()

stock.lift_from_bags()

first = band_for(BANDS, start)

if first is None:
    log("%s reads %s and no band covers it" % (skill_name, reading(start)))
    API.Stop()

if ingots_short(first) > 0:
    log("the pack holds %s, and one %s takes %d ingots"
        % (stock.pack_report(), first, ingot_cost(first)))
    API.Stop()

output = choice.ask(OUTPUT_OPTIONS)

# Kept: a key carried in is a house key, not the run's, and it is never unloaded into a barrel
dump = Dump(sources, PRODUCTS, {
    "pick_timeout": PICK_TIMEOUT,
    "move_delay": MOVE_DELAY,
    "keep_existing": True,
}, log)

if output == "sell":
    dump.limit_to(UNSOLD)

if output == "unload":
    dump.pick()

    if not dump.picked():
        output = "keep"

if output == "sell":
    log("selling every %d to the band's vendor" % SELL_AT)

    if unsold_ahead(start):
        dump.pick()

        if not dump.picked():
            log("nothing picked to unload into - the run ends once the pack holds %d unsold products"
                % MAX_HELD)
elif output != "unload":
    output = "keep"
    log("keeping what is made - the run ends once the pack holds %d" % MAX_HELD)

cap = skill.cap()

log("%s at %s%s, %s in the pack"
    % (skill_name, reading(start), "/%.1f" % cap if cap is not None and cap > 0 else "",
       stock.pack_report()))

recorder = attempt_log(DATA_PATH, skill_name, log)
materials = Materials(stock, MATERIAL_GRAPHICS)
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


def out_of_ingots():
    return ("out of %s ingots - %s in the pack, and one %s takes %d"
            % (IRON, stock.pack_report(), product, ingot_cost(product)))


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

        # The vendor changes with the band, so the paused trips get a fresh start too
        if wanted != product:
            log("%s at %s, making %s" % (skill_name, reading(value), wanted))
            product = wanted
            crafter.forget_last()
            seller.forget()

        held = dump.held()

        if output == "unload":
            if held >= DUMP_AT:
                if unloader.run():
                    stop = end_cycle(stall, "unloading", cycle, tally, stop)
                    continue

                if unloader.misses >= MAX_DUMP_MISSES:
                    stop = ("%d unloads in a row moved nothing into '%s'"
                            % (unloader.misses, dump.name()))
                    break
        elif output == "sell":
            if VENDORS[product] is None:
                if held >= DUMP_AT and dump.picked():
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

        if ingots_short(product) > 0:
            stop = out_of_ingots()
            break

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
            # A bag of ingots the craft cannot reach into is the one refusal the run can fix
            if stock.lift_from_bags() > 0:
                no_material = 0
                stall.progressed()
            elif ingots_short(product) > 0:
                stop = out_of_ingots()
                break
            else:
                no_material += 1

                if no_material >= MAX_NO_MATERIAL:
                    stop = ("the shard refused %s in the pack %d times - read the gump's own words "
                            "above, and set the menu's material to %s"
                            % (stock.pack_report(), no_material, IRON))
                    break
        elif outcome == "saving":
            stall.progressed()
        elif outcome == "toolWorn":
            crafter.forget_last()
            stall.progressed()
            log("the tools wore out, looking for another set")
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s at %s" % (product, reading(value))
            break
        elif outcome == "noRow":
            stop = "'%s' is not in RECIPES" % product
            break
        elif outcome in ("noTool", "noGump"):
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = ("no tinker's tools left" if outcome == "noTool"
                        else "the craft menu will not open")
                break

            log("%s (%d/%d), trying again"
                % ("no tinker's tools in the pack" if outcome == "noTool"
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
                   stock.report(stock.pack_stock()))
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
