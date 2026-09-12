# Built from src/inventory/index.py by build.py - do not edit.

import API
import time


# src/inventory/config.py
# One JSON object per item is appended here. "" turns recording off. A bare name lands in TazUO's
# working directory rather than beside the script - set an absolute path to put it somewhere you
# will find it.
DATA_PATH = "bag-items.jsonl"

# Whether a bag inside the bag is opened and read too
RECURSIVE = True

PICK_TIMEOUT = 30.0

# After UseObject on each container, so the client has seen inside before it is listed
OPEN_DELAY = 0.6

# One RequestOPLData per batch of this many serials, then this long for the tooltips to land
OPL_BATCH = 25
OPL_WAIT = 1.0

# Whole seconds: the API takes an int here
OPL_TIMEOUT = 1

# Further ask-and-read rounds for the tooltips that did not come. What still has none is written
# anyway, with the client's name and no lines.
RETRIES = 2

MAX_CONTAINERS = 50

# The whole line, matched without regard to case, kept as the shard wrote it. Stock ServUO
# ItemPower wording; "Minor" is here for a shard that says it instead of "Lesser".
TIER_TEXT = [
    "Minor Magic Item",
    "Lesser Magic Item",
    "Greater Magic Item",
    "Major Magic Item",
    "Lesser Artifact",
    "Greater Artifact",
    "Major Artifact",
    "Legendary Artifact",
]

# Line starts, matched without regard to case
DURABILITY_TEXT = ["durability"]
WEIGHT_TEXT = ["weight"]

# Line starts whose remainder is text rather than a number or a flag
PREFIX_TEXT = ["crafted by"]


# src/uo/clock.py
def now():
    return time.time()


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


# src/uo/pack.py
# None is an unreported stack, not an empty one: counted as 0 it would hide the ore a swing just
# delivered, which is the proof that the swing landed
def amount_of(item):
    amount = getattr(item, "Amount", None)

    return amount if amount is not None else 1


def hue_of(item):
    return getattr(item, "Hue", 0) or 0


# src/uo/paths.py
# TazUO's working directory is its own folder, and the scripts live in this subfolder of it
SCRIPTS_FOLDER = "LegionScripts"


# A bare name lands in TazUO's working directory; beside the script is where anyone looks for it.
# A name with a folder in it, relative or absolute, is left as written.
def beside_script(name):
    if not name or "/" in name or "\\" in name:
        return name

    script = getattr(API, "ScriptPath", None) or ""
    cut = max(script.rfind("/"), script.rfind("\\"))

    # A client that does not say where the script is still runs it out of the standard folder
    if cut < 0:
        return SCRIPTS_FOLDER + "/" + name

    return script[:cut + 1] + name


# src/uo/record.py
# Written by hand rather than with json.dumps, so the key order stays the one the README shows
def quoted(text):
    out = ['"']

    for character in text:
        code = ord(character)

        if character == '"' or character == "\\":
            out.append("\\" + character)
        elif character == "\n":
            out.append("\\n")
        elif character == "\r":
            out.append("\\r")
        elif character == "\t":
            out.append("\\t")
        # Non-ASCII escaped rather than written through: a character name carrying an accent is
        # ordinary here, and what encoding the runtime picked for the file is not knowable from in
        # here
        elif code < 0x20 or code > 0x7E:
            out.append("\\u%04x" % code)
        else:
            out.append(character)

    out.append('"')

    return "".join(out)


# Every scalar and container a row can carry. Dict keys are sorted because the property map has no
# order of its own, and a sorted row diffs; an order that matters is a json_object of pairs.
def json_value(value):
    if value is None:
        return "null"
    elif value is True:
        return "true"
    elif value is False:
        return "false"
    elif isinstance(value, (int, float)):
        return repr(value)
    elif isinstance(value, (list, tuple)):
        return "[%s]" % ",".join(json_value(entry) for entry in value)
    elif isinstance(value, dict):
        return json_object([(key, value[key]) for key in sorted(value)])

    return quoted(str(value))


def json_object(pairs):
    return "{%s}" % ",".join("%s:%s" % (quoted(key), json_value(value)) for key, value in pairs)


def append_line(path, line):
    handle = open(path, "a")

    try:
        handle.write(line + "\n")
    finally:
        handle.close()


