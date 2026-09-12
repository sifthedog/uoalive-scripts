import API

from uo.text import clipped

WIDTH = 720
MARGIN = 16
LABEL_X = 16
FIELD_X = 160
VALUE_X = 316
ROW = 28
LINE = 22
TITLE_HEIGHT = 40
BUTTON_HEIGHT = 24
FONT = 15
MAX_SOURCE_LINES = 4
LINE_CHARS = 92
RADIO_CHAR = 8
RADIO_GAP = 40

TEXT = "#E6E6E6"
MUTED = "#8C8C8C"
CURRENT = "#F2C14E"
WARN = "#FF7B6B"


class Setup(object):
    """The form the run is set up on: tools, wood sources, what is made, and the band table."""

    def __init__(self, config, log, stop_reason):
        self._config = config
        self._log = log
        self._stop_reason = stop_reason
        self._pending = None
        self._sources = []
        self._tools_line = None
        self._unload_line = None
        self._message = None
        self._controls = {}

    def _presser(self, key):
        def press():
            self._pending = key

        return press

    def _label(self, gump, text, x, y, color=TEXT, width=None):
        label = API.Gumps.CreateGumpTTFLabel(text, FONT, color)
        label.SetRect(x, y, width if width is not None else WIDTH - x - MARGIN, LINE)
        gump.Add(label)

        return label

    def _button(self, gump, key, caption, x, y, width):
        button = API.Gumps.CreateSimpleButton(caption, width, BUTTON_HEIGHT)
        button.SetPos(x, y)
        API.Gumps.AddControlOnClick(button, self._presser(key))
        gump.Add(button)

        return button

    def _show(self, heading, rows):
        outputs = self._config["outputs"]
        height = (TITLE_HEIGHT + ROW * 2 + ROW + LINE * MAX_SOURCE_LINES + ROW * 2
                  + LINE * (len(rows) + 1) + ROW + BUTTON_HEIGHT + MARGIN * 4)

        gump = API.Gumps.CreateGump(True, True)

        if gump is None:
            return None

        gump.SetRect(0, 0, WIDTH, height)
        gump.CenterXInViewPort()
        gump.CenterYInViewPort()

        background = API.Gumps.CreateGumpColorBox(0.9, "#1E1E1E")
        background.SetRect(0, 0, WIDTH, height)
        gump.Add(background)

        title = API.Gumps.CreateGumpLabel(self._config["title"], self._config["hue"])
        title.SetPos(MARGIN, 12)
        gump.Add(title)

        y = TITLE_HEIGHT
        c = self._controls

        self._label(gump, self._config["tool_noun"].capitalize(), LABEL_X, y)
        self._label(gump, "When they run out:", FIELD_X, y, MUTED, 150)
        c["modes"] = API.Gumps.CreateDropDown(200, [caption for _key, caption in
                                                    self._config["tool_modes"]], 0)
        c["modes"].SetPos(VALUE_X, y - 2)
        gump.Add(c["modes"])
        y += ROW

        c["tools_button"] = self._button(gump, "tools", "Pick tool container", FIELD_X, y, 148)
        c["tools_value"] = self._label(gump, "", VALUE_X, y + 3, MUTED)
        y += ROW + MARGIN // 2

        self._label(gump, "Wood", LABEL_X, y)
        self._button(gump, "source", "Add a source", FIELD_X, y, 140)
        self._button(gump, "clear", "Clear", FIELD_X + 148, y, 70)
        y += ROW

        c["sources"] = []

        for index in range(MAX_SOURCE_LINES):
            c["sources"].append(self._label(gump, "", FIELD_X, y + index * LINE, MUTED))

        y += LINE * MAX_SOURCE_LINES + MARGIN // 2

        self._label(gump, "What is made", LABEL_X, y)
        c["outputs"] = []

        x = FIELD_X

        # Spaced by caption: the classic font runs about RADIO_CHAR pixels a letter
        for index in range(len(outputs)):
            radio = API.Gumps.CreateGumpRadioButton(outputs[index][1], 1, 0x00D0, 0x00D1,
                                                    self._config["hue"], index == 0)
            radio.SetPos(x, y)
            gump.Add(radio)
            c["outputs"].append(radio)
            x += RADIO_GAP + RADIO_CHAR * len(outputs[index][1])

        y += ROW

        c["unload_button"] = self._button(gump, "unload", "Pick container", FIELD_X, y, 148)
        c["unload_value"] = self._label(gump, "", VALUE_X, y + 3, MUTED)
        y += ROW + MARGIN // 2

        self._label(gump, "Training", LABEL_X, y)
        self._label(gump, heading, FIELD_X, y)
        y += LINE

        for text, current in rows:
            self._label(gump, ("> " if current else "   ") + text, FIELD_X, y,
                        CURRENT if current else MUTED)
            y += LINE

        y += MARGIN // 2
        c["message"] = self._label(gump, "", LABEL_X, y, WARN)
        y += ROW

        self._button(gump, "cancel", "Cancel", WIDTH - MARGIN - 96 - 8 - 96, y, 96)
        self._button(gump, "ok", "OK", WIDTH - MARGIN - 96, y, 96)

        API.Gumps.AddGump(gump)

        return gump

    def _mode(self):
        return self._config["tool_modes"][self._controls["modes"].GetSelectedIndex()][0]

    def _output(self):
        for index in range(len(self._controls["outputs"])):
            if self._controls["outputs"][index].GetIsChecked():
                return self._config["outputs"][index][0]

        return self._config["outputs"][0][0]

    def _say(self, message):
        self._message = message
        self._controls["message"].SetText(message or "")

    def _refresh(self, actions):
        c = self._controls
        fetching = self._mode() == "fetch"
        c["tools_button"].IsVisible = fetching
        c["tools_value"].IsVisible = fetching
        c["tools_value"].SetText(clipped(self._tools_line or "required", LINE_CHARS))

        for index in range(MAX_SOURCE_LINES):
            if index < len(self._sources):
                c["sources"][index].SetText(clipped(self._sources[index], LINE_CHARS))
            elif index == 0:
                c["sources"][0].SetText("nothing picked - the run works through the wood you carry")
            else:
                c["sources"][index].SetText("")

        output = self._output()
        unsold = output == "sell" and actions["unsold_ahead"] is not None \
            and actions["unsold_ahead"]()
        showing = output == "unload" or unsold
        c["unload_button"].IsVisible = showing
        c["unload_value"].IsVisible = showing

        if self._unload_line is not None:
            c["unload_value"].SetText(clipped(self._unload_line, LINE_CHARS))
        else:
            c["unload_value"].SetText(self._config["unsold_hint"] if unsold else "required")

    def _validate(self, actions):
        if self._mode() == "fetch" and not actions["tools_ready"]():
            return ("pick a container holding %s, or choose to stop when they run out"
                    % self._config["tool_noun"])

        if self._output() == "unload" and not actions["unload_ready"]():
            return "pick the container to unload into"

        if len(self._sources) == 0 and not actions["has_wood"]():
            return "add a source of wood, or carry some"

        return None

    def _run(self, pending, actions):
        if pending == "source":
            if len(self._sources) >= MAX_SOURCE_LINES:
                self._say("that is as many sources as the form lists - clear them to start over")

                return None

            self._log("target a chest, a storage box or a pack animal holding wood")
            line, refusal = actions["source"]()

            if line is not None:
                self._sources.append(line)

            self._say(refusal)
        elif pending == "clear":
            actions["clear"]()
            del self._sources[:]
            self._say(None)
        elif pending == "tools":
            self._log("target the container holding %s" % self._config["tool_noun"])
            line, refusal = actions["tools"]()

            if line is not None:
                self._tools_line = line

            self._say(refusal)
        elif pending == "unload":
            self._log("target the container to unload into, a trash barrel or a chest")
            line, refusal = actions["unload"]()

            if line is not None:
                self._unload_line = line

            self._say(refusal)
        elif pending == "ok":
            failure = self._validate(actions)
            self._say(failure)

            return "ok" if failure is None else None
        elif pending == "cancel":
            return "cancel"

        return None

    def ask(self, actions):
        if API.HasTarget():
            API.CancelTarget()

        heading, rows = actions["table"]()
        gump = self._show(heading, rows)

        # API.Stop() only lands at the next Pause, and every client call before it answers nothing
        if gump is None:
            self._log("not asking - the run is being stopped")

            return None

        self._log("asking - the start-up form")
        self._refresh(actions)
        waited = 0.0
        why = None
        answers = None

        # The click only arrives through ProcessCallbacks, and a stopped script's client calls all
        # answer with nothing, so the stop flag is the one read that still means something then
        while why is None:
            if API.StopRequested:
                why = "the run is being stopped"
                break

            API.ProcessCallbacks()

            pending, self._pending = self._pending, None
            done = self._run(pending, actions) if pending is not None else None

            self._refresh(actions)

            if done == "ok":
                answers = {"tools": self._mode(), "output": self._output(),
                           "sources": len(self._sources)}
                why = "OK was pressed"
            elif done == "cancel":
                why = "Cancel was pressed"
            elif gump.IsDisposed:
                why = "the form was closed"
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

        return answers
