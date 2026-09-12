import API

from uo.gumpwait import wait_for_gump
from uo.setup import RADIO_CHAR, RADIO_GAP

PROMPT_WIDTH = 380
PROMPT_HEIGHT = 202
PROMPT_BUTTON_HEIGHT = 26
PROMPT_BOX_WIDTH = 60
RADIO_ROW_Y = 16
TILES_LABEL_Y = 62
TILES_BOX_Y = 92
DEBUG_LOGS_Y = 126


class StartPrompt(object):
    """Asked once, before the loop starts: how many tiles ahead to cast, and what to do with a
    junk catch (fish, boots, sandals, shoes, thigh boots) - a container, the pack, or the ground."""

    def __init__(self, config, log, stop_reason):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason
        self._radios = []

    # A blank, zero, negative or non-numeric box answers the default rather than refusing to start
    def _tiles_ahead(self, box):
        text = (box.Text or "").strip()

        return int(text) if text.isdigit() and int(text) > 0 else self._config["tiles_default"]

    # Falls back to catch_default, not the first option - a radio's isChecked at creation is not
    # always something GetIsChecked reflects back until something has actually clicked one
    def _catch_mode(self):
        options = self._config["catch_options"]

        for index in range(len(self._radios)):
            if self._radios[index].GetIsChecked():
                return options[index][0]

        return self._config["catch_default"]

    def _debug_logs(self, checkbox):
        return checkbox.GetIsChecked()

    def _show(self, on_press):
        gump = API.Gumps.CreateGump(True, True)

        if gump is None:
            return None, None, None

        gump.SetRect(0, 0, PROMPT_WIDTH, PROMPT_HEIGHT)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.85, "#1E1E1E")
        background.SetRect(0, 0, PROMPT_WIDTH, PROMPT_HEIGHT)
        gump.Add(background)

        catch_label = API.Gumps.CreateGumpLabel(self._config["catch_text"],
                                                self._config["catch_hue"])
        catch_label.SetPos(16, RADIO_ROW_Y)
        gump.Add(catch_label)

        options = self._config["catch_options"]
        default = self._config["catch_default"]
        x = 16

        # Spaced by caption: the classic font runs about RADIO_CHAR pixels a letter
        for index in range(len(options)):
            key, caption = options[index]
            radio = API.Gumps.CreateGumpRadioButton(caption, 1, 0x00D0, 0x00D1,
                                                     self._config["catch_hue"], key == default)
            radio.SetPos(x, RADIO_ROW_Y + 24)
            gump.Add(radio)
            self._radios.append(radio)
            x += RADIO_GAP + RADIO_CHAR * len(caption)

        label = API.Gumps.CreateGumpLabel(self._config["tiles_text"], self._config["tiles_hue"])
        label.SetPos(16, TILES_LABEL_Y)
        gump.Add(label)

        box = API.Gumps.CreateGumpTextBox(str(self._config["tiles_default"]), PROMPT_BOX_WIDTH,
                                          PROMPT_BUTTON_HEIGHT, False, 20)
        box.SetPos(16, TILES_BOX_Y)
        gump.Add(box)

        checkbox = API.Gumps.CreateGumpCheckbox("Debug logs", self._config["tiles_hue"], True)
        checkbox.SetPos(16, DEBUG_LOGS_Y)
        gump.Add(checkbox)

        ok = API.Gumps.CreateSimpleButton("OK", 90, PROMPT_BUTTON_HEIGHT)
        ok.SetPos(16, PROMPT_HEIGHT - 42)
        API.Gumps.AddControlOnClick(ok, lambda: on_press("ok"))
        gump.Add(ok)

        cancel = API.Gumps.CreateSimpleButton("Cancel", 90, PROMPT_BUTTON_HEIGHT)
        cancel.SetPos(114, PROMPT_HEIGHT - 42)
        API.Gumps.AddControlOnClick(cancel, lambda: on_press("cancel"))
        gump.Add(cancel)

        API.Gumps.AddGump(gump)

        return gump, box, checkbox

    def ask(self):
        defaults = {"tiles_ahead": self._config["tiles_default"],
                    "catch_mode": self._config["catch_default"],
                    "debug_logs": True}
        pressed = [None]
        gump, box, checkbox = self._show(lambda button: pressed.__setitem__(0, button))

        if gump is None:
            self._log("not asking - the run is being stopped")

            return defaults

        self._log("asking - %s / %s" % (self._config["tiles_text"], self._config["catch_text"]))

        def resolve():
            return pressed[0]

        # A gump closed by hand and a Cancel press read the same: both take the defaults
        why = wait_for_gump(gump, self._stop_reason, self._config["poll"], resolve,
                            closed_message="cancel")
        answers = ({"tiles_ahead": self._tiles_ahead(box), "catch_mode": self._catch_mode(),
                    "debug_logs": self._debug_logs(checkbox)}
                  if why == "ok" else defaults)

        self._log("%s, casting %d tiles ahead, junk catches: %s"
                  % (why, answers["tiles_ahead"], answers["catch_mode"]))

        return answers
