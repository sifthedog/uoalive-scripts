import API

from uo.entity import hex_of
from uo.pack import pack_contents
from uo.retry import settled


class Tool(object):
    """Find it, learn its graphic, get it onto the hand, and notice when it breaks."""

    def __init__(self, name, layers, spare_bag, attempts, timeout, poll, log):
        self._name = name
        self._layers = layers
        self._spare_bag = spare_bag
        self._attempts = attempts
        self._timeout = timeout
        self._poll = poll
        self._log = log
        self._graphic = None
        self._reported_empty_pack = False

    def learn(self, item):
        if item is not None and self._graphic is None:
            self._graphic = item.Graphic
            self._log("%s graphic is %s" % (self._name, hex_of(item.Graphic)))

    def is_tool(self, item):
        if item is None:
            return False

        if self._graphic is not None and item.Graphic == self._graphic:
            return True

        return self._name in (item.Name or "").lower()

    def held(self):
        for layer in self._layers:
            found = API.FindLayer(layer)

            if found is not None:
                return found

        return None

    def serial(self):
        item = self.held()

        return item.Serial if item is not None else None

    def find(self):
        for item in pack_contents():
            if self.is_tool(item):
                self._reported_empty_pack = False
                self.learn(item)

                return item

        if self._spare_bag is not None:
            for item in API.ItemsInContainer(self._spare_bag, True) or []:
                if self.is_tool(item):
                    self._reported_empty_pack = False
                    self.learn(item)

                    return item

        if not self._reported_empty_pack:
            self._reported_empty_pack = True
            arts = [hex_of(item.Graphic) for item in pack_contents()]
            self._log("no %s found. Pack holds: %s" % (self._name, ", ".join(arts) or "nothing"))

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

        self._log("could not get the %s %s onto the hand" % (self._name, hex_of(serial)))

        return False
