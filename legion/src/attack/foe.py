import API

from uo.notoriety import HOSTILE


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
