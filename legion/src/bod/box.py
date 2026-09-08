import API

from bod.smalls import is_deed
from uo.entity import hex_of
from uo.pack import pack_contents
from uo.retry import settled
from uo.text import any_in


class DeedBox(object):
    """The Bulk Order Deed Box: one large deed in, the small deeds and the large back out."""

    def __init__(self, config, log):
        self._config = config
        self._log = log

    def find(self):
        for item in pack_contents():
            if any_in(item.Name, self._config["names"]):
                return item.Serial

        return None

    def _deeds(self):
        return set(item.Serial for item in pack_contents() if is_deed(item, self._config))

    def _container_of(self, serial):
        item = API.FindItem(serial)

        return None if item is None else getattr(item, "Container", None)

    def generate(self, box, large):
        before = self._deeds()

        API.MoveItem(large, box)
        API.Pause(self._config["move_delay"])

        if self._container_of(large) != box:
            self._log("the large deed did not go into the box - it is in %s"
                      % hex_of(self._container_of(large) or 0))

            return None

        API.UseObject(box)

        def landed():
            return (self._container_of(large) == API.Backpack
                    and len(self._deeds() - before) > 0)

        if not settled(self._config["timeout"], self._config["poll"], landed):
            back = self._container_of(large) == API.Backpack
            self._log("the box put no deeds in the pack within %.0fs%s"
                      % (self._config["timeout"],
                         "" if back else " - and the large deed is still in it"))

            return []

        # The box drops them in one go, but the client lists them as they arrive
        API.Pause(self._config["move_delay"])
        fresh = sorted(self._deeds() - before)
        self._log("the box put %d deed(s) in the pack" % len(fresh))

        return fresh
