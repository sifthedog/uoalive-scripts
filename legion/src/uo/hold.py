import API

WIDTH = 340
HEIGHT = 110


class Hold(object):
    """Standing still behind a gump the script drew, until its button is pressed."""

    def __init__(self, config, log, stop_reason, heartbeat):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason
        self._heartbeat = heartbeat

    def _show(self, on_press):
        gump = API.Gumps.CreateGump(True, True)
        gump.SetRect(0, 0, WIDTH, HEIGHT)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.85, "#1E1E1E")
        background.SetRect(0, 0, WIDTH, HEIGHT)
        gump.Add(background)

        label = API.Gumps.CreateGumpLabel(self._config["text"], self._config["hue"])
        label.SetPos(16, 16)
        gump.Add(label)

        button = API.Gumps.CreateSimpleButton(self._config["button"], 120, 26)
        button.SetPos(16, HEIGHT - 42)
        API.Gumps.AddControlOnClick(button, on_press)
        gump.Add(button)

        API.Gumps.AddGump(gump)

        return gump

    # each() runs once a slice, so the caller's alarm can keep restarting while the gump is up
    def wait(self, each):
        if API.Pathfinding():
            API.CancelPathfinding()

        if API.HasTarget():
            API.CancelTarget()

        pressed = [False]

        def on_press():
            pressed[0] = True

        gump = self._show(on_press)
        self._log("holding - %s" % self._config["text"])
        why = None

        # The click only arrives through ProcessCallbacks, and a stopped script's client calls all
        # answer with nothing, so the stop flag is the one read that still means something then
        while why is None:
            if API.StopRequested:
                why = "the run is being stopped"
                break

            each()
            API.ProcessCallbacks()

            if pressed[0]:
                why = "the button was pressed"
            elif gump.IsDisposed:
                why = "the gump was closed"
            elif self._stop_reason() is not None:
                why = "the run has a reason to stop"
            else:
                API.Pause(self._config["poll"])

        if not gump.IsDisposed:
            gump.Dispose()

        self._heartbeat.reset()
        self._log("%s, carrying on" % why)

        return why in ("the button was pressed", "the gump was closed")