# src/uo/tooltip.py
"""An item's tooltip lines, read into a name, a tier, durability, weight and a property map.

Pure text: nothing here asks the client. Every rule is a string method because `re` is not in the
bundle. A line no rule understands is still kept, as a flag, so the map never loses one.
"""


# "15%" -> 15, "+20%" -> 20, "-10" -> -10, "2.5s" -> 2.5; anything else -> None
def tooltip_number(token):
    text = token.strip().rstrip("%")

    if len(text) > 1 and text.endswith("s") and text[-2].isdigit():
        text = text[:-1]

    if text.startswith("+") or text.startswith("-"):
        sign = -1 if text[0] == "-" else 1
        text = text[1:]
    else:
        sign = 1

    if not text or text.count(".") > 1 or not text.replace(".", "").isdigit():
        return None

    if "." in text:
        return sign * float(text)

    return sign * int(text)


def tooltip_key(tokens):
    return " ".join(tokens).strip().rstrip(":").strip()


def _numbers_in(text):
    found = []

    for token in text.replace(":", " ").replace("/", " ").split():
        number = tooltip_number(token)

        if number is not None:
            found.append(number)

    return found


def _starts_with_any(low, words):
    for word in words:
        if low.startswith(word.lower()):
            return word.lower()

    return None


def _tier_of(low, line, tiers):
    for tier in tiers:
        if low == tier.lower():
            return line

    return None


# A trailing number, and the two-number range before it: `weapon damage 13 - 15`
def _numbered(tokens):
    for index in range(len(tokens) - 1, -1, -1):
        number = tooltip_number(tokens[index])

        if number is None:
            continue

        if index >= 2 and tokens[index - 1] == "-":
            low = tooltip_number(tokens[index - 2])

            if low is not None:
                return tooltip_key(tokens[:index - 2]), [low, number]

        return tooltip_key(tokens[:index]), number

    return None, None


def parse_tooltip(lines, config):
    kept = [line.strip() for line in lines if line and line.strip()]
    parsed = {"name": kept[0] if kept else "", "tier": None, "durability": None, "weight": None,
              "props": {}}
    props = parsed["props"]

    for line in kept[1:]:
        low = line.lower()
        tier = _tier_of(low, line, config["tier"])

        if tier is not None:
            parsed["tier"] = tier
            continue

        word = _starts_with_any(low, config["durability"])

        if word is not None:
            numbers = _numbers_in(low[len(word):])

            if len(numbers) >= 2:
                parsed["durability"] = {"current": numbers[0], "max": numbers[1]}
                continue

        word = _starts_with_any(low, config["weight"])

        if word is not None:
            numbers = _numbers_in(low[len(word):])

            if numbers:
                parsed["weight"] = numbers[0]
                continue

        prefix = _starts_with_any(low, config["prefixes"])

        if prefix is not None:
            props[prefix] = line[len(prefix):].strip()
            continue

        key, value = _numbered(low.split())

        if key:
            props[key] = value
            continue

        if ":" in line:
            before, after = line.split(":", 1)
            props[tooltip_key(before.lower().split())] = after.strip()
            continue

        props[low] = True

    return parsed


# src/inventory/sweep.py
def tooltip_lines(serial, timeout):
    props = API.ItemNameAndProps(serial, True, timeout) or ""

    return [line.strip() for line in props.splitlines() if line.strip()]


def batches_of(items, size):
    return [items[start:start + size] for start in range(0, len(items), max(1, size))]


