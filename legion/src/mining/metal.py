import API

from uo.text import words_of


class MetalBook(object):
    """What the tooltip says each pile is made of, and how much that answer is trusted."""

    def __init__(self, config, log):
        self._metals = config["metals"]
        self._plain = config["plain"]
        self._line_extra = config["line_extra"]
        self._not_metal_words = config["not_metal_words"]
        self._asks = config["asks"]
        self._miss_limit = config["misses"]
        self._log = log

        self._known = {}
        self._asked = {}
        self._missed_this_pass = set()
        self._doubted = set()
        self._opl_names_metals = True
        self._opl_answered = False
        self._misses = 0

    def _looks_like_metal(self, line):
        if not line or not line[0].isalpha():
            return False

        for char in line:
            if not char.isalpha() and char not in self._line_extra:
                return False

        for word in words_of(line):
            if word in self._not_metal_words:
                return False

        return True

    def _body(self, props, name):
        lines = []

        for raw in (props or "").splitlines():
            line = raw.strip()

            if line and line != name:
                lines.append(line)

        return lines

    def _read_metal(self, props, name):
        lines = self._body(props, name)

        for line in lines:
            if line.lower() in self._metals:
                return line.lower()

        for line in lines:
            if self._looks_like_metal(line):
                self._metals.add(line.lower())
                self._log("'%s' is a metal too, remembering it" % line)

                return line.lower()

        return self._plain

    def _worth_asking(self, serial):
        return (
            self._opl_names_metals
            and serial not in self._missed_this_pass
            and self._asked.get(serial, 0) < self._asks
        )

    def _look_up(self, item):
        serial = item.Serial

        if serial in self._known or not self._worth_asking(serial):
            return

        self._asked[serial] = self._asked.get(serial, 0) + 1

        # Never waited for: a wait is a second of nothing else, and the pile is still there next pass
        props = API.ItemNameAndProps(serial, False) or ""

        if not props:
            self._missed_this_pass.add(serial)
            API.RequestOPLData([serial])

            return

        name = (item.Name or "").strip()

        # A miss is a tooltip that arrived carrying only the name
        if not self._body(props, name):
            self._missed_this_pass.add(serial)
            self._misses += 1

            if self._misses >= self._miss_limit:
                self._opl_names_metals = False
                self._log("tooltips are not naming the metal here, so a pair has to be refused "
                          "to be split")

            return

        self._misses = 0
        self._opl_answered = True
        self._known[serial] = self._read_metal(props, name)

    # None is 'the tooltip did not say', which is not a metal of its own: callers fall back to the
    # hue and the shard's refusal for those
    def of(self, item):
        self._look_up(item)

        metal = self._known.get(item.Serial)

        return None if metal is not None and metal in self._doubted else metal

    def pending(self, item):
        self._look_up(item)

        # Not _worth_asking: a pile that missed this pass is still pending, or it would be paired on
        # a guess the moment its lookup came back empty
        return (
            self._opl_answered
            and self._opl_names_metals
            and item.Serial not in self._known
            and self._asked.get(item.Serial, 0) < self._asks
        )

    def start_pass(self):
        self._missed_this_pass.clear()

    def doubt(self, metal):
        if metal in self._doubted:
            return

        self._doubted.add(metal)
        self._log("the shard refused two piles both read as '%s', so that line is not the metal"
                  % metal)

    # The shard reissues the serial of a pile a combine or a smelt consumed, so a stale entry would
    # name the wrong metal for whatever turns up wearing it next
    def forget_missing(self, piles):
        here = set(pile.Serial for pile in piles)

        for serial in list(self._known.keys()):
            if serial not in here:
                del self._known[serial]

        for serial in list(self._asked.keys()):
            if serial not in here:
                del self._asked[serial]
