# Built from src/alchemy/index.py by build.py - do not edit.

import API


# src/uo/phrases.py
"""The shard's own wordings, as far as they are the same whatever the script is doing."""

STOPPED = "stopped from the script manager"


# src/alchemy/config.py
SKILL_NAMES = ["Alchemy"]

# Mortar and pestle, 3739
TOOL_GRAPHICS = set([0x0E9B])
TOOL_NAME_WORDS = ["mortar"]

TOOL_MODES = [("stop", "Stop the run"), ("fetch", "Fetch from a container")]
OUTPUT_OPTIONS = [("unload", "Unload into a container"), ("keep", "Keep")]

# Products in the pack, counted as amounts, before they are unloaded
DUMP_AT = 10

# name -> graphics, filled in once the run crafts
PRODUCTS = {}

# The form the run is set up on. Closing it, Cancel, or no OK in the timeout ends the run.
SETUP = {
    "title": "Alchemy",
    "tool_noun": "mortars and pestles",
    "material": "reagents",
    "tool_modes": TOOL_MODES,
    "outputs": OUTPUT_OPTIONS,
    "unsold_hint": None,
    "dump_at": DUMP_AT,
    "hue": 996,
    "poll": 0.25,
    "timeout": 600.0,
}

# Bounds Sources.pick only; the form adds sources one cursor at a time and never calls it
MAX_PICKS = 8

CONTAINER_RANGE = 2

# One tool is fetched at a time from the container the form picked; how long the pack has to show it
FETCH_TIMEOUT = 3.0
FETCH_POLL = 0.25

# Seconds throughout - API.Pause takes seconds
PICK_TIMEOUT = 60.0

# Whole seconds: the API takes an int here
PATHFIND_TIMEOUT = 10

OPEN_DELAY = 0.6
MOVE_DELAY = 0.7

SKILL_TIMEOUT = 5.0
SKILL_POLL = 0.25


# src/uo/entity.py
# API.Player is None whenever the client is between world states - a recall, a server line change,
# the moment around a death - and reading through it threw a live restock away
def player():
    try:
        return API.Player
    except Exception:
        if API.StopRequested:
            raise

        return None


def hex_of(value):
    return "0x%x" % (value & 0xFFFFFFFF)


# unknown is what an unanswered client reads as, so the caller pathfinds and asks again rather than
# treating silence as arm's length
def chebyshev(x, y, unknown):
    me = player()

    if me is None:
        return unknown

    return max(abs(me.X - x), abs(me.Y - y))


# src/uo/pack.py
def pack_contents():
    items = API.ItemsInContainer(API.Backpack, True)

    return items if items else []


# The item cap is per container, so the guard and the combine both count the top level only
def pack_top_level():
    items = API.ItemsInContainer(API.Backpack, False)

    return items if items else []


# None is an unreported stack, not an empty one: counted as 0 it would hide the ore a swing just
# delivered, which is the proof that the swing landed
def amount_of(item):
    amount = getattr(item, "Amount", None)

    return amount if amount is not None else 1


def hue_of(item):
    return getattr(item, "Hue", 0) or 0


# src/uo/text.py
def words_of(text):
    letters = []

    for char in (text or "").lower():
        letters.append(char if char.isalnum() else " ")

    return "".join(letters).split()


def word_in(text, words):
    found = words_of(text)

    for word in words:
        if word in found:
            return True

    return False


def any_in(text, fragments):
    low = (text or "").lower()

    for fragment in fragments:
        if fragment in low:
            return True

    return False


def untagged(text):
    kept = []
    inside = False

    for char in text or "":
        if char == "<":
            inside = True
        elif char == ">":
            inside = False
        elif not inside:
            kept.append(char)

    return "".join(kept)


def clipped(text, limit):
    flat = " ".join((text or "").split())

    return flat if len(flat) <= limit else flat[:limit] + "..."


# src/uo/retry.py
def settled(timeout, poll, landed):
    waited = 0.0

    while waited < timeout:
        API.Pause(poll)
        waited += poll

        if landed():
            return True

    return False


# src/uo/tool.py
# Books carry the client's container flag, so the flag alone opens every spellbook in the pack
NOT_BAG_GRAPHICS = set([
    0x0EFA,  # spellbook
    0x2253,  # necromancer spellbook
    0x2252,  # book of chivalry
    0x238C,  # book of bushido
    0x23A0,  # book of ninjitsu
    0x2D50,  # spellweaving spellbook
    0x2D9D,  # mysticism spellbook
    0x22C5,  # runebook
    0x9C16,  # runic atlas
    0x2259,  # bulk order book
])
NOT_BAG_NAMES = ["spellbook", "runebook", "book", "atlas"]


def is_bag(item):
    if not getattr(item, "IsContainer", False) or getattr(item, "Opened", False):
        return False

    if item.Graphic in NOT_BAG_GRAPHICS:
        return False

    return not word_in(item.Name, NOT_BAG_NAMES)


# A bag the client has not opened this session reads as empty, whatever is in it. extra_serial, a
# spare bag outside the pack, joins the search if it is not open yet either. opened is mutated:
# every bag this call sends a double-click to is remembered so a later call leaves it alone.
def open_unopened_bags(noun, log, opened, extra_serial=None):
    bags = [item for item in pack_contents() if is_bag(item)]

    if extra_serial is not None:
        spare = API.FindItem(extra_serial)

        if spare is not None and not getattr(spare, "Opened", False):
            bags.append(spare)

    bags = [bag for bag in bags if bag.Serial not in opened]

    if not bags:
        return False

    # A cursor left up would take the double-click as its answer
    if API.HasTarget():
        API.CancelTarget()

    log("opening %d bag(s) to look inside for a %s" % (len(bags), noun))

    for bag in bags:
        opened.add(bag.Serial)
        API.UseObject(bag.Serial)

    return True


# search is called fresh each time: opening the bags is asynchronous, so what it finds only
# improves after settled() gives the pack a chance to catch up
def find_after_opening_bags(search, noun, log, opened, timeout, poll, extra_serial=None):
    found = search()

    if found is None and open_unopened_bags(noun, log, opened, extra_serial):
        settled(timeout, poll, lambda: search() is not None)
        found = search()

    return found


