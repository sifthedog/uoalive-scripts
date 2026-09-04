import API


# For a menu whose pages all share one type id: HasGump answers the gump's *type*, and ReplyGump
# disposes the gump it answers before the shard sends the next page, so the wait is for the menu to
# be back rather than for a different id
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
