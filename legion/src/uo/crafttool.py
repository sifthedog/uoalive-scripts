import API

from uo.entity import hex_of
from uo.pack import pack_contents
from uo.retry import settled
from uo.text import word_in
from uo.tool import is_bag


class CraftTool(object):
    """A crafting tool, used out of the pack rather than equipped."""

    def __init__(self, noun, graphics, name_words, log, prefer=None):
        self._noun = noun
        self._graphics = graphics
        self._name_words = name_words
        self._log = log
        self._prefer = prefer or set()
        self._opened = set()

    def is_tool(self, item):
        if item is None:
            return False

        if item.Graphic in self._graphics:
            return True

        if not word_in(item.Name, self._name_words):
            return False

        self._graphics.add(item.Graphic)
        self._log("%s '%s' is a %s too, remembering the art"
                  % (hex_of(item.Graphic), item.Name, self._noun))

        return True

    def serials(self):
        return [item.Serial for item in pack_contents() if self.is_tool(item)]

    def serial(self):
        found = None

        for item in pack_contents():
            if not self.is_tool(item):
                continue

            if item.Graphic in self._prefer:
                return item.Serial

            if found is None:
                found = item.Serial

        return found

    # A bag the client has not opened this session reads as empty, whatever is in it
    def open_bags(self):
        bags = [item for item in pack_contents()
                if is_bag(item) and item.Serial not in self._opened]

        if not bags:
            return False

        # A cursor left up would take the double-click as its answer
        if API.HasTarget():
            API.CancelTarget()

        self._log("opening %d bag(s) to look inside for a %s" % (len(bags), self._noun))

        for bag in bags:
            self._opened.add(bag.Serial)
            API.UseObject(bag.Serial)

        return True

    def find(self, timeout, poll):
        found = self.serial()

        if found is None and self.open_bags():
            settled(timeout, poll, lambda: self.serial() is not None)
            found = self.serial()

        return found
