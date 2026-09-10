import API

from uo.entity import hex_of
from uo.retry import settled


def describe_item(item):
    if item is None:
        return "nothing"

    return "%s ('%s')" % (hex_of(item.Serial), item.Name or "unnamed")


class Hands(object):
    """What the hands held at start-up, put in the pack for a trance and drawn again by serial."""

    def __init__(self, layers, attempts, timeout, poll, log):
        self._layers = layers
        self._attempts = attempts
        self._timeout = timeout
        self._poll = poll
        self._log = log
        self._held = []

    def remember(self):
        self._held = []
        items = []

        for layer in self._layers:
            item = API.FindLayer(layer)

            if item is not None:
                self._held.append((item.Serial, layer))
                items.append(item)

        return items

    def remembered(self):
        return len(self._held) > 0

    def _on_layer(self, serial, layer):
        item = API.FindLayer(layer)

        return item is not None and item.Serial == serial

    def _cancel_cursor(self):
        if API.HasTarget():
            API.CancelTarget()

    def stow(self):
        stowed = True

        for serial, layer in self._held:
            if not self._on_layer(serial, layer):
                continue

            self._cancel_cursor()

            for _attempt in range(self._attempts):
                API.MoveItem(serial, API.Backpack)

                if settled(self._timeout, self._poll, lambda: not self._on_layer(serial, layer)):
                    break
            else:
                stowed = False
                self._log("could not put %s in the pack" % hex_of(serial))

        return stowed

    def restore(self):
        restored = True

        for serial, layer in self._held:
            if self._on_layer(serial, layer):
                continue

            self._cancel_cursor()

            for _attempt in range(self._attempts):
                API.EquipItem(serial)

                if settled(self._timeout, self._poll, lambda: self._on_layer(serial, layer)):
                    break
            else:
                restored = False
                self._log("could not draw %s again" % hex_of(serial))

        return restored
