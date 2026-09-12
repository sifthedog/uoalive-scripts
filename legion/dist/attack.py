# Built from src/attack/index.py by build.py - do not edit.

import API


# src/attack/config.py
RANGE = 10

# ServUO appends these to a controlled creature's name line; blue ones never reach the scan
OWNED_PROP_WORDS = ["(tame)", "(summoned)", "(bonded)"]

# Whole seconds NameAndProps may wait for a tooltip the client has not fetched. The API takes an int
OPL_TIMEOUT = 1


# src/uo/notoriety.py
"""Passed through to the scans, never compared or OR-ed: the API.py stub lists every value as 1."""

# Innocent is out, or every blue NPC in the world is trouble
HOSTILE = [
    API.Notoriety.Gray,
    API.Notoriety.Criminal,
    API.Notoriety.Enemy,
    API.Notoriety.Murderer,
]


# src/attack/foe.py
def owned(mobile, words, opl_timeout):
    props = (mobile.NameAndProps(True, opl_timeout) or "").lower()

    return any(word.lower() in props for word in words)


def nearest_foe(within, owned_words, opl_timeout):
    found = API.GetAllMobiles(None, within, HOSTILE) or []
    me = API.Player.Serial

    candidates = [
        mobile
        for mobile in sorted(found, key=lambda mobile: mobile.Distance)
        if mobile.Serial != me
        and not mobile.IsDead
        and not mobile.IsDestroyed
        and not mobile.IsRenamable
    ]

    # The tooltip is a fetch, so only the ones in line for the attack are asked
    for mobile in candidates:
        if not owned(mobile, owned_words, opl_timeout):
            return mobile

    return None


# src/uo/entity.py
# API.Player is None whenever the client is between world states - a recall, a server line change,
# the moment around a death - and reading through it threw a live restock away
def player():
    try:
        return API.Player
    except Exception:
        if API.StopRequested:
            raise

        return None


def hex_of(value):
    return "0x%x" % (value & 0xFFFFFFFF)


# src/uo/guards.py
def first_reason(clauses):
    for clause in clauses:
        reason = clause()

        if reason is not None:
            return reason

    return None


def dead():
    def clause():
        me = player()

        return "you are dead" if me is not None and me.IsDead else None

    return clause


# src/uo/log.py
# Every stamp make_log has handed out. The client puts a SysMsg in the journal beside the shard's
# own lines, so a script reading the journal back needs to know which of them it wrote itself -
# without this a report of an unreadable outcome quotes the last report of an unreadable outcome.
# Lowercase, because that is how the journal readers compare. One entry per script in practice.
STAMPS = []


def make_log(prefix):
    stamp = prefix + ": "

    if stamp.lower() not in STAMPS:
        STAMPS.append(stamp.lower())

    def log(message):
        API.SysMsg(stamp + message)

    return log


# src/attack/index.py
log = make_log("attack")


def attack():
    if API.HasTarget():
        API.CancelTarget()

    reason = first_reason([dead()])

    if reason is not None:
        return reason

    foe = nearest_foe(RANGE, OWNED_PROP_WORDS, OPL_TIMEOUT)

    if foe is None:
        return "nothing hostile within %d tiles" % RANGE

    API.SetWarMode(True)
    API.Attack(foe.Serial)

    return "attacking '%s' %s %d tiles off" % (foe.Name or "?", hex_of(foe.Graphic), foe.Distance)


try:
    ending = attack()
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    ending = "threw - %s" % error

log(ending)
API.Stop()
