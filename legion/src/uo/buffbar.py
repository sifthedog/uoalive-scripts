import API


class BuffBar(object):
    """ApiBuff never refreshes after it is handed over, so the bar is re-read every time it matters."""

    def __init__(self, log):
        self._log = log
        self._dumped = False

    def active(self):
        buffs = API.ActiveBuffs()

        if not buffs:
            return []

        if not self._dumped:
            self._dumped = True
            self._log("buff bar: " + ", ".join("%s/%s" % (b.Type, b.Title or "") for b in buffs))

        return buffs

    # title is the localized fallback for a shard whose BuffIconType member name does not match
    def standing(self, kind, title=None):
        if not kind:
            return False

        for buff in self.active():
            if str(buff.Type) == kind:
                return True

            if title and title.lower() in (buff.Title or "").lower():
                return True

        return False
