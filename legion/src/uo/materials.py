import API

from uo.entity import hex_of
from uo.pack import counts_by_graphic, diff_counts, hue_of, pack_contents


class Materials(object):
    """What a craft spent, measured either side of it. Whitelisted: a potion drunk is not a cost."""

    def __init__(self, stock, extra_graphics):
        self._stock = stock
        self._extra = extra_graphics
        # Learned while the stack is there: the one that paid for a craft is often gone by the diff
        self._names = {}

    def _counted(self, item):
        return self._stock.is_stock(item) or item.Graphic in self._extra

    def _name_of(self, item):
        kind = self._stock.kind_of(item)

        if kind is not None:
            name = self._stock.type_of(item)

            return kind if name is None else "%s %s" % (name, kind)

        return (getattr(item, "Name", "") or "").strip() or hex_of(item.Graphic)

    def snapshot(self):
        wanted = [item for item in pack_contents() if self._counted(item)]

        for item in wanted:
            key = (item.Graphic, hue_of(item))

            if key not in self._names:
                self._names[key] = self._name_of(item)

        return counts_by_graphic(wanted)

    # The failure line lands before the deduction and refund, so a pack that has not moved yet is
    # not settled: only one that moved and then held still for a poll is
    def settled_snapshot(self, timeout, poll):
        last = self.snapshot()
        waited = 0.0
        moved = False

        while waited < timeout:
            API.Pause(poll)
            waited += poll
            now = self.snapshot()

            if now != last:
                moved = True
                last = now
            elif moved:
                return now

        return last

    # The lost side only: the product lands in the same pack and is not a cost
    def spent(self, before, after):
        _gained, lost = diff_counts(before, after)
        rows = []

        for key in sorted(lost):
            graphic, hue = key
            rows.append((self._names.get(key) or hex_of(graphic), graphic, hue, lost[key]))

        return rows
