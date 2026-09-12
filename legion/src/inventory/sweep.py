import API

from uo.clock import now
from uo.entity import hex_of, player
from uo.pack import amount_of, hue_of
from uo.paths import beside_script
from uo.record import append_line, json_object
from uo.tooltip import parse_tooltip


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
