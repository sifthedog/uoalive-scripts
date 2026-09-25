import API

from uo.entity import hex_of
from uo.notoriety import HOSTILE


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
