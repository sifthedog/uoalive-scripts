import API

from uo.text import words_of

COMMAND = "[SkillGainMode"
PROMPT = "skill gain path is"
PATHS = ("Modern", "Legacy", "Perilous")


def _named(text):
    low = (text or "").lower()
    at = low.find(PROMPT)

    if at < 0:
        return None

    words = words_of(text[at + len(PROMPT):])

    for path in PATHS:
        if path.lower() in words:
            return path

    return None


# Sent once per run, ahead of the loop that records attempts: the client answers "Your skill gain
# path is Modern. This character's ..." and every recorded row carries whichever of Modern, Legacy
# or Perilous follows.
def read_gain_path(budget, poll, log):
    API.Msg(COMMAND)

    waited = 0.0

    while not API.StopRequested:
        for entry in API.GetJournalEntries(budget + poll) or []:
            path = _named(getattr(entry, "Text", None))

            if path is not None:
                return path

        if waited >= budget:
            log("no skill gain path reported - recording without one")
            return None

        API.Pause(poll)
        waited += poll

    return None
