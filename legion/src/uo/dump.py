import API

from uo.entity import hex_of
from uo.pack import amount_of, pack_contents
from uo.target import request_one


class Dump(object):
    """The container the products are unloaded into: a trash barrel, or a chest."""

    def __init__(self, sources, graphics, config, log):
        self._sources = sources
        self._graphics = graphics
        self._config = config
        self._log = log
        self._entry = None
        keep_graphics = config.get("keep_graphics", graphics)
        # Carpentry narrows this to the deed art, which doubles as a house deed's - keeping every
        # matching graphic locked out leftover, un-dumped stock from a previous run for good
        self._kept = (set(item.Serial for item in pack_contents()
                           if item.Graphic in keep_graphics)
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

    # Sell watches only what nobody buys; the kept set was read against every product, a superset
    def limit_to(self, graphics):
        self._graphics = graphics

    def line(self):
        return "'%s' %s" % (self.name(), hex_of(self._entry["serial"]))

    def _refusal(self, serial):
        if serial == API.Backpack:
            return "that is your own pack"

        entry = self._sources.entry_for(serial)

        if entry is None:
            return "%s is neither a container nor a creature" % hex_of(serial)

        if entry["kind"] == "box":
            return ("'%s' is a storage box, which takes nothing you made - pick a barrel or a "
                    "chest" % self._sources.name_of(entry))

        if self._sources.open(entry) is None:
            return "'%s' has no backpack to unload into" % self._sources.name_of(entry)

        return None

    # (the picked container's line, None), (None, why it was refused), or (None, None) for ESC
    def pick_line(self):
        serial = request_one(self._config["pick_timeout"])

        if serial is None:
            return None, None

        refusal = self._refusal(serial)

        if refusal is not None:
            self._log(refusal)

            return None, refusal

        self._entry = self._sources.entry_for(serial)
        self._log("unloading into %s" % self.line())

        return self.line(), None

    def pick(self):
        self._log("target the container to unload into, a trash barrel or a chest - ESC to keep "
                  "everything in the pack")

        line, _refusal = self.pick_line()

        return self._entry if line is not None else None

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
