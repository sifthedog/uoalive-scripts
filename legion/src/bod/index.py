import API

from bod.box import DeedBox
from bod.checks import ingot_report, preflight
from bod.combine import DeedCombiner
from bod.config import (ARTICLES, BATCH_IDLE, BOD_COMBINE_BUTTON, BOD_GUMP_TEXT, BOX_NAMES,
                        BOX_POLL, BOX_TIMEOUT, BUTTON_STRIDE, CANCEL_MAKE_BUTTON,
                        CATEGORY_BUTTON_TYPE, CATEGORY_NAMES, CHECK_BEFORE_START, COMBINE_POLL,
                        COMBINE_TEXT, COMBINE_TIMEOUT, CONTEXT_TIMEOUT, CRAFT_INTERVAL,
                        CRAFT_POLL, CRAFT_SETTLE, CRAFT_TIMEOUT, CRAFT_TITLE,
                        CRAFT_TITLE_FRAGMENTS, CRAFT_TITLE_TEXT, DEED_GRAPHICS, DEED_NAME_WORDS,
                        DEED_TEXT, EXCEPTIONAL_TEXT, GUMP_POLL, GUMP_TIMEOUT, HEARTBEAT_EVERY,
                        INGOT_COST, INGOT_GRAPHICS, INGOT_HUES, INGOT_NAME_WORDS,
                        ITEM_BUTTON_TYPE, JOURNAL_TAIL_LINES, JOURNAL_TAIL_SECONDS,
                        LARGE_COMBINE_BUTTON, LARGE_COMBINE_TEXT, LAST_TEN_LABEL,
                        MAKE_NUMBER_BUTTON, MATERIAL_ALIASES, MATERIAL_BUTTON_TYPE,
                        MATERIAL_ORDER, MATERIAL_ROW_TYPE, MATERIAL_ROWS_AFTER, MAX_CATEGORIES,
                        MAX_CYCLES, MAX_ITEM_ROWS, MAX_MATERIAL_ROWS, MAX_NO_CURSOR,
                        MAX_NO_TOOL, MAX_THROTTLED, MAX_UNKNOWN, MAX_UNREADABLE_REPORTS,
                        MOVE_DELAY, OPEN_DELAY, OPL_ASKS, OPL_SETTLE, OPL_TIMEOUT, OUTCOME_TEXT,
                        PICK_TIMEOUT, PLAIN_MATERIAL, PROMPT_DELAY, RECIPES, REREAD_POLL,
                        REREAD_SETTLE, SALVAGE_AT_END, SALVAGE_ENTRIES, SALVAGE_SETTLE,
                        SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT, SAVING_TEXT, SKILL_NAMES,
                        STALL_STOP, STALL_WARN, STEP_DELAY, STOPPED, TARGET_TIMEOUT,
                        THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX, TOOL_BAG_NAMES, TOOL_GRAPHICS,
                        TOOL_NAME_WORDS, TOOL_PREFERENCE, UNREADABLE_TEXT_LIMIT, USES_TEXT)
from bod.craft import DeedCrafter
from bod.deed import Deed, entry_request
from bod.fill import SmallFill
from bod.items import ItemBook
from bod.material import MaterialPicker
from bod.smalls import find_small_deeds
from uo.craftmenu import CraftMenu
from uo.crafttool import CraftTool
from uo.entity import hex_of, player
from uo.guards import dead, first_reason, stopped
from uo.heartbeat import Heartbeat
from uo.log import make_log
from uo.loop import StallWatch
from uo.pack import pack_contents
from uo.save import SaveWatch
from uo.skill import SkillReader, find_skill_name, reading
from uo.text import any_in
from uo.vitals import position_and_weight

log = make_log("bod")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "combined", position_and_weight)
stall = StallWatch("cycles without progress", STALL_WARN, STALL_STOP, heartbeat, log)

if API.HasTarget():
    API.CancelTarget()


def stop_reason():
    return first_reason([stopped(STOPPED), dead()])


# RootContainer resolves to the mobile carrying the item, not to the backpack
def in_pack(item):
    me = player()
    mine = [API.Backpack] + ([me.Serial] if me is not None else [])

    return (getattr(item, "Container", None) in mine
            or getattr(item, "RootContainer", None) in mine)


INGOTS = {
    "ingot_graphics": INGOT_GRAPHICS,
    "ingot_words": INGOT_NAME_WORDS,
    "materials": sorted(set(INGOT_HUES.values()), key=len, reverse=True),
    "hues": INGOT_HUES,
    "costs": INGOT_COST,
    "uses_text": USES_TEXT,
    "opl_timeout": OPL_TIMEOUT,
}

