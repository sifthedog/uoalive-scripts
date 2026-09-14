import API

from uo.pack import amount_of, pack_contents
from uo.text import any_in, word_in


class Kegs(object):
    """The empty potion kegs in the pack. The shard pours a craft into a keg already holding that
    potion and bottles it otherwise, so the bottled one is dropped onto the first empty keg and the
    rest of the band pours in by itself. Dropped onto, never used: using a keg pours one out."""

    def __init__(self, dump, config, log):
        self._dump = dump
        self._config = config
        self._log = log

    def is_keg(self, item):
        return item.Graphic in self._config["graphics"] or word_in(item.Name, self._config["words"])

    def is_empty(self, item):
        return self.is_keg(item) and not any_in(item.Name, self._config["filled_text"])

    # Fullness is a tooltip line, not the name
    def is_full(self, item):
        if not self.is_keg(item):
            return False

        props = API.ItemNameAndProps(item.Serial, True, self._config["opl_timeout"]) or ""

        return any_in(props, self._config["full_text"])

    def empty(self):
        for item in pack_contents():
            if self.is_empty(item):
                return item

        return None

    def run(self):
        items = self._dump.items()

        if len(items) == 0:
            return 0

        keg = self.empty()

        if keg is None:
            self._log("no empty keg in the pack for the %d potions the run made" % self._dump.held())

            return 0

        before = self._dump.held()

        for item in items:
            API.MoveItem(item.Serial, keg.Serial, amount_of(item))
            API.Pause(self._config["move_delay"])

        moved = before - self._dump.held()

        if moved > 0:
            self._log("poured %d into '%s'" % (moved, keg.Name))
        else:
            self._log("'%s' took nothing" % keg.Name)

        return moved


class EmptyKegs(object):
    """What ToolStore fetches: an empty keg is the tool, and the pack holds one or none."""

    def __init__(self, kegs):
        self._kegs = kegs

    def is_tool(self, item):
        return self._kegs.is_empty(item)

    def serial(self):
        keg = self._kegs.empty()

        return keg.Serial if keg is not None else None
