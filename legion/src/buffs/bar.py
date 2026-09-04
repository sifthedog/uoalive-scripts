import API


class BuffBar(object):
    """ApiBuff never refreshes after it is handed over, so the bar is re-read every time it matters."""

    def __init__(self, log):
        self._log = log
        self._dumped = False

    def standing(self, entry):
        buffs = API.ActiveBuffs()

        if buffs and not self._dumped:
            self._dumped = True
            self._log("buff bar: " + ", ".join("%s/%s" % (b.Type, b.Title or "") for b in buffs))

        for buff in buffs if buffs else []:
            if str(buff.Type) == entry["buff"]:
                return True

            if entry["title"] and entry["title"].lower() in (buff.Title or "").lower():
                return True

        return False


# Either hand: a katana is one-handed and a no-dachi two-handed, and Consecrate Weapon takes both
def armed():
    return API.FindLayer("twohanded") is not None or API.FindLayer("onehanded") is not None