DEEDS = {
    "text": DEED_TEXT,
    "plain": PLAIN_MATERIAL,
    "articles": ARTICLES,
    "opl_timeout": OPL_TIMEOUT,
    "reread_settle": REREAD_SETTLE,
    "reread_poll": REREAD_POLL,
    "deed_graphics": DEED_GRAPHICS,
    "deed_words": DEED_NAME_WORDS,
}

COMBINES = {
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
}


def combine_config(button):
    config = dict(COMBINES)
    config["combine_button"] = button

    return config


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)
skill_name = find_skill_name(SKILL_NAMES)
skill = SkillReader(skill_name) if skill_name is not None else None

log("target the bulk order deed to fill, small or large, ESC to stop")

picked = API.RequestTarget(PICK_TIMEOUT)

if API.HasTarget():
    API.CancelTarget()

if not picked:
    log("nothing targeted - stopping")
    API.Stop()

deed = Deed(picked, DEEDS, log)
request, refused = deed.read()

if request is None:
    log("%s is not a deed this run can fill: %s" % (hex_of(picked), refused))
    API.Stop()

deed_item = API.FindItem(picked)

if deed_item is not None and not in_pack(deed_item):
    log("the deed has to be in your pack - the shard refuses a combine from anywhere else "
        "(container %s, root %s)" % (hex_of(getattr(deed_item, "Container", 0) or 0),
                                     hex_of(getattr(deed_item, "RootContainer", 0) or 0)))
    API.Stop()

bag = None

# ItemsInContainer reads nothing out of a bag the client has not seen inside
for held in pack_contents():
    if any_in(held.Name, TOOL_BAG_NAMES):
        API.UseObject(held.Serial)
        API.Pause(OPEN_DELAY)
        log("opened '%s' - the tools, the pieces and the salvage are all in it" % held.Name)
        bag = held.Serial
        break

if bag is None:
    log("no %s in the pack - combining from the pack itself, and salvaging nothing"
        % " or ".join(TOOL_BAG_NAMES))

tool = CraftTool("smith's tool", TOOL_GRAPHICS, TOOL_NAME_WORDS, log, TOOL_PREFERENCE)

if tool.serial() is None:
    log("no smith's hammer or tongs in the pack")
    API.Stop()

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
    "order": MATERIAL_ORDER,
    "rows_after": MATERIAL_ROWS_AFTER,
    "button_type": MATERIAL_BUTTON_TYPE,
    "row_type": MATERIAL_ROW_TYPE,
    "max_rows": MAX_MATERIAL_ROWS,
    "gump_timeout": GUMP_TIMEOUT,
}, log)

FILL = {
    # The pieces land beside the tool, so the bag is what the deed is aimed at
    "combine_target": bag if bag is not None else API.Backpack,
    "bag": bag,
    "salvage": SALVAGE_AT_END,
    "salvage_entries": SALVAGE_ENTRIES,
    "context_timeout": CONTEXT_TIMEOUT,
    "salvage_settle": SALVAGE_SETTLE,
    "ingots": INGOTS,
    "max_cycles": MAX_CYCLES,
    "max_unknown": MAX_UNKNOWN,
    "max_throttled": MAX_THROTTLED,
    "max_no_tool": MAX_NO_TOOL,
    "max_no_cursor": MAX_NO_CURSOR,
    "backoff": THROTTLE_BACKOFF,
    "backoff_max": THROTTLE_BACKOFF_MAX,
    "step_delay": STEP_DELAY,
}

WATCH = {
    "heartbeat": heartbeat,
    "stall": stall,
    "saves": saves,
    "stop_reason": stop_reason,
}

fills = []


# One small deed, start to finish: its own tooltip book, combiner and row proof
def fill_small(small):
    items = ItemBook(small.request, {
        "aliases": MATERIAL_ALIASES,
        "plain": PLAIN_MATERIAL,
        "articles": ARTICLES,
        "exceptional_text": EXCEPTIONAL_TEXT,
        "opl_timeout": OPL_TIMEOUT,
        "opl_settle": OPL_SETTLE,
        "asks": OPL_ASKS,
    }, log)
    crafter = DeedCrafter(tool, menu, items, picker, OUTCOME_TEXT, {
        "make_number_button": MAKE_NUMBER_BUTTON,
        "cancel_button": CANCEL_MAKE_BUTTON,
        "prompt_delay": PROMPT_DELAY,
        "craft_interval": CRAFT_INTERVAL,
        "batch_idle": BATCH_IDLE,
        "gump_timeout": GUMP_TIMEOUT,
        "craft_timeout": CRAFT_TIMEOUT,
        "craft_poll": CRAFT_POLL,
        "craft_settle": CRAFT_SETTLE,
        "recipes": RECIPES,
        "max_categories": MAX_CATEGORIES,
        "max_reports": MAX_UNREADABLE_REPORTS,
        "text_limit": UNREADABLE_TEXT_LIMIT,
        "tail_seconds": JOURNAL_TAIL_SECONDS,
        "tail_lines": JOURNAL_TAIL_LINES,
    }, log)
    combiner = DeedCombiner(small, items, COMBINE_TEXT, combine_config(BOD_COMBINE_BUTTON), log)
    fill = SmallFill(small, items, crafter, picker, combiner, FILL, log, WATCH)
    fills.append(fill)

    return fill.run()


