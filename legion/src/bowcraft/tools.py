from uo.entity import hex_of
from uo.pack import pack_contents
from uo.text import word_in


class Tools(object):
    """The fletcher's tools, which are used out of the pack rather than equipped."""

    def __init__(self, graphics, name_words, log):
        self._graphics = graphics
        self._name_words = name_words
        self._log = log

    def is_tool(self, item):
        if item is None:
            return False

        if item.Graphic in self._graphics:
            return True

        if not word_in(item.Name, self._name_words):
            return False

        self._graphics.add(item.Graphic)
        self._log("%s '%s' is a fletcher's tool too, remembering the art"
                  % (hex_of(item.Graphic), item.Name))

        return True

    def serial(self):
        for item in pack_contents():
            if self.is_tool(item):
                return item.Serial

        return None
