import API

from taming.quarry import is_pet
from uo.entity import find_mobile
from uo.gump import await_changed, gump_says
from uo.menu import context_menu
from uo.retry import settled


# Rename returns nothing, so the new name is polled for - and reissued, because a rename refused for
# an animal the shard has not finished handing over is silent and looks exactly like a slow one
def rename_pet(serial, name, attempts, timeout, poll):
    def answers_to():
        found = find_mobile(serial)

        return found is not None and (found.Name or "").lower() == name.lower()

    for _ in range(attempts):
        if answers_to():
            return "renamed"

        API.Rename(serial, name)

        if settled(timeout, poll, answers_to):
            return "renamed"

    return "unnamed"


class Release(object):
    def __init__(self, config, log):
        self._config = config
        self._log = log
        self._button = None
        self._said_no_gump = False
        self._said_no_button = False

    def _answer_confirm(self, before, button):
        gump = await_changed(before, self._config["confirm_timeout"], self._config["confirm_poll"])

        if not gump:
            if not self._said_no_gump:
                self._said_no_gump = True
                self._log("found no gump to confirm the release with")

            return

        if not self._said_no_button and not gump_says(gump, self._config["confirm_text"]):
            self._said_no_button = True
            self._log("the release gump says none of RELEASE_CONFIRM_TEXT - answering it anyway")

        API.ReplyGump(button, gump)

    def release(self, serial):
        attempts = self._config["attempts"]
        buttons = list(self._config["buttons"]) if self._button is None else [self._button]
        pressed = False
        missing = 0

        for button in buttons * attempts:
            before = API.HasGump()

            if not context_menu(serial, self._config["menu_text"], self._config["context_timeout"]):
                # Better proof than the flag, and free: the entry is on the menu only while it is
                # your pet, so one that has gone since a press means the press worked
                if pressed:
                    return "released"

                # Before any press it means the menu was asked for early - ContextMenu gives up the
                # moment the shard sends a menu without the entry on it
                missing += 1

                if missing >= attempts:
                    return "noEntry"

                API.Pause(self._config["retry_delay"])
                continue

            pressed = True
            self._answer_confirm(before, button)

            if settled(self._config["timeout"], self._config["poll"], lambda: not is_pet(serial)):
                if self._button is None:
                    self._button = button
                    self._log("the release gump answers to button %d" % button)

                return "released"

        # A confirmation nobody answered is modal on some clients, and would refuse the context menu
        # of every animal after this one
        if API.HasGump():
            API.CloseGump()

        return "stillPet" if pressed else "noEntry"


# The cursor the shard raises is left for the player to answer - nothing here targets anything, so
# what the pet attacks is always a human decision
def command_kill(serial, name, config, log):
    if API.HasTarget():
        API.CancelTarget()

    if not context_menu(serial, config["menu_text"], config["context_timeout"]):
        return "noEntry"

    if not API.WaitForTarget("any", config["cursor_timeout"]):
        return "noCursor"

    log("told '%s' to kill - pick its target" % name)

    picked = settled(config["pick_timeout"], config["pick_poll"], lambda: not API.HasTarget())

    return "ordered" if picked else "unanswered"
