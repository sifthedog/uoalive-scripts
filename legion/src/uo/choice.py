import API

CHOICE_WIDTH = 340
CHOICE_BUTTON_WIDTH = 96
CHOICE_BUTTON_HEIGHT = 26
CHOICE_GAP = 8


class Choice(object):
    """A gump the script draws with one button per option, answered by the first press."""

    def __init__(self, config, log, stop_reason):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason

    def _show(self, options, on_press):
        height = 16 + 20 + 16 + CHOICE_BUTTON_HEIGHT + 16
        width = max(CHOICE_WIDTH, 16 + len(options) * (CHOICE_BUTTON_WIDTH + CHOICE_GAP) + 8)

        gump = API.Gumps.CreateGump(True, True)
        gump.SetRect(0, 0, width, height)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.85, "#1E1E1E")
        background.SetRect(0, 0, width, height)
        gump.Add(background)

        label = API.Gumps.CreateGumpLabel(self._config["text"], self._config["hue"])
        label.SetPos(16, 16)
        gump.Add(label)

        for index in range(len(options)):
            key, caption = options[index]
            button = API.Gumps.CreateSimpleButton(caption, CHOICE_BUTTON_WIDTH,
                                                  CHOICE_BUTTON_HEIGHT)
            button.SetPos(16 + index * (CHOICE_BUTTON_WIDTH + CHOICE_GAP),
                          height - CHOICE_BUTTON_HEIGHT - 16)
            API.Gumps.AddControlOnClick(button, self._presser(key, on_press))
            gump.Add(button)

        API.Gumps.AddGump(gump)

        return gump

    # A closure per button rather than one in the loop: the loop variable would be the last key
    def _presser(self, key, on_press):
        def press():
            on_press(key)

        return press

    # The pressed key, or None when the gump was closed, timed out, or the run has a reason to stop
    def ask(self, options):
        if API.HasTarget():
            API.CancelTarget()

        chosen = [None]

        def on_press(key):
            chosen[0] = key

        gump = self._show(options, on_press)
        self._log("asking - %s" % self._config["text"])
        waited = 0.0
        why = None

        # The click only arrives through ProcessCallbacks, and a stopped script's client calls all
        # answer with nothing, so the stop flag is the one read that still means something then
        while why is None:
            if API.StopRequested:
                why = "the run is being stopped"
                break

            API.ProcessCallbacks()

            if chosen[0] is not None:
                why = "'%s' was pressed" % dict(options)[chosen[0]]
            elif gump.IsDisposed:
                why = "the gump was closed"
            elif self._stop_reason() is not None:
                why = "the run has a reason to stop"
            elif waited >= self._config["timeout"]:
                why = "nothing was pressed in %.0fs" % self._config["timeout"]
            else:
                API.Pause(self._config["poll"])
                waited += self._config["poll"]

        if not gump.IsDisposed:
            gump.Dispose()

        self._log(why)

        return chosen[0]
