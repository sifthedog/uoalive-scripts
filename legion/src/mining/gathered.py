from uo.entity import hex_of
from uo.pack import amount_of, hue_of, pack_contents


class Gathered(object):
    """What a swing and a smelt each put in the pack, as attempt rows, while the skill can still gain."""

    def __init__(self, recorder, skill, ore, metals, capped, ore_graphics, log):
        self._recorder = recorder
        self._skill = skill
        self._ore = ore
        self._metals = metals
        self._capped = capped
        self._ore_graphics = ore_graphics
        self._log = log
        self._names = {}
        self._from = None

    def recording(self):
        return self._recorder.recording() and self._capped() is None

    def settle(self):
        value = self._skill.read()
        self._recorder.settle(value)

        return value

    def _ore_name(self, item):
        metal = self._metals.of(item)

        if metal is not None:
            return "%s ore" % metal

        return (getattr(item, "Name", "") or "").strip() or "ore"

    # By hue rather than by (graphic, hue): an ore stack's art changes with its size, so the merge
    # after a swing would read as one art lost and another gained
    def _ore_by_hue(self):
        counts = {}

        for item in pack_contents():
            if not self._ore.is_ore(item):
                continue

            hue = hue_of(item)
            counts[hue] = counts.get(hue, 0) + amount_of(item)

            # The tooltip's metal is kept once seen: the pile that names it is often merged away
            if hue not in self._names or self._metals.of(item) is not None:
                self._names[hue] = (self._ore_name(item), item.Graphic)

        return counts

    def before_swing(self):
        return self._ore_by_hue() if self.recording() else None

    def after_swing(self, skill_from, outcome, before):
        if before is None:
            return

        after = self._ore_by_hue()
        rows = []

        for hue in sorted(after):
            delta = after[hue] - before.get(hue, 0)

            if delta > 0:
                name, graphic = self._names[hue]
                rows.append((name, graphic, hue, delta))

        self._recorder.record(skill_from, outcome, "pickaxe", gained=rows)

    def before_smelt(self):
        self._from = self._skill.read() if self.recording() else None

    def _product_name(self, graphic, hue):
        for item in pack_contents():
            if item.Graphic == graphic and hue_of(item) == hue:
                name = (getattr(item, "Name", "") or "").strip()

                if name:
                    return name

        return hex_of(graphic)

    def after_smelt(self, gained, lost):
        if self._from is None:
            return

        skill_from = self._from
        self._from = None
        ore_lost = {}
        ore_art = {}
        products = []

        for (graphic, hue), quantity in sorted(lost.items()):
            if graphic in self._ore_graphics:
                ore_lost[hue] = ore_lost.get(hue, 0) + quantity
                ore_art[hue] = graphic

        # A failed smelt halves the stack, and the smaller stack can wear another art
        for (graphic, hue), quantity in sorted(gained.items()):
            if graphic in self._ore_graphics:
                ore_lost[hue] = ore_lost.get(hue, 0) - quantity
            else:
                products.append((self._product_name(graphic, hue), graphic, hue, quantity))

        consumed = []

        for hue in sorted(ore_lost):
            if ore_lost[hue] > 0:
                name = self._names.get(hue, ("ore", None))[0]
                consumed.append((name, ore_art[hue], hue, ore_lost[hue]))

        outcome = "smelted" if products else "failed"
        self._recorder.record(skill_from, outcome, "fire beetle", consumed, products)