# src/uo/crafttool.py
class CraftTool(object):
    """A crafting tool, used out of the pack rather than equipped."""

    def __init__(self, noun, graphics, name_words, log, prefer=None):
        self._noun = noun
        self._graphics = graphics
        self._name_words = name_words
        self._log = log
        self._prefer = prefer or set()
        self._opened = set()

    def is_tool(self, item):
        if item is None:
            return False

        if item.Graphic in self._graphics:
            return True

        if not word_in(item.Name, self._name_words):
            return False

        self._graphics.add(item.Graphic)
        self._log("%s '%s' is a %s too, remembering the art"
                  % (hex_of(item.Graphic), item.Name, self._noun))

        return True

    def serials(self):
        return [item.Serial for item in pack_contents() if self.is_tool(item)]

    def serial(self):
        found = None

        for item in pack_contents():
            if not self.is_tool(item):
                continue

            if item.Graphic in self._prefer:
                return item.Serial

            if found is None:
                found = item.Serial

        return found

    def find(self, timeout, poll):
        return find_after_opening_bags(self.serial, self._noun, self._log, self._opened,
                                       timeout, poll)


# src/uo/target.py
# The serial one cursor answered, or None for ESC or a timeout. Clears a cursor left open from
# before, and the one just answered too, so a target flag never survives past it.
def request_one(timeout):
    if API.HasTarget():
        API.CancelTarget()

    serial = API.RequestTarget(timeout)

    if API.HasTarget():
        API.CancelTarget()

    return serial or None


# src/uo/dump.py
class Dump(object):
    """The container the products are unloaded into: a trash barrel, or a chest."""

    # products is the script's name -> graphics table, read live: an art the crafter learns lands
    # in it after this, and a frozen union of it would never see the item to unload
    def __init__(self, sources, products, config, log):
        self._sources = sources
        self._products_of = products
        self._names = None
        self._config = config
        self._log = log
        self._entry = None
        keep_graphics = config.get("keep_graphics", self._graphics())
        # Carpentry narrows this to the deed art, which doubles as a house deed's - keeping every
        # matching graphic locked out leftover, un-dumped stock from a previous run for good
        self._kept = (set(item.Serial for item in pack_contents()
                           if item.Graphic in keep_graphics)
                      if config["keep_existing"] else set())

    def _graphics(self):
        names = self._names if self._names is not None else self._products_of

        return set().union(*[self._products_of[name] for name in names])

    def _products(self):
        graphics = self._graphics()

        return [item for item in pack_contents() if item.Graphic in graphics]

    def items(self):
        return [item for item in self._products() if item.Serial not in self._kept]

    def held(self):
        return sum(amount_of(item) for item in self.items())

    def picked(self):
        return self._entry is not None

    def name(self):
        return self._sources.name_of(self._entry) if self._entry is not None else "nothing"

    # Sell watches only what nobody buys; the kept set was read against every product, a superset
    def limit_to(self, names):
        self._names = list(names)

    def line(self):
        return "'%s' %s" % (self.name(), hex_of(self._entry["serial"]))

    def _refusal(self, serial):
        if serial == API.Backpack:
            return "that is your own pack"

        entry = self._sources.entry_for(serial)

        if entry is None:
            return "%s is neither a container nor a creature" % hex_of(serial)

        if entry["kind"] == "box":
            return ("'%s' is a storage box, which takes nothing you made - pick a barrel or a "
                    "chest" % self._sources.name_of(entry))

        if self._sources.open(entry) is None:
            return "'%s' has no backpack to unload into" % self._sources.name_of(entry)

        return None

    # (the picked container's line, None), (None, why it was refused), or (None, None) for ESC
    def pick_line(self):
        serial = request_one(self._config["pick_timeout"])

        if serial is None:
            return None, None

        refusal = self._refusal(serial)

        if refusal is not None:
            self._log(refusal)

            return None, refusal

        self._entry = self._sources.entry_for(serial)
        self._log("unloading into %s" % self.line())

        return self.line(), None

    def pick(self):
        self._log("target the container to unload into, a trash barrel or a chest - ESC to keep "
                  "everything in the pack")

        line, _refusal = self.pick_line()

        return self._entry if line is not None else None

    def run(self):
        items = self.items()

        if self._entry is None or len(items) == 0:
            return 0

        if not self._sources.reach(self._entry):
            self._log("cannot reach '%s' to unload" % self.name())

            return 0

        container = self._sources.open(self._entry)

        if container is None:
            self._log("'%s' has no backpack to unload into" % self.name())

            return 0

        before = self.held()

        for item in items:
            API.MoveItem(item.Serial, container, amount_of(item))
            API.Pause(self._config["move_delay"])

        moved = before - self.held()

        if moved > 0:
            self._log("unloaded %d into '%s'" % (moved, self.name()))
        else:
            self._log("'%s' took nothing" % self.name())

        return moved


# src/uo/guards.py
def first_reason(clauses):
    for clause in clauses:
        reason = clause()

        if reason is not None:
            return reason

    return None


def stopped(text):
    def clause():
        return text if API.StopRequested else None

    return clause


def dead():
    def clause():
        me = player()

        return "you are dead" if me is not None and me.IsDead else None

    return clause


# By the value as well as the base: with no base reported, or a lifted value, the run never ends
def skill_capped(name):
    def clause():
        skill = API.GetSkill(name) if name is not None else None

        if skill is None:
            return None

        base = getattr(skill, "Base", None) or 0.0
        value = skill.Value

        if max(base, value) <= 0 or max(base, value) < skill.Cap:
            return None

        if base >= skill.Cap:
            return "%s is capped at %.1f" % (name, base)

        if base > 0:
            return ("%s shows %.1f against its %.1f cap while its base is %.1f - take off what lifts "
                    "it to keep gaining" % (name, value, skill.Cap, base))

        return "%s is capped at %.1f" % (name, value)

    return clause


# src/uo/log.py
def make_log(prefix):
    stamp = prefix + ": "

    def log(message):
        if log.enabled:
            API.SysMsg(stamp + message)

    # The client puts a SysMsg in the journal beside the shard's own lines, so a script reading the
    # journal back needs to know which lines it wrote itself - without this a report of an unreadable
    # outcome quotes the last report of an unreadable outcome. Lowercase, because that is how the
    # journal readers compare. Carried on the function itself rather than a module-level list: a
    # bundle is one script and one prefix, and a shared list would leak between scripts sharing this
    # process, such as the test suite.
    log.stamp = stamp.lower()
    log.enabled = True

    return log


