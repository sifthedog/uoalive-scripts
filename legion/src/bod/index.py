import API

from bod.combine import DeedCombiner
from bod.config import (ARTICLES, BOD_COMBINE_BUTTON, BOD_GUMP_TEXT, BUTTON_STRIDE,
                        CATEGORY_BUTTON_TYPE, CATEGORY_NAMES, COMBINE_POLL, COMBINE_TEXT,
                        COMBINE_TIMEOUT, CRAFT_POLL, CRAFT_SETTLE, CRAFT_TIMEOUT, CRAFT_TITLE,
                        CRAFT_TITLE_FRAGMENTS, CRAFT_TITLE_TEXT, DEED_TEXT, EXCEPTIONAL_TEXT,
                        GUMP_POLL, GUMP_TIMEOUT, HEARTBEAT_EVERY, INGOT_GRAPHICS, INGOT_HUES,
                        INGOT_NAME_WORDS, ITEM_BUTTON_TYPE, JOURNAL_TAIL_LINES,
                        JOURNAL_TAIL_SECONDS, LAST_TEN_LABEL, MAKE_LAST_BUTTON, MATERIAL_ALIASES,
                        MATERIAL_BUTTON_TYPE, MATERIAL_ROW_TYPE, MAX_CATEGORIES, MAX_CYCLES,
                        MAX_ITEM_PROBES, MAX_ITEM_ROWS, MAX_MATERIAL_ROWS, MAX_NO_CURSOR,
                        MAX_NO_TOOL, MAX_THROTTLED, MAX_UNKNOWN, MAX_UNREADABLE_REPORTS,
                        OPL_ASKS, OPL_SETTLE, OPL_TIMEOUT, OUTCOME_TEXT, PICK_TIMEOUT,
                        PLAIN_MATERIAL, REREAD_POLL, REREAD_SETTLE, SAVE_DONE_TEXT, SAVE_POLL,
                        SAVE_WAIT, SAVING_TEXT, SKILL_NAMES, STALL_STOP, STALL_WARN, STEP_DELAY,
                        STOPPED, TARGET_TIMEOUT, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX,
                        TOOL_GRAPHICS, TOOL_NAME_WORDS, UNREADABLE_TEXT_LIMIT)
from bod.craft import DeedCrafter
from bod.deed import Deed
from bod.items import ItemBook
from bod.material import MaterialPicker
from uo.craftmenu import CraftMenu
from uo.crafttool import CraftTool
from uo.entity import hex_of
from uo.guards import dead, first_reason, stopped
from uo.heartbeat import Heartbeat
from uo.log import make_log
from uo.loop import StallWatch, backoff_for
from uo.pack import amount_of, hue_of, pack_contents
from uo.save import SaveWatch
from uo.skill import SkillReader, find_skill_name, reading
from uo.text import word_in
from uo.vitals import position_and_weight

log = make_log("bod")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "combined", position_and_weight)
stall = StallWatch("cycles without progress", STALL_WARN, STALL_STOP, heartbeat, log)

if API.HasTarget():
    API.CancelTarget()


def stop_reason():
    return first_reason([stopped(STOPPED), dead()])


def is_ingot(item):
    return item.Graphic in INGOT_GRAPHICS or word_in(item.Name, INGOT_NAME_WORDS)


def ingot_report():
    counts = {}

    for item in pack_contents():
        if not is_ingot(item):
            continue

        hue = hue_of(item)
        name = INGOT_HUES.get(hue, "hue %s" % hex_of(hue))
        counts[name] = counts.get(name, 0) + amount_of(item)

    if len(counts) == 0:
        return "no ingots"

    return ", ".join("%d %s" % (counts[name], name) for name in sorted(counts))


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)
skill_name = find_skill_name(SKILL_NAMES)
skill = SkillReader(skill_name) if skill_name is not None else None

log("target the small bulk order deed to fill, ESC to stop")

picked = API.RequestTarget(PICK_TIMEOUT)

if API.HasTarget():
    API.CancelTarget()

if not picked:
    log("nothing targeted - stopping")
    API.Stop()

