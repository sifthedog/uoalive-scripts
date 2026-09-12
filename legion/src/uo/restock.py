from uo.stock import total_of
from uo.journal import matched_bucket
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

    # One pool by default; a table of kind -> fill-to pulls each kind on its own, so a craft that
    # spends several things does not fill the pack with whichever pile the container lists first
    def _targets(self, targets):
        if targets is None:
            return [(None, self._config["batch"] - self._wood.in_pack())]

        held = self._wood.pack_stock()

        return [(kind, targets[kind] - held.get(kind, 0)) for kind in sorted(targets)]

    def _grew(self, before, after):
        return ", ".join(sorted(name for name in after if after[name] > before.get(name, 0)))

    def _pull(self, entry, kind, wanted):
        moved = 0
        stalled = 0
        cap = self._sources.cap(entry)

        if cap is not None:
            wanted = min(wanted, cap)

        while moved < wanted and stalled < self._config["max_empty_moves"]:
            if not self._sources.has_stock(entry, kind):
                break

            before = self._wood.in_pack()
            others = self._wood.pack_other()
            token = self._sources.take(entry, kind, wanted - moved)
            gained = self._wood.in_pack() - before

            # Every container answers the same, so the first refusal ends the whole pull
            if gained <= 0 and matched_bucket([("heavy", self._config["heavy_text"])]):
                self._heavy = True
                self._log("the shard will not load more %s - too heavy at %s"
                          % (self._wood.noun(), weight_reading()))
                break

            if gained <= 0:
                gave = self._grew(others, self._wood.pack_other())

                if gave:
                    self._sources.took_wrong(entry, token, gave)

                stalled += 1
            else:
                stalled = 0
                moved += gained

        return moved

    # Moves are asynchronous: the pack is re-counted after each rather than a return value read
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

            if self._sources.open(entry) is None:
                self._log("'%s' did not open" % self._sources.name_of(entry))
                continue

            if self._config["return_wrong_wood"]:
                self._sources.put_back(entry)

            for kind in sorted(wanted, key=lambda name: name or ""):
                if wanted[kind] <= 0 or self._heavy:
                    continue

                pulled = self._pull(entry, kind, wanted[kind])
                wanted[kind] -= pulled
                moved += pulled

        if moved > 0:
            self._log("pulled %d %s, %s in the pack, %d left in what you picked"
                      % (moved, self._wood.noun(), self._wood.pack_report(),
                         self._sources.stock_left()))

        return lifted + moved