# src/uo/gumpwait.py
# Waits behind a gump the script drew, one poll slice at a time, until resolve() answers a reason
# to stop (checked first, so a click wins over the gump closing), the gump is disposed, stop_reason
# gives one, or timeout seconds pass - timeout=None means no ceiling. each(), when given, runs once
# a slice before resolve(), so an alarm or a heartbeat keeps going while the gump is up. Disposes
# the gump before returning why. The click only arrives through ProcessCallbacks, and a stopped
# script's client calls all answer with nothing, so the stop flag is the one read that still means
# something then.
def wait_for_gump(gump, stop_reason, poll, resolve, closed_message="the gump was closed",
                  timeout=None, each=None):
    waited = 0.0
    why = None

    while why is None:
        if API.StopRequested:
            why = "the run is being stopped"
            break

        if each is not None:
            each()

        API.ProcessCallbacks()

        why = resolve()

        if why is not None:
            pass
        elif gump.IsDisposed:
            why = closed_message
        elif stop_reason() is not None:
            why = "the run has a reason to stop"
        elif timeout is not None and waited >= timeout:
            why = "nothing was pressed in %.0fs" % timeout
        else:
            API.Pause(poll)
            waited += poll

    if not gump.IsDisposed:
        gump.Dispose()

    return why


# src/uo/setup.py
SETUP_WIDTH = 720
MARGIN = 16
LABEL_X = 16
FIELD_X = 160
VALUE_X = 316
ROW = 28
LINE = 22
TITLE_HEIGHT = 40
BUTTON_HEIGHT = 24
FONT = 15
SOURCE_LINES = 4
LINE_CHARS = 92
RADIO_CHAR = 8
RADIO_GAP = 40
DUMP_AT_WIDTH = 56

TEXT = "#E6E6E6"
MUTED = "#8C8C8C"
CURRENT = "#F2C14E"
WARN = "#FF7B6B"


