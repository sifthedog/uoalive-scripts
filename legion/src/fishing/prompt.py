import API

from uo.gumpwait import wait_for_gump

PROMPT_WIDTH = 320
PROMPT_HEIGHT = 110
PROMPT_BUTTON_HEIGHT = 26
PROMPT_BOX_WIDTH = 60


class TilesAheadPrompt(object):
    """Asked once, before the loop starts: how many tiles ahead of your facing to cast at."""

    def __init__(self, config, log, stop_reason):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason

    # A blank, zero, negative or non-numeric box answers the default rather than refusing to start
    def _reading(self, box):
        text = (box.Text or "").strip()

        return int(text) if text.isdigit() and int(text) > 0 else self._config["default"]

    def _show(self, on_press):
        gump = API.Gumps.CreateGump(True, True)

        if gump is None:
            return None, None

        gump.SetRect(0, 0, PROMPT_WIDTH, PROMPT_HEIGHT)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.85, "#1E1E1E")
        background.SetRect(0, 0, PROMPT_WIDTH, PROMPT_HEIGHT)
        gump.Add(background)

        label = API.Gumps.CreateGumpLabel(self._config["text"], self._config["hue"])
        label.SetPos(16, 16)
        gump.Add(label)

        box = API.Gumps.CreateGumpTextBox(str(self._config["default"]), PROMPT_BOX_WIDTH,
                                          PROMPT_BUTTON_HEIGHT, False, 20)
        box.SetPos(16, 46)
        gump.Add(box)

        ok = API.Gumps.CreateSimpleButton("OK", 90, PROMPT_BUTTON_HEIGHT)
        ok.SetPos(16, PROMPT_HEIGHT - 42)
        API.Gumps.AddControlOnClick(ok, lambda: on_press("ok"))
        gump.Add(ok)

        cancel = API.Gumps.CreateSimpleButton("Cancel", 90, PROMPT_BUTTON_HEIGHT)
        cancel.SetPos(114, PROMPT_HEIGHT - 42)
        API.Gumps.AddControlOnClick(cancel, lambda: on_press("cancel"))
        gump.Add(cancel)

        API.Gumps.AddGump(gump)

        return gump, box

    def ask(self):
        pressed = [None]
        gump, box = self._show(lambda button: pressed.__setitem__(0, button))

        if gump is None:
            self._log("not asking - the run is being stopped")

            return self._config["default"]

        self._log("asking - how many tiles ahead to cast at")

        def resolve():
            return pressed[0]

        # A gump closed by hand and a Cancel press read the same: both take the default
        why = wait_for_gump(gump, self._stop_reason, self._config["poll"], resolve,
                            closed_message="cancel")
        value = self._reading(box) if why == "ok" else self._config["default"]

        self._log("%s, casting %d tiles ahead" % (why, value))

        return value
