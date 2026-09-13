import API
import time

from craftmap.table import recipes_block
from uo.craftmenu import CraftMenu
from uo.entity import hex_of
from uo.gump import controls, open_ids
from uo.log import make_log
from uo.paths import beside_script
from uo.text import untagged

# Open a craft menu by hand, then run this: it presses each CATEGORIES button, which spends nothing,
# and writes the RECIPES block for that script's config.py. A row's label is read where its button
# is, every page at once.

OUT = "craft-map.txt"

# Buttons are 1 + type + index * 20 on this shard's menus, as every craft script's config says
BUTTON_STRIDE = 20
CATEGORY_BUTTON_TYPE = 0
ITEM_BUTTON_TYPE = 1

GUMP_TIMEOUT = 5.0

# The redraw lands a moment after WaitForGump answers
REDRAW_DELAY = 0.4

log = make_log("craft-map")


class NoTool(object):
    def serial(self):
        return None


menu = CraftMenu(NoTool(), {
    "stride": BUTTON_STRIDE,
    "category_type": CATEGORY_BUTTON_TYPE,
    "item_type": ITEM_BUTTON_TYPE,
}, log)


def title_of(gump):
    for _button, text in controls(gump) or []:
        if text and "MENU" in text.upper():
            return untagged(text).strip()

    return "CRAFT MENU"


found = None
categories = []

for ident in open_ids():
    categories = menu.categories_of(ident)

    if categories:
        found = ident
        break

if found is None:
    log("no craft menu is open - open one with its tool, then run this again")
    API.Stop()

title = title_of(found)
log("%s on gump %s, %d categories" % (title, hex_of(found), len(categories)))

rows = {}

for label, button in categories:
    if not menu.has_button(button, found):
        log("gump %s has no button %d for '%s' - skipping it" % (hex_of(found), button, label))
        continue

    API.ReplyGump(button, found)

    if not API.WaitForGump(found, GUMP_TIMEOUT):
        log("the menu did not come back after pressing '%s' (button %d) - stopping" % (label, button))
        break

    API.Pause(REDRAW_DELAY)
    rows[button] = menu.rows_of(found)
    log("%s (button %d): %d rows" % (label, button, len(rows[button])))

path = beside_script(OUT)
handle = open(path, "w")
handle.write(recipes_block(title, time.strftime("%Y-%m-%d"), categories, rows))
handle.close()

log("wrote %s - paste its RECIPES and CATEGORY_NAMES into the script's config.py" % path)