class Setup(object):
    """The form the run is set up on: tools, wood sources, what is made, and the band table."""

    def __init__(self, config, log, stop_reason):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason
        self._pending = None
        self._sources = []
        self._tools_line = None
        self._unload_line = None
        self._message = None
        self._controls = {}

    def _presser(self, key):
        def press():
            self._pending = key

        return press

    def _label(self, gump, text, x, y, color=TEXT, width=None):
        label = API.Gumps.CreateGumpTTFLabel(text, FONT, color)
        label.SetRect(x, y, width if width is not None else SETUP_WIDTH - x - MARGIN, LINE)
        gump.Add(label)

        return label

    def _button(self, gump, key, caption, x, y, width):
        button = API.Gumps.CreateSimpleButton(caption, width, BUTTON_HEIGHT)
        button.SetPos(x, y)
        API.Gumps.AddControlOnClick(button, self._presser(key))
        gump.Add(button)

        return button

    def _show(self, heading, rows):
        outputs = self._config["outputs"]
        height = (TITLE_HEIGHT + ROW * 2 + ROW + LINE * SOURCE_LINES + ROW * 3
                  + LINE * (len(rows) + 1) + ROW * 2 + BUTTON_HEIGHT + MARGIN * 4)

        gump = API.Gumps.CreateGump(True, True)

        if gump is None:
            return None

        gump.SetRect(0, 0, SETUP_WIDTH, height)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.9, "#1E1E1E")
        background.SetRect(0, 0, SETUP_WIDTH, height)
        gump.Add(background)

        title = API.Gumps.CreateGumpLabel(self._config["title"], self._config["hue"])
        title.SetPos(MARGIN, 12)
        gump.Add(title)

        y = TITLE_HEIGHT
        c = self._controls

        self._label(gump, self._config["tool_noun"].capitalize(), LABEL_X, y)
        self._label(gump, "When they run out:", FIELD_X, y, MUTED, 150)
        c["modes"] = API.Gumps.CreateDropDown(200, [caption for _key, caption in
                                                    self._config["tool_modes"]], 0)
        c["modes"].SetPos(VALUE_X, y - 2)
        gump.Add(c["modes"])
        y += ROW

        c["tools_button"] = self._button(gump, "tools", "Pick tool container", FIELD_X, y, 148)
        c["tools_value"] = self._label(gump, "", VALUE_X, y + 3, MUTED)
        y += ROW + MARGIN // 2

        self._label(gump, self._material().capitalize(), LABEL_X, y)
        self._button(gump, "source", "Add a source", FIELD_X, y, 140)
        self._button(gump, "clear", "Clear", FIELD_X + 148, y, 70)
        y += ROW

        c["sources"] = []

        for index in range(SOURCE_LINES):
            c["sources"].append(self._label(gump, "", FIELD_X, y + index * LINE, MUTED))

        y += LINE * SOURCE_LINES + MARGIN // 2

        self._label(gump, "What is made", LABEL_X, y)
        c["outputs"] = []

        x = FIELD_X

        # Spaced by caption: the classic font runs about RADIO_CHAR pixels a letter
        for index in range(len(outputs)):
            radio = API.Gumps.CreateGumpRadioButton(outputs[index][1], 1, 0x00D0, 0x00D1,
                                                    self._config["hue"], index == 0)
            radio.SetPos(x, y)
            gump.Add(radio)
            c["outputs"].append(radio)
            x += RADIO_GAP + RADIO_CHAR * len(outputs[index][1])

        y += ROW

        c["unload_button"] = self._button(gump, "unload", "Pick container", FIELD_X, y, 148)
        c["unload_value"] = self._label(gump, "", VALUE_X, y + 3, MUTED)
        y += ROW

        c["dump_label"] = self._label(gump, "Unload every", FIELD_X, y + 3, MUTED, 148)
        c["dump_at"] = API.Gumps.CreateGumpTextBox(str(self._config["dump_at"]), DUMP_AT_WIDTH,
                                                   BUTTON_HEIGHT, False, FONT)
        c["dump_at"].SetPos(VALUE_X, y)
        gump.Add(c["dump_at"])
        c["dump_unit"] = self._label(gump, "products", VALUE_X + DUMP_AT_WIDTH + 8, y + 3, MUTED)
        y += ROW + MARGIN // 2

        self._label(gump, "Training", LABEL_X, y)
        self._label(gump, heading, FIELD_X, y)
        y += LINE

        for text, current in rows:
            self._label(gump, ("> " if current else "   ") + text, FIELD_X, y,
                        CURRENT if current else MUTED)
            y += LINE

        y += MARGIN // 2
        c["message"] = self._label(gump, "", LABEL_X, y, WARN)
        y += ROW

        c["debug_logs"] = API.Gumps.CreateGumpCheckbox("Debug logs", self._config["hue"], True)
        c["debug_logs"].SetPos(LABEL_X, y)
        gump.Add(c["debug_logs"])
        y += ROW

        self._button(gump, "cancel", "Cancel", SETUP_WIDTH - MARGIN - 96 - 8 - 96, y, 96)
        self._button(gump, "ok", "OK", SETUP_WIDTH - MARGIN - 96, y, 96)

        API.Gumps.AddGump(gump)

        return gump

    def _material(self):
        return self._config.get("material", "wood")

    def _mode(self):
        return self._config["tool_modes"][self._controls["modes"].GetSelectedIndex()][0]

    def _output(self):
        for index in range(len(self._controls["outputs"])):
            if self._controls["outputs"][index].GetIsChecked():
                return self._config["outputs"][index][0]

        return self._config["outputs"][0][0]

    def _debug_logs(self):
        return self._controls["debug_logs"].GetIsChecked()

    def _dump_at(self):
        text = (self._controls["dump_at"].Text or "").strip()

        return int(text) if text.isdigit() and int(text) > 0 else None

    def _unloading(self, actions):
        output = self._output()
        unsold = output == "sell" and actions["unsold_ahead"] is not None \
            and actions["unsold_ahead"]()

        return output == "unload" or unsold

    def _say(self, message):
        self._message = message
        self._controls["message"].SetText(message or "")

    def _refresh(self, actions):
        c = self._controls
        fetching = self._mode() == "fetch"
        c["tools_button"].IsVisible = fetching
        c["tools_value"].IsVisible = fetching
        c["tools_value"].SetText(clipped(self._tools_line or "required", LINE_CHARS))

        lines = list(self._sources)

        if len(lines) > SOURCE_LINES:
            lines[SOURCE_LINES - 1:] = ["... and %d more" % (len(lines) - SOURCE_LINES + 1)]

        for index in range(SOURCE_LINES):
            if index < len(lines):
                c["sources"][index].SetText(clipped(lines[index], LINE_CHARS))
            elif index == 0:
                c["sources"][0].SetText("nothing picked - the run works through the %s you carry"
                                        % self._material())
            else:
                c["sources"][index].SetText("")

        showing = self._unloading(actions)

        for key in ("unload_button", "unload_value", "dump_label", "dump_at", "dump_unit"):
            c[key].IsVisible = showing

        if self._unload_line is not None:
            c["unload_value"].SetText(clipped(self._unload_line, LINE_CHARS))
        else:
            c["unload_value"].SetText(self._config["unsold_hint"] if self._output() == "sell"
                                      else "required")

    def _validate(self, actions):
        if self._mode() == "fetch" and not actions["tools_ready"]():
            return ("pick a container holding %s, or choose to stop when they run out"
                    % self._config["tool_noun"])

        if self._output() == "unload" and not actions["unload_ready"]():
            return "pick the container to unload into"

        if self._unloading(actions) and self._dump_at() is None:
            return "unload every: a whole number of products, 1 or more"

        if len(self._sources) == 0 and not actions["has_wood"]():
            return "add a source of %s, or carry some" % self._material()

        return None

    def _run(self, pending, actions):
        if pending == "source":
            self._log("target a chest, a storage box or a pack animal holding %s" % self._material())
            line, refusal = actions["source"]()

            if line is not None:
                self._sources.append(line)

            self._say(refusal)
        elif pending == "clear":
            actions["clear"]()
            del self._sources[:]
            self._say(None)
        elif pending == "tools":
            self._log("target the container holding %s" % self._config["tool_noun"])
            line, refusal = actions["tools"]()

            if line is not None:
                self._tools_line = line

            self._say(refusal)
        elif pending == "unload":
            self._log("target the container to unload into, a trash barrel or a chest")
            line, refusal = actions["unload"]()

            if line is not None:
                self._unload_line = line

            self._say(refusal)
        elif pending == "ok":
            failure = self._validate(actions)
            self._say(failure)

            return "ok" if failure is None else None
        elif pending == "cancel":
            return "cancel"

        return None

    def ask(self, actions):
        if API.HasTarget():
            API.CancelTarget()

        heading, rows = actions["table"]()
        gump = self._show(heading, rows)

        # API.Stop() only lands at the next Pause, and every client call before it answers nothing
        if gump is None:
            self._log("not asking - the run is being stopped")

            return None

        self._log("asking - the start-up form")
        self._refresh(actions)
        answers = [None]

        def resolve():
            pending, self._pending = self._pending, None
            done = self._run(pending, actions) if pending is not None else None

            self._refresh(actions)

            if done == "ok":
                dump_at = self._dump_at()
                answers[0] = {"tools": self._mode(), "output": self._output(),
                              "sources": len(self._sources),
                              "dump_at": dump_at if dump_at is not None else self._config["dump_at"],
                              "debug_logs": self._debug_logs()}

                return "OK was pressed"

            return "Cancel was pressed" if done == "cancel" else None

        why = wait_for_gump(gump, self._stop_reason, self._config["poll"], resolve,
                            closed_message="the form was closed", timeout=self._config["timeout"])

        self._log(why)

        return answers[0]


# src/uo/skill.py
# A name the client does not carry throws on some builds rather than answering None
def find_skill_name(names):
    for name in names:
        try:
            if API.GetSkill(name) is not None:
                return name
        except Exception:
            if API.StopRequested:
                raise

            continue

    return None


def reading(value):
    return "unknown" if value is None else "%.1f" % value


class SkillReader(object):
    """Value reads 0.0 before the skill list arrives, which is also a real skill value."""

    def __init__(self, name):
        self._name = name
        self._seen = False
        self._last = None

    def read(self):
        skill = API.GetSkill(self._name)

        if skill is None:
            return None

        value = skill.Value

        if value <= 0.0 and not self._seen:
            return None

        self._seen = True
        self._last = value

        return value

    # Once the stop button is pressed the client answers nothing, so the last row of a run would
    # end unknown; the latest reading that did arrive is never further off than that
    def last(self):
        value = self.read()

        return value if value is not None else self._last

    def name(self):
        skill = API.GetSkill(self._name)

        return skill.Name if skill is not None and skill.Name else self._name

    def cap(self):
        skill = API.GetSkill(self._name)

        return skill.Cap if skill is not None else None

    def wait(self, timeout, poll):
        waited = 0.0

        while not API.StopRequested:
            value = self.read()

            if value is not None:
                return value

            if waited >= timeout:
                return self._accept_zero()

            API.Pause(poll)
            waited += poll

        return None

    # A 0 the client still answers once the wait is over is a real 0, not an unsent skill list
    def _accept_zero(self):
        skill = API.GetSkill(self._name)

        if skill is None:
            return None

        self._seen = True
        self._last = skill.Value

        return skill.Value


