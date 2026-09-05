from uo.clock import now
from uo.entity import hex_of, player


# Written by hand rather than with json.dumps: the bundler admits API and time and nothing else, and
# a row of numbers and two short strings is not worth relaxing that rule for.
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


def skill_json(value):
    return "null" if value is None else "%.1f" % value


def append_line(path, line):
    handle = open(path, "a")

    try:
        handle.write(line + "\n")
    finally:
        handle.close()


class AttemptLog(object):
    """One JSON object per attempt, appended as it happens.

    A row is buffered when the attempt resolves and written on the *next* skill read, because the
    client applies a gain some time after the outcome and a value read straight away is usually
    still the old one. The cost of that is one row in the air at any moment, which a killed script
    loses; the alternative is a file that under-reports every gain it exists to measure.
    """

    def __init__(self, path, character, serial, skill, log, append=None):
        self._path = path or ""
        self._character = character or ""
        self._serial = serial
        self._skill = skill
        self._log = log
        self._append = append if append is not None else append_line
        self._off = not self._path
        # Milliseconds, not seconds: two runs started inside the same second would mint the
        # same ids, and the converter reads a repeated id as the same row arriving twice
        self._run = int(now() * 1000)
        self._seq = 0
        self._pending = None
        self._said = False

    # Asked before an attempt so a caller can skip the work of measuring what it spent
    def recording(self):
        return not self._off

    # consumed is a list of (name, graphic, hue, quantity) - measured, so an attempt that spent
    # nothing passes nothing rather than a guess at what the recipe charges
    def record(self, skill_from, outcome, success, consumed=None, stock=None):
        if self._off or skill_from is None:
            return

        # A caller that records twice without settling in between would otherwise drop the first
        # row. This later read is exactly what the missed settle would have passed.
        self.settle(skill_from)

        self._seq += 1
        self._pending = {
            "id": "%s/%d/%d" % (hex_of(self._serial), self._run, self._seq),
            "at": now(),
            "from": skill_from,
            "outcome": outcome,
            "ok": success,
            "consumed": list(consumed) if consumed else [],
            # (before, after) totals of the material the attempt is costed in, written raw so the
            # subtraction in 'consumed' can be checked without trusting it
            "stock": tuple(stock) if stock else None,
        }

    def settle(self, skill_to):
        pending = self._pending
        self._pending = None

        if pending is None or self._off:
            return

        self._write(pending, skill_to)

    def _line(self, row, skill_to):
        fields = [
            '"v":1',
            '"id":%s' % quoted(row["id"]),
            '"t":%.3f' % row["at"],
            '"char":%s' % quoted(self._character),
            '"serial":%s' % quoted(hex_of(self._serial)),
            '"skill":%s' % quoted(self._skill),
            '"from":%s' % skill_json(row["from"]),
            '"to":%s' % skill_json(skill_to),
            '"outcome":%s' % quoted(row["outcome"]),
            '"ok":%s' % ("true" if row["ok"] else "false"),
        ]

        if row.get("stock"):
            fields.append('"stock_from":%d,"stock_to":%d' % (row["stock"][0], row["stock"][1]))

        if row["consumed"]:
            fields.append('"consumed":[%s]' % ",".join(
                '{"name":%s,"graphic":%s,"hue":%d,"qty":%d}'
                % (quoted(name), quoted(hex_of(graphic)), hue, quantity)
                for name, graphic, hue, quantity in row["consumed"]
            ))

        return "{%s}" % ",".join(fields)

    # A run that cannot write its log is still a run: the recorder retires itself and says so once,
    # rather than ending the training over a file
    def _write(self, row, skill_to):
        try:
            self._append(self._path, self._line(row, skill_to))
        except Exception as error:
            self._off = True

            if not self._said:
                self._said = True
                self._log("cannot write %s (%s) - not recording this run" % (self._path, error))


# The character is read once, here, rather than on every row: it cannot change under a running
# script, and a client between world states answers None for the player without that meaning the
# run should stop recording.
def attempt_log(path, skill, log):
    me = player()

    if me is None and path:
        log("the client is not reporting the character - rows will not name it")

    return AttemptLog(path, getattr(me, "Name", ""), getattr(me, "Serial", 0), skill, log)
