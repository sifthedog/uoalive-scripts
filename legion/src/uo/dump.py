import API

from uo.entity import hex_of
from uo.pack import amount_of, pack_contents


class Dump(object):
    """The container the products are unloaded into: a trash barrel, or a chest."""

    def __init__(self, sources, graphics, config, log):
        self._sources = sources
        self._graphics = graphics
        self._config = config
        self._log = log
        self._entry = None
        # Carpentry keeps: the deed art is also a house deed's
        self._kept = (set(item.Serial for item in self._products())
                      if config["keep_existing"] else set())

    def _products(self):
        return [item for item in pack_contents() if item.Graphic in self._graphics]

    def items(self):
        return [item for item in self._products() if item.Serial not in self._kept]

    def held(self):
        return sum(amount_of(item) for item in self.items())

    def picked(self):
        return self._entry is not None

    def name(self):
        return self._sources.name_of(self._entry) if self._entry is not None else "nothing"

    def pick(self):
        self._log("target the container to unload into, a trash barrel or a chest - ESC to keep "
                  "everything in the pack")

        if API.HasTarget():
            API.CancelTarget()

        serial = API.RequestTarget(self._config["pick_timeout"])

        if API.HasTarget():
            API.CancelTarget()

        if not serial:
            return None

        if serial == API.Backpack:
            self._log("that is your own pack")

            return None

        entry = self._sources.entry_for(serial)

        if entry is None:
            self._log("%s is neither a container nor a creature" % hex_of(serial))

            return None

        if entry["kind"] == "box":
            self._log("'%s' is a storage box, which takes nothing you made - pick a barrel or a "
                      "chest" % self._sources.name_of(entry))

            return None

        if self._sources.open(entry) is None:
            self._log("'%s' has no backpack to unload into" % self._sources.name_of(entry))

            return None

        self._entry = entry
        self._log("unloading into '%s' %s" % (self.name(), hex_of(serial)))

        return entry

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