# src/uo/gump.py
# HasGump() only ever answers the last gump the shard sent, and a gump the shard re-sends on its own
# steals that slot: the id-addressed calls below do not go through it
def open_ids():
    found = []
    last = API.HasGump()

    if last:
        found.append(last)

    try:
        for gump in API.GetAllGumps() or []:
            serial = getattr(gump, "ServerSerial", 0)

            if serial and serial not in found:
                found.append(serial)
    except Exception:
        if API.StopRequested:
            raise

    return found


def is_open(ident):
    return bool(ident) and bool(API.WaitForGump(ident, 0))


# A getter can throw on its own (Control.X does), which is not the whole gump being unreadable
def _field(control, name):
    try:
        return getattr(control, name, None)
    except Exception:
        if API.StopRequested:
            raise

        return None


# The controls in the order the layout drew them, every page at once, as (button id, text) with
# None for whichever a control lacks. None for the list is "could not read them", which no caller
# treats as "none": the shard drops the connection for a button the gump does not have, so an
# unreadable gump must not be mistaken for an empty one
def controls(ident):
    if not ident:
        return None

    try:
        gump = API.GetGump(ident)

        if gump is None:
            return None

        found = []

        for control in gump.Children or []:
            button = _field(control, "ButtonID")
            text = _field(control, "Text")

            found.append((None if button is None else int(button), text or None))

        return found
    except Exception:
        if API.StopRequested:
            raise

        return None


def button_ids(ident):
    read = controls(ident)

    if read is None:
        return None

    return set(button for button, _text in read if button is not None)


# A recognised gump wins; failing that, one that was not up before the use. Returns (id, recognised)
def await_recognised(known, before, timeout, poll):
    waited = 0.0
    newcomer = 0

    while waited < timeout:
        for ident in open_ids():
            if known(ident):
                return ident, True

            if not newcomer and ident not in before:
                newcomer = ident

        if newcomer:
            return newcomer, False

        API.Pause(poll)
        waited += poll

    return 0, False


def gump_says(gump, texts):
    for text in texts:
        if API.GumpContains(text, gump):
            return True

    return False


# src/uo/box.py
def _is_int(token):
    return token.lstrip("-").isdigit()


# The packet is the strings, one a line, then the layout: 'text x y hue index', 'button x y ... id'
def _split_layout(packet):
    lines = (packet or "").replace("\x00", "").split("\n")

    for start in range(len(lines)):
        tokens = lines[start].split()

        if len(tokens) > 1 and tokens[0].isalpha() and tokens[0].islower() \
                and all(_is_int(token) for token in tokens[1:]):
            return lines[:start], [line.split() for line in lines[start:] if line.split()]

    return lines, []


# A row's button is the nearest one to the left of its label on the same line of the layout
def layout_buttons(packet, labels):
    strings, layout = _split_layout(packet)
    texts = {}
    buttons = []

    for tokens in layout:
        if tokens[0] in ("text", "croppedtext") and len(tokens) >= 5:
            texts[int(tokens[-1])] = (int(tokens[1]), int(tokens[2]))
        elif tokens[0] == "button" and len(tokens) >= 8:
            buttons.append((int(tokens[1]), int(tokens[2]), int(tokens[-1])))

    found = {}

    lowered = [string.lower() for string in strings]

    for label in labels:
        if label.lower() not in lowered:
            continue

        spot = texts.get(lowered.index(label.lower()))

        if spot is None:
            continue

        beside = [(x, ident) for x, y, ident in buttons if y == spot[1] and x < spot[0]]

        if beside:
            found[label] = max(beside)[1]

    return found


