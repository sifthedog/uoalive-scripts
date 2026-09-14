import API

from alchemy.config import (BANDS, BATCH_CRAFTS, BUTTON_STRIDE, CATEGORY_BUTTON_TYPE,
                            CATEGORY_NAMES, CONTAINER_RANGE, CRAFT_POLL, CRAFT_TIMEOUT,
                            CRAFT_TITLE, CRAFT_TITLE_FRAGMENTS, CRAFT_TITLE_TEXT, DATA_PATH,
                            DUMP_AT, FETCH_POLL, FETCH_TIMEOUT, GUMP_POLL, GUMP_TIMEOUT,
                            HEARTBEAT_EVERY, ITEM_BUTTON_TYPE, JOURNAL_TAIL_LINES,
                            JOURNAL_TAIL_SECONDS, KEG_FILLED_TEXT, KEG_GRAPHICS, KEG_NAME_WORDS,
                            KIND_ORDER, LAST_TEN_LABEL, LOG_EVERY, MAKE_LAST_BUTTON, MAX_CYCLES,
                            MAX_DUMP_MISSES, MAX_EMPTY_MOVES, MAX_HELD, MAX_KEG_MISSES,
                            MAX_NO_MATERIAL, MAX_NO_TOOL, MAX_PICKS, MAX_THROTTLED,
                            MAX_UNKNOWN, MAX_UNREADABLE_REPORTS, MIN_SKILL, MOVE_DELAY, NEEDS,
                            NOTES_PATH, NOTES_TAIL_SECONDS, OPEN_DELAY, OUTCOME_TEXT,
                            PATHFIND_TIMEOUT, PICK_TIMEOUT, PRODUCTS, RECIPES, REFUND_POLL,
                            REFUND_SETTLE, RESTOCK_AT, SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT,
                            SAVING_TEXT, SETUP, SKILL_NAMES, SKILL_POLL, SKILL_TIMEOUT,
                            STALL_STOP, STALL_WARN, STEP_DELAY, STOCK_KINDS, STOPPED,
                            THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX, TOOL_GRAPHICS,
                            TOOL_NAME_WORDS, TOO_HEAVY_TEXT, UNREADABLE_TEXT_LIMIT)
from alchemy.kegs import Kegs
from uo.components import affordable, short_of, shortfall_report
from uo.craft import Crafter
from uo.craftmenu import CraftMenu
from uo.craftrun import CraftRecorder, Unloader, end_cycle, make_room
from uo.crafttool import CraftTool
from uo.dump import Dump
from uo.guards import dead, first_reason, skill_capped, stopped
from uo.heartbeat import Heartbeat
from uo.log import make_log
from uo.loop import StallWatch, backoff_for
from uo.materials import Materials
from uo.notes import note_log
from uo.record import attempt_log
from uo.restock import Restock
from uo.save import SaveWatch
from uo.setup import Setup
from uo.skill import SkillReader, find_skill_name, reading
from uo.sources import Sources
from uo.stages import band_for, band_rows
from uo.stock import StockBook
from uo.toolstore import ToolStore
from uo.vitals import position_and_weight

log = make_log("alchemy")
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


def short_for(item):
    return short_of(NEEDS[item], stock.pack_stock())


def crafts_left(item):
    return affordable(NEEDS[item], stock.pack_stock())


# Only the kinds the band spends, enough for BATCH_CRAFTS of it
def targets_for(item):
    return dict((kind, BATCH_CRAFTS * NEEDS[item][kind]) for kind in NEEDS[item])


def needs_report(item):
    return shortfall_report(NEEDS[item], KIND_ORDER)


def left_in_sources(kinds):
    total = 0

    for entry in sources.picked():
        counts = sources.counts(entry)
        total += sum(counts.get(kind, 0) for kind in kinds)

    return total


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