# True when the run may go on. Stop() ends the script only at the next client call, so nothing
# here relies on it: each flow returns its reason and finish() is called once
def check(requests):
    if not CHECK_BEFORE_START:
        return True

    problems, notes = preflight(requests, tool.serials(), INGOTS)

    for note in notes:
        log(note)

    for problem in problems:
        log("not enough: " + problem)

    if len(problems) > 0:
        log("stopping before the first craft - set CHECK_BEFORE_START = False to run anyway")

    return len(problems) == 0


def finish(reason):
    up = API.HasGump()

    if up:
        API.CloseGump(up)

    if API.HasTarget():
        API.CancelTarget()

    for fill in fills:
        log(fill.summary())

    log("stopping - %s" % reason)
    API.Stop()


def run_small():
    if not check([request]):
        return "not enough to start"

    return fill_small(deed) or "the deed is full"


def small_deed_for(item, smalls):
    known = smalls.get(item)

    if known is None:
        return None

    small = Deed(known["serial"], DEEDS, log)
    small.read()

    return small


# The smalls in the pack first, the box for the rest, each small filled and combined into the
# large in the deed's own order
def run_large():
    pending = [(item, done) for item, done in request["entries"] if done < request["total"]]

    if len(pending) == 0:
        return "the large deed is already complete"

    smalls = find_small_deeds(request, picked, DEEDS)

    if not check([entry_request(request, item, smalls[item]["done"] if item in smalls else 0)
                  for item, _done in pending]):
        return "not enough to start"

    missing = [item for item, _done in pending if item not in smalls]

    if len(missing) > 0:
        log("%d of %d entries have no small deed in the pack: %s"
            % (len(missing), len(pending), ", ".join(missing)))
        box = DeedBox({
            "names": BOX_NAMES,
            "deed_graphics": DEED_GRAPHICS,
            "deed_words": DEED_NAME_WORDS,
            "move_delay": MOVE_DELAY,
            "timeout": BOX_TIMEOUT,
            "poll": BOX_POLL,
        }, log)
        box_serial = box.find()

        if box_serial is None:
            return "no %s in the pack to get the small deeds from" % " or ".join(BOX_NAMES)

        if not box.generate(box_serial, picked):
            return "the box gave no small deeds"

        smalls = find_small_deeds(request, picked, DEEDS)
        missing = [item for item, _done in pending if item not in smalls]

        if len(missing) > 0:
            return "still no small deed for %s after the box" % ", ".join(missing)

    large_combiner = DeedCombiner(deed, None, LARGE_COMBINE_TEXT,
                                  combine_config(LARGE_COMBINE_BUTTON), log)
    index = 0

    for item, _done in pending:
        index += 1
        small = small_deed_for(item, smalls)

        if small is None or small.request is None:
            return "could not read the small deed for %s" % item

        log("entry %d/%d: %s, small deed %s with %d/%d done"
            % (index, len(pending), item, hex_of(small.serial), small.request["done"],
               small.request["total"]))

        if small.request["done"] < small.request["total"]:
            stop = fill_small(small)

            if stop is not None:
                return "%s (on entry %d/%d, %s)" % (stop, index, len(pending), item)

        outcome, taken = large_combiner.combine(small.serial, [small.serial])

        if len(taken) == 0 and outcome not in ("combined", "full"):
            return ("the large deed refused the small deed %s for %s (%s) - read the line above"
                    % (hex_of(small.serial), item, outcome))

        log("%s is in the large deed (%d/%d)" % (item, index, len(pending)))

    final, _refused = deed.read()

    if final is not None and all(done >= final["total"] for _item, done in final["entries"]):
        return "the large deed is complete"

    return "every entry was combined, but the large deed reads %s" % (
        deed.describe() if final is not None else "(no tooltip)")


start = skill.read() if skill is not None else None

log("%s: %s%s, %s in the pack"
    % (deed.describe(), skill_name or "Blacksmithy", " at %s" % reading(start),
       ingot_report(INGOTS)))

try:
    reason = run_large() if request["large"] else run_small()
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    reason = "threw - %s" % error

finish(reason)