class StorageBox(object):
    """The shard's resource box: stock read off its gump, drawn a button press at a time."""

    def __init__(self, table, config, log):
        self._table = table
        self._rows = dict((label.lower(), label) for label in table["rows"])
        self._config = config
        self._log = log
        self._id = 0
        self._serial = None
        self._seen = {}
        self._skipped = set()
        self._said = set()

    def _say_once(self, key, text):
        if key in self._said:
            return

        self._said.add(key)
        self._log(text)

    def is_box_gump(self, ident):
        if not ident:
            return False

        if any_in(API.GetGumpContents(ident) or "", self._table["title"]):
            return True

        return gump_says(ident, self._table["title"])

    def _showing(self):
        if self._id and is_open(self._id):
            return self._id

        for ident in open_ids():
            if self.is_box_gump(ident):
                self._id = ident

                return ident

        return 0

    def open(self, serial):
        showing = self._showing()

        if showing and self._serial in (None, serial):
            self._serial = serial
            self._seen[serial] = self._parse(showing)

            return showing

        before = open_ids()
        API.UseObject(serial)

        found, recognised = await_recognised(self.is_box_gump, before,
                                             self._config["gump_timeout"],
                                             self._config["gump_poll"])

        if not found or not recognised:
            return 0

        self._id = found
        self._serial = serial
        self._seen[serial] = self._parse(found)

        return found

    # Keyed by the table's spelling of a label, whatever case the gump shows it in
    def _parse(self, gump):
        rows = {}
        tokens = untagged(API.GetGumpContents(gump) or "").split()

        for index in range(1, len(tokens)):
            if tokens[index].isdigit():
                label = tokens[index - 1]

                if label.lower() in self._rows:
                    rows[self._rows[label.lower()]] = int(tokens[index])
                else:
                    self._say_once(("row", label.lower()),
                                   "the box lists '%s', which the BOX rows do not name" % label)

        return rows

    # Live while the gump is up, else as last seen: UseObject from across the house opens nothing
    def rows(self, serial):
        showing = self._showing()

        if showing and self._serial == serial:
            self._seen[serial] = self._parse(showing)

        return self._seen.get(serial, {})

    def _kind_of(self, label):
        return self._table["rows"][label][0]

    def _type_of(self, label):
        wood_type = self._table["rows"][label][1]

        return wood_type if wood_type is not None else self._config["plain"]

    def _labels(self, kind, wanted):
        return [label for label in self._table["rows"]
                if (kind is None or self._kind_of(label) == kind)
                and self._type_of(label) == wanted]

    def counts(self, serial, wanted):
        rows = self.rows(serial)
        counts = {}

        for label in self._labels(None, wanted):
            if rows.get(label, 0) > 0:
                kind = self._kind_of(label)
                counts[kind] = counts.get(kind, 0) + rows[label]

        return counts

    def other_counts(self, serial, wanted):
        rows = self.rows(serial)
        counts = {}

        for label in rows:
            if self._type_of(label) != wanted and rows[label] > 0:
                name = self._type_of(label)
                counts[name] = counts.get(name, 0) + rows[label]

        return counts

    def _pressable(self, serial, kind, wanted):
        rows = self.rows(serial)
        labels = [label for label in self._labels(kind, wanted)
                  if label not in self._skipped and rows.get(label, 0) > 0]
        labels.sort(key=lambda label: -rows[label])

        return labels

    def has_stock(self, serial, kind, wanted):
        return len(self._pressable(serial, kind, wanted)) > 0

    # One press lands per_press; the caller re-counts the pack rather than trusting the reply
    def take(self, serial, kind, wanted):
        labels = self._pressable(serial, kind, wanted)

        if len(labels) == 0:
            return None

        label = labels[0]
        gump = self.open(serial)

        if not gump:
            return None

        button = self._button_for(label, gump)

        if button is None:
            self._skipped.add(label)
            self._say_once(("button", label),
                           "no button known for the '%s' row - run box-probe.py and fill the BOX "
                           "buttons" % label)

            return None

        known = button_ids(gump)

        if known is not None and button not in known:
            self._skipped.add(label)
            self._say_once(("missing", label), "gump %s has no button %d for '%s' - not pressing it"
                           % (hex_of(gump), button, label))

            return None

        if not API.ReplyGump(button, gump):
            return None

        # The reply disposes the gump, so the next read opens it again
        self._id = 0

        return label

    # Read off the gump's own layout; the table is for a client that hands back no packet text
    def _button_for(self, label, gump):
        try:
            found = API.GetGump(gump)
            packet = getattr(found, "PacketGumpText", None) if found is not None else None
        except Exception:
            if API.StopRequested:
                raise

            packet = None

        derived = layout_buttons(packet, [label]) if packet else {}

        if label in derived:
            return derived[label]

        return self._table["buttons"].get(label)

    def wrong_row(self, label, gave):
        self._skipped.add(label)
        self._log("the button table is out of date for '%s' - it gave %s" % (label, gave))


