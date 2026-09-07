import API

from bowcraft.wood import total_of
from uo.journal import matched_bucket
from uo.pack import amount_of
from uo.vitals import weight_reading


class Restock(object):
    def __init__(self, wood, sources, config, log):
        self._wood = wood
        self._sources = sources
        self._config = config
        self._log = log
        self._heavy = False

    def refused_for_weight(self):
        return self._heavy

    # Wrong wood goes back while its container is open and in reach, the one moment it costs nothing
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

    # Moves are asynchronous: the pack is re-counted after each rather than MoveItem's return read
    def run(self):
        self._heavy = False
        lifted = self._wood.lift_from_bags()

        # After the lift: in_pack reads bags too, and counting the lift twice left it short
        wanted = self._config["batch"] - self._wood.in_pack()
        moved = 0

        for entry in self._sources.picked():
            if moved >= wanted or self._heavy:
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

            while moved < wanted and stalled < self._config["max_empty_moves"]:
                piles = self._sources.container_wood(container)

                if len(piles) == 0:
                    break

                before = self._wood.in_pack()

                API.MoveItem(piles[0].Serial, API.Backpack,
                             min(wanted - moved, amount_of(piles[0])))
                API.Pause(self._config["move_delay"])

                gained = self._wood.in_pack() - before

                # Every container answers the same, so the first refusal ends the whole pull
                if gained <= 0 and matched_bucket([("heavy", self._config["heavy_text"])]):
                    self._heavy = True
                    self._log("the shard will not load more wood - too heavy at %s"
                              % weight_reading())
                    break

                if gained <= 0:
                    stalled += 1
                else:
                    stalled = 0
                    moved += gained

        if moved > 0:
            self._log("pulled %d wood, %s in the pack, %d left in what you picked"
                      % (moved, self._wood.pack_report(), self._sources.stock_left()))

        return lifted + moved
