import API

from uo.gumpwait import wait_for_gump
from uo.setup import RADIO_CHAR, RADIO_GAP

PROMPT_WIDTH = 340
PROMPT_HEIGHT = 178
PROMPT_BUTTON_HEIGHT = 26
PROMPT_BOX_WIDTH = 60
RADIO_LABEL_Y = 16
RADIO_ROW_Y = 40
COUNT_LABEL_Y = 74
COUNT_BOX_Y = 100


class StartPrompt(object):
    """Asked once, before the loop: which assembly to make, and how many. None means do not start."""

    def __init__(self, config, log, stop_reason):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason
        self._radios = []

    # A blank, zero, negative or non-numeric box answers the default rather than refusing to start
    def _count(self, box):
        text = (box.Text or "").strip()

        return int(text) if text.isdigit() and int(text) > 0 else self._config["default"]

    # None until something has actually clicked one: a radio's isChecked at creation is not always
    # something GetIsChecked reflects back
    def _checked(self):
        options = self._config["options"]

        for index in range(len(self._radios)):
            if self._radios[index].GetIsChecked():
                return options[index][0]

        return None

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
        label.SetPos(16, RADIO_LABEL_Y)
        gump.Add(label)

        options = self._config["options"]
        default = self._config["assembly_default"]
        x = 16

        # Spaced by caption: the classic font runs about RADIO_CHAR pixels a letter
        for index in range(len(options)):
            key, caption = options[index]
            radio = API.Gumps.CreateGumpRadioButton(caption, 1, 0x00D0, 0x00D1,
                                                    self._config["hue"], key == default)
            radio.SetPos(x, RADIO_ROW_Y)
            gump.Add(radio)
            self._radios.append(radio)
            x += RADIO_GAP + RADIO_CHAR * len(caption)

        count_label = API.Gumps.CreateGumpLabel(self._config["count_text"], self._config["hue"])
        count_label.SetPos(16, COUNT_LABEL_Y)
        gump.Add(count_label)

        box = API.Gumps.CreateGumpTextBox(str(self._config["default"]), PROMPT_BOX_WIDTH,
                                          PROMPT_BUTTON_HEIGHT, False, 20)
        box.SetPos(16, COUNT_BOX_Y)
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
        answers = {"assembly": self._config["assembly_default"], "wanted": self._config["default"]}
        gump, box = self._show(lambda button: pressed.__setitem__(0, button))

        if gump is None:
            self._log("not asking - the run is being stopped")

            return None

        self._log("asking - %s" % self._config["text"])

        # Read every slice, not once at the end: wait_for_gump disposes the gump before returning
        # and a disposed radio reports nothing checked, which read as the default and sent a clock
        # run down the potion keg rows
        def resolve():
            checked = self._checked()

            if checked is not None:
                answers["assembly"] = checked

            answers["wanted"] = self._count(box)

            return pressed[0]

        why = wait_for_gump(gump, self._stop_reason, self._config["poll"], resolve,
                            closed_message="cancel")

        if why != "ok":
            self._log(why)

            return None

        return answers