deed = Deed(picked, {
    "text": DEED_TEXT,
    "plain": PLAIN_MATERIAL,
    "articles": ARTICLES,
    "opl_timeout": OPL_TIMEOUT,
    "reread_settle": REREAD_SETTLE,
    "reread_poll": REREAD_POLL,
}, log)

request, refused = deed.read()

if request is None:
    log("%s is not a deed this run can fill: %s" % (hex_of(picked), refused))
    API.Stop()

deed_item = API.FindItem(picked)
root = getattr(deed_item, "RootContainer", None) if deed_item is not None else None

if root is not None and root != API.Backpack:
    log("the deed has to be in your pack - the shard refuses a combine from anywhere else")
    API.Stop()

tool = CraftTool("smith's tool", TOOL_GRAPHICS, TOOL_NAME_WORDS, log)

if tool.serial() is None:
    log("no smith's hammer or tongs in the pack")
    API.Stop()

items = ItemBook(request, {
    "aliases": MATERIAL_ALIASES,
    "plain": PLAIN_MATERIAL,
    "articles": ARTICLES,
    "exceptional_text": EXCEPTIONAL_TEXT,
    "opl_timeout": OPL_TIMEOUT,
    "opl_settle": OPL_SETTLE,
    "asks": OPL_ASKS,
}, log)
menu = CraftMenu(tool, {
    "stride": BUTTON_STRIDE,
    "category_type": CATEGORY_BUTTON_TYPE,
    "item_type": ITEM_BUTTON_TYPE,
    "category_names": CATEGORY_NAMES,
    "last_ten_label": LAST_TEN_LABEL,
    "title": CRAFT_TITLE,
    "title_text": CRAFT_TITLE_TEXT,
    "title_fragments": CRAFT_TITLE_FRAGMENTS,
    "tool_noun": "smith's tools",
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
    "max_categories": MAX_CATEGORIES,
    "max_item_rows": MAX_ITEM_ROWS,
}, log)
picker = MaterialPicker(menu, {
    "aliases": MATERIAL_ALIASES,
    "button_type": MATERIAL_BUTTON_TYPE,
    "row_type": MATERIAL_ROW_TYPE,
    "max_rows": MAX_MATERIAL_ROWS,
    "gump_timeout": GUMP_TIMEOUT,
}, log)
crafter = DeedCrafter(tool, menu, items, picker, OUTCOME_TEXT, {
    "make_last_button": MAKE_LAST_BUTTON,
    "craft_timeout": CRAFT_TIMEOUT,
    "craft_poll": CRAFT_POLL,
    "craft_settle": CRAFT_SETTLE,
    "max_probes": MAX_ITEM_PROBES,
    "max_categories": MAX_CATEGORIES,
    "max_reports": MAX_UNREADABLE_REPORTS,
    "text_limit": UNREADABLE_TEXT_LIMIT,
    "tail_seconds": JOURNAL_TAIL_SECONDS,
    "tail_lines": JOURNAL_TAIL_LINES,
}, log)
combiner = DeedCombiner(deed, items, COMBINE_TEXT, {
    "combine_button": BOD_COMBINE_BUTTON,
    "gump_text": BOD_GUMP_TEXT,
    "gump_timeout": GUMP_TIMEOUT,
    "gump_poll": GUMP_POLL,
    "target_timeout": TARGET_TIMEOUT,
    "combine_timeout": COMBINE_TIMEOUT,
    "combine_poll": COMBINE_POLL,
    "max_reports": MAX_UNREADABLE_REPORTS,
    "text_limit": UNREADABLE_TEXT_LIMIT,
    "tail_seconds": JOURNAL_TAIL_SECONDS,
    "tail_lines": JOURNAL_TAIL_LINES,
}, log)

start = skill.read() if skill is not None else None

log("%s: %s%s, %s in the pack"
    % (deed.describe(), skill_name or "Blacksmithy", " at %s" % reading(start), ingot_report()))

stop = None
done = request["done"]
combined = 0
made = 0
fails = 0
unknown = 0
throttled = 0
no_tool = 0
no_cursor = 0
cycle = 0
said_throttle = False


def end_cycle(phase):
    global stop

    stall.end_cycle(phase, cycle, combined)

    if stop is None:
        stop = stall.reason()


