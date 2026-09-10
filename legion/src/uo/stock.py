import API

from uo.entity import hex_of
from uo.pack import amount_of, hue_of, pack_contents, pack_top_level
from uo.text import word_in, words_of


class StockBook(object):
    """What in the pack is the craft's material, which type it is, and how much the menu will spend."""

    def __init__(self, config, log):
        self._noun = config["noun"]
        self._kinds = config["kinds"]
        # Longest first: 'copper' would otherwise take 'dull copper'
        self._types = sorted(config["types"], key=lambda name: -len(words_of(name)))
        self._hues = config["hues"]
        self._wanted = config["wanted"]
        self._move_delay = config["move_delay"]
        self._log = log

    def noun(self):
        return self._noun

    # For a snapshot key, which has no item left to read a name off
    def is_stock_graphic(self, graphic):
        for _kind, graphics, _words in self._kinds:
            if graphic in graphics:
                return True

        return False

    # Names are empty until the tooltip arrives, so the graphic is tried first across every kind
    def kind_of(self, item):
        if item is None:
            return None

        for kind, graphics, _words in self._kinds:
            if item.Graphic in graphics:
                return kind

        for kind, graphics, words in self._kinds:
            if word_in(item.Name, words):
                graphics.add(item.Graphic)
                self._log("%s '%s' counts as %s, remembering the art"
                          % (hex_of(item.Graphic), item.Name, kind))

                return kind

        return None

    def is_stock(self, item):
        return self.kind_of(item) is not None

    # The name is where the shard writes it; a hue in neither table is not guessed at
    def type_of(self, item):
        words = words_of(item.Name)

        for name in self._types:
            wanted = words_of(name)

            for start in range(len(words) - len(wanted) + 1):
                if words[start:start + len(wanted)] == wanted:
                    return name

        return self._hues.get(hue_of(item))

    def usable(self, item):
        return self.is_stock(item) and self.type_of(item) == self._wanted

    def wrong(self, item):
        return self.is_stock(item) and self.type_of(item) != self._wanted

    def usable_kind(self, item, kind):
        return self.usable(item) and self.kind_of(item) == kind

    # Only what the menu will spend: counting oak let a run sit on a full pack and craft none
    def counts(self, items):
        counts = {}

        for item in items:
            if not self.usable(item):
                continue

            kind = self.kind_of(item)
            counts[kind] = counts.get(kind, 0) + amount_of(item)

        return counts

    # The rest, by type, so a pack that reads as empty says why
    def other_counts(self, items):
        counts = {}

        for item in items:
            if not self.wrong(item):
                continue

            name = self.type_of(item) or "unknown"
            counts[name] = counts.get(name, 0) + amount_of(item)

        return counts

    def other_report(self, counts):
        parts = ["%d %s" % (counts[name], name)
                 for name in sorted(counts, key=lambda name: -counts[name])]

        return ", ".join(parts)

    # In kind order, so it reads the same each time
    def report(self, counts):
        parts = []

        for kind, _graphics, _words in self._kinds:
            if counts.get(kind, 0) > 0:
                parts.append("%d %s" % (counts[kind], kind))

        return ", ".join(parts) if parts else "no %s" % self._noun

    def pack_stock(self):
        return self.counts(pack_contents())

    def pack_other(self):
        return self.other_counts(pack_contents())

    def in_pack(self):
        return total_of(self.pack_stock())

    def pack_report(self):
        text = self.report(self.pack_stock())
        other = self.other_report(self.pack_other())

        return text if not other else "%s (%s set aside)" % (text, other)

    # By hue: oak, ash and yew are all 'boards' by graphic. Missing hue rows come from here.
    def hue_report(self):
        counts = {}

        for item in pack_contents():
            kind = self.kind_of(item)

            if kind is None:
                continue

            key = (kind, hue_of(item), self.type_of(item) or "unknown")
            counts[key] = counts.get(key, 0) + amount_of(item)

        parts = ["%d %s %s hue %s" % (counts[key], key[2], key[0], hex_of(key[1]))
                 for key in sorted(counts, key=lambda pair: -counts[pair])]

        return ", ".join(parts) if parts else "no %s" % self._noun

    def wrong_piles(self):
        return [item for item in pack_contents() if self.wrong(item)]

    # The craft may not reach into a bag inside the pack
    def _nested(self):
        top = set(item.Serial for item in pack_top_level())
        piles = [item for item in pack_contents()
                 if item.Serial not in top and self.usable(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def lift_from_bags(self):
        moved = 0

        for pile in self._nested():
            before = total_of(self.counts(pack_top_level()))

            API.MoveItem(pile.Serial, API.Backpack, amount_of(pile))
            API.Pause(self._move_delay)

            gained = total_of(self.counts(pack_top_level())) - before

            if gained > 0:
                moved += gained

        if moved > 0:
            self._log("brought %d %s up out of the bags in your pack" % (moved, self._noun))

        return moved


def total_of(counts):
    return sum(counts[kind] for kind in counts)
