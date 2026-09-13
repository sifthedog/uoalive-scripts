import API

from uo.entity import player
from uo.text import any_in


def said(texts):
    for text in texts:
        if API.InJournal(text, False):
            return True

    return False


# A craft's mana coming back gains Meditation and Focus, which buries the one line that matters
SKILL_GAIN_TEXT = ["your skill in", "has changed by"]


# What the shard itself speaks under - anything else in the journal is a mobile in earshot
SHARD_SPEAKERS = ["", "system"]


# matchingText is left off on purpose: the client only applies it as a regex, so a plain string
# there filters everything out
def journal_entries(seconds, stamp=None):
    try:
        entries = API.GetJournalEntries(seconds)
    except Exception:
        if API.StopRequested:
            raise

        return []

    kept = []
    stamps = [stamp] if stamp else []

    for entry in entries if entries else []:
        text = getattr(entry, "Text", None)

        if (text and text.strip() and not any_in(text, SKILL_GAIN_TEXT)
                and not any_in(text, stamps)):
            kept.append(((getattr(entry, "Name", None) or "").strip(), text.strip()))

    return kept


# The text alone: fishing reads the catch off the end of the line it returns
def journal_tail(seconds, limit, stamp=None):
    return [text for _name, text in journal_entries(seconds, stamp)][-limit:]


# What the shard said is preferred rather than kept alone: a chatty NPC used to fill the whole tail
# and evict the line a craft was reported on, but a shard answering under some other name still has
# to reach the report. shard_first off keeps every speaker, which is what the notes file wants.
def journal_report(seconds, limit, stamp=None, shard_first=True):
    entries = journal_entries(seconds, stamp)
    me = player()
    speakers = SHARD_SPEAKERS + [(getattr(me, "Name", "") or "").strip().lower()]
    theirs = [pair for pair in entries if pair[0].lower() in speakers]
    shown = (theirs or entries) if shard_first else entries

    if limit is not None:
        shown = shown[-limit:]

    return [text if name.lower() in speakers else "%s: %s" % (name, text)
            for name, text in shown]


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
