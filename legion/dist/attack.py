# Built from src/attack/index.py by build.py - do not edit.

import API


# src/attack/config.py
RANGE = 10

# ServUO appends these to a controlled creature's name line; blue ones never reach the scan
OWNED_PROP_WORDS = ["(tame)", "(summoned)", "(bonded)"]

# Whole seconds NameAndProps may wait for a tooltip the client has not fetched. The API takes an int
OPL_TIMEOUT = 2


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
# Name is empty until the client has been told it, and the tooltip's first line is the name
def label(mobile, props):
    first = props.splitlines()[0].strip() if props else ""

    return first or mobile.Name or hex_of(mobile.Serial)


def owned(props, words):
    low = props.lower()

    return any(word.lower() in low for word in words)


# Chebyshev is the reach, but two mobiles at the same reach draw at very different places on the
# isometric screen, so the one that looks nearest goes first among equals
def nearness(mobile):
    dx = mobile.X - API.Player.X
    dy = mobile.Y - API.Player.Y

    return (mobile.Distance, dx * dx + dy * dy)


def nearest_foe(within, owned_words, opl_timeout):
    """(the mobile, its tooltip) - the tooltip is "" when it never came"""
    found = API.GetAllMobiles(None, within, HOSTILE) or []
    me = API.Player.Serial

    candidates = [
        mobile
        for mobile in sorted(found, key=nearness)
        if mobile.Serial != me
        and not mobile.IsDead
        and not mobile.IsDestroyed
        and not mobile.IsRenamable
    ]

    if candidates:
        API.RequestOPLData([mobile.Serial for mobile in candidates])

    for mobile in candidates:
        props = mobile.NameAndProps(True, opl_timeout) or ""

        if not owned(props, owned_words):
            return mobile, props

    return None, ""


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
def make_log(prefix):
    stamp = prefix + ": "

    def log(message):
        if log.enabled:
            API.SysMsg(stamp + message)

    # The client puts a SysMsg in the journal beside the shard's own lines, so a script reading the
    # journal back needs to know which lines it wrote itself - without this a report of an unreadable
    # outcome quotes the last report of an unreadable outcome. Lowercase, because that is how the
    # journal readers compare. Carried on the function itself rather than a module-level list: a
    # bundle is one script and one prefix, and a shared list would leak between scripts sharing this
    # process, such as the test suite.
    log.stamp = stamp.lower()
    log.enabled = True

    return log


# src/attack/index.py
log = make_log("attack")


def attack():
    if API.HasTarget():
        API.CancelTarget()

    reason = first_reason([dead()])

    if reason is not None:
        return reason

    foe, props = nearest_foe(RANGE, OWNED_PROP_WORDS, OPL_TIMEOUT)

    if foe is None:
        return "nothing hostile within %d tiles" % RANGE

    API.SetWarMode(True)
    API.Attack(foe.Serial)

    ending = "attacking '%s' %s %d tiles off" % (label(foe, props), hex_of(foe.Graphic), foe.Distance)

    return ending if props else ending + " - tooltip never came"


try:
    ending = attack()
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    ending = "threw - %s" % error

log(ending)
API.Stop()
