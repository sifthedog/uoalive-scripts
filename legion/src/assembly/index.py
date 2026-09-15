import API

from assembly.config import (ASSEMBLIES, BUTTON_STRIDE, CATEGORY_BUTTON_TYPE, CRAFT_POLL,
                             CRAFT_TIMEOUT, GUMP_POLL, GUMP_TIMEOUT, ITEM_BUTTON_TYPE,
                             JOURNAL_TAIL_LINES, JOURNAL_TAIL_SECONDS, LAST_TEN_LABEL,
                             MADE_KEG_TYPES, MAKE_LAST_BUTTON, MAX_NO_TOOL, MAX_THROTTLED,
                             MAX_UNKNOWN, MAX_UNREADABLE_REPORTS, MENUS, MOVE_DELAY, NOTES_PATH,
                             NOTES_TAIL_SECONDS, OUTCOME_TEXT, PART_KINDS, PART_ORDER,
                             START_PROMPT, UNREADABLE_TEXT_LIMIT, WEIGHT_BUFFER)
from assembly.plan import next_stage
from assembly.prompt import StartPrompt
from uo.components import short_of, shortfall_report
from uo.craft import Crafter
from uo.craftmenu import CraftMenu
from uo.crafttool import CraftTool
from uo.guards import dead, first_reason, overweight, stopped
from uo.log import make_log
from uo.loop import backoff_for
from uo.notes import note_log
from uo.phrases import STOPPED
from uo.stock import StockBook
from uo.timings import STEP_DELAY, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX

log = make_log("assembly")

if API.HasTarget():
    API.CancelTarget()


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), overweight(WEIGHT_BUFFER)])


parts = StockBook({
    "noun": "assembly parts",
    "kinds": PART_KINDS,
    "types": MADE_KEG_TYPES,
    "hues": {},
    "wanted": None,
    "move_delay": MOVE_DELAY,
}, log)
notes = note_log(NOTES_PATH, log)


def crafter_for(spec):
    tools = CraftTool(spec["tool_noun"], spec["tool_graphics"], spec["tool_name_words"], log)
    others = [other for other in MENUS.values() if other is not spec]
    menu = CraftMenu(tools, {
        "foreign_fragments": [phrase.lower() for other in others for phrase in other["title_text"]],
        "stride": BUTTON_STRIDE,
        "category_type": CATEGORY_BUTTON_TYPE,
        "item_type": ITEM_BUTTON_TYPE,
        "category_names": spec["category_names"],
        "last_ten_label": LAST_TEN_LABEL,
        "title": spec["title"],
        "title_text": spec["title_text"],
        "title_fragments": [phrase.lower() for phrase in spec["title_text"]],
        "tool_noun": spec["tool_noun"],
        "gump_timeout": GUMP_TIMEOUT,
        "gump_poll": GUMP_POLL,
    }, log)

    return tools, Crafter(tools, menu, parts, OUTCOME_TEXT, {
        "recipes": spec["recipes"],
        "make_last_button": MAKE_LAST_BUTTON,
        "gump_timeout": GUMP_TIMEOUT,
        "craft_timeout": CRAFT_TIMEOUT,
        "craft_poll": CRAFT_POLL,
        "max_reports": MAX_UNREADABLE_REPORTS,
        "text_limit": UNREADABLE_TEXT_LIMIT,
        "tail_seconds": JOURNAL_TAIL_SECONDS,
        "tail_lines": JOURNAL_TAIL_LINES,
        "notes_seconds": NOTES_TAIL_SECONDS,
        "material": "assembly parts",
    }, log, log.stamp, notes)


crafters = dict((name, crafter_for(MENUS[name])) for name in MENUS)

answers = StartPrompt(START_PROMPT, log, stop_reason).ask()

# The stop lands at the next Pause, so the lines until then read a prompt that was never answered
picked = answers["assembly"] if answers is not None else ASSEMBLIES[0][0]
wanted = answers["wanted"] if answers is not None else 0

if answers is None:
    API.Stop()

chosen = [row for row in ASSEMBLIES if row[0] == picked][0]
stages = chosen[2]
noun = chosen[1].lower()
plural = noun if wanted == 1 else noun + "s"

for name in set([menu for _row, menu, _needs in stages]):
    if crafters[name][0].serial() is None:
        log("no %s in the pack" % MENUS[name]["tool_noun"])
        API.Stop()

log("making %d %s, %s in the pack" % (wanted, plural, parts.pack_report()))

stop = None
made = 0
fails = 0
unknown = 0
throttled = 0
no_tool = 0
last_row = {}


try:
    while stop is None and made < wanted:
        stop = stop_reason()

        if stop is not None:
            break

        stock = parts.pack_stock()
        product, menu_name, needs = next_stage(stages, stock)
        short = short_of(needs, stock)

        if short:
            stop = ("short of %s for the %s of %s %d of %d - the pack holds %s"
                    % (shortfall_report(short, PART_ORDER), product, noun, made + 1, wanted,
                       parts.pack_report()))
            break

        tools, crafter = crafters[menu_name]

        # MAKE LAST would repeat the menu's previous row
        if last_row.get(menu_name) != product:
            last_row[menu_name] = product
            crafter.forget_last()

        outcome = crafter.craft_once(product)

        if outcome != "throttled":
            throttled = 0

        if outcome not in ("noTool", "noGump"):
            no_tool = 0

        if outcome is not None:
            unknown = 0

        if outcome == "made":
            if product == stages[-1][0]:
                made += 1
                log("%s %d of %d" % (noun, made, wanted))
            else:
                log("made %s" % product)
        elif outcome == "failed":
            fails += 1
        elif outcome == "noMaterial":
            stop = ("the shard refused the parts in the pack for a %s (%s) - read the gump's words "
                    "above" % (product, parts.pack_report()))
        elif outcome == "skillTooLow":
            stop = "the shard says you cannot make a %s yet" % product
        elif outcome == "noRow":
            stop = "'%s' is not in MENUS" % product
        elif outcome == "toolWorn":
            crafter.forget_last()
            log("the tool wore out, looking for another")
        elif outcome in ("noTool", "noGump"):
            no_tool += 1

            if no_tool >= MAX_NO_TOOL:
                stop = ("no %s left" % MENUS[menu_name]["tool_noun"] if outcome == "noTool"
                        else "the %s menu will not open" % menu_name)
                break

            API.Pause(backoff_for(no_tool, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
        elif outcome == "throttled":
            throttled += 1

            if throttled >= MAX_THROTTLED:
                stop = "%d throttled crafts in a row" % MAX_THROTTLED
                break

            API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))
        elif outcome is None:
            unknown += 1

            if unknown >= MAX_UNKNOWN:
                stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
                break

            log("unreadable outcome (%d/%d), check OUTCOME_TEXT" % (unknown, MAX_UNKNOWN))

        API.Pause(STEP_DELAY)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    if stop is None:
        stop = "threw - %s" % error

log("%d made, %d failed, %s left in the pack" % (made, fails, parts.pack_report()))
log("stopping - %s" % (stop or "done"))
API.Stop()
