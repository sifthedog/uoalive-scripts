import API

from bowcraft.wood import total_of
from uo.entity import player
from uo.pack import amount_of
from uo.vitals import weight_reading
from uo.weight import over_buffer


class Restock(object):
    def __init__(self, wood, sources, config, log):
        self._wood = wood
        self._sources = sources
        self._config = config
        self._log = log
        self._each = config["wood_weight"]

    def _carried(self):
        me = player()

        return None if me is None else me.Weight

    # None when the client has not said, which reads as no limit - the same call over_buffer makes
    def _room_for_wood(self):
        me = player()

        if me is None or me.WeightMax <= 0:
            return None

        return int((me.WeightMax - self._config["buffer"] - me.Weight) / max(self._each, 0.1))

    def _learn_weight(self, each):
        # Sanity: a move the client mis-timed can read as any weight at all
        if each < 0.1 or each > 50 or abs(each - self._each) < 0.05:
            return

        self._each = each
        self._log("one wood weighs %.1f here, pulling to fit" % each)

    # Wood of another type is weight and nothing else, and the container it came out of is open and
    # in reach at exactly this moment - which is the only moment putting it back costs nothing
    def _put_back(self, container):
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

    # Moves are asynchronous, so the pack is re-counted between them rather than MoveItem's return
    # value being trusted. A move that gains nothing enough times running is a container that is done.
    def run(self):
        # The pack is read before anything is fetched: what is already here, bags included, counts
        moved = self._wood.lift_from_bags()

        wanted = self._config["batch"] - self._wood.in_pack()

        if wanted <= 0:
            return moved

        buffer = self._config["buffer"]

        for entry in self._sources.picked():
            if moved >= wanted or over_buffer(buffer):
                break

            if not self._sources.reach(entry):
                self._log("cannot reach '%s', trying the next" % self._sources.name_of(entry))
                continue

            container = self._sources.open(entry)

            if container is None:
                self._log("'%s' has no backpack to draw from" % self._sources.name_of(entry))
                continue

            if self._config["return_wrong_wood"]:
                self._put_back(container)

            stalled = 0

            while (moved < wanted and stalled < self._config["max_empty_moves"]
                   and not over_buffer(buffer)):
                piles = self._sources.container_wood(container)

                if len(piles) == 0:
                    break

                room = self._room_for_wood()
                take = min(wanted - moved, amount_of(piles[0]))

                if room is not None:
                    take = min(take, room)

                # Not a stall: there is wood there and no room for it, which the caller reports
                if take <= 0:
                    break

                before = self._wood.in_pack()
                heavy = self._carried()

                API.MoveItem(piles[0].Serial, API.Backpack, take)
                API.Pause(self._config["move_delay"])

                gained = self._wood.in_pack() - before

                if gained <= 0:
                    stalled += 1
                else:
                    stalled = 0
                    moved += gained

                    now = self._carried()

                    if heavy is not None and now is not None and now > heavy:
                        self._learn_weight((now - heavy) / float(gained))

        if moved > 0:
            self._log("pulled %d wood, %s in the pack, %d left in what you picked"
                      % (moved, self._wood.pack_report(), self._sources.stock_left()))

        if over_buffer(buffer) and moved < wanted:
            self._log("stopped short of the batch at %s" % weight_reading())

        return moved