tools = CraftTool("mortar and pestle", TOOL_GRAPHICS, TOOL_NAME_WORDS, log)
stock = StockBook({
    "noun": "bottles and reagents",
    "kinds": STOCK_KINDS,
    "types": [],
    "hues": {},
    "wanted": None,
    "move_delay": MOVE_DELAY,
}, log)
sources = Sources(stock, {
    "max_picks": MAX_PICKS,
    "pick_timeout": PICK_TIMEOUT,
    "open_delay": OPEN_DELAY,
    "move_delay": MOVE_DELAY,
    "container_range": CONTAINER_RANGE,
    "pathfind_timeout": PATHFIND_TIMEOUT,
    "box": None,
}, log)
# batch is unread: every run hands the restock a per-kind target
restock = Restock(stock, sources, {
    "batch": 0,
    "move_delay": MOVE_DELAY,
    "max_empty_moves": MAX_EMPTY_MOVES,
    "return_wrong_wood": False,
    "heavy_text": TOO_HEAVY_TEXT,
}, log)
# Kept: a potion carried in is not the run's
dump = Dump(sources, PRODUCTS, {
    "pick_timeout": PICK_TIMEOUT,
    "move_delay": MOVE_DELAY,
    "keep_existing": True,
}, log)
kegs = Kegs(dump, {
    "graphics": KEG_GRAPHICS,
    "words": KEG_NAME_WORDS,
    "filled_text": KEG_FILLED_TEXT,
    "move_delay": MOVE_DELAY,
}, log)
tool_store = ToolStore(tools, sources, {
    "noun": "mortars and pestles",
    "pick_timeout": PICK_TIMEOUT,
    "move_delay": MOVE_DELAY,
    "fetch_timeout": FETCH_TIMEOUT,
    "fetch_poll": FETCH_POLL,
}, log)
setup = Setup(SETUP, log, stop_reason)
menu = CraftMenu(tools, {
    "stride": BUTTON_STRIDE,
    "category_type": CATEGORY_BUTTON_TYPE,
    "item_type": ITEM_BUTTON_TYPE,
    "category_names": CATEGORY_NAMES,
    "last_ten_label": LAST_TEN_LABEL,
    "title": CRAFT_TITLE,
    "title_text": CRAFT_TITLE_TEXT,
    "title_fragments": CRAFT_TITLE_FRAGMENTS,
    "tool_noun": "mortars and pestles",
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
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
    "material": "empty bottles and reagents",
}, log, log.stamp, notes)

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
first = band_for(BANDS, start)

if first is None:
    log("%s reads %s and no band covers it" % (skill_name, reading(start)))
    API.Stop()


def training_rows():
    heading = "%s %s%s" % (skill_name, reading(start),
                           " / %.1f" % cap if cap is not None and cap > 0 else "")

    return heading, band_rows(BANDS, start, needs_report, MIN_SKILL)


answers = setup.ask({
    "table": training_rows,
    "tools": tool_store.pick,
    "tools_ready": lambda: tool_store.count() > 0,
    "source": sources.pick_one,
    "clear": sources.clear,
    "unload": dump.pick_line,
    "unload_ready": dump.picked,
    "has_wood": lambda: stock.in_pack() > 0,
    "unsold_ahead": None,
})

# The stop lands at the next Pause, so the lines until then read a form that was never answered
output = answers["output"] if answers is not None else "kegs"
dump_at = answers["dump_at"] if answers is not None else DUMP_AT
log.enabled = answers["debug_logs"] if answers is not None else False

if answers is None:
    API.Stop()

# The radio, not the cursor: a container picked before switching to Keep stays unused
unloading = output == "unload"
kegging = output == "kegs"

if unloading:
    log("unloading every %d potions" % dump_at)
elif kegging:
    log("pouring into the kegs in the pack - a bottled potion goes onto the first empty keg")
else:
    log("keeping what is made - the run ends once the pack holds %d potions" % MAX_HELD)

# A picked tool container fills an empty pack before the first craft
if (tools.find(FETCH_TIMEOUT, FETCH_POLL) is None
        and not (tool_store.picked() and tool_store.fetch())):
    log("no mortar and pestle in the pack")
    API.Stop()

log("%s at %s%s, %s in the pack, %s"
    % (skill_name, reading(start), "/%.1f" % cap if cap is not None and cap > 0 else "",
       stock.pack_report(), sources.stock_line()))

