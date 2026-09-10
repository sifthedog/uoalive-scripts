import API

from inventory.config import (DATA_PATH, DURABILITY_TEXT, MAX_CONTAINERS, OPEN_DELAY, OPL_BATCH,
                              OPL_TIMEOUT, OPL_WAIT, PICK_TIMEOUT, PREFIX_TEXT, RECURSIVE, RETRIES,
                              TIER_TEXT, WEIGHT_TEXT)
from inventory.sweep import bag_sweep
from uo.entity import hex_of
from uo.log import make_log

log = make_log("inventory")

CONFIG = {
    "recursive": RECURSIVE,
    "open_delay": OPEN_DELAY,
    "opl_wait": OPL_WAIT,
    "opl_timeout": OPL_TIMEOUT,
    "opl_batch": OPL_BATCH,
    "retries": RETRIES,
    "max_containers": MAX_CONTAINERS,
    "parser": {
        "tier": TIER_TEXT,
        "durability": DURABILITY_TEXT,
        "weight": WEIGHT_TEXT,
        "prefixes": PREFIX_TEXT,
    },
}

# A cursor left open by whatever ran last would swallow this query
if API.HasTarget():
    API.CancelTarget()

log("target the bag to read, ESC to stop")

bag = API.RequestTarget(PICK_TIMEOUT)

if not bag:
    if API.HasTarget():
        API.CancelTarget()

    log("nothing targeted - stopping")
    API.Stop()

if API.FindItem(bag) is None:
    log("%s is not an item - target a bag or chest" % hex_of(bag))
    API.Stop()

sweep = bag_sweep(DATA_PATH, CONFIG, log)

try:
    written, unread, opened = sweep.run(bag)
except Exception as error:
    if API.StopRequested:
        raise

    log("threw - %s" % error)
    API.Stop()

log("%d item%s written to %s from %d container%s, %d without a tooltip"
    % (written, "" if written == 1 else "s", DATA_PATH or "nowhere",
       opened, "" if opened == 1 else "s", unread))

API.Stop()