def owed():
    return request["total"] - done


try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1

        stop = stop_reason()

        if stop is not None:
            break

        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            stall.progressed()
            end_cycle("saving")
            continue

        if owed() <= 0:
            stop = "the deed is full"
            break

        candidate = items.qualifying()

        if candidate is not None:
            outcome = combiner.combine(candidate)

            if outcome == "combined":
                combined += 1
                no_cursor = 0
                items.forget_missing()
                done = deed.settle_after_combine(done + 1)
                stall.progressed()
                log("combined %s (%d/%d)" % (hex_of(candidate), done, request["total"]))
            elif outcome == "full":
                stop = "the deed is full"
                break
            elif outcome in ("notRequested", "notExceptional", "wrongMaterial", "tooMany"):
                items.reject(candidate)
                stall.progressed()
                log("the deed refused %s (%s), leaving it in the pack" % (hex_of(candidate), outcome))

                if outcome == "wrongMaterial":
                    picker.forget()
                    crafter.forget_last()
            elif outcome == "notInPack":
                stop = "the shard says the item is not in your pack - is the deed in a bag?"
                break
            elif outcome in ("noCursor", "noGump"):
                no_cursor += 1

                if no_cursor >= MAX_NO_CURSOR:
                    stop = ("the deed's gump raised no cursor %d times - check BOD_COMBINE_BUTTON"
                            % MAX_NO_CURSOR)
                    break

                API.Pause(backoff_for(no_cursor, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
            else:
                unknown += 1
                log("unreadable combine outcome (%d/%d), check COMBINE_TEXT" % (unknown, MAX_UNKNOWN))

            if unknown >= MAX_UNKNOWN:
                stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
                break

            end_cycle(outcome if outcome is not None else "unknown")
            API.Pause(STEP_DELAY)
            continue

        outcome = crafter.craft_once(request["item"], request["material"])

        if outcome != "throttled":
            throttled = 0

        if outcome is not None:
            unknown = 0

        if outcome in ("made", "failed"):
            if outcome == "made":
                made += 1
            else:
                fails += 1

            stall.progressed()
        elif outcome == "noMaterial":
            stop = ("the shard says there are not enough %s ingots - %s in the pack, %d still owed"
                    % (request["material"], ingot_report(), owed()))
            break
        elif outcome in ("wrongRow", "saving"):
            stall.progressed()
        elif outcome == "toolWorn":
            crafter.forget_last()
            stall.progressed()
            log("the tool wore out, looking for another")
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s" % request["item"]
            break
        elif outcome == "noAnvil":
            stop = "stand next to an anvil and a forge"
            break
        elif outcome == "noRow":
            stop = "could not find the SELECTIONS row for '%s'" % request["item"]
            break
        elif outcome == "noMaterialRow":
            stop = "the material page has no row for %s" % request["material"]
            break
        elif outcome in ("noTool", "noGump"):
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = ("no smith's tool left" if outcome == "noTool"
                        else "the craft menu will not open")
                break

            log("%s (%d/%d), trying again"
                % ("no smith's tool in the pack" if outcome == "noTool"
                   else "the tool opened no craft menu", no_tool, MAX_NO_TOOL))
            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
        elif outcome == "throttled":
            throttled += 1

            if throttled >= MAX_THROTTLED:
                stop = "%d throttled crafts in a row" % MAX_THROTTLED
                break

            waiting = backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX)

            if not said_throttle:
                said_throttle = True
                log("the shard is pacing the crafts - waiting %.1fs" % waiting)

            API.Pause(waiting)
        else:
            unknown += 1
            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        if outcome not in ("noTool", "noGump"):
            no_tool = 0

        if unknown >= MAX_UNKNOWN:
            stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
            break

        end_cycle(outcome if outcome is not None else "unknown")
        API.Pause(STEP_DELAY)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    if stop is None:
        stop = "threw - %s" % error

up = API.HasGump()

if up:
    API.CloseGump(up)

if API.HasTarget():
    API.CancelTarget()

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES

log("%d combined, %d made, %d failed, %d/%d in the deed"
    % (combined, made, fails, done, request["total"]))
log("stopping - %s" % reason)
API.Stop()