stock.lift_from_bags()

# Past the last ceiling the start-up Stop has not landed yet; the loop's band check ends the run
if first is not None and crafts_left(first) < RESTOCK_AT:
    restock.run(targets_for(first))

recorder = attempt_log(DATA_PATH, skill_name, log)
materials = Materials(stock, set())
craft_recorder = CraftRecorder(recorder, materials, REFUND_SETTLE, REFUND_POLL)
unloader = Unloader(dump)
kegger = Unloader(kegs)

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
product = None
last_skill = start


# A pack the shard will not load for weight is unloaded first, when there is anything in it to move
def try_make_room():
    return make_room(restock, log, "", unload=(lambda: unloading, dump.held, unloader.run))


def out_of_stock():
    return ("out of %s - %s in the pack, none left in what you picked, and one %s takes %s"
            % (shortfall_report(short_for(product), KIND_ORDER), stock.pack_report(), product,
               needs_report(product)))


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

        if wanted != product:
            log("%s at %s, making %s (%s)"
                % (skill_name, reading(value), wanted, needs_report(wanted)))
            product = wanted
            crafter.forget_last()

        held = dump.held()

        if unloading and held >= dump_at:
            if unloader.run():
                stop = end_cycle(stall, "unloading", cycle, tally, stop)
                continue

            if unloader.misses >= MAX_DUMP_MISSES:
                stop = ("%d unloads in a row moved nothing into '%s'"
                        % (unloader.misses, dump.name()))
                break
        elif kegging and held > 0:
            if kegger.run():
                stall.progressed()
            elif kegger.misses >= MAX_KEG_MISSES:
                stop = ("%d keg runs in a row poured nothing - no empty keg in the pack, or the "
                        "drop was refused" % kegger.misses)
                break
        elif not unloading and not kegging and held >= MAX_HELD:
            stop = "the pack holds %d potions and nothing was picked to unload into" % held
            break

        if crafts_left(product) < RESTOCK_AT:
            # An unreachable container also pulls nothing, which the stall watch ends
            pulled = restock.run(targets_for(product))

            phase = try_make_room()

            if phase is not None:
                stop = end_cycle(stall, phase, cycle, tally, stop)
                continue

            short = short_for(product)

            if pulled == 0 and len(short) > 0 and left_in_sources(short) == 0:
                stop = out_of_stock()
                break

            # A short pack that can still make something crafts
            if len(short) > 0:
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
            pulled = restock.run(targets_for(product))

            phase = try_make_room()

            if phase is not None:
                stop = end_cycle(stall, phase, cycle, tally, stop)
                continue

            short = short_for(product)

            if pulled > 0:
                no_material = 0
                stall.progressed()
            elif len(short) > 0 and left_in_sources(short) == 0:
                stop = out_of_stock()
                break
            else:
                # Everything the recipe takes is in the pack and refused: the row is another potion
                no_material += 1

                if no_material >= MAX_NO_MATERIAL:
                    stop = ("the shard refused %s in the pack %d times - read the gump's own words "
                            "above; the row pressed may not be %s" % (stock.pack_report(),
                                                                      no_material, product))
                    break
        elif outcome == "saving":
            stall.progressed()
        elif outcome == "toolWorn":
            crafter.forget_last()
            stall.progressed()
            log("the mortar wore out, looking for another")
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s at %s" % (product, reading(value))
            break
        elif outcome == "noRow":
            stop = "'%s' is not in RECIPES" % product
            break
        elif outcome == "noTool" and tool_store.picked() and tool_store.fetch():
            crafter.forget_last()
            stall.progressed()
            log("the mortars ran out - fetched another")
        elif outcome in ("noTool", "noGump"):
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = ("no mortar and pestle left" if outcome == "noTool"
                        else "the craft menu will not open")
                break

            log("%s (%d/%d), trying again"
                % ("no mortar and pestle in the pack" if outcome == "noTool"
                   else "the mortar opened no craft menu", no_tool, MAX_NO_TOOL))
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
