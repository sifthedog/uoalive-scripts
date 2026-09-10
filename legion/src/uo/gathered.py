from uo.entity import hex_of
from uo.pack import amount_of, hue_of, pack_contents


class Gathered(object):
    """What a swing and a conversion each put in the pack, as attempt rows, while the skill can still gain."""

    def __init__(self, recorder, skill, capped, config, log):
        self._recorder = recorder
        self._skill = skill
        self._capped = capped
        self._config = config
        self._log = log
        self._names = {}
        self._from = None

    def recording(self):
        return self._recorder.recording() and self._capped() is None

    def settle(self):
        value = self._skill.read()
        self._recorder.settle(value)

        return value

    def _resource_name(self, item):
        name = self._config["name_of"](item)

        if name is not None:
            return name

        return (getattr(item, "Name", "") or "").strip() or self._config["noun"]

    # By hue rather than by (graphic, hue): a stack's art changes with its size, so the merge after a
    # swing would read as one art lost and another gained
    def _resource_by_hue(self):
        counts = {}

        for item in pack_contents():
            if not self._config["is_resource"](item):
                continue

            hue = hue_of(item)
            counts[hue] = counts.get(hue, 0) + amount_of(item)

            # A name the caller vouches for is kept once seen: the pile carrying it is often merged away
            if hue not in self._names or self._config["name_of"](item) is not None:
                self._names[hue] = (self._resource_name(item), item.Graphic)

        return counts

    def before_swing(self):
        return self._resource_by_hue() if self.recording() else None

    def after_swing(self, skill_from, outcome, before):
        if before is None:
            return

        after = self._resource_by_hue()
        rows = []

        for hue in sorted(after):
            delta = after[hue] - before.get(hue, 0)

            if delta > 0:
                name, graphic = self._names[hue]
                rows.append((name, graphic, hue, delta))

        self._recorder.record(skill_from, outcome, self._config["tool"], gained=rows)

    def before_convert(self):
        self._from = self._skill.read() if self.recording() else None

    def _product_name(self, graphic, hue):
        for item in pack_contents():
            if item.Graphic == graphic and hue_of(item) == hue:
                name = (getattr(item, "Name", "") or "").strip()

                if name:
                    return name

        return hex_of(graphic)

    def after_convert(self, gained, lost):
        if self._from is None:
            return

        skill_from = self._from
        self._from = None
        graphics = self._config["resource_graphics"]
        spent = {}
        art = {}
        products = []

        for (graphic, hue), quantity in sorted(lost.items()):
            if graphic in graphics:
                spent[hue] = spent.get(hue, 0) + quantity
                art[hue] = graphic

        # A failed smelt halves the stack, and the smaller stack can wear another art
        for (graphic, hue), quantity in sorted(gained.items()):
            if graphic in graphics:
                spent[hue] = spent.get(hue, 0) - quantity
            else:
                products.append((self._product_name(graphic, hue), graphic, hue, quantity))

        consumed = []

        for hue in sorted(spent):
            if spent[hue] > 0:
                name = self._names.get(hue, (self._config["noun"], None))[0]
                consumed.append((name, art[hue], hue, spent[hue]))

        outcome = self._config["made"] if products else "failed"
        self._recorder.record(skill_from, outcome, self._config["converter_tool"], consumed, products)
