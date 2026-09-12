import API


# Waits behind a gump the script drew, one poll slice at a time, until resolve() answers a reason
# to stop (checked first, so a click wins over the gump closing), the gump is disposed, stop_reason
# gives one, or timeout seconds pass - timeout=None means no ceiling. each(), when given, runs once
# a slice before resolve(), so an alarm or a heartbeat keeps going while the gump is up. Disposes
# the gump before returning why. The click only arrives through ProcessCallbacks, and a stopped
# script's client calls all answer with nothing, so the stop flag is the one read that still means
# something then.
def wait_for_gump(gump, stop_reason, poll, resolve, closed_message="the gump was closed",
                  timeout=None, each=None):
    waited = 0.0
    why = None

    while why is None:
        if API.StopRequested:
            why = "the run is being stopped"
            break

        if each is not None:
            each()

        API.ProcessCallbacks()

        why = resolve()

        if why is not None:
            pass
        elif gump.IsDisposed:
            why = closed_message
        elif stop_reason() is not None:
            why = "the run has a reason to stop"
        elif timeout is not None and waited >= timeout:
            why = "nothing was pressed in %.0fs" % timeout
        else:
            API.Pause(poll)
            waited += poll

    if not gump.IsDisposed:
        gump.Dispose()

    return why
