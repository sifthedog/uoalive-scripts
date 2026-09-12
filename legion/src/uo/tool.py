import API

from uo.entity import hex_of
from uo.pack import pack_contents
from uo.retry import settled
from uo.text import word_in

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


class Tool(object):
    """Find it, learn its graphic, get it onto the hand, and notice when it breaks."""

    def __init__(self, noun, names, veto, layers, spare_bag, attempts, timeout, poll, log):
        self._noun = noun
        self._names = names
        self._veto = veto
        self._layers = layers
        self._spare_bag = spare_bag
        self._attempts = attempts
        self._timeout = timeout
        self._poll = poll
        self._log = log
        self._graphic = None
        self._reported_empty_pack = False
        self._opened = set()

    # Refused only on positive evidence. A name reads empty until the client has tooltip data, and
    # a tool in hand is the documented precondition, so an unnamed one is taken at its word - but a
    # vetoed tool learned here would be the tool for the whole run, and every swing would be wrong.
    def learn(self, item):
        if item is None or self._graphic is not None:
            return

        name = item.Name or ""

        if word_in(name, self._veto):
            self._log("you are holding a '%s', which this run does not use as its %s - "
                      "not learning its graphic" % (name, self._noun))

            return

        self._graphic = item.Graphic
        self._log("%s graphic is %s ('%s')" % (self._noun, hex_of(item.Graphic), name or "unnamed"))

    def is_tool(self, item):
        if item is None:
            return False

        name = item.Name or ""

        # The veto is asked before the graphic, not after it: one already learned off a shard that
        # names nothing, or off a hand that held it at startup, would go on matching every cycle
        if word_in(name, self._veto):
            return False

        if self._graphic is not None and item.Graphic == self._graphic:
            return True

        return word_in(name, self._names)

    def held(self):
        for layer in self._layers:
            found = API.FindLayer(layer)

            if found is not None:
                return found

        return None

    def serial(self):
        item = self.held()

        return item.Serial if item is not None else None

    def _search(self):
        for item in pack_contents():
            if self.is_tool(item):
                return item

        if self._spare_bag is not None:
            for item in API.ItemsInContainer(self._spare_bag, True) or []:
                if self.is_tool(item):
                    return item

        return None

    def find(self):
        found = find_after_opening_bags(self._search, self._noun, self._log, self._opened,
                                        self._timeout, self._poll, self._spare_bag)

        if found is not None:
            self._reported_empty_pack = False
            self.learn(found)

            return found

        if not self._reported_empty_pack:
            self._reported_empty_pack = True
            arts = [hex_of(item.Graphic) for item in pack_contents()]
            self._log("no %s found - nothing named %s in the pack. It holds: %s"
                      % (self._noun, "/".join(self._names), ", ".join(arts) or "nothing"))

        return None

    # A broken tool can linger on the layer, and is_tool would match it by graphic, so the world is
    # asked rather than the layer
    def still_holding(self):
        item = self.held()

        return item is not None and self.is_tool(item) and API.FindItem(item.Serial) is not None

    def equip(self):
        if self.still_holding():
            return True

        found = self.find()

        if found is None:
            return False

        # A cursor left open by the swing that broke the tool would swallow the equip
        if API.HasTarget():
            API.CancelTarget()

        serial = found.Serial

        for _attempt in range(self._attempts):
            API.EquipItem(serial)

            if settled(self._timeout, self._poll, lambda: self.serial() == serial):
                return True

        self._log("could not get the %s %s onto the hand" % (self._noun, hex_of(serial)))

        return False