# src/uo/stock.py
class StockBook(object):
    """What in the pack is the craft's material, which type it is, and how much the menu will spend."""

    def __init__(self, config, log):
        self._noun = config["noun"]
        self._kinds = config["kinds"]
        # Longest first: 'copper' would otherwise take 'dull copper'
        self._types = sorted(config["types"], key=lambda name: -len(words_of(name)))
        self._hues = config["hues"]
        self._wanted = config["wanted"]
        self._move_delay = config["move_delay"]
        self._log = log

    def noun(self):
        return self._noun

    def wanted(self):
        return self._wanted

    # For a snapshot key, which has no item left to read a name off
    def is_stock_graphic(self, graphic):
        for _kind, graphics, _words in self._kinds:
            if graphic in graphics:
                return True

        return False

    # Names are empty until the tooltip arrives, so the graphic is tried first across every kind
    def kind_of(self, item):
        if item is None:
            return None

        for kind, graphics, _words in self._kinds:
            if item.Graphic in graphics:
                return kind

        for kind, graphics, words in self._kinds:
            if word_in(item.Name, words):
                graphics.add(item.Graphic)
                self._log("%s '%s' counts as %s, remembering the art"
                          % (hex_of(item.Graphic), item.Name, kind))

                return kind

        return None

    def is_stock(self, item):
        return self.kind_of(item) is not None

    # The name is where the shard writes it; a hue in neither table is not guessed at
    def type_of(self, item):
        words = words_of(item.Name)

        for name in self._types:
            wanted = words_of(name)

            for start in range(len(words) - len(wanted) + 1):
                if words[start:start + len(wanted)] == wanted:
                    return name

        return self._hues.get(hue_of(item))

    def usable(self, item):
        return self.is_stock(item) and self.type_of(item) == self._wanted

    def wrong(self, item):
        return self.is_stock(item) and self.type_of(item) != self._wanted

    def usable_kind(self, item, kind):
        return self.usable(item) and self.kind_of(item) == kind

    # Only what the menu will spend: counting oak let a run sit on a full pack and craft none
    def counts(self, items):
        counts = {}

        for item in items:
            if not self.usable(item):
                continue

            kind = self.kind_of(item)
            counts[kind] = counts.get(kind, 0) + amount_of(item)

        return counts

    # The rest, by type, so a pack that reads as empty says why
    def other_counts(self, items):
        counts = {}

        for item in items:
            if not self.wrong(item):
                continue

            name = self.type_of(item) or "unknown"
            counts[name] = counts.get(name, 0) + amount_of(item)

        return counts

    def other_report(self, counts):
        parts = ["%d %s" % (counts[name], name)
                 for name in sorted(counts, key=lambda name: -counts[name])]

        return ", ".join(parts)

    # In kind order, so it reads the same each time
    def report(self, counts):
        parts = []

        for kind, _graphics, _words in self._kinds:
            if counts.get(kind, 0) > 0:
                parts.append("%d %s" % (counts[kind], kind))

        return ", ".join(parts) if parts else "no %s" % self._noun

    def pack_stock(self):
        return self.counts(pack_contents())

    def pack_other(self):
        return self.other_counts(pack_contents())

    def in_pack(self):
        return total_of(self.pack_stock())

    def pack_report(self):
        text = self.report(self.pack_stock())
        other = self.other_report(self.pack_other())

        return text if not other else "%s (%s set aside)" % (text, other)

    # By hue: oak, ash and yew are all 'boards' by graphic. Missing hue rows come from here.
    def hue_report(self):
        counts = {}

        for item in pack_contents():
            kind = self.kind_of(item)

            if kind is None:
                continue

            key = (kind, hue_of(item), self.type_of(item) or "unknown")
            counts[key] = counts.get(key, 0) + amount_of(item)

        parts = ["%d %s %s hue %s" % (counts[key], key[2], key[0], hex_of(key[1]))
                 for key in sorted(counts, key=lambda pair: -counts[pair])]

        return ", ".join(parts) if parts else "no %s" % self._noun

    def wrong_piles(self):
        return [item for item in pack_contents() if self.wrong(item)]

    # The craft may not reach into a bag inside the pack
    def _nested(self):
        top = set(item.Serial for item in pack_top_level())
        piles = [item for item in pack_contents()
                 if item.Serial not in top and self.usable(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def lift_from_bags(self):
        moved = 0

        for pile in self._nested():
            before = total_of(self.counts(pack_top_level()))

            API.MoveItem(pile.Serial, API.Backpack, amount_of(pile))
            API.Pause(self._move_delay)

            gained = total_of(self.counts(pack_top_level())) - before

            if gained > 0:
                moved += gained

        if moved > 0:
            self._log("brought %d %s up out of the bags in your pack" % (moved, self._noun))

        return moved


def total_of(counts):
    return sum(counts[kind] for kind in counts)


# src/uo/sources.py
KIND_NOUNS = {"item": "container", "mobile": "pack animal", "box": "storage box"}


class Sources(object):
    """The containers, storage boxes and pack animals the wood is drawn from."""

    def __init__(self, wood, config, log):
        self._wood = wood
        self._config = config
        self._log = log
        self._picked = []
        self._box = StorageBox(config["box"], config, log) if config["box"] else None

    def picked(self):
        return self._picked

    def name_of(self, entry):
        return entry["name"] or hex_of(entry["serial"])

    # Never UseObject the animal itself: on a rideable body that mounts you
    def _animal_pack(self, serial):
        animal = API.FindMobile(serial)

        if animal is None:
            return None

        pack = getattr(animal, "Backpack", None)

        if pack is None:
            pack = API.FindLayer("backpack", serial)

        if pack is None:
            return None

        return getattr(pack, "Serial", pack)

    def container_of(self, entry):
        if entry["kind"] == "box":
            return None

        if entry["kind"] == "mobile":
            return self._animal_pack(entry["serial"])

        return entry["serial"]

    def _is_box(self, item):
        if self._box is None:
            return False

        table = self._config["box"]

        return item.Graphic in table["graphics"] or any_in(item.Name, table["names"])

    def entry_for(self, serial):
        item = API.FindItem(serial)

        if item is not None:
            return {"kind": "box" if self._is_box(item) else "item", "serial": serial,
                    "name": item.Name or "?", "spot": (item.X, item.Y, item.Z)}

        animal = API.FindMobile(serial)

        if animal is None:
            return None

        return {"kind": "mobile", "serial": serial, "name": animal.Name or "?", "spot": None}

    # ItemsInContainer reads nothing out of a container the client has never seen inside
    def open(self, entry):
        if entry["kind"] == "box":
            return self._box.open(entry["serial"]) or None

        container = self.container_of(entry)

        if container is None:
            return None

        API.UseObject(container)
        API.Pause(self._config["open_delay"])

        return container

    def _noun_of(self, allowed):
        if allowed is None:
            return ("container, storage box or pack animal" if self._box is not None
                    else "container or pack animal")

        return " or ".join(KIND_NOUNS[kind] for kind in allowed if kind in KIND_NOUNS)

    def clear(self):
        del self._picked[:]

    def line_for(self, entry):
        other = self._wood.other_report(self.other_counts(entry))

        return "'%s' %s, %s in it%s" % (self.name_of(entry), hex_of(entry["serial"]),
                                        self._wood.report(self.counts(entry)),
                                        "" if not other else " (%s it will not use)" % other)

    def _refusal(self, serial, allowed):
        me = player()

        if serial == API.Backpack or (me is not None and serial == me.Serial):
            return "your own pack is always counted, no need to pick it"

        if serial in [entry["serial"] for entry in self._picked]:
            return "%s is already picked" % hex_of(serial)

        entry = self.entry_for(serial)

        if entry is None:
            return "%s is neither a container nor a creature" % hex_of(serial)

        if allowed is not None and entry["kind"] not in allowed:
            return ("'%s' is a %s - the gump chose the %s"
                    % (self.name_of(entry), KIND_NOUNS[entry["kind"]], self._noun_of(allowed)))

        # One storage box holds everything, and its gump is read one box at a time
        if entry["kind"] == "box" and any(held["kind"] == "box" for held in self._picked):
            return "'%s' is a second storage box - one holds everything" % self.name_of(entry)

        return None

    # One cursor, one answer: (the picked entry's line, None), (None, why it was refused), or
    # (None, None) for ESC
    def pick_one(self, allowed=None):
        serial = request_one(self._config["pick_timeout"])

        if serial is None:
            return None, None

        refusal = self._refusal(serial, allowed)

        if refusal is not None:
            self._log(refusal)

            return None, refusal

        entry = self.entry_for(serial)

        # Opened now, while it is in reach
        if self.open(entry) is None:
            refusal = "'%s' did not open" % self.name_of(entry)
            self._log(refusal)

            return None, refusal

        self._picked.append(entry)
        line = self.line_for(entry)
        self._log("picked %s" % line)

        return line, None

    # Every kind by default; a list of kinds, as the gump at the start chose, refuses the others
    def pick(self, allowed=None):
        single = allowed == ["box"]

        if single:
            self._log("target the storage box holding %s" % self._wood.noun())
        else:
            self._log("target every %s holding %s, ESC when done"
                      % (self._noun_of(allowed), self._wood.noun()))

        for _pick in range(self._config["max_picks"]):
            line, refusal = self.pick_one(allowed)

            # ESC or a timed-out cursor, either ends the selection
            if line is None and refusal is None:
                break

            if line is not None and single:
                break

        if API.HasTarget():
            API.CancelTarget()

        return self._picked

    # Only the type the menu is set to, and only one kind of it when a kind is named
    def container_wood(self, serial, kind=None):
        items = API.ItemsInContainer(serial, True)
        piles = [item for item in (items or [])
                 if (self._wood.usable(item) if kind is None
                     else self._wood.usable_kind(item, kind))]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def wood(self, entry):
        container = self.container_of(entry)

        return [] if container is None else self.container_wood(container)

    # Wrong type included, for the report lines
    def all_wood(self, entry):
        container = self.container_of(entry)
        items = API.ItemsInContainer(container, True) if container else None

        return [item for item in items if self._wood.is_stock(item)] if items else []

    def counts(self, entry):
        if entry["kind"] == "box":
            return self._box.counts(entry["serial"], self._wood.wanted())

        return self._wood.counts(self.wood(entry))

    def other_counts(self, entry):
        if entry["kind"] == "box":
            return self._box.other_counts(entry["serial"], self._wood.wanted())

        return self._wood.other_counts(self.all_wood(entry))

    def total(self, entry):
        return total_of(self.counts(entry))

    def stock_left(self):
        return sum(self.total(entry) for entry in self._picked)

    def stock_line(self):
        if len(self._picked) == 0:
            return "nothing picked to restock from"

        return "%d in the %d you picked" % (self.stock_left(), len(self._picked))

    def has_stock(self, entry, kind):
        if entry["kind"] == "box":
            return self._box.has_stock(entry["serial"], kind, self._wood.wanted())

        container = self.container_of(entry)

        return container is not None and len(self.container_wood(container, kind)) > 0

    # The most one restock draws from a source; None is as much as it asks for
    def cap(self, entry):
        return self._config["box_take"] if entry["kind"] == "box" else None

    # Moves are asynchronous: the caller re-counts the pack rather than reading a return value
    def take(self, entry, kind, amount):
        if entry["kind"] == "box":
            before = self._wood.in_pack()
            label = self._box.take(entry["serial"], kind, self._wood.wanted())

            # A press counted before its boards land is pressed again, and lands twice
            if label is not None:
                settled(self._config["press_timeout"], self._config["press_poll"],
                        lambda: self._wood.in_pack() != before)

            return label

        container = self.container_of(entry)
        piles = self.container_wood(container, kind) if container is not None else []

        if len(piles) == 0:
            return None

        API.MoveItem(piles[0].Serial, API.Backpack, min(amount, amount_of(piles[0])))
        API.Pause(self._config["move_delay"])

        return None

    def took_wrong(self, entry, token, gave):
        if entry["kind"] == "box" and token is not None:
            self._box.wrong_row(token, gave)

    # Wrong wood goes back while its container is open and in reach, the one moment it costs nothing
    def put_back(self, entry):
        container = self.container_of(entry)

        if container is None:
            return 0

        before = total_of(self._wood.pack_other())

        if before == 0:
            return 0

        for pile in self._wood.wrong_piles():
            API.MoveItem(pile.Serial, container, amount_of(pile))
            API.Pause(self._config["move_delay"])

        moved = before - total_of(self._wood.pack_other())

        if moved > 0:
            self._log("put %d wood the menu will not spend back" % moved)

        return moved

    # Re-resolved after the walk: a pathfind that ends early leaves you short
    def reach(self, entry):
        within = self._config["container_range"]

        if entry["kind"] == "mobile":
            animal = API.FindMobile(entry["serial"])

            if animal is None:
                return False

            if animal.Distance <= within:
                return True

            API.PathfindEntity(entry["serial"], within, True, self._config["pathfind_timeout"])
            API.CancelPathfinding()

            animal = API.FindMobile(entry["serial"])

            return animal is not None and animal.Distance <= within

        spot = entry["spot"]

        # A container inside the pack has no world position
        if spot is None or (spot[0] == 0 and spot[1] == 0):
            return True

        if chebyshev(spot[0], spot[1], within + 1) <= within:
            return True

        API.Pathfind(spot[0], spot[1], spot[2], within, True, self._config["pathfind_timeout"])

        return chebyshev(spot[0], spot[1], within + 1) <= within


# src/uo/toolstore.py
class ToolStore(object):
    """The container the craft tools are fetched from, one at a time, once the pack runs out."""

    def __init__(self, tools, sources, config, log):
        self._tools = tools
        self._sources = sources
        self._config = config
        self._log = log
        self._entry = None

    def picked(self):
        return self._entry is not None

    def name(self):
        return self._sources.name_of(self._entry) if self._entry is not None else "nothing"

    def _inside(self):
        container = self._sources.container_of(self._entry) if self._entry is not None else None
        items = API.ItemsInContainer(container, True) if container else None

        return [item for item in (items or []) if self._tools.is_tool(item)]

    def count(self):
        return len(self._inside())

    def line(self):
        return "'%s' %s - %d %s" % (self.name(), hex_of(self._entry["serial"]), self.count(),
                                    self._config["noun"])

    def _refusal(self, serial):
        if serial == API.Backpack:
            return "that is your own pack"

        entry = self._sources.entry_for(serial)

        if entry is None:
            return "%s is neither a container nor a creature" % hex_of(serial)

        if entry["kind"] == "box":
            return ("'%s' is a storage box, which holds no %s - pick a chest or a pack animal"
                    % (self._sources.name_of(entry), self._config["noun"]))

        if self._sources.open(entry) is None:
            return "'%s' did not open" % self._sources.name_of(entry)

        return None

    # (the container's line, None) or (line, why OK will refuse it), (None, why it was refused),
    # or (None, None) for ESC
    def pick(self):
        serial = request_one(self._config["pick_timeout"])

        if serial is None:
            return None, None

        refusal = self._refusal(serial)

        if refusal is not None:
            self._log(refusal)

            return None, refusal

        self._entry = self._sources.entry_for(serial)
        line = self.line()
        self._log("fetching %s from %s" % (self._config["noun"], line))

        if self.count() == 0:
            return line, "'%s' holds no %s" % (self.name(), self._config["noun"])

        return line, None

    # True once the pack holds a tool again; the move is asynchronous, so the pack is watched
    def fetch(self):
        if self._entry is None:
            return False

        if not self._sources.reach(self._entry):
            self._log("cannot reach '%s' for a tool" % self.name())

            return False

        if self._sources.open(self._entry) is None:
            self._log("'%s' did not open for a tool" % self.name())

            return False

        inside = self._inside()

        if len(inside) == 0:
            self._log("'%s' has no %s left" % (self.name(), self._config["noun"]))

            return False

        API.MoveItem(inside[0].Serial, API.Backpack)
        API.Pause(self._config["move_delay"])

        landed = settled(self._config["fetch_timeout"], self._config["fetch_poll"],
                         lambda: self._tools.serial() is not None)

        if landed:
            self._log("fetched a tool from '%s', %d left" % (self.name(), self.count()))
        else:
            self._log("'%s' gave up no tool" % self.name())

        return landed


# src/alchemy/index.py
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

answers = setup.ask({
    "table": lambda: ("%s %s" % (skill_name, reading(start)), []),
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
