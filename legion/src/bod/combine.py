import API

from uo.entity import hex_of
from uo.gump import await_any, gump_says
from uo.journal import journal_tail, matched_bucket
from uo.text import clipped


class DeedCombiner(object):
    """One item into the deed, through the deed's own gump and the cursor it raises."""

    def __init__(self, deed, items, buckets, config, log):
        self._deed = deed
        self._items = items
        self._buckets = buckets
        self._config = config
        self._log = log
        self._said_gump_text = False
        self._reported = 0

    def _lines(self, gump):
        text = API.GetGumpContents(gump)

        return [line.strip() for line in (text or "").split("\n") if line.strip()]

    # Whatever is up - the craft menu, the last deed gump - would answer the wait below
    def _open(self):
        up = API.HasGump()

        if up:
            API.CloseGump(up)
            API.Pause(self._config["gump_poll"])

        API.UseObject(self._deed.serial)

        found = await_any(self._config["gump_timeout"], self._config["gump_poll"])

        if found and not self._said_gump_text and not gump_says(found, self._config["gump_text"]):
            self._said_gump_text = True
            lines = self._lines(found)
            self._log("the deed opened a gump that does not say bulk order - it starts '%s'"
                      % (lines[0] if lines else "(no text)"))

        return found

    def _report(self, why, gump):
        if self._reported >= self._config["max_reports"]:
            return

        self._reported += 1
        text = clipped(" ".join(self._lines(gump)), self._config["text_limit"]) if gump else ""
        lines = journal_tail(self._config["tail_seconds"], self._config["tail_lines"])

        self._log("%s - the gump says '%s'" % (why, text or "(nothing)"))
        self._log("the journal says '%s'" % (" | ".join(lines) or "(nothing)"))

    # The item leaving the pack is the proof no wording can argue with
    def _read_outcome(self, serial):
        waited = 0.0

        while not API.StopRequested:
            hit = matched_bucket(self._buckets)

            if hit is not None:
                return hit

            if serial not in self._items.serials():
                return "combined"

            if waited >= self._config["combine_timeout"]:
                return None

            API.Pause(self._config["combine_poll"])
            waited += self._config["combine_poll"]

    # The shard re-sends the deed gump before it raises the cursor, so one is left up either way
    def _close(self):
        if API.HasTarget():
            API.CancelTarget()

        up = API.HasGump()

        if up:
            API.CloseGump(up)

    def combine(self, serial):
        gump = self._open()

        if not gump:
            return "noGump"

        API.ClearJournal()

        if not API.ReplyGump(self._config["combine_button"], gump):
            return "noGump"

        if not API.WaitForTarget("any", self._config["target_timeout"]):
            self._report("no cursor came up for the combine", gump)
            self._close()

            return "noCursor"

        API.Target(serial)

        outcome = self._read_outcome(serial)

        if outcome is None:
            self._report("nothing readable came back for %s" % hex_of(serial), gump)

        self._close()

        return outcome