class Sweep(object):
    """Every item in a bag, one JSON line each, written as soon as its tooltip is read.

    Rows go out batch by batch rather than at the end, so a stop halfway keeps what was read. An
    item whose tooltip never comes is written last with the client's name and no lines: the row
    says it was there, and `unread` says the rest is missing rather than absent.
    """

    def __init__(self, path, character, config, log, append=None):
        self._path = beside_script(path or "")
        self._character = character or ""
        self._config = config
        self._log = log
        self._append = append if append is not None else append_line
        self._off = not self._path
        self._run = int(now() * 1000)
        self._said = False

    def recording(self):
        return not self._off

    def run(self, bag):
        items, opened = self._collect(bag)
        self._log("reading %d item%s" % (len(items), "" if len(items) == 1 else "s"))

        written = 0
        left = []

        for batch in batches_of(items, self._config["opl_batch"]):
            if API.StopRequested:
                break

            self._prime(batch)

            for item in batch:
                if API.StopRequested:
                    break

                if self._read(bag, item):
                    written += 1
                else:
                    left.append(item)

        for _round in range(self._config["retries"]):
            if not left or API.StopRequested:
                break

            self._prime(left)
            still = []

            for item in left:
                if self._read(bag, item):
                    written += 1
                else:
                    still.append(item)

            left = still

        for item in left:
            self._write(bag, item, [], True)
            written += 1

        return written, len(left), opened

    # Asked once per batch: a tooltip is a round trip each, and asked together they land together
    def _prime(self, items):
        if len(items) == 0:
            return

        API.RequestOPLData([item.Serial for item in items])
        API.Pause(self._config["opl_wait"])

    def _read(self, bag, item):
        lines = tooltip_lines(item.Serial, self._config["opl_timeout"])

        if len(lines) == 0:
            return False

        self._write(bag, item, lines, False)

        return True

    # ItemsInContainer reads nothing out of a container the client has never seen inside, so each
    # one is opened before it is listed. Breadth first on the flat listing, so every item's row
    # names the bag it sits in
    def _collect(self, bag):
        self._open(bag)

        queue = [bag]
        seen = set([bag])
        found = []
        opened = 1

        while queue and not API.StopRequested:
            parent = queue.pop(0)

            for item in API.ItemsInContainer(parent, False) or []:
                found.append(item)

                if not self._config["recursive"]:
                    continue

                serial = item.Serial

                if getattr(item, "IsContainer", False) and serial not in seen:
                    if opened >= self._config["max_containers"]:
                        continue

                    seen.add(serial)
                    opened += 1
                    self._open(serial)
                    queue.append(serial)

        return found, opened

    def _open(self, serial):
        API.UseObject(serial)
        API.Pause(self._config["open_delay"])

    def _row(self, bag, item, lines, unread):
        parsed = parse_tooltip(lines, self._config["parser"])
        name = parsed["name"] or getattr(item, "Name", "") or hex_of(item.Serial)
        pairs = [
            ("v", 1),
            ("scan", "%s/%d" % (hex_of(bag), self._run)),
            ("t", round(now(), 3)),
            ("char", self._character),
            ("bag", hex_of(bag)),
            ("serial", hex_of(item.Serial)),
            ("graphic", hex_of(getattr(item, "Graphic", 0) or 0)),
            ("hue", hue_of(item)),
            ("amount", amount_of(item)),
            ("container", hex_of(getattr(item, "Container", 0) or 0)),
            ("name", name),
            ("tier", parsed["tier"]),
            ("durability", parsed["durability"]),
            ("weight", parsed["weight"]),
            ("props", parsed["props"]),
            ("lines", lines),
        ]

        if unread:
            pairs.append(("unread", True))

        return json_object(pairs)

    # A run that cannot write is still a run: it retires the file and says so once
    def _write(self, bag, item, lines, unread):
        if self._off:
            return

        try:
            self._append(self._path, self._row(bag, item, lines, unread))
        except Exception as error:
            if API.StopRequested:
                raise

            self._off = True

            if not self._said:
                self._said = True
                self._log("cannot write %s (%s) - not recording this run" % (self._path, error))


# The character is read once: it cannot change under a running script, and a client between world
# states answers None without that meaning the run should stop
def bag_sweep(path, config, log):
    me = player()

    if me is None and path:
        log("the client is not reporting the character - rows will not name it")

    return Sweep(path, getattr(me, "Name", ""), config, log)


# src/uo/log.py
# Every stamp make_log has handed out. The client puts a SysMsg in the journal beside the shard's
# own lines, so a script reading the journal back needs to know which of them it wrote itself -
# without this a report of an unreadable outcome quotes the last report of an unreadable outcome.
# Lowercase, because that is how the journal readers compare. One entry per script in practice.
STAMPS = []


def make_log(prefix):
    stamp = prefix + ": "

    if stamp.lower() not in STAMPS:
        STAMPS.append(stamp.lower())

    def log(message):
        API.SysMsg(stamp + message)

    return log


# src/inventory/index.py
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
