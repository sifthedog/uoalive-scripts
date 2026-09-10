import API


# HasGump() only ever answers the last gump the shard sent, and a gump the shard re-sends on its own
# steals that slot: the id-addressed calls below do not go through it
def open_ids():
    found = []
    last = API.HasGump()

    if last:
        found.append(last)

    try:
        for gump in API.GetAllGumps() or []:
            serial = getattr(gump, "ServerSerial", 0)

            if serial and serial not in found:
                found.append(serial)
    except Exception:
        if API.StopRequested:
            raise

    return found


def is_open(ident):
    return bool(ident) and bool(API.WaitForGump(ident, 0))


def await_gump(ident, timeout):
    if not ident:
        return 0

    return ident if API.WaitForGump(ident, timeout) else 0


# None is "could not read them", which no caller treats as "none": the shard drops the connection
# for a button the gump does not have, so an unreadable list must not be mistaken for an empty one
def button_ids(ident):
    if not ident:
        return None

    try:
        gump = API.GetGump(ident)

        if gump is None:
            return None

        found = set()

        for control in gump.Children or []:
            button = getattr(control, "ButtonID", None)

            if button is not None:
                found.add(int(button))

        return found
    except Exception:
        if API.StopRequested:
            raise

        return None


# A recognised gump wins; failing that, one that was not up before the use. Returns (id, recognised)
def await_recognised(known, before, timeout, poll):
    waited = 0.0
    newcomer = 0

    while waited < timeout:
        for ident in open_ids():
            if known(ident):
                return ident, True

            if not newcomer and ident not in before:
                newcomer = ident

        if newcomer:
            return newcomer, False

        API.Pause(poll)
        waited += poll

    return 0, False


def await_any(timeout, poll):
    waited = 0.0

    while waited < timeout:
        found = API.HasGump()

        if found:
            return found

        API.Pause(poll)
        waited += poll

    return 0


# The answer is the gump id *changing*. WaitForGump with no id resolves to whatever LastGumpID
# already is, so it answers a stale gump when one is open and times out when none is.
def await_changed(before, timeout, poll):
    waited = 0.0

    while waited < timeout:
        found = API.HasGump()

        if found and found != before:
            return found

        API.Pause(poll)
        waited += poll

    return 0


def gump_says(gump, texts):
    for text in texts:
        if API.GumpContains(text, gump):
            return True

    return False
