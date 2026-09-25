import API

from uo.journal import forget, forget_outcomes, journal_tail, said
from uo.text import any_in


def caught_name(lines, fragments):
    for line in reversed(lines):
        if any_in(line, fragments):
            return line.partition(":")[2].strip()

    return None


class Angler(object):
    """One cast: the pole, the cursor, the water tile, the shard's answer."""

    def __init__(self, buckets, config, log, stamp=None):
        self._buckets = buckets
        self._config = config
        self._log = log
        self._stamp = stamp
        self._caught_fragments = [phrase.lower() for phrase in config["caught_text"]]

    # HasTarget alone was not enough on the web client: the prompt was in the journal well before
    # the cursor flag rose
    def _cursor_opened(self):
        waited = 0.0

        while waited < self._config["cursor_timeout"]:
            if API.HasTarget() or said(self._config["prompt_text"]):
                return True

            API.Pause(self._config["cursor_poll"])
            waited += self._config["cursor_poll"]

        return False

    # Read off the tail rather than through InJournalAny: that clears the line, and the name is on it
    def _caught(self):
        return caught_name(journal_tail(self._config["tail_seconds"], self._config["tail_lines"],
                                         self._stamp),
                           self._caught_fragments)

    # In declaration order, the way read_outcome does, with the catch bucket answered by the tail
    def _matched(self):
        for name, phrases in self._buckets:
            if name == "caught":
                caught = self._caught()

                if caught is not None:
                    return name, caught
            elif API.InJournalAny(phrases, True):
                return name, ""

        return None, ""

    def _read(self, budget, poll):
        waited = 0.0

        while not API.StopRequested:
            name, caught = self._matched()

            if name is not None:
                return name, caught

            if waited >= budget:
                return None, ""

            API.Pause(poll)
            waited += poll

        return None, ""

    # No cursor is not the same as nothing having happened: a shard that refused the cast says so
    def _refused_outcome(self):
        name, caught = self._read(self._config["no_cursor_read"], self._config["cursor_poll"])

        if name is not None:
            return name, caught

        self._log("no target cursor - the shard never asked where to fish")

        return "noCursor", ""

    def cast_once(self, serial, tile):
        # Cancelled only when there is one to cancel: an unconditional cancel a few hundred
        # milliseconds before the use left the next cursor unusable in the run this was copied from
        if API.HasTarget():
            API.CancelTarget()

        forget(self._config["prompt_text"])
        forget_outcomes(self._buckets)

        API.UseObject(serial)

        if not self._cursor_opened():
            return self._refused_outcome()

        # Art names a static; a land tile named by its own art makes the shard look for a static
        # that is not there and answer nothing. Open ocean, all a boat deck casts over, is land.
        if tile.get("source") == "static":
            API.Target(tile["x"], tile["y"], tile["z"], tile["graphic"])
        else:
            API.Target(tile["x"], tile["y"], tile["z"])

        name, caught = self._read(self._config["cast_timeout"], self._config["cast_poll"])

        return (name, caught) if name is not None else ("unknown", "")
