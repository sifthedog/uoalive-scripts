import API

from uo.stock import total_of
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

    # One pool by default; a table of kind -> fill-to pulls each kind on its own, so a craft that
    # spends several things does not fill the pack with whichever pile the container lists first
    def _targets(self, targets):
        if targets is None:
            return [(None, self._config["batch"] - self._wood.in_pack())]

        held = self._wood.pack_stock()

        return [(kind, targets[kind] - held.get(kind, 0)) for kind in sorted(targets)]

    def _pull(self, container, kind, wanted):
        moved = 0
        stalled = 0

        while moved < wanted and stalled < self._config["max_empty_moves"]:
            piles = self._sources.container_wood(container, kind)

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
                self._log("the shard will not load more %s - too heavy at %s"
                          % (self._wood.noun(), weight_reading()))
                break

            if gained <= 0:
                stalled += 1
            else:
                stalled = 0
                moved += gained

        return moved

    # Moves are asynchronous: the pack is re-counted after each rather than MoveItem's return read
    def run(self, targets=None):
        self._heavy = False
        lifted = self._wood.lift_from_bags()

        # After the lift: in_pack reads bags too, and counting the lift twice left it short
        wanted = dict(self._targets(targets))
        moved = 0

        for entry in self._sources.picked():
            if max(wanted.values()) <= 0 or self._heavy:
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

            for kind in sorted(wanted, key=lambda name: name or ""):
                if wanted[kind] <= 0 or self._heavy:
                    continue

                pulled = self._pull(container, kind, wanted[kind])
                wanted[kind] -= pulled
                moved += pulled

        if moved > 0:
            self._log("pulled %d %s, %s in the pack, %d left in what you picked"
                      % (moved, self._wood.noun(), self._wood.pack_report(),
                         self._sources.stock_left()))

        return lifted + moved
