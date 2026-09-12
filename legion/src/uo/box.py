import API

from uo.entity import hex_of
from uo.gump import await_recognised, button_ids, gump_says, is_open, open_ids
from uo.text import any_in, untagged


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
