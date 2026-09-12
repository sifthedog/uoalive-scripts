import API

from uo.entity import hex_of
from uo.retry import settled
from uo.target import request_one


class ToolStore(object):
    """The container the craft tools are fetched from, one at a time, once the pack runs out."""

    def __init__(self, tools, sources, config, log):
        self._tools = tools
        self._sources = sources
        self._config = config
        self._log = log
        self._entry = None

    def picked(self):
        return self._entry is not None

    def name(self):
        return self._sources.name_of(self._entry) if self._entry is not None else "nothing"

    def _inside(self):
        container = self._sources.container_of(self._entry) if self._entry is not None else None
        items = API.ItemsInContainer(container, True) if container else None

        return [item for item in (items or []) if self._tools.is_tool(item)]

    def count(self):
        return len(self._inside())

    def line(self):
        return "'%s' %s - %d %s" % (self.name(), hex_of(self._entry["serial"]), self.count(),
                                    self._config["noun"])

    def _refusal(self, serial):
        if serial == API.Backpack:
            return "that is your own pack"

        entry = self._sources.entry_for(serial)

        if entry is None:
            return "%s is neither a container nor a creature" % hex_of(serial)

        if entry["kind"] == "box":
            return ("'%s' is a storage box, which holds no %s - pick a chest or a pack animal"
                    % (self._sources.name_of(entry), self._config["noun"]))

        if self._sources.open(entry) is None:
            return "'%s' did not open" % self._sources.name_of(entry)

        return None

    # (the container's line, None) or (line, why OK will refuse it), (None, why it was refused),
    # or (None, None) for ESC
    def pick(self):
        serial = request_one(self._config["pick_timeout"])

        if serial is None:
            return None, None

        refusal = self._refusal(serial)

        if refusal is not None:
            self._log(refusal)

            return None, refusal

        self._entry = self._sources.entry_for(serial)
        line = self.line()
        self._log("fetching %s from %s" % (self._config["noun"], line))

        if self.count() == 0:
            return line, "'%s' holds no %s" % (self.name(), self._config["noun"])

        return line, None

    # True once the pack holds a tool again; the move is asynchronous, so the pack is watched
    def fetch(self):
        if self._entry is None:
            return False

        if not self._sources.reach(self._entry):
            self._log("cannot reach '%s' for a tool" % self.name())

            return False

        if self._sources.open(self._entry) is None:
            self._log("'%s' did not open for a tool" % self.name())

            return False

        inside = self._inside()

        if len(inside) == 0:
            self._log("'%s' has no %s left" % (self.name(), self._config["noun"]))

            return False

        API.MoveItem(inside[0].Serial, API.Backpack)
        API.Pause(self._config["move_delay"])

        landed = settled(self._config["fetch_timeout"], self._config["fetch_poll"],
                         lambda: self._tools.serial() is not None)

        if landed:
            self._log("fetched a tool from '%s', %d left" % (self.name(), self.count()))
        else:
            self._log("'%s' gave up no tool" % self.name())

        return landed
