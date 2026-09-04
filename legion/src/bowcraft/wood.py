import API

from uo.entity import hex_of
from uo.pack import amount_of, hue_of, pack_contents, pack_top_level
from uo.text import word_in


class WoodBook(object):
    """What in the pack is wood, which wood it is, and how much of it the menu will actually spend."""

    def __init__(self, config, log):
        self._kinds = config["kinds"]
        self._types = config["types"]
        self._hues = config["hues"]
        self._wanted = config["wanted"]
        self._move_delay = config["move_delay"]
        self._log = log

    # Graphic first across every kind, name second: names are empty until the client has tooltip
    # data, and an art learned by name joins its kind's set, so it costs one name read and no more.
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

    def is_wood(self, item):
        return self.kind_of(item) is not None

    # The name first, because that is where the shard writes it. A name that has not arrived leaves
    # the hue: plain is regular, coloured is a wood this table has no word for, neither is guessed.
    def type_of(self, item):
        for wood in self._types:
            if word_in(item.Name, [wood]):
                return wood

        return self._hues.get(hue_of(item))

    def usable(self, item):
        return self.is_wood(item) and self.type_of(item) == self._wanted

    def wrong(self, item):
        return self.is_wood(item) and self.type_of(item) != self._wanted

    # Only what the menu will spend. Wood of another type is not stock, however much of it there is
    # - counting it is what let a run sit on 300 oak boards reporting a full pack and crafting none.
    def counts(self, items):
        counts = {}

        for item in items:
            if not self.usable(item):
                continue

            kind = self.kind_of(item)
            counts[kind] = counts.get(kind, 0) + amount_of(item)

        return counts

    # The rest of the wood, by the name the shard gives it, so a pack that reads as empty says why
    def other_counts(self, items):
        counts = {}

        for item in items:
            if not self.wrong(item):
                continue

            wood = self.type_of(item) or "unknown"
            counts[wood] = counts.get(wood, 0) + amount_of(item)

        return counts

    def other_report(self, counts):
        parts = ["%d %s" % (counts[wood], wood)
                 for wood in sorted(counts, key=lambda name: -counts[name])]

        return ", ".join(parts)

    # In kind order, so two runs of the same pack read the same
    def report(self, counts):
        parts = []

        for kind, _graphics, _words in self._kinds:
            if counts.get(kind, 0) > 0:
                parts.append("%d %s" % (counts[kind], kind))

        return ", ".join(parts) if parts else "no wood"

    def pack_wood(self):
        return self.counts(pack_contents())

    def pack_other(self):
        return self.other_counts(pack_contents())

    def in_pack(self):
        return total_of(self.pack_wood())

    # What the pack holds, in one phrase: what the menu will spend, and what it will not
    def pack_report(self):
        text = self.report(self.pack_wood())
        other = self.other_report(self.pack_other())

        return text if not other else "%s (%s set aside)" % (text, other)

    # Hue is what tells one wood from another - oak, ash, yew and heartwood are all 'boards' by name
    # and graphic, and the menu spends only the one it is set to
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

        return ", ".join(parts) if parts else "no wood"

    def wrong_piles(self):
        return [item for item in pack_contents() if self.wrong(item)]

    # Wood in a bag inside the pack is wood the craft may not reach, and it is nearer than a source
    def _nested(self):
        top = set(item.Serial for item in pack_top_level())
        piles = [item for item in pack_contents()
                 if item.Serial not in top and self.usable(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    # Moves inside the pack cost no weight, so this is free and always worth doing first
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
            self._log("brought %d wood up out of the bags in your pack" % moved)

        return moved


def total_of(counts):
    return sum(counts[kind] for kind in counts)
