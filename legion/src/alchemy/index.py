import API

from alchemy.config import (BANDS, CONTAINER_RANGE, FETCH_POLL, FETCH_TIMEOUT, MAX_PICKS,
                            MIN_SKILL, MOVE_DELAY, OPEN_DELAY, PATHFIND_TIMEOUT, PICK_TIMEOUT,
                            PRODUCTS, REAGENT_COST, SETUP, SKILL_NAMES, SKILL_POLL, SKILL_TIMEOUT,
                            STOPPED, TOOL_GRAPHICS, TOOL_NAME_WORDS)
from uo.crafttool import CraftTool
from uo.dump import Dump
from uo.guards import dead, first_reason, skill_capped, stopped
from uo.log import make_log
from uo.setup import Setup
from uo.skill import SkillReader, find_skill_name, reading
from uo.sources import Sources
from uo.stages import band_rows
from uo.stock import StockBook
from uo.toolstore import ToolStore

log = make_log("alchemy")

if API.HasTarget():
    API.CancelTarget()

skill_name = find_skill_name(SKILL_NAMES)

if skill_name is None:
    log("the client reports none of %s - check SKILL_NAMES" % ", ".join(SKILL_NAMES))
    API.Stop()

skill = SkillReader(skill_name)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(skill_name)])


tools = CraftTool("mortar and pestle", TOOL_GRAPHICS, TOOL_NAME_WORDS, log)
# No reagent table yet: the form only needs the pickers this book backs
stock = StockBook({
    "noun": "reagents",
    "kinds": [],
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
dump = Dump(sources, PRODUCTS, {
    "pick_timeout": PICK_TIMEOUT,
    "move_delay": MOVE_DELAY,
    "keep_existing": True,
}, log)
tool_store = ToolStore(tools, sources, {
    "noun": "mortars and pestles",
    "pick_timeout": PICK_TIMEOUT,
    "move_delay": MOVE_DELAY,
    "fetch_timeout": FETCH_TIMEOUT,
    "fetch_poll": FETCH_POLL,
}, log)
setup = Setup(SETUP, log, stop_reason)

start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)

if start is None:
    log("%s is not reading yet - start it again once the skill list has arrived" % skill_name)
    API.Stop()

def training_rows():
    return ("%s %s" % (skill_name, reading(start)),
            band_rows(BANDS, start, lambda row: "%d %s" % REAGENT_COST[row], MIN_SKILL))


answers = setup.ask({
    "table": training_rows,
    "tools": tool_store.pick,
    "tools_ready": lambda: tool_store.count() > 0,
    "source": sources.pick_one,
    "clear": sources.clear,
    "unload": dump.pick_line,
    "unload_ready": dump.picked,
    "has_wood": lambda: True,
    "unsold_ahead": None,
})

if answers is None:
    API.Stop()

log.enabled = answers["debug_logs"] if answers is not None else False

if answers is not None:
    log("%s, tools: %s, %d sources, unloading into %s every %d"
        % (answers["output"], answers["tools"], answers["sources"],
           dump.name() if answers["output"] == "unload" else "nothing", answers["dump_at"]))

log("stopping - the form is all this run does yet")
API.Stop()
