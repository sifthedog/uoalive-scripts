import API


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
