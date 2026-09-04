from uo.entity import hex_of
from uo.pack import amount_of, pack_contents, pack_top_level
from uo.text import word_in


class Wood(object):
    """What in the pack is a log and what is a board, learning both arts as it goes."""

    def __init__(self, log_graphics, log_words, board_graphics, board_words, log):
        self._log_graphics = log_graphics
        self._log_words = log_words
        self._board_graphics = board_graphics
        self._board_words = board_words
        self._log = log

    def _matches(self, item, graphics, words, noun):
        if item is None:
            return False

        if item.Graphic in graphics:
            return True

        if not word_in(item.Name, words):
            return False

        graphics.add(item.Graphic)
        self._log("%s '%s' is a %s too, remembering the art"
                  % (hex_of(item.Graphic), item.Name, noun))

        return True

    def is_log(self, item):
        return self._matches(item, self._log_graphics, self._log_words, "log")

    def is_board(self, item):
        return self._matches(item, self._board_graphics, self._board_words, "board")

    # Top level only, unlike log_total: the conversion acts by serial on loose items. Largest first,
    # so the biggest stack is the one turned into boards first.
    def log_piles(self):
        piles = [item for item in pack_top_level() if self.is_log(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def board_piles(self):
        return [item for item in pack_top_level() if self.is_board(item)]

    # Hue-blind on purpose: a shard with special woods hues its logs, and those still count, still
    # convert and still need hauling
    def log_total(self):
        return sum(amount_of(item) for item in pack_contents() if self.is_log(item))
