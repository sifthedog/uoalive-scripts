import API

from uo.box import StorageBox
from uo.stock import total_of
from uo.entity import chebyshev, hex_of, player
from uo.pack import amount_of
from uo.retry import settled
from uo.text import any_in


KIND_NOUNS = {"item": "container", "mobile": "pack animal", "box": "storage box"}


class Sources(object):
    """The containers, storage boxes and pack animals the wood is drawn from."""

    def __init__(self, wood, config, log):
        self._wood = wood
        self._config = config
        self._log = log
        self._picked = []
        self._box = StorageBox(config["box"], config, log) if config["box"] else None

    def picked(self):
        return self._picked

    def name_of(self, entry):
        return entry["name"] or hex_of(entry["serial"])

    # Never UseObject the animal itself: on a rideable body that mounts you
    def _animal_pack(self, serial):
        animal = API.FindMobile(serial)

        if animal is None:
            return None

        pack = getattr(animal, "Backpack", None)

        if pack is None:
            pack = API.FindLayer("backpack", serial)

        if pack is None:
            return None

        return getattr(pack, "Serial", pack)

    def container_of(self, entry):
        if entry["kind"] == "box":
            return None

        if entry["kind"] == "mobile":
            return self._animal_pack(entry["serial"])

        return entry["serial"]

    def _is_box(self, item):
        if self._box is None:
            return False

        table = self._config["box"]

        return item.Graphic in table["graphics"] or any_in(item.Name, table["names"])

    def entry_for(self, serial):
        item = API.FindItem(serial)

        if item is not None:
            return {"kind": "box" if self._is_box(item) else "item", "serial": serial,
                    "name": item.Name or "?", "spot": (item.X, item.Y, item.Z)}

        animal = API.FindMobile(serial)

        if animal is None:
            return None

        return {"kind": "mobile", "serial": serial, "name": animal.Name or "?", "spot": None}

    # ItemsInContainer reads nothing out of a container the client has never seen inside
    def open(self, entry):
        if entry["kind"] == "box":
            return self._box.open(entry["serial"]) or None

        container = self.container_of(entry)

        if container is None:
            return None

        API.UseObject(container)
        API.Pause(self._config["open_delay"])

        return container

    def _noun_of(self, allowed):
        if allowed is None:
            return ("container, storage box or pack animal" if self._box is not None
                    else "container or pack animal")

        return " or ".join(KIND_NOUNS[kind] for kind in allowed if kind in KIND_NOUNS)

    def clear(self):
        del self._picked[:]

    def line_for(self, entry):
        other = self._wood.other_report(self.other_counts(entry))

        return "'%s' %s, %s in it%s" % (self.name_of(entry), hex_of(entry["serial"]),
                                        self._wood.report(self.counts(entry)),
                                        "" if not other else " (%s it will not use)" % other)

    def _refusal(self, serial, allowed):
        me = player()

        if serial == API.Backpack or (me is not None and serial == me.Serial):
            return "your own pack is always counted, no need to pick it"

        if serial in [entry["serial"] for entry in self._picked]:
            return "%s is already picked" % hex_of(serial)

        entry = self.entry_for(serial)

        if entry is None:
            return "%s is neither a container nor a creature" % hex_of(serial)

        if allowed is not None and entry["kind"] not in allowed:
            return ("'%s' is a %s - the gump chose the %s"
                    % (self.name_of(entry), KIND_NOUNS[entry["kind"]], self._noun_of(allowed)))

        # One storage box holds everything, and its gump is read one box at a time
        if entry["kind"] == "box" and any(held["kind"] == "box" for held in self._picked):
            return "'%s' is a second storage box - one holds everything" % self.name_of(entry)

        return None

    # One cursor, one answer: (the picked entry's line, None), (None, why it was refused), or
    # (None, None) for ESC
    def pick_one(self, allowed=None):
        if API.HasTarget():
            API.CancelTarget()

        serial = API.RequestTarget(self._config["pick_timeout"])

        if API.HasTarget():
            API.CancelTarget()

        if not serial:
            return None, None

        refusal = self._refusal(serial, allowed)

        if refusal is not None:
            self._log(refusal)

            return None, refusal

        entry = self.entry_for(serial)

        # Opened now, while it is in reach
        if self.open(entry) is None:
            refusal = "'%s' did not open" % self.name_of(entry)
            self._log(refusal)

            return None, refusal

        self._picked.append(entry)
        line = self.line_for(entry)
        self._log("picked %s" % line)

        return line, None

    # Every kind by default; a list of kinds, as the gump at the start chose, refuses the others
    def pick(self, allowed=None):
        single = allowed == ["box"]

        if single:
            self._log("target the storage box holding %s" % self._wood.noun())
        else:
            self._log("target every %s holding %s, ESC when done"
                      % (self._noun_of(allowed), self._wood.noun()))

        for _pick in range(self._config["max_picks"]):
            line, refusal = self.pick_one(allowed)

            # ESC or a timed-out cursor, either ends the selection
            if line is None and refusal is None:
                break

            if line is not None and single:
                break

        if API.HasTarget():
            API.CancelTarget()

        return self._picked

    # Only the type the menu is set to, and only one kind of it when a kind is named
    def container_wood(self, serial, kind=None):
        items = API.ItemsInContainer(serial, True)
        piles = [item for item in (items or [])
                 if (self._wood.usable(item) if kind is None
                     else self._wood.usable_kind(item, kind))]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def wood(self, entry):
        container = self.container_of(entry)

        return [] if container is None else self.container_wood(container)

    # Wrong type included, for the report lines
    def all_wood(self, entry):
        container = self.container_of(entry)
        items = API.ItemsInContainer(container, True) if container else None

        return [item for item in items if self._wood.is_stock(item)] if items else []

    def counts(self, entry):
        if entry["kind"] == "box":
            return self._box.counts(entry["serial"], self._wood.wanted())

        return self._wood.counts(self.wood(entry))

    def other_counts(self, entry):
        if entry["kind"] == "box":
            return self._box.other_counts(entry["serial"], self._wood.wanted())

        return self._wood.other_counts(self.all_wood(entry))

    def total(self, entry):
        return total_of(self.counts(entry))

    def stock_left(self):
        return sum(self.total(entry) for entry in self._picked)

    def stock_line(self):
        if len(self._picked) == 0:
            return "nothing picked to restock from"

        return "%d in the %d you picked" % (self.stock_left(), len(self._picked))

    def has_stock(self, entry, kind):
        if entry["kind"] == "box":
            return self._box.has_stock(entry["serial"], kind, self._wood.wanted())

        container = self.container_of(entry)

        return container is not None and len(self.container_wood(container, kind)) > 0

    # The most one restock draws from a source; None is as much as it asks for
    def cap(self, entry):
        return self._config["box_take"] if entry["kind"] == "box" else None

    # Moves are asynchronous: the caller re-counts the pack rather than reading a return value
    def take(self, entry, kind, amount):
        if entry["kind"] == "box":
            before = self._wood.in_pack()
            label = self._box.take(entry["serial"], kind, self._wood.wanted())

            # A press counted before its boards land is pressed again, and lands twice
            if label is not None:
                settled(self._config["press_timeout"], self._config["press_poll"],
                        lambda: self._wood.in_pack() != before)

            return label

        container = self.container_of(entry)
        piles = self.container_wood(container, kind) if container is not None else []

        if len(piles) == 0:
            return None

        API.MoveItem(piles[0].Serial, API.Backpack, min(amount, amount_of(piles[0])))
        API.Pause(self._config["move_delay"])

        return None

    def took_wrong(self, entry, token, gave):
        if entry["kind"] == "box" and token is not None:
            self._box.wrong_row(token, gave)

    # Wrong wood goes back while its container is open and in reach, the one moment it costs nothing
    def put_back(self, entry):
        container = self.container_of(entry)

        if container is None:
            return 0

        before = total_of(self._wood.pack_other())

        if before == 0:
            return 0

        for pile in self._wood.wrong_piles():
            API.MoveItem(pile.Serial, container, amount_of(pile))
            API.Pause(self._config["move_delay"])

        moved = before - total_of(self._wood.pack_other())

        if moved > 0:
            self._log("put %d wood the menu will not spend back" % moved)

        return moved

    # Re-resolved after the walk: a pathfind that ends early leaves you short
    def reach(self, entry):
        within = self._config["container_range"]

        if entry["kind"] == "mobile":
            animal = API.FindMobile(entry["serial"])

            if animal is None:
                return False

            if animal.Distance <= within:
                return True

            API.PathfindEntity(entry["serial"], within, True, self._config["pathfind_timeout"])
            API.CancelPathfinding()

            animal = API.FindMobile(entry["serial"])

            return animal is not None and animal.Distance <= within

        spot = entry["spot"]

        # A container inside the pack has no world position
        if spot is None or (spot[0] == 0 and spot[1] == 0):
            return True

        if chebyshev(spot[0], spot[1], within + 1) <= within:
            return True

        API.Pathfind(spot[0], spot[1], spot[2], within, True, self._config["pathfind_timeout"])

        return chebyshev(spot[0], spot[1], within + 1) <= within
