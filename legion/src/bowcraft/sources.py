import API

from bowcraft.wood import total_of
from uo.entity import chebyshev, hex_of, player
from uo.pack import amount_of


class Sources(object):
    """The containers and pack animals the wood is drawn from."""

    def __init__(self, wood, config, log):
        self._wood = wood
        self._config = config
        self._log = log
        self._picked = []

    def picked(self):
        return self._picked

    def name_of(self, entry):
        return entry["name"] or hex_of(entry["serial"])

    # The animal holds nothing itself - what is read and drawn from is the backpack it wears. Never
    # UseObject the animal to open that: on a rideable body a double-click mounts you, and nothing
    # in this script dismounts.
    def _animal_pack(self, serial):
        animal = API.FindMobile(serial)

        if animal is None:
            return None

        pack = getattr(animal, "Backpack", None)

        if pack is None:
            pack = API.FindLayer("backpack", serial)

        if pack is None:
            return None

        # A build that answers with the serial itself rather than the item is fine too
        return getattr(pack, "Serial", pack)

    def container_of(self, entry):
        if entry["kind"] == "mobile":
            return self._animal_pack(entry["serial"])

        return entry["serial"]

    def _entry_for(self, serial):
        item = API.FindItem(serial)

        if item is not None:
            return {"kind": "item", "serial": serial, "name": item.Name or "?",
                    "spot": (item.X, item.Y, item.Z)}

        animal = API.FindMobile(serial)

        if animal is None:
            return None

        return {"kind": "mobile", "serial": serial, "name": animal.Name or "?", "spot": None}

    # ItemsInContainer reads nothing out of a container the client has never seen inside, so a
    # source is opened before it is counted or drawn from
    def open(self, entry):
        container = self.container_of(entry)

        if container is None:
            return None

        API.UseObject(container)
        API.Pause(self._config["open_delay"])

        return container

    def pick(self):
        self._log("target every container or pack animal holding logs or boards, ESC when done")

        me = player()
        mine = me.Serial if me is not None else None

        for _pick in range(self._config["max_picks"]):
            if API.HasTarget():
                API.CancelTarget()

            serial = API.RequestTarget(self._config["pick_timeout"])

            # Falsy is ESC or a cursor that timed out, and either one ends the selection
            if not serial:
                break

            # Your own pack is where the wood is being counted from in the first place
            if serial == API.Backpack or (mine is not None and serial == mine):
                self._log("your own pack is always counted, no need to pick it")
                continue

            if serial in [entry["serial"] for entry in self._picked]:
                continue

            entry = self._entry_for(serial)

            # Not an ending: a misclick on the ground should cost the click and nothing more
            if entry is None:
                self._log("%s is neither a container nor a creature" % hex_of(serial))
                continue

            # Opened here, and the spot recorded now, because this is the one moment it is in reach
            if self.open(entry) is None:
                self._log("'%s' has no backpack to draw from" % self.name_of(entry))
                continue

            self._picked.append(entry)

            other = self._wood.other_report(self._wood.other_counts(self.all_wood(entry)))

            self._log("picked '%s' %s, %s in it%s"
                      % (self.name_of(entry), hex_of(serial),
                         self._wood.report(self.counts(entry)),
                         "" if not other else " (%s it will not use)" % other))

        if API.HasTarget():
            API.CancelTarget()

        return self._picked

    # Only the type the menu is set to: pulling a pile of oak into a pack a regular menu will not
    # spend it from is the whole of what went wrong before
    def container_wood(self, serial):
        items = API.ItemsInContainer(serial, True)
        piles = [item for item in (items or []) if self._wood.usable(item)]
        piles.sort(key=amount_of, reverse=True)

        return piles

    def wood(self, entry):
        container = self.container_of(entry)

        return [] if container is None else self.container_wood(container)

    # Every wood in there, wrong type included, for the lines that report what a source is holding
    def all_wood(self, entry):
        container = self.container_of(entry)
        items = API.ItemsInContainer(container, True) if container else None

        return [item for item in items if self._wood.is_wood(item)] if items else []

    def counts(self, entry):
        return self._wood.counts(self.wood(entry))

    def total(self, entry):
        return total_of(self.counts(entry))

    def stock_left(self):
        return sum(self.total(entry) for entry in self._picked)

    def stock_line(self):
        if len(self._picked) == 0:
            return "nothing picked to restock from"

        return "%d in the %d you picked" % (self.stock_left(), len(self._picked))

    # Re-resolved rather than the picked entry trusted: a pathfind that ends early leaves you short
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

        # A container picked inside the pack has no world position worth walking to
        if spot is None or (spot[0] == 0 and spot[1] == 0):
            return True

        if chebyshev(spot[0], spot[1], within + 1) <= within:
            return True

        API.Pathfind(spot[0], spot[1], spot[2], within, True, self._config["pathfind_timeout"])

        return chebyshev(spot[0], spot[1], within + 1) <= within
