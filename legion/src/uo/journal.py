import API

from uo.log import STAMPS
from uo.text import any_in


def said(texts):
    for text in texts:
        if API.InJournal(text, False):
            return True

    return False


# A craft's mana coming back gains Meditation and Focus, which buries the one line that matters
SKILL_GAIN_TEXT = ["your skill in", "has changed by"]


# matchingText is left off on purpose: the client only applies it as a regex, so a plain string
# there filters everything out
def journal_tail(seconds, limit):
    try:
        entries = API.GetJournalEntries(seconds)
    except Exception:
        if API.StopRequested:
            raise

        return []

    texts = []

    for entry in entries if entries else []:
        text = getattr(entry, "Text", None)

        if (text and text.strip() and not any_in(text, SKILL_GAIN_TEXT)
                and not any_in(text, STAMPS)):
            texts.append(text.strip())

    return texts[-limit:]


# Line by line rather than the whole journal: a wholesale clear before every swing wiped the ambush
# warning before the threat watch got its once-a-cycle look at it
def forget(phrases):
    for text in phrases:
        API.ClearJournal(text)


def forget_outcomes(buckets):
    for _name, phrases in buckets:
        forget(phrases)


def matched_bucket(buckets):
    for name, phrases in buckets:
        # clearMatches, or a line already read answers the next wait as well
        if API.InJournalAny(phrases, True):
            return name

    return None


def read_outcome(buckets, budget, poll, between=None):
    waited = 0.0

    while not API.StopRequested:
        hit = matched_bucket(buckets)

        if hit is not None:
            return hit

        if waited >= budget:
            return None

        # Between the slices rather than around the wait: a mobile walks while its attempt resolves
        if between is not None:
            between()

        API.Pause(poll)
        waited += poll
