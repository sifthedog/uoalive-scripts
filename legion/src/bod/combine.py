import API

from uo.gump import await_recognised, button_ids, gump_says, open_ids
from uo.journal import journal_tail, matched_bucket
from uo.pack import pack_contents
from uo.text import clipped


class DeedCombiner(object):
    """The deed's 'combine with contained items', aimed at the bag the pieces are in."""

    def __init__(self, deed, items, buckets, config, log):
        self._deed = deed
        self._items = items
        self._buckets = buckets
        self._config = config
        self._log = log
        self._said_gump_text = False
        self._reported = 0
        self._gump = 0

    def _lines(self, gump):
        text = API.GetGumpContents(gump)

        return [line.strip() for line in (text or "").split("\n") if line.strip()]

    def _is_deed_gump(self, ident):
        return gump_says(ident, self._config["gump_text"])

    def _open(self):
        before = open_ids()

        API.UseObject(self._deed.serial)

        found, recognised = await_recognised(self._is_deed_gump, before,
                                             self._config["gump_timeout"],
                                             self._config["gump_poll"])

        if found and not recognised and not self._said_gump_text:
            self._said_gump_text = True
            lines = self._lines(found)
            self._log("the deed opened a gump that does not say bulk order - it starts '%s'"
                      % (lines[0] if lines else "(no text)"))

        self._gump = found

        return found

    def _report(self, why, gump):
        if self._reported >= self._config["max_reports"]:
            return

        self._reported += 1
        text = clipped(" ".join(self._lines(gump)), self._config["text_limit"]) if gump else ""
        lines = journal_tail(self._config["tail_seconds"], self._config["tail_lines"])

        self._log("%s - the gump says '%s'" % (why, text or "(nothing)"))
        self._log("the journal says '%s'" % (" | ".join(lines) or "(nothing)"))

    # Without a book the pack itself is read, which is what the large flow watches
    def _serials(self):
        if self._items is not None:
            return self._items.serials()

        return set(item.Serial for item in pack_contents())

    def _gone(self, offered):
        here = self._serials()

        return [serial for serial in offered if serial not in here]

    # The pieces leaving the bag are the proof; the wording is read only when none did, because a
    # bag holding both kinds gets a refusal per piece alongside the successes
    def _read_outcome(self, offered):
        waited = 0.0

        while not API.StopRequested:
            gone = self._gone(offered)

            if len(gone) > 0:
                API.Pause(self._config["combine_poll"])

                return "combined", self._gone(offered)

            hit = matched_bucket(self._buckets)

            if hit is not None and hit != "combined":
                return hit, []

            if waited >= self._config["combine_timeout"]:
                return None, []

            API.Pause(self._config["combine_poll"])
            waited += self._config["combine_poll"]

    # The shard re-sends the deed gump before it raises the cursor, so one is left up either way
    def _close(self):
        if API.HasTarget():
            API.CancelTarget()

        if self._gump:
            API.CloseGump(self._gump)

    def combine(self, container, offered):
        gump = self._open()

        if not gump:
            return "noGump", []

        # The shard drops the connection for a button the gump does not have
        known = button_ids(gump)

        if known is not None and self._config["combine_button"] not in known:
            self._report("the deed gump has no button %d" % self._config["combine_button"], gump)

            return "noGump", []

        API.ClearJournal()

        if not API.ReplyGump(self._config["combine_button"], gump):
            return "noGump", []

        if not API.WaitForTarget("any", self._config["target_timeout"]):
            self._report("no cursor came up for the combine", gump)
            self._close()

            return "noCursor", []

        API.Target(container)

        outcome, taken = self._read_outcome(offered)

        if outcome is None:
            self._report("nothing readable came back from the combine", gump)

        self._close()

        return outcome, taken
