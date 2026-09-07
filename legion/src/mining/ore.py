import API

from uo.entity import hex_of
from uo.pack import amount_of, hue_of, pack_contents, pack_top_level
from uo.text import word_in


class OrePack(object):
    def __init__(self, graphics, name_word, min_smelt, log):
        self._graphics = graphics
        self._name_word = name_word
        self._min_smelt = min_smelt
        self._log = log

    # Graphic first, name second: names are empty until the client has tooltip data. An art learned
    # by name joins the set, so it costs one tooltip and no more.
    def is_ore(self, item):
        if item.Graphic in self._graphics:
            return True

        if not word_in(item.Name, [self._name_word]):
            return False

        self._graphics.add(item.Graphic)
        self._log("%s '%s' is ore too, remembering the art" % (hex_of(item.Graphic), item.Name))

        return True

    # Top level only, unlike total: the combine and the smelt both act by serial on loose items.
    # Largest first, so the pile a combine consumes is always the smaller one.
    def piles(self):
        piles = [item for item in pack_top_level() if self.is_ore(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    # Hue-blind on purpose: every ore type counts toward the pack, whatever it smelts into
    def total(self):
        return sum(amount_of(item) for item in pack_contents() if self.is_ore(item))

    # Reads the total rather than the number of piles, so a shard that does merge ore on arrival is
    # satisfied immediately instead of waiting out the timeout on every swing
    def wait_for_ore(self, before, timeout, poll):
        waited = 0.0

        while not API.StopRequested:
            # Read before the first pause: the delivery has usually already happened by the time the
            # journal line announcing it is read
            if self.total() > before:
                return True

            if waited >= timeout:
                return False

            API.Pause(poll)
            waited += poll

    # item.Amount reads 0 for a stack the client has no data for, so 'amount >= 2' skips every pile
    # in the pack. An unknown size is worth one attempt; only a size reported as one is skipped.
    def big_enough(self, item):
        amount = item.Amount or 0

        return amount == 0 or amount >= self._min_smelt

    def next_ore(self, written_off):
        for item in self.piles():
            if hue_of(item) not in written_off and self.big_enough(item):
                return item

        return None

    def describe_skipped(self, item, written_off):
        amount = item.Amount or 0
        hue = hue_of(item)

        if hue in written_off:
            return "%d hue %d (written off)" % (amount, hue)

        if not self.big_enough(item):
            return "%d hue %d (too small)" % (amount, hue)

        return "%d hue %d" % (amount, hue)
