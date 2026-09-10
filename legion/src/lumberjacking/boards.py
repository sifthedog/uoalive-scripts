import API

from uo.convert import Converter
from uo.entity import hex_of
from uo.journal import forget
from uo.pack import hue_of


class Boards(object):
    """The wood side of the converter: the axe is used and the log stack is the target."""

    def __init__(self, wood, tool, saves, config, log):
        self._wood = wood
        self._tool = tool
        self._config = config
        self._log = log
        self._reported_nothing = False

        self._converter = Converter({
            "noun": "logs",
            "attempts": config["attempts"],
            "passes": config["passes"],
            "delay": config["delay"],
            "timeout": config["timeout"],
            "poll": config["poll"],
            "throttled_text": config["throttled_text"],
            "unskilled_text": config["unskilled_text"],
            "wait_on_save": True,
            "saving_message": "the world is saving, leaving the logs for now",
            "next_source": self._next_log,
            "perform": self._perform,
            "blocked": self._no_axe_in_hand,
            "learn_product": self._learn_board,
            "converted": self._nothing_to_note,
            "nothing_to_do": self._say_nothing_to_convert,
            "about_to_convert": self._converting,
        }, log, saves)

    def _next_log(self, skip):
        for pile in self._wood.log_piles():
            if hue_of(pile) not in skip:
                return pile

        return None

    def _no_axe_in_hand(self):
        return "no axe in hand" if self._tool.serial() is None else None

    # The diff names the real board art, which is why the seed set can be wrong and corrects itself
    # on the first conversion
    def _learn_board(self, gained):
        for graphic, _hue in gained:
            if graphic in self._config["log_graphics"]:
                continue

            if graphic in self._config["board_graphics"]:
                continue

            self._config["board_graphics"].add(graphic)
            self._log("board graphic is %s" % hex_of(graphic))

    # Said once per stretch, not once a cycle: the haul fires at HAUL_BUFFER and stays true for a
    # long run of them
    def _say_nothing_to_convert(self, _written_off):
        piles = self._wood.log_piles()

        if len(piles) > 0 and not self._reported_nothing:
            self._reported_nothing = True
            self._log("nothing to convert in %d log pile(s)" % len(piles))

    # Logs become boards by using the axe and targeting the log stack - the inverse of smelting,
    # where the ore is used and the forge targeted
    def _perform(self, stack):
        serial = self._tool.serial()

        if serial is None:
            return False

        # No cancel unless there is one to cancel: an unconditional cancel shortly before the action
        # leaves the cursor that follows unusable
        if API.HasTarget():
            API.CancelTarget()

        forget(self._config["throttled_text"] + self._config["unskilled_text"])
        API.UseObject(serial)

        if not API.WaitForTarget("any", self._config["target_timeout"]):
            API.CancelTarget()
            self._log("no target cursor for the logs, nothing usable in hand?")

            return False

        # The one-argument overload: an item serial, not the tile form the chop uses
        API.Target(stack.Serial)

        return True

    def _converting(self):
        self._reported_nothing = False

    def _nothing_to_note(self, _gained, _lost):
        pass

    def run(self):
        return self._converter.run()

    # Forced, unlike mining's progress-gated retry: only boards ever go onto an animal, so a log
    # given up on to a lost cursor or a broken axe would ride out the whole run as weight. The
    # verdict is a backstop for one pass, never for the run.
    def make_boards(self):
        self._converter.retry_written_off(True)

        return self._converter.run()
